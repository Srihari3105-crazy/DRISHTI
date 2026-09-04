"""
Tests for Image Quality Assessment module.
Verifies Tenengrad focus, histogram illumination, circular FOV detection, and decision outputs.
"""
import numpy as np
import pytest
from services.ai_pipeline.quality_assessment import assess_quality, QualityResult


def test_quality_sharp_image():
    # Create an image with high-contrast sharp checkerboard pattern in green channel
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    for i in range(0, 300, 20):
        for j in range(0, 300, 20):
            if (i // 20 + j // 20) % 2 == 0:
                img[i:i+20, j:j+20, :] = 160

    res = assess_quality(img)
    assert isinstance(res, QualityResult)
    assert res.metrics_valid is True
    assert res.focus_score > 50  # sharp gradients
    assert res.illumination_mean > 50


def test_quality_severely_blurred_image():
    # Uniform gray image with zero gradient energy
    img = np.full((300, 300, 3), 120, dtype=np.uint8)
    res = assess_quality(img)
    assert isinstance(res, QualityResult)
    # Zero gradients should fail focus check
    assert res.focus_score == 0.0
    assert res.decision in ("QUALITY_UNGRADABLE", "QUALITY_BORDERLINE")
    assert any("blur" in msg.lower() or "focus" in msg.lower() for msg in res.feedback)


def test_quality_underexposed_image():
    # Extremely dark image (<10 pixel values)
    img = np.full((300, 300, 3), 15, dtype=np.uint8)
    res = assess_quality(img)
    assert res.underexposed_frac > 0.5
    assert res.decision == "QUALITY_UNGRADABLE"
    assert any("illumination" in msg.lower() or "dark" in msg.lower() for msg in res.feedback)


def test_quality_empty_input():
    empty_img = np.zeros((0, 0, 3), dtype=np.uint8)
    res = assess_quality(empty_img)
    assert res.decision == "QUALITY_UNGRADABLE"
    assert res.metrics_valid is False
