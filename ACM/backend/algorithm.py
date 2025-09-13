#!/usr/bin/env python3
"""
IoU-based Shape Matching for GPS routes vs SVG target

Approach (as requested):
1) Center and scale BOTH shapes to a common frame without altering aspect ratio
2) Rotate the GPS route to maximize area-based similarity with the target
3) Output an area-based similarity score (intersection - GPS-outside - target-missed), IoU, and coverage metrics

Single-file script. Set these two inputs manually below:
 - TARGET_SVG: SVG path string (M/L/H/V/C/Q/Z supported)
 - GPS_ROUTE: list of [lat, lng] points (dense, noisy acceptable)
"""

import math
import re
import numpy as np
import matplotlib.path as mpath
from celsius import *


# ===================== USER INPUTS (EDIT THESE) =====================

# Example SVGs (uncomment one and paste your own as needed)
# Ellipse target (center at 12,12; radii rx=9, ry=6)
TARGET_SVG = """
<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <rect x="6" y="8" width="12" height="8"/>
 </svg>
"""

# Example GPS route: list of [latitude, longitude]
# Replace with your Strava (or other) route points
GPS_ROUTE = RECTANGLE_STRAVA_COORDINATES

# ===================================================================


# ---------------------- SVG path parsing ---------------------------
def parse_svg_path(path_string: str) -> np.ndarray:
    """Parse SVG path string into array of [x, y] points.
    Supports M, L, H, V, C, Q and Z absolute commands.
    Curves (C/Q) are sampled into line segments.
    """
    s = path_string.strip().replace("\n", " ").replace(",", " ")
    tokens = re.findall(r"[MLCQHVZz]|[-+]?\d*\.?\d+", s)
    if not tokens:
        raise ValueError("TARGET_SVG is empty or invalid.")

    pts = []
    i = 0
    cur = [0.0, 0.0]
    start = [0.0, 0.0]

    def add(p):
        pts.append([float(p[0]), float(p[1])])

    def cubic(p0, p1, p2, p3, t):
        mt = 1 - t
        return [
            mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0],
            mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1],
        ]

    def quad(p0, p1, p2, t):
        mt = 1 - t
        return [
            mt**2 * p0[0] + 2 * mt * t * p1[0] + t**2 * p2[0],
            mt**2 * p0[1] + 2 * mt * t * p1[1] + t**2 * p2[1],
        ]

    while i < len(tokens):
        cmd = tokens[i]
        if cmd == "M":
            cur = [float(tokens[i+1]), float(tokens[i+2])]
            start = cur.copy()
            add(cur)
            i += 3
        elif cmd == "L":
            cur = [float(tokens[i+1]), float(tokens[i+2])]
            add(cur)
            i += 3
        elif cmd == "H":
            cur = [float(tokens[i+1]), cur[1]]
            add(cur)
            i += 2
        elif cmd == "V":
            cur = [cur[0], float(tokens[i+1])]
            add(cur)
            i += 2
        elif cmd == "C":
            p1 = [float(tokens[i+1]), float(tokens[i+2])]
            p2 = [float(tokens[i+3]), float(tokens[i+4])]
            p3 = [float(tokens[i+5]), float(tokens[i+6])]
            # sample 12 segments along the cubic
            for t in np.linspace(0.1, 1.0, 12):
                p = cubic(cur, p1, p2, p3, t)
                add(p)
            cur = p3
            i += 7
        elif cmd == "Q":
            p1 = [float(tokens[i+1]), float(tokens[i+2])]
            p2 = [float(tokens[i+3]), float(tokens[i+4])]
            # sample 10 segments along the quadratic
            for t in np.linspace(0.1, 1.0, 10):
                p = quad(cur, p1, p2, t)
                add(p)
            cur = p2
            i += 5
        elif cmd in ("z", "Z"):
            if not np.allclose(pts[0], pts[-1]):
                pts.append(pts[0])
            i += 1
        else:
            # Unrecognized token (number when command expected) → skip
            i += 1

    arr = np.array(pts, dtype=float)
    if arr.size == 0:
        raise ValueError("Parsed SVG produced 0 points.")
    return arr


# ----------------- SVG convenience: accept full <svg> with shapes -------------
def parse_svg_input(svg_text: str) -> np.ndarray:
    """Accept either a raw path string (M/L/H/V/C/Q/Z) or a full <svg> containing
    <path d="...">, <ellipse ...>, <circle ...>, or <rect ...> and return Nx2 points.
    """
    s = svg_text.strip()
    # If it looks like XML, try to extract supported elements
    if s.startswith('<'):
        # path d="..." or d='...'
        m = re.search(r"\bd=\s*['\"]([^'\"]+)['\"]", s)
        if m:
            return parse_svg_path(m.group(1))

        # ellipse cx cy rx ry
        me = re.search(r"<ellipse[^>]*\bcx=\s*['\"]([\d.+-]+)['\"][^>]*\bcy=\s*['\"]([\d.+-]+)['\"][^>]*\brx=\s*['\"]([\d.+-]+)['\"][^>]*\bry=\s*['\"]([\d.+-]+)['\"]", s)
        if me:
            cx = float(me.group(1)); cy = float(me.group(2))
            rx = float(me.group(3)); ry = float(me.group(4))
            t = np.linspace(0, 2*np.pi, 256, endpoint=True)
            x = cx + rx * np.cos(t)
            y = cy + ry * np.sin(t)
            pts = np.column_stack([x, y])
            if not np.allclose(pts[0], pts[-1]):
                pts = np.vstack([pts, pts[0]])
            return pts

        # circle cx cy r
        mc = re.search(r"<circle[^>]*\bcx=\s*['\"]([\d.+-]+)['\"][^>]*\bcy=\s*['\"]([\d.+-]+)['\"][^>]*\br=\s*['\"]([\d.+-]+)['\"]", s)
        if mc:
            cx = float(mc.group(1)); cy = float(mc.group(2)); r = float(mc.group(3))
            t = np.linspace(0, 2*np.pi, 256, endpoint=True)
            x = cx + r * np.cos(t)
            y = cy + r * np.sin(t)
            pts = np.column_stack([x, y])
            if not np.allclose(pts[0], pts[-1]):
                pts = np.vstack([pts, pts[0]])
            return pts

        # rect x y width height (x/y optional; default 0)
        mr = re.search(r"<rect[^>]*\bwidth=\s*['\"]([\d.+-]+)['\"][^>]*\bheight=\s*['\"]([\d.+-]+)['\"][^>]*", s)
        if mr:
            # pull x/y if present
            mx = re.search(r"\bx=\s*['\"]([\d.+-]+)['\"]", s)
            my = re.search(r"\by=\s*['\"]([\d.+-]+)['\"]", s)
            x = float(mx.group(1)) if mx else 0.0
            y = float(my.group(1)) if my else 0.0
            w = float(mr.group(1)); h = float(mr.group(2))
            pts = np.array([[x, y], [x+w, y], [x+w, y+h], [x, y+h], [x, y]], dtype=float)
            return pts

        raise ValueError("SVG did not contain a supported <path>, <ellipse>, <circle>, or <rect> element.")

    # Otherwise assume raw path commands
    return parse_svg_path(s)


# ----------------- GPS: lat/lng → local XY (meters) ----------------
def latlng_to_xy(points: list[list[float]]) -> np.ndarray:
    arr = np.array(points, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 2 or arr.shape[0] < 2:
        raise ValueError("GPS_ROUTE must be a list of [lat, lng] with at least 2 points.")

    lat = arr[:, 0]
    lng = arr[:, 1]
    lat0 = np.mean(lat)
    lng0 = np.mean(lng)

    # Equirectangular projection (good for small areas)
    R = 6371000.0
    x = R * np.radians(lng - lng0) * np.cos(np.radians(lat0))
    y = R * np.radians(lat - lat0)
    return np.column_stack([x, y])


# ----------------- Normalize: center + scale (aspect kept) ---------
def center_and_scale(points: np.ndarray) -> np.ndarray:
    if points.ndim != 2 or points.shape[0] < 2:
        raise ValueError("Need at least 2 points to normalize.")
    centroid = np.mean(points, axis=0)
    centered = points - centroid
    max_dim = np.max(np.abs(centered))
    if max_dim <= 0:
        return centered
    return centered / max_dim


# ----------------- Rasterization helpers ---------------------------
def grid_lin(grid_size: int):
    lin = np.linspace(-1, 1, grid_size)
    X, Y = np.meshgrid(lin, lin)
    return X, Y


def target_polygon_mask(poly_norm: np.ndarray, grid_size: int) -> np.ndarray:
    # Ensure closed
    if not np.allclose(poly_norm[0], poly_norm[-1]):
        poly_norm = np.vstack([poly_norm, poly_norm[0]])
    Path = mpath.Path
    path = Path(poly_norm)
    X, Y = grid_lin(grid_size)
    pts = np.column_stack([X.ravel(), Y.ravel()])
    inside = path.contains_points(pts)
    return inside.reshape(grid_size, grid_size)


def gps_path_mask(gps_norm: np.ndarray, grid_size: int, stroke_norm: float) -> np.ndarray:
    # Draw thick polyline by distance-to-segment thresholding in normalized space
    X, Y = grid_lin(grid_size)
    mask = np.zeros((grid_size, grid_size), dtype=bool)
    r = float(stroke_norm)
    for i in range(len(gps_norm) - 1):
        p0 = gps_norm[i]
        p1 = gps_norm[i + 1]
        v = p1 - p0
        vv = v[0] * v[0] + v[1] * v[1]
        if vv <= 1e-18:
            # treat as disk around p0
            dist = np.sqrt((X - p0[0]) ** 2 + (Y - p0[1]) ** 2)
            mask |= dist <= r
            continue
        dx = X - p0[0]
        dy = Y - p0[1]
        t = (dx * v[0] + dy * v[1]) / vv
        t = np.clip(t, 0.0, 1.0)
        projx = p0[0] + t * v[0]
        projy = p0[1] + t * v[1]
        dist = np.sqrt((X - projx) ** 2 + (Y - projy) ** 2)
        mask |= dist <= r
    return mask


def iou(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    inter = np.logical_and(mask_a, mask_b).sum()
    union = np.logical_or(mask_a, mask_b).sum()
    return (inter / union) if union > 0 else 0.0


def signed_overlap(mask_gps: np.ndarray, mask_target: np.ndarray) -> float:
    """Signed overlap measure with dual penalties:
    score = (intersection - gps_outside - target_missed) / target_area
    - intersection: pixels inside both GPS and Target
    - gps_outside: pixels of GPS that extend outside Target
    - target_missed: pixels of Target not covered by GPS
    - target_area: total pixels of Target
    Can be negative if penalties dominate.
    """
    inter = np.logical_and(mask_gps, mask_target).sum()
    outside = np.logical_and(mask_gps, np.logical_not(mask_target)).sum()
    target_missed = np.logical_and(mask_target, np.logical_not(mask_gps)).sum()
    target_area = mask_target.sum()
    if target_area == 0:
        return 0.0
    return (inter - outside - target_missed) / float(target_area)


# ----------------- Rotation search -------------------------------
def best_overlap_iou(gps_latlng: list, svg_path: str,
                     grid_size: int = 256,
                     stroke_width_norm: float = 0.02,
                     coarse_step: int = 5,
                     fine_step: int = 1):

    # Prepare GPS
    gps_xy = latlng_to_xy(gps_latlng)
    gps_norm = center_and_scale(gps_xy)

    # Prepare target
    svg_pts = parse_svg_input(svg_path)
    target_norm = center_and_scale(svg_pts)

    # Precompute target mask once
    tgt_mask = target_polygon_mask(target_norm, grid_size)

    # Coarse rotation search (maximize signed overlap)
    best_score = -1e9
    best_angle = 0
    for ang in range(0, 360, coarse_step):
        a = math.radians(ang)
        c, s = math.cos(a), math.sin(a)
        R = np.array([[c, -s], [s, c]])
        gps_rot = gps_norm @ R.T
        gps_mask = gps_path_mask(gps_rot, grid_size, stroke_width_norm)
        val = signed_overlap(gps_mask, tgt_mask)
        if val > best_score:
            best_score = val
            best_angle = ang

    # Fine search around best
    start = best_angle - coarse_step
    end = best_angle + coarse_step
    for ang in range(start, end + 1, fine_step):
        a = math.radians((ang + 360) % 360)
        c, s = math.cos(a), math.sin(a)
        R = np.array([[c, -s], [s, c]])
        gps_rot = gps_norm @ R.T
        gps_mask = gps_path_mask(gps_rot, grid_size, stroke_width_norm)
        val = signed_overlap(gps_mask, tgt_mask)
        if val > best_score:
            best_score = val
            best_angle = (ang + 360) % 360

    # Coverage diagnostics at best angle
    a = math.radians(best_angle)
    c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s], [s, c]])
    gps_rot = gps_norm @ R.T
    gps_mask = gps_path_mask(gps_rot, grid_size, stroke_width_norm)
    inter = np.logical_and(gps_mask, tgt_mask).sum()
    outside = np.logical_and(gps_mask, np.logical_not(tgt_mask)).sum()
    missed = np.logical_and(tgt_mask, np.logical_not(gps_mask)).sum()
    tgt_area = tgt_mask.sum()
    gps_area = gps_mask.sum()
    cov_target = (inter / tgt_area) * 100 if tgt_area > 0 else 0.0
    cov_gps = (inter / gps_area) * 100 if gps_area > 0 else 0.0
    # Report both signed and plain IoU for transparency
    signed_score = (inter - outside - missed) / float(tgt_area) if tgt_area > 0 else 0.0
    iou_score = iou(gps_mask, tgt_mask)

    return {
        "similarity_score_pct": round(signed_score * 100, 1),
        "overlap_signed_pct": round(signed_score * 100, 1),
        "overlap_iou_pct": round(iou_score * 100, 1),
        "coverage_of_target_pct": round(cov_target, 1),
        "coverage_of_gps_pct": round(cov_gps, 1),
        "best_rotation_deg": int(best_angle)
    }


def main():
    print("=" * 60)
    print("SHAPE MATCHING ANALYSIS")
    print("=" * 60)
    try:
        result = best_overlap_iou(
            gps_latlng=GPS_ROUTE,
            svg_path=TARGET_SVG,
            grid_size=256,
            stroke_width_norm=0.02,
            coarse_step=5,
            fine_step=1,
        )

        print("\n📊 OVERLAP RESULTS:")
        print(f"  Similarity (area-based): {result['similarity_score_pct']:.1f}%")
        print(f"  Overlap (IoU): {result['overlap_iou_pct']:.1f}%")
        print(f"  Coverage of Target: {result['coverage_of_target_pct']:.1f}%")
        print(f"  Coverage of GPS: {result['coverage_of_gps_pct']:.1f}%")
        print(f"  Best Rotation: {result['best_rotation_deg']}°")

        # Final single number as requested
        print(f"\nFINAL SCORE: {result['similarity_score_pct']:.1f}%")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nPlease check that:")
        print("  1) GPS_ROUTE is a list of [lat, lng] with ≥ 2 points")
        print("  2) TARGET_SVG is a valid SVG path string (M/L/H/V/C/Q/Z)")
        print("  3) Shapes are non-degenerate (not all points equal)")


if __name__ == "__main__":
    main()


