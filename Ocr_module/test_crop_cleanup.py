"""Review crop cleanup (crop_cleanup.py). Works in a temporary folder."""
import os
import shutil
import tempfile
import time
import unittest

import config
import crop_cleanup


def _session(upload, row):
    return {"ocr_data": {"fields": [
        {"category": "NAME", "crop": f"{upload}/p1_r{row}_c3.png", "row_crop": f"{upload}/s0_r{row}_row.png"},
        {"category": "BDAY", "crop": f"{upload}/p1_r{row}_c4.png", "row_crop": f"{upload}/s0_r{row}_row.png"},
    ]}}


class CropCleanupTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="crops_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def make(self, relative, age_days=0):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(b"png")
        if age_days:
            stamp = time.time() - age_days * 86400
            os.utime(path, (stamp, stamp))
        return path

    def test_setting_defaults_to_30_days(self):
        self.assertEqual(config.REVIEW_CROPS_MAX_AGE_DAYS, 30)

    def test_exported_session_loses_only_its_own_crops(self):
        mine = [self.make(f"up1/{n}") for n in ("p1_r2_c3.png", "p1_r2_c4.png", "s0_r2_row.png")]
        other = self.make("up1/p1_r3_c3.png")   # another row of the same upload, not exported
        removed = crop_cleanup.delete_session_crops(_session("up1", 2), folder=self.root)
        self.assertEqual(removed, 3)
        self.assertTrue(all(not os.path.exists(p) for p in mine))
        self.assertTrue(os.path.exists(other))

    def test_upload_folder_left_empty_is_removed(self):
        for n in ("p1_r2_c3.png", "p1_r2_c4.png", "s0_r2_row.png"):
            self.make(f"up1/{n}")
        crop_cleanup.delete_session_crops(_session("up1", 2), folder=self.root)
        self.assertFalse(os.path.exists(os.path.join(self.root, "up1")))
        self.assertTrue(os.path.isdir(self.root))

    def test_missing_files_and_paths_outside_the_folder_are_ignored(self):
        outside = tempfile.NamedTemporaryFile(delete=False, dir=os.path.dirname(self.root))
        outside.close()
        self.addCleanup(os.remove, outside.name)
        session = {"ocr_data": {"fields": [{"crop": "../" + os.path.basename(outside.name)},
                                           {"crop": "gone/p1_r1_c1.png"}]}}
        self.assertEqual(crop_cleanup.delete_session_crops(session, folder=self.root), 0)
        self.assertTrue(os.path.exists(outside.name))

    def test_session_without_ocr_data_is_fine(self):
        self.assertEqual(crop_cleanup.delete_session_crops(None, folder=self.root), 0)
        self.assertEqual(crop_cleanup.delete_session_crops({"ocr_data": None}, folder=self.root), 0)

    def test_startup_purge_removes_only_old_crops(self):
        old = self.make("old_upload/p1_r1_c1.png", age_days=45)
        recent = self.make("new_upload/p1_r1_c1.png", age_days=5)
        removed = crop_cleanup.purge_old_crops(30, folder=self.root)
        self.assertEqual(removed, 1)
        self.assertFalse(os.path.exists(old))
        self.assertFalse(os.path.exists(os.path.dirname(old)))
        self.assertTrue(os.path.exists(recent))

    def test_purge_turned_off_with_zero_days(self):
        old = self.make("old_upload/p1_r1_c1.png", age_days=400)
        self.assertEqual(crop_cleanup.purge_old_crops(0, folder=self.root), 0)
        self.assertTrue(os.path.exists(old))

    def test_purge_of_a_missing_folder_does_nothing(self):
        self.assertEqual(crop_cleanup.purge_old_crops(30, folder=os.path.join(self.root, "nope")), 0)


if __name__ == "__main__":
    unittest.main()
