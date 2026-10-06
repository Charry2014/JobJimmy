#!/usr/bin/env python3
"""Assess a role's location and working model against private location preferences.

Standard library only; makes no network request. The preferences live in the
private vault (default ``JobSearch/Templates/location-preferences.json``)::

    {
      "home": {"label": "Home town", "lat": 0.0, "lon": 0.0},
      "max_daily_commute_km": 30,
      "max_travel_percent": 50,
      "accepted_regions": ["Example metropolitan area"],
      "road_factor": 1.25
    }

The office location of the role is public advert data and is passed as
coordinates. Output never contains the home label or coordinates: the distance
is rounded to a 5 km band so a hosted agent can use the result as a fit factor.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "JobSearch/Templates/location-preferences.json"
WORK_MODES = ("onsite", "hybrid", "remote", "unknown")
WORKDAYS = 5
DISTANCE_BAND_KM = 5


def load_preferences(path: Path) -> dict:
    try:
        prefs = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError("Location preferences not found; location fit unavailable.") from None
    except json.JSONDecodeError:
        raise ValueError("Location preferences are not valid JSON.") from None
    home = prefs.get("home") if isinstance(prefs, dict) else None
    if not isinstance(home, dict) or not all(isinstance(home.get(k), (int, float)) for k in ("lat", "lon")):
        raise ValueError("Location preferences need home.lat and home.lon as numbers.")
    if not (-90 <= home["lat"] <= 90 and -180 <= home["lon"] <= 180):
        raise ValueError("Home coordinates are out of range.")
    for key in ("max_daily_commute_km", "max_travel_percent"):
        value = prefs.get(key)
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"Location preferences need a non-negative {key}.")
    if prefs["max_travel_percent"] > 100:
        raise ValueError("max_travel_percent cannot exceed 100.")
    factor = prefs.setdefault("road_factor", 1.25)
    if not isinstance(factor, (int, float)) or factor < 1:
        raise ValueError("road_factor must be a number of at least 1.")
    prefs.setdefault("accepted_regions", [])
    return prefs


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def band(km: float) -> int:
    return int(DISTANCE_BAND_KM * round(km / DISTANCE_BAND_KM))


def assess(prefs: dict, work_mode: str, office: tuple[float, float] | None = None,
           office_days: float | None = None, travel_percent: float | None = None,
           in_region: bool = False) -> dict:
    """Return a verdict: compatible, review, incompatible or unknown, with reasons."""
    max_commute = prefs["max_daily_commute_km"]
    max_travel = prefs["max_travel_percent"]
    reasons: list[str] = []
    result = {"work_mode": work_mode, "max_daily_commute_km": max_commute,
              "max_travel_percent": max_travel, "accepted_regions": prefs["accepted_regions"]}
    verdicts: list[str] = []

    if travel_percent is not None:
        result["stated_travel_percent"] = travel_percent
        if travel_percent > max_travel:
            verdicts.append("incompatible")
            reasons.append(f"Stated travel {travel_percent:g}% exceeds the {max_travel:g}% limit.")
        else:
            reasons.append(f"Stated travel {travel_percent:g}% is within the {max_travel:g}% limit.")

    if work_mode == "remote":
        verdicts.append("compatible")
        reasons.append("Remote role: no daily commute.")
    elif work_mode == "unknown" or office is None:
        verdicts.append("unknown")
        reasons.append("Working model or office location not stated; ask before scoring it.")
    else:
        straight = haversine_km(prefs["home"]["lat"], prefs["home"]["lon"], *office)
        road = straight * prefs["road_factor"]
        result["straight_line_km_band"] = band(straight)
        result["estimated_road_km_band"] = band(road)
        if road <= max_commute:
            verdicts.append("compatible")
            reasons.append(f"Office within daily commute (about {band(road)} km by road).")
        elif road <= max_commute * 1.2:
            verdicts.append("review")
            reasons.append(f"Office near the commute limit (about {band(road)} km by road); "
                           "check the actual route.")
        elif in_region:
            verdicts.append("review")
            reasons.append(f"Office about {band(road)} km by road, beyond the daily commute limit "
                           "but inside an accepted region; check the actual commute.")
        elif work_mode == "onsite":
            verdicts.append("incompatible")
            reasons.append(f"Full on-site role about {band(road)} km by road, beyond daily commute.")
        else:
            if office_days is None:
                verdicts.append("unknown")
                reasons.append("Hybrid office beyond daily commute; office days per week not stated.")
            else:
                share = 100 * office_days / WORKDAYS + (travel_percent or 0)
                result["time_away_percent"] = round(share)
                if share <= max_travel:
                    verdicts.append("review")
                    reasons.append(f"Office beyond daily commute; {office_days:g} office day(s)/week "
                                   f"means about {share:.0f}% time away, within the {max_travel:g}% limit.")
                else:
                    verdicts.append("incompatible")
                    reasons.append(f"Office beyond daily commute; about {share:.0f}% time away "
                                   f"exceeds the {max_travel:g}% limit.")

    order = ("incompatible", "unknown", "review", "compatible")
    result["verdict"] = next(v for v in order if v in verdicts)
    result["reasons"] = reasons
    result["note"] = ("Distances are straight-line estimates rounded to 5 km bands; "
                      "road distance uses road_factor. Region membership is judged by the agent.")
    return result


def parse_coords(text: str) -> tuple[float, float]:
    try:
        lat, lon = (float(part) for part in text.split(","))
    except ValueError:
        raise argparse.ArgumentTypeError("Use LAT,LON, for example 51.5,-0.12.") from None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise argparse.ArgumentTypeError("Coordinates out of range.")
    return lat, lon


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                        help="private location preferences JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check-config", help="validate the preferences without printing them")
    run = sub.add_parser("assess", help="assess one role's location and working model")
    run.add_argument("--work-mode", choices=WORK_MODES, required=True)
    run.add_argument("--office", type=parse_coords, help="office coordinates as LAT,LON")
    run.add_argument("--office-days", type=float, help="required office days per week (hybrid)")
    run.add_argument("--travel-percent", type=float, help="stated business travel share")
    run.add_argument("--in-accepted-region", action="store_true",
                     help="the office lies inside one of the accepted regions")
    args = parser.parse_args(argv)

    try:
        prefs = load_preferences(args.config)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    if args.command == "check-config":
        print("Location preferences valid.")
        return 0
    if args.office_days is not None and not 0 <= args.office_days <= WORKDAYS:
        parser.error(f"--office-days must be between 0 and {WORKDAYS}.")
    print(json.dumps(assess(prefs, args.work_mode, args.office, args.office_days,
                            args.travel_percent, args.in_accepted_region), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
