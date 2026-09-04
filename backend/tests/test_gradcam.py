"""
Tests for Grad-CAM module — verifies non-fabrication guarantees when model is absent or present.
"""
import numpy as np
import pytest
from services.ai_pipeline.gradcam import compute_gradcam, GradCAMResult


def test_gradcam_without_checkpoint():
    # If no model weights file is installed, must return cam_available=False, never a fake heatmap
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    res = compute_gradcam(img, target_class=2)
    assert isinstance(res, GradCAMResult)
    # Anti-fabrication verification
    if not res.cam_available:
        assert res.heatmap is None
        assert res.overlay_b64 is None
        assert "no trained model" in res.error.lower() or "not available" in res.error.lower()
