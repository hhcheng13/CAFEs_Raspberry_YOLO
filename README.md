# Training-Only YOLOv11n Pipeline

This repository provides a training-only pipeline for YOLOv11n on camera-based agricultural datasets.

## Data Preparation (Roboflow)

Before training, prepare your dataset in Roboflow:

1. Go to [Roboflow workspace](https://app.roboflow.com/hhs-workspace-f6gsb/home).
2. Create your own account and set up your project.
3. Upload your images.
4. Run semi-auto annotation, then manually correct labels where needed. (...\CAFEs_Raspberry_YOLO\screen cap on using roboflow)
5. Create a dataset version.
6. Download/export the annotated dataset and place it under `annotated_data_source/`.

Note:
- Originally this workflow used Grounding DINO for assisted annotation.
- It appears the platform workflow has been updated to use SAM3-assisted annotation.

## Repository Scope

- Included: training, evaluation, inference
- Excluded from canonical flow: annotation scripts/workflows
- Legacy snapshot kept at `agricultural-cobot-main_legacy/` for reference only

## Setup

```bash
pip install -r requirements.txt
```

## Dataset/Model Source

- Datasets are expected under `annotated_data_source/`
- Pretrained weights are expected under `pre_trained_model/`

## Dataset Location

Current dataset roots in config:

- `annotated_data_source/camera_1`
- `annotated_data_source/camera_2`

## Model/Output Structure

- Pretrained input models: `pre_trained_model/`
- Trained output models: `output_model/`

## Config-Driven Modes

In `configs/train.yaml`:

- `training_mode: finetune` uses `finetune_model` (`.pt` file)
- `training_mode: scratch` uses `scratch_model` (for example `yolo11n.yaml`)

## Run (Using `train.yaml`)

```bash
python training/yolov11n_finetuning.py --config configs/train.yaml
```

## Backward-Compatible Legacy-Style Command

```bash
python training/yolov11n_finetuning.py --cam_id 1 --epochs 5 --batch_size 8 --image_size 1280
```

## Outputs

Outputs are written under:

- `output_model/camera_{cam_id}/<run_name>/...`
