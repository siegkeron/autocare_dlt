import copy
import os
import shutil
import unittest

from attrdict import AttrDict

from autocare_dlt.core.trainer import DetectionTrainer
from autocare_dlt.utils.config import json_to_dict


class TestDetectionTrainer(unittest.TestCase):
    def setUp(self):
        self.model_cfg = (
            "tests/assets/detection/configs/retinanet_resnet18.json"
        )
        self.data_cfg = "tests/assets/detection/configs/coco_small.json"
        self.dummy_cfg = {}
        self.dummy_cfg.update(json_to_dict(self.model_cfg))
        self.dummy_cfg.update(json_to_dict(self.data_cfg))
        self.dummy_cfg.update(
            {
                "exp_name": "test_base_trainer",
                "ema": False,
                "ema_cfg": None,
                "num_gpus": 1,
                "resume": False,
                "ckpt": None,
                "fp16": False,
            }
        )
        self.dummy_cfg = AttrDict(self.dummy_cfg)

    def tearDown(self):
        shutil.rmtree(self.trainer.log_path)
        shutil.rmtree(self.trainer.output_path)
        del self.trainer

    def test_build_trainer(self):

        self.trainer = DetectionTrainer(self.dummy_cfg)
        self.assertTrue(os.path.exists(self.trainer.log_path))
        self.assertTrue(os.path.exists(self.trainer.output_path))
        self.assertEqual(
            self.trainer.cfg["model"]["head"]["num_classes"],
            self.dummy_cfg.num_classes,
        )
        with self.assertRaises(ValueError):
            cfg = copy.deepcopy(self.dummy_cfg)
            cfg.pop("optim")
            trainer = DetectionTrainer(cfg)

    def test_run_trainer(self):
        self.trainer = DetectionTrainer(self.dummy_cfg)
        ckpt_path = os.path.join(self.trainer.output_path, "best_ckpt.pth")
        self.assertFalse(os.path.exists(ckpt_path))
        self.trainer.train()
        self.assertTrue(os.path.exists(ckpt_path))
