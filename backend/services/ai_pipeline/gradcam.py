"""
DRISHTI-LENS — Grad-CAM Explainability
========================================
Implements genuine Gradient-weighted Class Activation Mapping (Grad-CAM)
for the DR classification model.

Reference:
  Selvaraju et al., "Grad-CAM: Visual Explanations from Deep Networks via
  Gradient-based Localization", ICCV 2017.

How it works:
  1. Forward pass: compute model prediction.
  2. Backward pass: compute gradients of target class score w.r.t. final conv layer.
  3. Global average pool gradients → channel weights (alpha_k).
  4. Weighted sum of activation maps → raw CAM.
  5. ReLU → normalize to [0,1] → resize to input dimensions.
  6. Overlay as heatmap on original image.

IMPORTANT:
  - Grad-CAM is only computed when a trained DL model is loaded.
  - If no model is available, returns cam_available=False and no heatmap.
  - The heatmap corresponds to the predicted class (not a fabricated overlay).
  - Heatmap quality depends on model quality — an untrained model produces noise.
  - Do NOT interpret heatmap regions as clinically confirmed lesion locations
    without validation against expert annotations.
"""
from __future__ import annotations
import numpy as np
import logging
import base64
import io
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class GradCAMResult:
    cam_available: bool           # True only when model was loaded and inference succeeded
    heatmap: Optional[np.ndarray]  # Float32 (H, W) normalized [0,1]; None if unavailable
    overlay_b64: Optional[str]    # Base64-encoded JPEG of heatmap overlaid on original
    predicted_class: Optional[int]
    predicted_class_name: Optional[str]
    method: str = "GradCAM_final_conv_layer"
    disclaimer: str = (
        "Grad-CAM highlights regions that influenced the model prediction. "
        "These regions do NOT necessarily correspond to clinically confirmed lesions. "
        "Ophthalmologist review required."
    )
    error: str = ""


class GradCAMHook:
    """PyTorch forward/backward hook to capture activations and gradients."""

    def __init__(self):
        self.activations = None
        self.gradients = None

    def forward_hook(self, module, input, output):
        self.activations = output.detach()

    def backward_hook(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()


def _get_target_layer(model):
    """Get the final convolutional layer from EfficientNet-B4."""
    try:
        # EfficientNet: features[-1][0] is the last conv block's depthwise conv
        return model.features[-1][0]
    except Exception:
        # Fallback: try to find last Conv2d
        last_conv = None
        for module in model.modules():
            import torch.nn as nn
            if isinstance(module, nn.Conv2d):
                last_conv = module
        return last_conv


def compute_gradcam(image_rgb: np.ndarray, target_class: Optional[int] = None) -> GradCAMResult:
    """
    Compute Grad-CAM heatmap for a fundus image.

    Args:
        image_rgb:    uint8 numpy array (H, W, 3), RGB.
        target_class: Class index to explain (0–4). If None, uses predicted class.

    Returns:
        GradCAMResult. cam_available=False if no model loaded.
    """
    # Import grading module to get model
    try:
        from .grading import _get_dl_model, ICDR_LABELS, INPUT_SIZE
    except ImportError:
        return GradCAMResult(
            cam_available=False, heatmap=None, overlay_b64=None,
            predicted_class=None, predicted_class_name=None,
            error="Could not import grading module"
        )

    model, device = _get_dl_model()
    if model is None:
        return GradCAMResult(
            cam_available=False, heatmap=None, overlay_b64=None,
            predicted_class=None, predicted_class_name=None,
            error="No trained model checkpoint available. Train or provide dr_efficientnet_b4.pth."
        )

    try:
        import torch
        import torchvision.transforms as T
        import cv2

        # Prepare input tensor
        transform = T.Compose([
            T.Resize((INPUT_SIZE, INPUT_SIZE)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        from PIL import Image
        pil_img = Image.fromarray(image_rgb)
        tensor = transform(pil_img).unsqueeze(0).to(device)
        tensor.requires_grad_(True)

        # Register hooks on final conv layer
        hook = GradCAMHook()
        target_layer = _get_target_layer(model)
        if target_layer is None:
            return GradCAMResult(
                cam_available=False, heatmap=None, overlay_b64=None,
                predicted_class=None, predicted_class_name=None,
                error="Could not find target conv layer for Grad-CAM"
            )

        fwd_handle = target_layer.register_forward_hook(hook.forward_hook)
        bwd_handle = target_layer.register_full_backward_hook(hook.backward_hook)

        try:
            # Forward pass
            model.zero_grad()
            output = model(tensor)
            probs = torch.softmax(output, dim=1)
            pred_class = int(torch.argmax(probs, dim=1).item())

            if target_class is None:
                target_class = pred_class

            # Backward pass for target class
            score = output[0, target_class]
            score.backward()

        finally:
            fwd_handle.remove()
            bwd_handle.remove()

        if hook.activations is None or hook.gradients is None:
            return GradCAMResult(
                cam_available=False, heatmap=None, overlay_b64=None,
                predicted_class=pred_class, predicted_class_name=ICDR_LABELS.get(pred_class),
                error="Hook did not capture activations/gradients"
            )

        # Compute Grad-CAM weights: global average pool of gradients
        gradients = hook.gradients.squeeze(0).cpu().numpy()  # (C, H, W)
        activations = hook.activations.squeeze(0).cpu().numpy()  # (C, H, W)

        weights = np.mean(gradients, axis=(1, 2))  # (C,)
        cam = np.zeros(activations.shape[1:], dtype=np.float32)
        for k, w in enumerate(weights):
            cam += w * activations[k]

        # ReLU and normalize
        cam = np.maximum(cam, 0)
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        # Resize to original image dimensions
        h_orig, w_orig = image_rgb.shape[:2]
        cam_resized = cv2.resize(cam, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR)

        # Create heatmap overlay
        heatmap_uint8 = np.uint8(255 * cam_resized)
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        heatmap_rgb = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

        # Blend with original: 60% original + 40% heatmap
        original_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        heatmap_bgr = cv2.cvtColor(heatmap_rgb, cv2.COLOR_RGB2BGR)
        overlay = cv2.addWeighted(original_bgr, 0.6, heatmap_bgr, 0.4, 0)
        overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)

        # Encode overlay as base64 JPEG
        pil_overlay = Image.fromarray(overlay_rgb)
        buf = io.BytesIO()
        pil_overlay.save(buf, format="JPEG", quality=85)
        overlay_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return GradCAMResult(
            cam_available=True,
            heatmap=cam_resized,
            overlay_b64=overlay_b64,
            predicted_class=pred_class,
            predicted_class_name=ICDR_LABELS.get(pred_class, "Unknown"),
            method="GradCAM_EfficientNetB4_final_conv",
        )

    except Exception as exc:
        logger.error(f"Grad-CAM computation failed: {exc}", exc_info=True)
        return GradCAMResult(
            cam_available=False, heatmap=None, overlay_b64=None,
            predicted_class=None, predicted_class_name=None,
            error=str(exc)
        )


def save_gradcam_image(gradcam_result: GradCAMResult, output_path: str) -> bool:
    """Save Grad-CAM overlay to file. Returns True on success."""
    if not gradcam_result.cam_available or gradcam_result.overlay_b64 is None:
        return False
    try:
        img_bytes = base64.b64decode(gradcam_result.overlay_b64)
        with open(output_path, "wb") as f:
            f.write(img_bytes)
        return True
    except Exception as exc:
        logger.error(f"Failed to save Grad-CAM image: {exc}")
        return False
