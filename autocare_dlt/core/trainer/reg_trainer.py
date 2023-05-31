import os
import sys
from collections import defaultdict

import numpy as np
import torch
from loguru import logger

from autocare_dlt.core.dataset.utils import (
    DataIterator,
    reg_eval,
)
from autocare_dlt.core.model.utils.functions import is_parallel
from autocare_dlt.core.trainer import BaseTrainer
from autocare_dlt.core.utils.functions import check_gpu_availability


class RegressionTrainer(BaseTrainer):
    def __init__(self, model, datasets, cfg):

        super().__init__(model, datasets, cfg)

        # === Trainer Configs ===#

        self.classes = self.cfg.classes
        self.metrics = self.cfg.get("eval_metrics", ["mae", "mse", "rmse"])

        # === Values ===#
        self.best_score = 9999999

    def _get_dataloader(self):
        def collate_fn(datas):
            imgs, labels = zip(*datas)
            return torch.stack(imgs), torch.stack(labels).transpose(0, 1)

        data_cfg = self.cfg.data
        if self.datasets.get("train", False):
            self.train_dataset = self.datasets["train"]
            self.train_dataloader = torch.utils.data.DataLoader(
                self.train_dataset,
                batch_size=data_cfg.batch_size_per_gpu,
                num_workers=data_cfg.workers_per_gpu * self.num_gpus,
                shuffle=True,
                pin_memory=True,
                collate_fn=collate_fn,
            )
        if self.datasets.get("val", False):
            self.val_dataset = self.datasets["val"]
            self.val_dataloader = torch.utils.data.DataLoader(
                self.val_dataset,
                batch_size=data_cfg.batch_size_per_gpu,
                num_workers=data_cfg.workers_per_gpu,
                shuffle=False,
                pin_memory=True,
                collate_fn=collate_fn,
            )
        if self.datasets.get("test", False):
            self.test_dataset = self.datasets["test"]
            self.test_dataloader = torch.utils.data.DataLoader(
                self.test_dataset,
                batch_size=data_cfg.batch_size_per_gpu,
                num_workers=data_cfg.workers_per_gpu,
                shuffle=False,
                pin_memory=True,
                collate_fn=collate_fn,
            )

    def before_iter(self):
        self.update_lr(self.progress_in_iter())

    def run_iter(self):
        loss = 0

        labeled_inputs, labeled_targets = self.labeled_iter()
        if torch.cuda.is_available():
            labeled_inputs = labeled_inputs.cuda()
            labeled_targets = labeled_targets.cuda()

        sup_outputs = self.model(labeled_inputs)

        # loss
        sup_loss_dict = defaultdict(
            lambda: torch.tensor(0.0, device=labeled_inputs.device)
        )
        for loss_name, loss_fn in self.loss_fn.items():
            for output, target in zip(sup_outputs, labeled_targets):
                sup_loss_dict[loss_name] += loss_fn(output, target)
        loss = sum(sup_loss_dict.values())
        self.loss_aver.update(loss)

        # Backward
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # mae
        for output, target in zip(sup_outputs, labeled_targets):
            self.acc_aver.update(
                reg_eval(output.detach().cpu(), target.detach().cpu())["mae"]
            )

        # log
        if self.iter % 100 == 0 or self.iter == 1:
            log_str = f"epoch {self.epoch}/{self.max_epoch} [{self.iter}/{self.iters_per_epoch}] - lr: {self.lr:0.6f} loss: {self.loss_aver.avg:.6f} acc: {self.acc_aver.avg:.6f} "
            for loss_name, loss_value in sup_loss_dict.items():
                log_str += f"{loss_name}: {loss_value.item():.6f} "
            logger.info(log_str)

        if self.ema:
            self.ema_model.update(self.model)

    def after_iter(self):
        pass

    def before_train(self):

        self._get_dataloader()
        self.labeled_iter = DataIterator(self.train_dataloader)
        self.iters_per_epoch = self.cfg.get(
            "iters_per_epoch", len(self.train_dataloader)
        )

        # TODO: temporal functions, not pretty
        if self.cfg.ema:
            from autocare_dlt.core.model.utils.ema import ModelEMA

            self.burn_in_iters = (
                len(self.train_dataloader) * self.cfg.ema_cfg.burn_in_epoch
            )
            self.ema_model = ModelEMA(
                self.model,
                decay=self.cfg.ema_cfg.decay,
                max_iter=self.burn_in_iters,
            )
        if self.distributed:
            self.model = self.model.to(self.rank)

        self._get_optimizer()
        self._get_loss_fn()

        self.resume_train()

        self._get_lr_scheduler(self.start_lr, self.iters_per_epoch)

        # === GPU memory availability check === #
        gpu_availability = check_gpu_availability(
            model=self.model,
            input_size=self.cfg.data.img_size,
            batch_size=self.cfg.data.batch_size_per_gpu,
            dtype=self.data_type,
            gpu_total_mem=torch.cuda.get_device_properties(
                0
            ).total_memory,  # Bytes
        )  # Bool. # TODO: Consider allocated memory

        if not gpu_availability:
            sys.exit(-1)

        if torch.cuda.is_available():
            self.cuda()

    def after_train(self):
        logger.info(
            f"Training of experiment is done and the best {self.metrics[0]} is {self.best_score:.2f}"
        )
        self.test_model()

    def before_epoch(self):
        logger.info(f"---> start train epoch{self.epoch}")
        self.model.train()

    def after_epoch(self):
        tags = ["train/lr", "train/loss", "train/mae"]
        values = [self.lr, self.loss_aver.avg, self.acc_aver.avg]
        for tag, value in zip(tags, values):
            self.tblogger.add_scalar(tag, value, self.epoch)

        self.evaluate_and_save_model()

    def evaluate_and_save_model(self):
        # === Evaluate ===#
        logger.info("Validation start...")

        evalmodel = self.ema_model.ema if self.ema else self.model
        if is_parallel(evalmodel):
            evalmodel = evalmodel.module

        evalmodel.eval()
        outputss, targetss = self.inference(evalmodel, self.val_dataloader)

        logger.info("Evaluate..")

        res = {metric: [] for metric in self.metrics}
        for outputs, targets in zip(outputss, targetss):
            for output, target in zip(outputs, targets):
                values = reg_eval(output.detach().cpu(), target.detach().cpu())
                for metric in self.metrics:
                    res[metric].append(values[metric])
        score = np.mean(res[self.metrics[0]])

        # === Log ===#
        score_texts = []
        tags = []
        values = []
        for method in self.metrics:
            metric = res[method]
            # logger
            if isinstance(metric, list):
                score_str = f"{method:<20}"
                for attr, s in zip(self.classes, metric):
                    score_str += f"{attr}: {s}, "
                score_texts.append(score_str)
                metric = np.mean(metric)
            else:
                score_texts.append(f"{method:<20}{metric:.6f}")

            tags.append(f"val/{method}")
            values.append(metric)

        for tag, value in zip(tags, values):
            self.tblogger.add_scalar(tag, value, self.epoch)

        score_text = "\n".join(score_texts)
        logger.info("Validation scores\n" + score_text)

        # === Save Checkpoints ===#
        self.save_ckpt(
            self.model,
            self.ema_model.ema if self.ema else None,
            "last_epoch",
            score < self.best_score,
        )

        self.best_score = min(self.best_score, score)

    def test_model(self):
        # === Evaluate ===#
        logger.info("Test start...")

        self.cfg.resume = False
        self.cfg.ckpt = os.path.join(self.output_path, "best_ckpt.pth")
        self.resume_train()
        evalmodel = self.model
        if is_parallel(evalmodel):
            evalmodel = evalmodel.module

        evalmodel.eval()
        outputss, targetss = self.inference(evalmodel, self.test_dataloader)

        logger.info("Evaluate..")

        res = {metric: [] for metric in self.metrics}
        for outputs, targets in zip(outputss, targetss):
            for output, target in zip(outputs, targets):
                values = reg_eval(output.detach().cpu(), target.detach().cpu())
                for metric in self.metrics:
                    res[metric].append(values[metric])
        score = np.mean(res[self.metrics[0]])

        # === Log ===#
        score_texts = []
        tags = []
        values = []
        for method in self.metrics:
            metric = res[method]
            # logger
            if isinstance(metric, list):
                score_str = f"{method:<20}"
                for attr, s in zip(self.classes, metric):
                    score_str += f"{attr}: {s}, "
                score_texts.append(score_str)
                metric = np.mean(metric)
            else:
                score_texts.append(f"{method:<20}{metric:.6f}")

            tags.append(f"test/{method}")
            values.append(metric)

        for tag, value in zip(tags, values):
            self.tblogger.add_scalar(tag, value, self.epoch)

        score_text = "\n".join(score_texts)
        logger.info("Test scores\n" + score_text)
