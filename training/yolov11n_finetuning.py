#!/usr/bin/env python3
"""
YOLOv11n training pipeline (training-only release).

Default usage (config-first):
    python training/yolov11n_finetuning.py --config configs/train.yaml

Legacy-compatible usage:
    python training/yolov11n_finetuning.py --cam_id 1 --epochs 5 --batch_size 8 --image_size 1280
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import yaml
from tqdm import tqdm


def run_yolo_command(command: str, description: str = "Processing") -> None:
    print(f"Executing: {command}")
    print("-" * 60)

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            universal_newlines=True,
        )

        with tqdm(desc=description, unit="step", dynamic_ncols=True, leave=True) as pbar:
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    tqdm.write(line)

                    if "Epoch" in line or "epoch" in line:
                        pbar.set_postfix_str(line[:80] if len(line) > 80 else line)
                        pbar.update(1)
                    elif "val" in line.lower() or "valid" in line.lower():
                        pbar.set_postfix_str("Validating...")
                        pbar.update(1)
                    elif "predict" in line.lower() or "inference" in line.lower():
                        pbar.set_postfix_str("Running predictions...")
                        pbar.update(1)
                    elif "image" in line.lower() and ("/" in line or "%" in line):
                        pbar.set_postfix_str("Processing images...")
                        pbar.update(1)
                    elif line and not line.startswith(" "):
                        pbar.update(1)

        return_code = process.poll()
        if return_code != 0:
            print(f"\nError: Command failed with return code: {return_code}")
            sys.exit(1)

        print(f"\n{description} completed successfully!")
        print("-" * 60)

    except Exception as exc:
        print(f"Exception while executing command: {exc}")
        sys.exit(1)


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a YAML mapping: {path}")
    return data


def resolve_dataset(dataset_cfg: Dict[str, Any], cam_id: int, repo_root: Path) -> Dict[str, Any]:
    cameras = dataset_cfg.get("cameras", {})
    cam_key = f"camera_{cam_id}"
    if cam_key not in cameras:
        raise ValueError(f"Camera '{cam_key}' missing in datasets config.")

    cam_info = cameras[cam_key]
    rel_root = cam_info.get("dataset_root", f"data/{cam_key}")
    dataset_root = (repo_root / rel_root).resolve()

    return {
        "camera_key": cam_key,
        "dataset_root": dataset_root,
        "train_images": cam_info.get("train_images", "train/images"),
        "val_images": cam_info.get("val_images", "valid/images"),
        "predict_source": cam_info.get("predict_source", "valid/images"),
        "class_names": cam_info.get("class_names", ["Riped berries"]),
    }


def write_data_yaml(path: Path, dataset: Dict[str, Any]) -> None:
    names = dataset["class_names"]
    names_yaml = "\n".join([f"  {idx}: '{name}'" for idx, name in enumerate(names)])
    content = (
        f"path: {dataset['dataset_root'].as_posix()}\n"
        f"train: '{dataset['train_images']}'\n"
        f"val: '{dataset['val_images']}'\n\n"
        f"names:\n{names_yaml}\n"
    )
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YOLOv11n Training for Agricultural Cobot")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/train.yaml",
        help="Path to train config YAML (default: configs/train.yaml)",
    )
    parser.add_argument("--cam_id", type=int, help="Camera ID (legacy compatible; overrides config).")
    parser.add_argument("--epochs", type=int, help="Number of epochs (overrides config).")
    parser.add_argument("--batch_size", type=int, help="Batch size (overrides config).")
    parser.add_argument("--image_size", type=int, help="Image size (overrides config).")
    parser.add_argument("--device", type=str, help="Device (e.g., cpu, 0) overrides config.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    train_cfg_path = (repo_root / args.config).resolve()
    train_cfg = load_yaml(train_cfg_path)

    datasets_cfg_rel = train_cfg.get("datasets_config", "configs/datasets.yaml")
    datasets_cfg_path = (repo_root / datasets_cfg_rel).resolve()
    datasets_cfg = load_yaml(datasets_cfg_path)

    cam_id = args.cam_id if args.cam_id is not None else int(train_cfg.get("cam_id", 1))
    epochs = args.epochs if args.epochs is not None else int(train_cfg.get("epochs", 5))
    batch_size = args.batch_size if args.batch_size is not None else int(train_cfg.get("batch_size", 8))
    image_size = args.image_size if args.image_size is not None else int(train_cfg.get("image_size", 1280))
    training_mode = str(train_cfg.get("training_mode", "finetune")).strip().lower()
    finetune_model = str(train_cfg.get("finetune_model", "pre_trained_model/yolo11n.pt"))
    scratch_model = str(train_cfg.get("scratch_model", "yolo11n.yaml"))
    run_name = str(train_cfg.get("run_name", "yolov11n_train"))
    device = args.device if args.device is not None else str(train_cfg.get("device", ""))
    output_model_dir = str(train_cfg.get("output_model_dir", "output_model"))
    aug_cfg = train_cfg.get("augmentation", {}) if isinstance(train_cfg.get("augmentation", {}), dict) else {}

    dataset = resolve_dataset(datasets_cfg, cam_id, repo_root)
    if not dataset["dataset_root"].exists():
        raise FileNotFoundError(f"Dataset path does not exist: {dataset['dataset_root']}")

    temp_data_yaml = script_dir / f"yolov11n_config_camera_{cam_id}.yaml"
    write_data_yaml(temp_data_yaml, dataset)

    if training_mode not in {"finetune", "scratch"}:
        raise ValueError("training_mode must be either 'finetune' or 'scratch'.")

    if training_mode == "finetune":
        target_model_path = Path(finetune_model)
        model_arg = str((repo_root / target_model_path).resolve()) if not target_model_path.is_absolute() else str(target_model_path)
        if not Path(model_arg).exists():
            raise FileNotFoundError(
                f"Fine-tune model not found: {model_arg}. Put a .pt file in pre_trained_model/ or set finetune_model."
            )
    else:
        target_model_path = Path(scratch_model)
        model_arg = str(target_model_path)

    run_root = (repo_root / output_model_dir / f"camera_{cam_id}").resolve()
    best_model = run_root / run_name / "weights" / "best.pt"
    predict_source = dataset["dataset_root"] / dataset["predict_source"]

    print("Resolved configuration:")
    print(f"  train_config:   {train_cfg_path}")
    print(f"  datasets_config:{datasets_cfg_path}")
    print(f"  cam_id:         {cam_id}")
    print(f"  dataset_root:   {dataset['dataset_root']}")
    print(f"  training_mode:  {training_mode}")
    print(f"  model:          {model_arg}")
    print(f"  epochs:         {epochs}")
    print(f"  batch_size:     {batch_size}")
    print(f"  image_size:     {image_size}")
    print(f"  device:         {device or 'default'}")
    print(f"  output_model:   {run_root}")
    print(f"  augmentation:   {'enabled' if aug_cfg.get('enabled', False) else 'disabled'}")

    device_part = f" device={device}" if device else ""
    aug_part = ""
    if aug_cfg.get("enabled", False):
        saturation = float(aug_cfg.get("saturation", 0.25))
        brightness = float(aug_cfg.get("brightness", 0.15))
        exposure = float(aug_cfg.get("exposure", 0.10))
        crop_fraction = float(aug_cfg.get("crop_fraction", 0.9))
        random_crops_only = bool(aug_cfg.get("random_crops_only", True))

        # Ultralytics in this project supports hsv_s/hsv_v/crop_fraction directly.
        hsv_s = max(0.0, saturation)
        hsv_v = max(0.0, brightness + exposure)
        aug_part = f" hsv_s={hsv_s} hsv_v={hsv_v} crop_fraction={crop_fraction}"
        if random_crops_only:
            aug_part += " mosaic=0.0 mixup=0.0 copy_paste=0.0"

        blur = aug_cfg.get("blur", None)
        noise = aug_cfg.get("noise", None)
        if blur is not None or noise is not None:
            print("  note: blur/noise are recorded in config but not directly passed by this Ultralytics CLI version.")

    model_mode = "fine-tuning" if training_mode == "finetune" else "from-scratch training"
    print("\n" + "=" * 50)
    print(f"STARTING TRAINING ({model_mode})")
    print("=" * 50)
    train_command = (
        f"yolo task=detect mode=train model=\"{model_arg}\" imgsz={image_size} "
        f"epochs={epochs} batch={batch_size} data=\"{temp_data_yaml}\" "
        f"project=\"{run_root}\" name=\"{run_name}\" exist_ok=True{aug_part}{device_part}"
    )
    run_yolo_command(train_command, f"Training YOLOv11n (Camera {cam_id})")

    print("\n" + "=" * 50)
    print("STARTING EVALUATION")
    print("=" * 50)
    eval_command = (
        f"yolo task=detect mode=val model=\"{best_model}\" data=\"{temp_data_yaml}\" "
        f"project=\"{run_root}\" name=\"yolov11n_eval\" exist_ok=True{device_part}"
    )
    run_yolo_command(eval_command, f"Evaluating Model (Camera {cam_id})")

    print("\n" + "=" * 50)
    print("STARTING INFERENCE")
    print("=" * 50)
    inference_command = (
        f"yolo task=detect mode=predict model=\"{best_model}\" source=\"{predict_source}\" "
        f"imgsz={image_size} project=\"{run_root}\" name=\"yolov11n_inference\" "
        f"exist_ok=True hide_labels=True{device_part}"
    )
    run_yolo_command(inference_command, f"Running Inference (Camera {cam_id})")

    print("\n" + "=" * 50)
    print("TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print(f"Best model saved at: {best_model}")
    print(f"Evaluation results saved in: {run_root / 'yolov11n_eval'}")
    print(f"Inference results saved in: {run_root / 'yolov11n_inference'}")


if __name__ == "__main__":
    main()
