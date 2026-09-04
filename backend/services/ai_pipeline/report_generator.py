"""
DRISHTI-LENS — Clinical Report Generator
==========================================
Generates an HTML annotated clinical report for each screening event.

Report contains:
  - Patient / screening ID
  - Image quality assessment result
  - Enhancement status
  - DR severity grade + ICDR level
  - Referable status
  - Confidence (raw and calibrated if available)
  - Lesion findings (count + type)
  - Vessel / structure findings
  - Grad-CAM (embedded as base64 if available)
  - Annotated lesion image (embedded as base64 if available)
  - ICDR rule trace
  - Recommendation
  - Timestamp / model version / pipeline version
  - Mandatory disclaimer

DISCLAIMER:
  All reports carry a mandatory header:
  "AI-ASSISTED SCREENING — Ophthalmologist review required before any clinical action."
"""
from __future__ import annotations
import os
import logging
import base64
import datetime
from typing import Optional
from io import BytesIO

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1.0.0-prototype"
DISCLAIMER_TEXT = (
    "⚠️ AI-ASSISTED SCREENING — This report was generated automatically by an AI pipeline. "
    "It is intended to assist, not replace, evaluation by a qualified ophthalmologist. "
    "Accuracy has not been clinically validated. "
    "Do NOT make clinical decisions based solely on this report."
)


def _b64_image(image_rgb_or_bytes) -> Optional[str]:
    """Return base64-encoded JPEG string from RGB array or raw bytes."""
    if image_rgb_or_bytes is None:
        return None
    try:
        if isinstance(image_rgb_or_bytes, bytes):
            return base64.b64encode(image_rgb_or_bytes).decode("utf-8")
        import numpy as np
        from PIL import Image
        pil = Image.fromarray(image_rgb_or_bytes.astype("uint8"))
        buf = BytesIO()
        pil.save(buf, format="JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as exc:
        logger.warning(f"Could not encode image to base64: {exc}")
        return None


def generate_html_report(
    screening_id: str,
    patient_id: str,
    eye: str,
    quality_result,      # QualityResult | None
    enhancement_applied: bool,
    grading_result,      # GradingResult | None
    seg_result,          # SegmentationResult | None
    gradcam_result,      # GradCAMResult | None
    original_image_rgb=None,
    enhanced_image_rgb=None,
    annotated_image_rgb=None,
    operator_name: str = "Unknown",
    output_path: str = None,
) -> str:
    """
    Generate a full HTML clinical report.

    Args:
        output_path: If provided, saves HTML to this path.

    Returns:
        HTML string.
    """
    now = datetime.datetime.utcnow().isoformat() + "Z"

    # ── Severity / grade info ───────────────────────────────────────────────
    if grading_result:
        severity_level = grading_result.severity_level
        severity_name = grading_result.severity_name
        referable = grading_result.referable
        confidence_raw = grading_result.confidence
        calibrated_conf = grading_result.calibrated_confidence
        method = grading_result.method
        dme_risk = grading_result.dme_risk
        efs_score = grading_result.efs_score
        rule_trace = grading_result.rule_trace or []
        model_available = grading_result.model_available
    else:
        severity_level = -1
        severity_name = "UNGRADED"
        referable = False
        confidence_raw = 0.0
        calibrated_conf = None
        method = "not_run"
        dme_risk = 0.0
        efs_score = 0.0
        rule_trace = []
        model_available = False

    # ── Lesion findings ─────────────────────────────────────────────────────
    lesion_rows = ""
    if seg_result:
        for lesion_attr, label in [
            ("microaneurysms", "Microaneurysms (MA)"),
            ("exudates", "Exudates (EX)"),
            ("hemorrhages", "Hemorrhages (HE)"),
            ("neovascularization", "Neovascularization (NV)"),
        ]:
            lr = getattr(seg_result, lesion_attr, None)
            if lr:
                lesion_rows += f"""
                <tr>
                    <td>{label}</td>
                    <td>{lr.candidate_count}</td>
                    <td>{lr.confidence:.2f}</td>
                    <td style="font-size:0.8em;color:#888">{lr.disclaimer[:80]}…</td>
                </tr>"""

    # ── Quality info ─────────────────────────────────────────────────────────
    quality_html = ""
    if quality_result:
        quality_html = f"""
        <table class="info-table">
            <tr><td>Decision</td><td><strong>{quality_result.decision}</strong></td></tr>
            <tr><td>Focus score (Tenengrad)</td><td>{quality_result.focus_score:.1f}</td></tr>
            <tr><td>Laplacian variance</td><td>{quality_result.laplacian_var:.1f}</td></tr>
            <tr><td>Illumination mean</td><td>{quality_result.illumination_mean:.1f} / 255</td></tr>
            <tr><td>Overexposed fraction</td><td>{quality_result.overexposed_frac*100:.1f}%</td></tr>
            <tr><td>FOV coverage</td><td>{quality_result.fov_coverage*100:.1f}%</td></tr>
            <tr><td>FOV circle detected</td><td>{'Yes' if quality_result.fov_detected else 'No'}</td></tr>
        </table>"""
        if quality_result.feedback:
            quality_html += "<ul class='feedback-list'>"
            for fb in quality_result.feedback:
                quality_html += f"<li>{fb}</li>"
            quality_html += "</ul>"

    # ── Images ───────────────────────────────────────────────────────────────
    def img_tag(b64: Optional[str], caption: str) -> str:
        if b64 is None:
            return f'<div class="img-placeholder">[{caption} not available]</div>'
        return f'<figure><img src="data:image/jpeg;base64,{b64}" alt="{caption}" /><figcaption>{caption}</figcaption></figure>'

    original_b64 = _b64_image(original_image_rgb)
    enhanced_b64 = _b64_image(enhanced_image_rgb)
    annotated_b64 = _b64_image(annotated_image_rgb)
    gradcam_b64 = gradcam_result.overlay_b64 if (gradcam_result and gradcam_result.cam_available) else None

    # ── Rule trace ───────────────────────────────────────────────────────────
    rule_rows = ""
    for rule in rule_trace:
        met_color = "#c0392b" if rule.get("met") else "#27ae60"
        rule_rows += f"""
        <tr>
            <td style="font-family:monospace">{rule.get('rule_id','—')}</td>
            <td style="color:{met_color}">{'✔' if rule.get('met') else '✘'}</td>
            <td>{rule.get('description','')}</td>
            <td>{', '.join(rule.get('zones', []))}</td>
        </tr>"""

    # ── Referral recommendation ───────────────────────────────────────────────
    if referable:
        recommendation = "⚠️ REFER TO OPHTHALMOLOGIST — DR level ≥ 2 detected. Urgent review recommended."
        rec_color = "#c0392b"
    else:
        recommendation = "✔ Routine follow-up — No referable DR detected. Recommend annual re-screening."
        rec_color = "#27ae60"

    calibrated_str = (f"{calibrated_conf:.3f}" if calibrated_conf is not None
                      else "NOT CALIBRATED (validation data required)")

    severity_color = {0: "#27ae60", 1: "#f39c12", 2: "#e67e22",
                      3: "#c0392b", 4: "#7b241c"}.get(severity_level, "#666")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DRISHTI-LENS Screening Report — {screening_id[:8]}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 24px;
         background: #f8f9fa; color: #2c3e50; }}
  .header {{ background: #1a1a2e; color: white; padding: 20px 24px; border-radius: 10px;
             margin-bottom: 20px; }}
  .disclaimer {{ background: #fff3cd; border: 2px solid #e0a800; border-radius: 8px;
                 padding: 14px 18px; margin-bottom: 20px; font-weight: bold;
                 color: #856404; font-size: 0.95em; }}
  .card {{ background: white; border-radius: 10px; padding: 20px;
           margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.07); }}
  .card h3 {{ margin: 0 0 14px; font-size: 0.9em; text-transform: uppercase;
              color: #7f8c8d; letter-spacing: 1px; }}
  .severity-badge {{ display: inline-block; padding: 8px 20px; border-radius: 20px;
                     font-weight: 800; font-size: 1.2em; color: white;
                     background: {severity_color}; margin-bottom: 10px; }}
  .referable {{ font-size: 1.05em; font-weight: 700; color: {rec_color};
                padding: 10px 16px; border-radius: 8px;
                background: {'#fdf0f0' if referable else '#f0fdf4'};
                border: 1px solid {rec_color}; margin: 10px 0; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
  th, td {{ padding: 8px 12px; border-bottom: 1px solid #ecf0f1; text-align: left; }}
  th {{ background: #f8f9fa; font-weight: 600; }}
  .info-table td:first-child {{ color: #7f8c8d; width: 220px; }}
  .img-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }}
  figure {{ margin: 0; text-align: center; }}
  figure img {{ max-width: 100%; border-radius: 8px; border: 1px solid #ddd; }}
  figcaption {{ font-size: 0.8em; color: #666; margin-top: 4px; }}
  .img-placeholder {{ height: 150px; background: #f0f0f0; border-radius: 8px;
                      display: flex; align-items: center; justify-content: center;
                      color: #999; font-size: 0.85em; border: 1px dashed #ccc; }}
  .feedback-list {{ color: #e74c3c; margin: 8px 0; padding-left: 20px; font-size: 0.9em; }}
  .footer {{ font-size: 0.75em; color: #95a5a6; margin-top: 24px; text-align: center; }}
  .badge-uncal {{ display:inline-block; padding:2px 8px; border-radius:4px;
                  background:#fff3cd; color:#856404; font-size:0.8em; }}
</style>
</head>
<body>

<div class="header">
  <div style="font-size:1.4em; font-weight:800; letter-spacing:1px">DRISHTI-LENS</div>
  <div style="opacity:0.8; font-size:0.9em">Diabetic Retinopathy Screening Report</div>
</div>

<div class="disclaimer">{DISCLAIMER_TEXT}</div>

<!-- Identity -->
<div class="card">
  <h3>Screening Identity</h3>
  <table class="info-table">
    <tr><td>Screening ID</td><td><code>{screening_id}</code></td></tr>
    <tr><td>Patient ID</td><td><code>{patient_id}</code></td></tr>
    <tr><td>Eye</td><td>{eye}</td></tr>
    <tr><td>Operator</td><td>{operator_name}</td></tr>
    <tr><td>Timestamp (UTC)</td><td>{now}</td></tr>
    <tr><td>Grading method</td><td>{method}</td></tr>
    <tr><td>Model available</td><td>{'Yes (DL model)' if model_available else 'No (rule-based prototype)'}</td></tr>
    <tr><td>Pipeline version</td><td>{PIPELINE_VERSION}</td></tr>
  </table>
</div>

<!-- Grade -->
<div class="card">
  <h3>AI Grading Result</h3>
  <div class="severity-badge">{severity_name} (Level {severity_level})</div>
  <div class="referable">{recommendation}</div>
  <table class="info-table">
    <tr><td>DME Risk</td><td>{dme_risk*100:.1f}%</td></tr>
    <tr><td>EFS Score</td><td>{efs_score:.3f}</td></tr>
    <tr><td>Raw Confidence</td><td>{confidence_raw:.3f}
      <span class="badge-uncal">NOT CALIBRATED until validation data run</span></td></tr>
    <tr><td>Calibrated Confidence</td><td>{calibrated_str}</td></tr>
  </table>
</div>

<!-- Quality -->
<div class="card">
  <h3>Image Quality Assessment</h3>
  {quality_html if quality_html else '<p style="color:#999">Quality assessment not run.</p>'}
  <p style="font-size:0.8em;color:#888">Enhancement applied: {'Yes' if enhancement_applied else 'No'}</p>
</div>

<!-- Lesion Findings -->
<div class="card">
  <h3>Lesion Findings — PROTOTYPE (not clinically validated)</h3>
  {'<table><thead><tr><th>Lesion</th><th>Candidates</th><th>Confidence</th><th>Disclaimer</th></tr></thead><tbody>' + lesion_rows + '</tbody></table>'
   if lesion_rows else '<p style="color:#999">Segmentation not run or no lesions detected.</p>'}
</div>

<!-- ICDR Rule Trace -->
<div class="card">
  <h3>ICDR Rule Trace</h3>
  {'<table><thead><tr><th>Rule ID</th><th>Met</th><th>Description</th><th>Zones</th></tr></thead><tbody>' + rule_rows + '</tbody></table>'
   if rule_rows else '<p style="color:#999">No rule trace available.</p>'}
</div>

<!-- Images -->
<div class="card">
  <h3>Images</h3>
  <div class="img-grid">
    {img_tag(original_b64, "Original Fundus")}
    {img_tag(enhanced_b64, "Enhanced (CLAHE + NLM)")}
    {img_tag(gradcam_b64, "Grad-CAM Overlay")}
    {img_tag(annotated_b64, "Annotated Lesions")}
  </div>
  {'<p style="font-size:0.8em;color:#c0392b;margin-top:8px">⚠ Grad-CAM not available — no trained model checkpoint. <br>Train model using backend/validation/train.py and provide dr_efficientnet_b4.pth.</p>'
   if not gradcam_b64 else ''}
</div>

<div class="footer">
  Generated by DRISHTI-LENS AI Pipeline v{PIPELINE_VERSION} at {now}<br>
  Smart India Hackathon 2026 — Team DRISHTI-LENS<br>
  This is an engineering prototype. Not for clinical use without ophthalmologist supervision.
</div>
</body>
</html>"""

    if output_path:
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            logger.info(f"Report saved to {output_path}")
        except Exception as exc:
            logger.error(f"Failed to save report: {exc}")

    return html
