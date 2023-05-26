# Autocare DLT

Autocare DeepLearning Toolkit은 SNUAILAB의 모델 개발 및 Autocare T의 학습을 지원하기 위한 pytorch 기반 deep learning toolkit입니다.
## Updates
- v0.2
    - HPO 추가
    - Mutli-GPU 지원
    - inference 및 data_selection에서 coco input 지원

## 설치

### Prerequisite

- Python >= 3.9
- CUDA == 11.3
- pytorch >= 1.12.1 ([link](https://pytorch.org/get-started/locally/))
    - torchvision >= 0.13.1

### Install
- tx_model은 repo를 clone하여 CLI로 사용하는 방식 및 python package(*.whl) 파일을 통하여 설치하는 방법 2가지를 지원한다.

#### git clone
```bash
git clone git@github.com:snuailab/autocare_dlt.git
cd autocare_dlt
pip install -r requirements.txt
```
#### package 설치
```bash
pip install autocare_dlt
```

## 실행

### Model config 준비

- 기본적인 template은 ./models참조
- 사용하고자 하는 Model에 맞춰서 config값 수정
    - 모듈에 따라 hyper-parameter값이 다양해지기 때문에 해당 모듈의 code를 참조하여 수정 할 것을 권장

### Data config 준비

- 기본적인 template은 ./datasets 참조
- 사용하고자 하는 Dataset에 맞춰서 config값 수정
    - workers_per_gpu (int) : dataloader work 갯수
    - batch_size_per_gpu (int): GPU당 batch size
    - img_size (int): 모델의 image size (img_size, img_size) → 추후 업데이트 예정
    - train, val, test, unlabeled (dict): 각 dataset의 config
        - type: dataset의 type
        - data_root: data의 root path
        - ann: annotation 파일의 path
        - input_paths (unlabeled data only): unlabled data 파일 리스트
            - dir path : "data_root: ''" 로 맞추어 사용 할것
            - *.txt
            - *.json(coco형식)
        - augmentation: data augmentation세팅
            - CV2 모듈들이 먼저 적용되고 pytorch(torchvision) 모듈 적용됨
            - top down 순서대로 적용

### 지원 하는 package Tools
- 해당 tool들을 import하여 사용 혹은 cli로 실행
> **autocare_dlt.tools.train.run**(*exp_name: str*, *model_cfg: str*, *data_cfg: str*, *gpus: str = '0'*, *ckpt: ~typing.Union[str*, *dict] = None*, *world_size: int = 1*, *output_dir: str = 'outputs'*, *resume: bool = False*, *fp16: bool = False*, *ema: bool = False*)**→ tooNone**

Run training

**Parameters**

- **exp_name** (*str*) – experiment name. a folder with this name will be created in the `output_dir`, and the log files will be saved there.

- **model_cfg** (*str*) – path for model configuration file

- **data_cfg** (*str*) – path for dataset configuration file

- **gpus** (*str, optional*) – GPU IDs to use. Default to ‘0’

- **ckpt** (*str, optional*) – path for checkpoint file. Defaults to None.

- **world_size** (*int, optional*) – world size for ddp. Defaults to 1.

- **output_dir** (*str, optional*) – log output directory. Defaults to ‘outputs’.

- **resume** (*bool, optional*) – whether to resume the previous training or not. Defaults to False.

- **fp16** (*bool, optional*) – whether to use float point 16 or not. Defaults to False.

- **ema** (*bool, optional*) – whether to use EMA(exponential moving average) or not. Defaults to False.

> **autocare_dlt.tools.inference.run**(*inputs: str*, *model_cfg: str*, *output_dir: str*, *gpus: str*, *ckpt: Union[str, dict]*, *input_size: list = None*, *letter_box: bool = None*, *vis: bool = False*, *save_imgs: bool = False*, *root_dir: str = ''*)**→ None**

Run inference

**Parameters**

- **inputs** (*str*) – path for input - image, directory, or json

- **model_cfg** (*str*) – path for model configuration file

- **output_dir** (*str*) – path for inference results

- **gpus** (*str*) – GPU IDs to use

- **ckpt** (*Union[str, dict]*) – path for checkpoint file or state dict

- **input_size** (*list, optional*) – input size of model inference. Defaults to [640].

- **letter_box** (*bool, optional*) – whether to use letter box or not. Defaults to False.

- **vis** (*bool, optional*) – whether to visualize inference in realtime or not. Defaults to False.

- **save_imgs** (*bool, optional*) – whether to draw and save inference results as images or not. Defaults to False.

- **root_dir** (*str, optional*) – path for input image when using json input. Defaults to “”.

> **autocare_dlt.tools.eval.run**(*model_cfg: str*, *data_cfg: str*, *gpus: str*, *ckpt: Union[str, dict]*)**→ None**

Evaluate a model

**Parameters**

- **model_cfg** (*str*) – path for model configuration file

- **data_cfg** (*str*) – path for dataset configureation file

- **gpus** (*str*) – GPU IDs to use

- **ckpt** (*Union[str, dict]*) – path for checkpoint file or state dict

> **autocare_dlt.tools.export_onnx.run**(*output_name: str*, *model_cfg: str*, *ckpt: Union[str, dict]*, *input_size: list = None*, *opset: int = 11*, *no_onnxsim: bool = False*)**→ None**

Export onnx file

**Parameters**

- **output_name** (*str*) – file name for onnx output (.onnx)

- **model_cfg** (*str*) – path for model configuration file

- **ckpt** (*Union[str, dict]*) – path for checkpoint file or state dict

- **input_size** (*list, optional*) – input size of model. use model config value if input_size is None. Default to None.

- **opset** (*int, optional*) – onnx opset version. Defaults to 11.

- **no_onnxsim** (*bool, optional*) – whether to use onnxsim or not. Defaults to False.

> **autocare_dlt.tools.data_selection.run**(*model_cfg: str*, *ckpt: Union[str, dict]*, *inputs: str*, *num_outputs: int*, *output_dir: str*, *gpus: str*, *input_size: list = None*, *letter_box: bool = None*, *copy_img: bool = False*, *root_dir: str = ''*)**→ None**

Select active learning data

**Parameters**

- **model_cfg** (*str*) – path for model configuration file

- **ckpt** (*Union[str, dict]*) – path for checkpoint file or state dict

- **inputs** (*str*) – path for input - image, directory, or json

- **num_outputs** (*int*) – number of images to select

- **output_dir** (*str*) – path for output result

- **gpus** (*str*) – GPU IDs to use

- **input_size** (*list, optional*) – input size of model inference. Defaults to [640].

- **letter_box** (*bool, optional*) – whether to use letter box or not. Defaults to False.

- **copy_img** (*bool, optional*) – whether to copy images to output. Defaults to False.

- **root_dir** (*str, optional*) – path for input image when using json input. Defaults to “”.

> **autocare_dlt.tools.hpo.run**(*exp_name: str*, *model_cfg: str*, *data_cfg: str*, *hpo_cfg: str = None* *gpus: str = '0'*, *ckpt: ~typing.Union[str*, *dict] = None*, *world_size: int = 1*, *output_dir: str = 'outputs'*, *resume: bool = False*, *fp16: bool = False*, *ema: bool = False*)**→ None**

Run Hyperparameter Optimization

**Parameters**

- **exp_name** (*str*) – experiment name. a folder with this name will be created in the `output_dir`, and the log files will be saved there.

- **model_cfg** (*str*) – path for model configuration file

- **data_cfg** (*str*) – path for dataset configuration file

- **hpo_cfg** (str, optional): path for hpo configuration file. Default to None.

- **gpus** (*str, optional*) – GPU IDs to use. Default to ‘0’

- **ckpt** (*str, optional*) – path for checkpoint file. Defaults to None.

- **world_size** (*int, optional*) – world size for ddp. Defaults to 1.

- **output_dir** (*str, optional*) – log output directory. Defaults to ‘outputs’.

- **resume** (*bool, optional*) – whether to resume the previous training or not. Defaults to False.

- **fp16** (*bool, optional*) – whether to use float point 16 or not. Defaults to False.

- **ema** (*bool, optional*) – whether to use EMA(exponential moving average) or not. Defaults to False.

### CLI 명령어 예시
Supervised Learning
```bash
python autocare_dlt/tools/train.py --exp_name {your_exp} --model_cfg {path}/{model}.json --data_cfg {path}/{data}.json} --ckpt {path}/{ckpt}.pth --gpus {gpu #}
```

### Distributed training (Multi-GPU training)
Multi-GPU 훈련을 진행하기 위해서는 'python'이 아닌 'torchrun'을 이용해야 함
```bash
torchrun autocare_dlt/tools/train.py --exp_name {your_exp} --model_cfg {path}/{model}.json --data_cfg {path}/{data}.json} --ckpt {path}/{ckpt}.pth --gpus {gpu #,#,...} --multi_gpu True
```
[권장] 같은 서버에서 다수의 Multi-GPU 훈련을 하기 위해서는 아래 명령어를 이용해야 함
```bash
torchrun --rdzv_backend=c10d --rdzv_endpoint=localhost:0 --nnodes=1 autocare_dlt/tools/train.py --exp_name {your_exp} --model_cfg {path}/{model}.json --data_cfg {path}/{data}.json} --ckpt {path}/{ckpt}.pth --gpus {gpu #,#,...}
```
- training 결과는 outputs/{your_exp} 위치에 저장됨
### run evaluation

```bash
python autocare_dlt/tools/eval.py --model_cfg {path}/{model}.json --data_cfg {path}/{data}.json} --ckpt {path}/{ckpt}.pth --gpus 0
```

### export onnx

```bash
python autocare_dlt/tools/export_onnx.py --output_name {path}/{model_name}.onnx --model_cfg {path}/{model}.json --batch_size 1 --ckpt {path}/{ckpt}.pth
```

### run inference
- OCR관련
	- Prerequest : 한글 폰트 파일 (ex. NanumPen.ttf)

```bash
python tools/inference.py --inputs {path}/{input_dir, img, video, coco json} --model_cfg {path}/{model}.json --output_dir {path}/{output dir name} --ckpt {path}/{model_name}.pth --input_size {width} {height} --gpus {gpu_id} (optional)--root_dir {root path of coco}
```

### run data selection
```bash
python tools/data_selection.py --inputs {path}/{input_dir, cocojson} --model_cfg {path}/{model}.json --output_dir {path}/{output dir name} --ckpt {path}/{model_name}.pth --num_outputs {int} --input_size {width} {height} --letter_box {bool} --gpus {gpu_id} (optional)--root_dir {root path of coco}
```

# References
This code is based on and inspired on those repositories (TBD)
- [YOLOv5](https://github.com/ultralytics/yolov5)
- [Detectron2](https://github.com/facebookresearch)
- [MMCV](https://github.com/open-mmlab/mmcv)
- [YOLOX](https://github.com/Megvii-BaseDetection/YOLOX/tree/main)
