"""
Tests for DR Grading module and ICDR criteria mapping.
"""
import numpy as np
import pytest
from services.ai_pipeline.grading import grade_image, _grade_rule_based
from services.ai_pipeline.segmentation import (
    SegmentationResult, OpticDiscResult, FoveaResult, VesselResult, LesionResult
)


def _make_dummy_seg(ma=0, ex=0, he=0, nv=0):
    shape = (200, 200)
    return SegmentationResult(
        optic_disc=OpticDiscResult(mask=None, center_xy=(100, 100), radius_px=15, confidence=0.7),
        fovea=FoveaResult(center_xy=(150, 100), confidence=0.4),
        vessels=VesselResult(mask=None, probability_map=None),
        microaneurysms=LesionResult("MA", None, ma, 0.5 if ma > 0 else 0.0, [], "test"),
        exudates=LesionResult("EX", None, ex, 0.5 if ex > 0 else 0.0, [], "test"),
        hemorrhages=LesionResult("HE", None, he, 0.5 if he > 0 else 0.0, [], "test"),
        neovascularization=LesionResult("NV", None, nv, 0.5 if nv > 0 else 0.0, [], "test"),
        image_shape=shape,
    )


def test_grading_no_dr():
    seg = _make_dummy_seg(ma=0, ex=0, he=0, nv=0)
    res = _grade_rule_based(seg)
    assert res.severity_level == 0
    assert res.severity_name == "No DR"
    assert res.referable is False


def test_grading_mild_dr():
    seg = _make_dummy_seg(ma=2, ex=0, he=0, nv=0)
    res = _grade_rule_based(seg)
    assert res.severity_level == 1
    assert res.severity_name == "Mild NPDR"
    assert res.referable is False


def test_grading_moderate_dr():
    seg = _make_dummy_seg(ma=4, ex=3, he=1, nv=0)
    res = _grade_rule_based(seg)
    assert res.severity_level == 2
    assert res.severity_name == "Moderate NPDR"
    assert res.referable is True


def test_grading_severe_dr():
    seg = _make_dummy_seg(ma=8, ex=6, he=12, nv=0)
    res = _grade_rule_based(seg)
    assert res.severity_level == 3
    assert res.severity_name == "Severe NPDR"
    assert res.referable is True


def test_grading_pdr():
    seg = _make_dummy_seg(ma=5, ex=2, he=3, nv=2)
    res = _grade_rule_based(seg)
    assert res.severity_level == 4
    assert res.severity_name == "Proliferative DR"
    assert res.referable is True
