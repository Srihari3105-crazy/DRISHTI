"""
DRISHTI-LENS — APTOS 2019 Dataset Loader
=========================================
Loads and prepares the APTOS 2019 Blindness Detection dataset for validation.

Dataset:
  Name:      APTOS 2019 Blindness Detection
  Source:    https://www.kaggle.com/competitions/aptos2019-blindness-detection
  License:   Community Data License Agreement - Permissive - Version 1.0
  Labels:    0=No DR, 1=Mild, 2=Moderate, 3=Severe, 4=PDR (maps directly to ICDR)
  Size:      3,662 labelled training images + 1,928 test images (unlabelled)
  Resolution: Variable (fundus photographs, ~1200x1200 to 3388x2588)

Split Strategy:
  Patient-level separation is not possible (APTOS does not provide patient IDs
  per image). We use stratified random split:
    Train:      60%  (~2197 images)
    Validation: 20%  (~732 images) — for threshold tuning and calibration
    Test:       20%  (~733 images) — held-out, only used for final reporting

  The test set is NEVER used during threshold selection or calibration.

TO DOWNLOAD:
  1. Accept competition rules at kaggle.com/competitions/aptos2019-blindness-detection
  2. kaggle competitions download -c aptos2019-blindness-detection
  3. Unzip to backend/validation/data/aptos2019/
     Expected structure:
       backend/validation/data/aptos2019/
         train_images/   (3662 .png files)
         train.csv       (id_code, diagnosis)
"""
from __future__ import annotations
import os
import logging
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

DATASET_DIR = os.environ.get(
    "APTOS_DATASET_DIR",
    os.path.join(os.path.dirname(__file__), "data", "aptos2019")
)
IMAGE_SIZE = 512   # resize to this for pipeline input


def check_dataset_available() -> Tuple[bool, str]:
    """Check if APTOS 2019 dataset is present."""
    csv_path = os.path.join(DATASET_DIR, "train.csv")
    img_dir = os.path.join(DATASET_DIR, "train_images")
    if not os.path.exists(csv_path):
        return False, f"train.csv not found at {csv_path}"
    if not os.path.isdir(img_dir):
        return False, f"train_images/ not found at {img_dir}"
    n = len(list(Path(img_dir).glob("*.png")))
    if n < 100:
        return False, f"Only {n} images found — expected ~3662"
    return True, f"Dataset found: {n} images"


def load_labels() -> Optional[Tuple[list, list]]:
    """
    Load image IDs and ICDR labels from train.csv.

    Returns:
        (image_ids, labels) or None if dataset not available.
    """
    import csv
    csv_path = os.path.join(DATASET_DIR, "train.csv")
    if not os.path.exists(csv_path):
        logger.error(f"Dataset CSV not found: {csv_path}")
        return None

    ids, labels = [], []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.append(row["id_code"])
            labels.append(int(row["diagnosis"]))

    logger.info(f"Loaded {len(ids)} labels from APTOS 2019")
    return ids, labels


def get_train_val_test_split(seed: int = 42) -> Optional[Tuple]:
    """
    Stratified split into train/val/test sets.
    Returns (train_ids, train_labels, val_ids, val_labels, test_ids, test_labels)
    or None if dataset not available.
    """
    from sklearn.model_selection import train_test_split

    result = load_labels()
    if result is None:
        return None
    ids, labels = result
    ids = np.array(ids)
    labels = np.array(labels)

    # First split: 80% train+val, 20% test
    ids_tv, ids_test, y_tv, y_test = train_test_split(
        ids, labels, test_size=0.20, random_state=seed, stratify=labels
    )
    # Second split: 75% of 80% = 60% train, 25% of 80% = 20% val
    ids_train, ids_val, y_train, y_val = train_test_split(
        ids_tv, y_tv, test_size=0.25, random_state=seed, stratify=y_tv
    )

    logger.info(
        f"Split: train={len(ids_train)}, val={len(ids_val)}, test={len(ids_test)}"
        f" | Class dist: {np.bincount(y_test)}"
    )
    return ids_train, y_train, ids_val, y_val, ids_test, y_test


def load_image(image_id: str) -> Optional[np.ndarray]:
    """Load and resize a single APTOS image. Returns RGB uint8 array or None."""
    try:
        import cv2
        path = os.path.join(DATASET_DIR, "train_images", f"{image_id}.png")
        bgr = cv2.imread(path)
        if bgr is None:
            logger.warning(f"Could not read image: {path}")
            return None
        bgr_resized = cv2.resize(bgr, (IMAGE_SIZE, IMAGE_SIZE))
        return cv2.cvtColor(bgr_resized, cv2.COLOR_BGR2RGB)
    except Exception as exc:
        logger.error(f"Failed to load image {image_id}: {exc}")
        return None
