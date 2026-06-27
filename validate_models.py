#!/usr/bin/env python3
"""
Historical validation / backtest for the space-weather physics models.

Compares model predictions against documented major storms:
 - CME transit time (Sun -> Earth) vs. observed arrival
 - Geomagnetic Dst minimum + NOAA G-category vs. observed

Observed values are representative figures from the space-weather literature
(CDAW/SOHO LASCO CME catalog, WDC Kyoto Dst, NOAA SWPC event reports). They are
approximate and meant for model-skill assessment, not official reconstruction.
"""

import numpy as np
from cme_physics_model import CMEPropagationModel
from geomagnetic_model import GeomagneticModel

cme = CMEPropagationModel()
gm = GeomagneticModel()

# ── CME arrival events: (label, initial speed km/s, observed Sun-Earth transit h) ──
CME_EVENTS = [
    ("2003-10-28 Halloween",   2029, 19.0),
    ("2000-07-14 Bastille Day", 1674, 28.0),
    ("2012-07-23 Extreme (STEREO-A)", 2246, 18.6),
    ("2006-12-13",             1774, 30.0),
    ("2015-03-15 St Patrick",   720, 48.0),
    ("2024-05-08 Gannon (lead CME)", 1500, 42.0),
]

# ── Geomagnetic storms: (label, v km/s, B nT, n cm^-3, observed min Dst nT) ──
DST_EVENTS = [
    ("2024-05-11 Gannon (G5)",   1000, 50, 20, -412),
    ("2003-10-29 Halloween (G5)", 1850, 40, 15, -383),
    ("2015-03-17 St Patrick (G4)", 600, 30, 12, -223),
    ("2017-09-08 (G4)",            800, 30, 10, -142),
    ("Quiet baseline",             400,  5,  5,  -10),
]

def dst_to_category(dst):
    if dst > -30:   return "quiet"
    if dst > -50:   return "G1"
    if dst > -100:  return "G2"
    if dst > -200:  return "G3"
    return "G4+"

print("=" * 78)
print("CME ARRIVAL-TIME BACKTEST  (ensemble: drag + kinematic + ENLIL-like)")
print("=" * 78)
print(f"{'Event':<32}{'v km/s':>8}{'obs h':>8}{'pred h':>9}{'err h':>8}  in-window")
arr_err = []
in_window = 0
for label, v, obs in CME_EVENTS:
    r = cme.ensemble_prediction({"speed": v})
    pred = r["arrival_time_hours"]
    lo = r.get("arrival_window_start_hours", pred)
    hi = r.get("arrival_window_end_hours", pred)
    err = pred - obs
    arr_err.append(err)
    win = lo <= obs <= hi
    in_window += win
    print(f"{label:<32}{v:>8}{obs:>8.1f}{pred:>9.1f}{err:>+8.1f}  {'YES' if win else 'no'}")
arr_err = np.array(arr_err)
print("-" * 78)
print(f"  MAE = {np.mean(np.abs(arr_err)):.1f} h   bias = {np.mean(arr_err):+.1f} h   "
      f"obs inside uncertainty window: {in_window}/{len(CME_EVENTS)}")

print()
print("=" * 78)
print("GEOMAGNETIC Dst BACKTEST  (Burton-equation ring-current model)")
print("=" * 78)
print(f"{'Event':<28}{'obs Dst':>9}{'pred Dst':>10}{'err':>8}{'obs G':>8}{'pred G':>9}  cat?")
dst_err = []
cat_hits = 0
for label, v, b, n, obs in DST_EVENTS:
    r = gm.dst_index_model({"wind_speed_km_s": v, "magnetic_field_nt": b, "density_cm3": n})
    pred = r["dst_predicted_nt"]
    err = pred - obs
    dst_err.append(err)
    obs_cat = dst_to_category(obs)
    pred_cat = r["storm_category"] or "quiet"
    hit = (obs_cat == pred_cat)
    cat_hits += hit
    print(f"{label:<28}{obs:>9.0f}{pred:>10.0f}{err:>+8.0f}{obs_cat:>8}{pred_cat:>9}  {'OK' if hit else 'x'}")
dst_err = np.array(dst_err)
print("-" * 78)
print(f"  Dst MAE = {np.mean(np.abs(dst_err)):.0f} nT   bias = {np.mean(dst_err):+.0f} nT   "
      f"G-category correct: {cat_hits}/{len(DST_EVENTS)}")
print()
print("Note: predicted vs observed are model-skill estimates against representative")
print("literature values; the category (NOAA G-scale) match is the most robust metric.")
