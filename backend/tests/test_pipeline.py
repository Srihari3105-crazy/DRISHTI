"""
Tests for Full AI Screening Pipeline Orchestrator.
"""
import io
import cv2
import numpy as np
import pytest
from services.ai_pipeline.pipeline import run_pipeline, PipelineResult


def _create_synthetic_fundus_bytes():
    # Synthetic circular image simulating a fundus photograph with realistic FOV and brightness
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    # Bright retinal fundus circle covering ~75% of image
    cv2.circle(img, (200, 200), 190, (40, 150, 210), -1)  # warm orange-red fundus
    cv2.circle(img, (130, 200), 30, (100, 210, 245), -1)  # bright optic disc
    cv2.circle(img, (260, 200), 8, (20, 80, 130), -1)     # fovea
    # Synthetic microaneurysm dot
    cv2.circle(img, (220, 170), 4, (10, 30, 60), -1)

    _, encoded = cv2.imencode('.jpg', img)
    return encoded.tobytes()


def test_pipeline_valid_image():
    img_bytes = _create_synthetic_fundus_bytes()
    res = run_pipeline(
        image_bytes=img_bytes,
        screening_id="test_scr_01",
        patient_id="test_pat_01",
        eye="OD"
    )

    assert isinstance(res, PipelineResult)
    assert res.final_quality_decision in ("QUALITY_GOOD", "QUALITY_BORDERLINE")
    assert res.severity_level >= 0
    assert isinstance(res.severity_name, str)
    assert res.report_html is not None
    assert "DRISHTI-LENS" in res.report_html
    assert "AI-ASSISTED SCREENING" in res.report_html
    assert res.processing_time_ms > 0


def test_pipeline_corrupted_bytes():
    bad_bytes = b"not_an_image_data"
    res = run_pipeline(
        image_bytes=bad_bytes,
        screening_id="test_scr_bad",
        patient_id="test_pat_bad",
    )
    assert res.final_quality_decision == "QUALITY_UNGRADABLE"
    assert "Image decode failed" in res.quality_feedback[0]
