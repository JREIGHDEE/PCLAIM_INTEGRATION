"""Tests for image_quality.py. Pure OpenCV/numpy on synthetic in-memory
images - no files, no DB, no Flask. Same flat-file unittest convention as
test_template_matching.py / test_philhealth_mapping.py.
"""
import unittest

import cv2
import numpy as np

import config
from image_quality import assess_image_quality, compute_blur_score, compute_brightness_score


def _solid_image(value, size=200):
    """size x size x 3 BGR image, every pixel the same gray value."""
    return np.full((size, size, 3), value, dtype=np.uint8)


def _noisy_image(size=200, seed=0):
    """size x size x 3 BGR image of random noise - lots of high-frequency
    edges (sharp), centered near mid-gray brightness."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, size=(size, size, 3), dtype=np.uint8)


class ImageQualityScoreTests(unittest.TestCase):
    def test_compute_blur_score_zero_for_flat_image(self):
        # A perfectly uniform image has no edges at all - Laplacian variance is 0.
        self.assertEqual(compute_blur_score(_solid_image(128)), 0.0)

    def test_compute_blur_score_high_for_noisy_image(self):
        self.assertGreater(compute_blur_score(_noisy_image()), config.IMAGE_QUALITY_BLUR_THRESHOLD)

    def test_compute_blur_score_handles_none_and_empty(self):
        self.assertEqual(compute_blur_score(None), 0.0)
        self.assertEqual(compute_blur_score(np.zeros((0, 0, 3), dtype=np.uint8)), 0.0)

    def test_compute_brightness_score_matches_solid_value(self):
        self.assertAlmostEqual(compute_brightness_score(_solid_image(128)), 128.0, places=1)

    def test_compute_brightness_score_handles_none_and_empty(self):
        self.assertEqual(compute_brightness_score(None), 0.0)
        self.assertEqual(compute_brightness_score(np.zeros((0, 0, 3), dtype=np.uint8)), 0.0)


class AssessImageQualityTests(unittest.TestCase):
    def test_flat_bright_image_is_blurry_and_too_bright(self):
        result = assess_image_quality(_solid_image(255))
        self.assertTrue(result["is_blurry"])
        self.assertTrue(result["is_too_bright"])
        self.assertFalse(result["is_too_dark"])
        self.assertEqual(len(result["warnings"]), 2)

    def test_flat_dark_image_is_blurry_and_too_dark(self):
        result = assess_image_quality(_solid_image(10))
        self.assertTrue(result["is_blurry"])
        self.assertTrue(result["is_too_dark"])
        self.assertFalse(result["is_too_bright"])

    def test_mid_gray_flat_image_has_no_brightness_warning_but_is_blurry(self):
        result = assess_image_quality(_solid_image(128))
        self.assertTrue(result["is_blurry"])
        self.assertFalse(result["is_too_dark"])
        self.assertFalse(result["is_too_bright"])
        self.assertEqual(len(result["warnings"]), 1)
        self.assertIn("blurry", result["warnings"][0])

    def test_sharp_mid_brightness_image_has_no_warnings(self):
        result = assess_image_quality(_noisy_image())
        self.assertFalse(result["is_blurry"])
        self.assertFalse(result["is_too_dark"])
        self.assertFalse(result["is_too_bright"])
        self.assertEqual(result["warnings"], [])

    def test_clean_white_document_is_not_overexposed(self):
        # Mostly white paper with a little dark text - a normal scan has a
        # high mean brightness but is not overexposed.
        page = _solid_image(250, size=400)
        for row in range(40, 360, 40):
            cv2.putText(page, "Dela Cruz 06/10/2026", (20, row), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 20, 20), 1)
        result = assess_image_quality(page)
        self.assertGreater(result["brightness_score"], config.IMAGE_QUALITY_BRIGHTNESS_HIGH)
        self.assertFalse(result["is_too_bright"])
        self.assertTrue(result["passed"])

    def test_washed_out_document_is_overexposed(self):
        page = _solid_image(250, size=400)
        for row in range(40, 360, 40):
            cv2.putText(page, "Dela Cruz 06/10/2026", (20, row), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        result = assess_image_quality(page)
        self.assertTrue(result["is_too_bright"])
        self.assertFalse(result["passed"])

    def test_result_is_tagged_as_rule_iq_01(self):
        self.assertEqual(assess_image_quality(_noisy_image())["rule_id"], "IQ-01")

    def test_never_raises_on_none(self):
        result = assess_image_quality(None)
        self.assertEqual(result["blur_score"], 0.0)
        self.assertEqual(result["brightness_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
