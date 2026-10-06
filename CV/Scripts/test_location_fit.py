import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import location_fit as lf

# Synthetic home on the equator: 0.1 degree of longitude is about 11.1 km.
PREFS = {"home": {"label": "Synthetic town", "lat": 0.0, "lon": 0.0},
         "max_daily_commute_km": 30, "max_travel_percent": 50,
         "accepted_regions": ["Example metro area"]}


def prefs(**overrides):
    data = json.loads(json.dumps(PREFS))
    data.update(overrides)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "prefs.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return lf.load_preferences(path)


class LocationFitTest(unittest.TestCase):
    def test_remote_is_compatible(self):
        self.assertEqual(lf.assess(prefs(), "remote")["verdict"], "compatible")

    def test_nearby_office_is_compatible(self):
        result = lf.assess(prefs(), "onsite", (0.0, 0.1))
        self.assertEqual(result["verdict"], "compatible")
        self.assertEqual(result["straight_line_km_band"], 10)

    def test_far_onsite_is_incompatible(self):
        self.assertEqual(lf.assess(prefs(), "onsite", (0.0, 1.0))["verdict"], "incompatible")

    def test_far_hybrid_within_travel_limit_needs_review(self):
        result = lf.assess(prefs(), "hybrid", (0.0, 1.0), office_days=2)
        self.assertEqual(result["verdict"], "review")
        self.assertEqual(result["time_away_percent"], 40)

    def test_far_hybrid_with_travel_over_limit_is_incompatible(self):
        result = lf.assess(prefs(), "hybrid", (0.0, 1.0), office_days=2, travel_percent=20)
        self.assertEqual(result["verdict"], "incompatible")

    def test_far_hybrid_without_office_days_is_unknown(self):
        self.assertEqual(lf.assess(prefs(), "hybrid", (0.0, 1.0))["verdict"], "unknown")

    def test_travel_over_limit_blocks_remote(self):
        self.assertEqual(lf.assess(prefs(), "remote", travel_percent=60)["verdict"], "incompatible")

    def test_commute_limit_margin_needs_review(self):
        # 0.24 degrees is about 26.7 km straight, about 33 km by road.
        self.assertEqual(lf.assess(prefs(), "onsite", (0.0, 0.24))["verdict"], "review")

    def test_accepted_region_softens_commute_limit(self):
        result = lf.assess(prefs(), "onsite", (0.0, 0.5), in_region=True)
        self.assertEqual(result["verdict"], "review")

    def test_unknown_mode_is_unknown(self):
        self.assertEqual(lf.assess(prefs(), "unknown", (0.0, 0.1))["verdict"], "unknown")

    def test_output_never_contains_home(self):
        result = json.dumps(lf.assess(prefs(), "hybrid", (0.0, 1.0), office_days=1))
        self.assertNotIn("Synthetic town", result)
        self.assertNotIn('"lat"', result)

    def test_invalid_preferences_rejected(self):
        with self.assertRaises(ValueError):
            prefs(home={"lat": "x", "lon": 0})
        with self.assertRaises(ValueError):
            prefs(max_travel_percent=120)
        with self.assertRaises(ValueError):
            lf.load_preferences(Path("/nonexistent/prefs.json"))

    def test_cli_check_config_prints_no_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prefs.json"
            path.write_text(json.dumps(PREFS), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = lf.main(["--config", str(path), "check-config"])
        self.assertEqual(code, 0)
        self.assertNotIn("Synthetic", out.getvalue())


if __name__ == "__main__":
    unittest.main()
