import unittest

from template_engine import build_template_payload, score_template_match, match_templates


class TemplateMatchingTests(unittest.TestCase):
    def test_score_template_match_prefers_similar_layout(self):
        template = build_template_payload(
            name="Invoice A",
            grid_lines=[0.25, 0.5, 0.75],
            segment_info=[{"category": "A"}, {"category": "B"}, {"category": "C"}],
            crop_box_percent={"left": 0.05, "top": 0.1, "width": 0.9, "height": 0.2},
            row_template={"y": 100, "height": 40, "spacing": 0},
            crop_presets=[{"name": "Case", "x": 0.1, "y": 0.2, "width": 0.3, "height": 0.05}],
            image_width=1000,
            image_height=1200,
        )

        current = {
            "gridLines": [0.255, 0.505, 0.755],
            "rowTemplate": {"y": 100, "height": 40, "spacing": 0},
            "image_width": 1000,
            "image_height": 1200,
            "cropBoxPercent": {"left": 0.05, "top": 0.1, "width": 0.9, "height": 0.2},
        }

        score = score_template_match(template, current)
        self.assertGreaterEqual(score, 0.75)

    def test_template_payload_includes_crop_and_grid_presets(self):
        payload = build_template_payload(
            name="Form 1",
            grid_lines=[0.2, 0.4],
            segment_info=[{"category": "A"}, {"category": "B"}],
            crop_box_percent={"left": 0.1, "top": 0.2, "width": 0.8, "height": 0.1},
            row_template={"y": 80, "height": 30, "spacing": 4},
            crop_presets=[{"name": "Case", "x": 0.1, "y": 0.2, "width": 0.3, "height": 0.05}],
            image_width=800,
            image_height=1000,
        )

        self.assertEqual(payload["name"], "Form 1")
        self.assertEqual(payload["gridLines"], [0.2, 0.4])
        self.assertEqual(payload["cropPresets"][0]["name"], "Case")
        self.assertEqual(payload["rowTemplate"]["height"], 30)

    def test_match_templates_prefers_similar_line_spacing(self):
        similar_template = build_template_payload(
            name="Similar Layout",
            grid_lines=[0.2, 0.5],
            segment_info=[{"category": "A"}, {"category": "B"}],
            crop_box_percent={"left": 0.05, "top": 0.1, "width": 0.9, "height": 0.2},
            row_template={"y": 100, "height": 40, "spacing": 0},
            crop_presets=[{"name": "Case", "x": 0.1, "y": 0.2, "width": 0.3, "height": 0.05}],
            image_width=1000,
            image_height=1200,
            metadata={"line_spacing": 0.018},
        )
        different_template = build_template_payload(
            name="Different Layout",
            grid_lines=[0.2, 0.5],
            segment_info=[{"category": "A"}, {"category": "B"}],
            crop_box_percent={"left": 0.05, "top": 0.1, "width": 0.9, "height": 0.2},
            row_template={"y": 100, "height": 40, "spacing": 0},
            crop_presets=[{"name": "Case", "x": 0.1, "y": 0.2, "width": 0.3, "height": 0.05}],
            image_width=1000,
            image_height=1200,
            metadata={"line_spacing": 0.05},
        )
        current = {
            "gridLines": [0.2, 0.5],
            "rowTemplate": {"y": 100, "height": 40, "spacing": 0},
            "image_width": 1000,
            "image_height": 1200,
            "cropBoxPercent": {"left": 0.05, "top": 0.1, "width": 0.9, "height": 0.2},
            "lineSpacing": 0.018,
            "rowCount": 4,
        }

        best_template, best_score = match_templates([different_template, similar_template], current)
        self.assertEqual(best_template["name"], "Similar Layout")
        self.assertGreaterEqual(best_score, 0.75)


if __name__ == "__main__":
    unittest.main()
