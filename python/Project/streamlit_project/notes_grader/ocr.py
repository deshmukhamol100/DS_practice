from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import pytesseract
from PIL import Image, ImageOps


PreprocessMode = Literal["auto", "none", "threshold", "adaptive_threshold"]


@dataclass(frozen=True)
class OcrConfig:
    tesseract_cmd: Optional[str] = None
    lang: str = "eng"
    psm: int = 6
    preprocess: PreprocessMode = "auto"

def _preprocess_pil(img: Image.Image, mode: PreprocessMode) -> Image.Image:
    # Basic preprocessing that works without OpenCV.
    gray = ImageOps.grayscale(img)
    # Scale up a bit for handwriting OCR.
    w, h = gray.size
    gray = gray.resize((int(w * 1.6), int(h * 1.6)))

    if mode == "none":
        return gray

    if mode == "threshold":
        # Simple global threshold.
        return gray.point(lambda p: 255 if p > 160 else 0)

    if mode == "adaptive_threshold":
        # If OpenCV is available, use adaptive thresholding.
        try:
            import cv2
            import numpy as np

            arr = np.array(gray)
            arr = cv2.GaussianBlur(arr, (5, 5), 0)
            thr = cv2.adaptiveThreshold(
                arr,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                21,
                10,
            )
            return Image.fromarray(thr)
        except Exception:
            # Fallback to simple threshold.
            return gray.point(lambda p: 255 if p > 160 else 0)

    # auto
    # Try adaptive threshold first, fallback gracefully.
    return _preprocess_pil(img, "adaptive_threshold")


def extract_text_from_image(image_bytes: bytes, cfg: OcrConfig) -> str:
    import io

    if cfg.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = cfg.tesseract_cmd

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = _preprocess_pil(img, cfg.preprocess)

    config = f"--psm {cfg.psm}"
    text = pytesseract.image_to_string(img, lang=cfg.lang, config=config)
    return (text or "").strip()

