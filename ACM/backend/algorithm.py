#!/usr/bin/env python3
"""
IoU-based Shape Matching for GPS routes vs SVG target

Approach (as requested):
1) Center and scale BOTH shapes to a common frame without altering aspect ratio
2) Rotate the GPS route to maximize AREA OVERLAP with the target
3) Output a single numerical overlap percentage (IoU) and coverage metrics

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
# Oval target (center at 12,12; radii rx=9, ry=6)
TARGET_SVG = """
<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <rect x="3" y="6" width="18" height="12"/>
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
def center_svg_points(points: np.ndarray) -> np.ndarray:
    """Center SVG points so their centroid is at the viewBox center (12,12 for 24x24 viewBox)."""
    if points.shape[0] < 2:
        return points
    
    # Calculate centroid of the points
    centroid = np.mean(points, axis=0)
    
    # Calculate shift to center at viewBox center (assuming 24x24 viewBox)
    viewbox_center = np.array([12.0, 12.0])
    shift = viewbox_center - centroid
    
    # Apply shift
    centered_points = points + shift
    
    return centered_points


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
            return center_svg_points(pts)

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
            return center_svg_points(pts)

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
            return center_svg_points(pts)

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
    
    # Center the points at origin
    centroid = np.mean(points, axis=0)
    centered = points - centroid
    
    # Scale to fit in [-1, 1] range while preserving aspect ratio
    max_dim = np.max(np.abs(centered))
    if max_dim <= 0:
        return centered
    
    # Scale by 0.85 to leave some padding
    scaled = centered / max_dim * 0.85
    
    # Ensure the centroid is exactly at (0,0) after scaling
    final_centroid = np.mean(scaled, axis=0)
    return scaled - final_centroid


# ----------------- Rasterization helpers ---------------------------
def grid_lin(grid_size: int):
    lin = np.linspace(-1, 1, grid_size)
    X, Y = np.meshgrid(lin, lin)
    return X, Y




def get_mask_geometric_center(mask: np.ndarray) -> tuple[float, float]:
    """Get the geometric center of a binary mask in grid coordinates."""
    if mask.sum() == 0:
        return (mask.shape[1] // 2, mask.shape[0] // 2)  # return grid center if empty
    
    y_coords, x_coords = np.where(mask)
    center_x = np.mean(x_coords)
    center_y = np.mean(y_coords)
    return (center_x, center_y)


def align_shapes_to_target_center(gps_points: np.ndarray, target_mask: np.ndarray, grid_size: int) -> np.ndarray:
    """Align GPS points so their center matches the target mask center."""
    if gps_points.shape[0] < 2:
        return gps_points
    
    # Get target mask center in normalized coordinates
    target_mask_center = get_mask_geometric_center(target_mask)
    target_center_norm = (
        (target_mask_center[0] / (grid_size - 1)) * 2 - 1,  # Convert to [-1, 1]
        (target_mask_center[1] / (grid_size - 1)) * 2 - 1
    )
    
    # Get current GPS center
    gps_center = np.mean(gps_points, axis=0)
    
    # Calculate shift needed to align centers
    shift = np.array(target_center_norm) - gps_center
    
    # Apply shift to GPS points
    aligned_gps = gps_points + shift
    
    return aligned_gps


def center_svg_mask(mask: np.ndarray) -> np.ndarray:
    """Center the SVG mask by shifting it so its centroid is at the grid center."""
    if mask.sum() == 0:
        return mask
    
    # Find the centroid of the mask
    y_coords, x_coords = np.where(mask)
    if len(x_coords) == 0:
        return mask
    
    centroid_x = np.mean(x_coords)
    centroid_y = np.mean(y_coords)
    
    # Calculate shift needed to center at grid center
    grid_center = mask.shape[0] // 2
    shift_x = int(grid_center - centroid_x)
    shift_y = int(grid_center - centroid_y)
    
    # Create shifted mask
    shifted_mask = np.zeros_like(mask)
    for i, j in zip(y_coords, x_coords):
        new_i = i + shift_y
        new_j = j + shift_x
        if 0 <= new_i < mask.shape[0] and 0 <= new_j < mask.shape[1]:
            shifted_mask[new_i, new_j] = True
    
    return shifted_mask


def polygon_mask(poly_norm: np.ndarray, grid_size: int) -> np.ndarray:
    """Rasterize a closed polygon given normalized vertices into a boolean mask."""
    if poly_norm.shape[0] < 3:
        return np.zeros((grid_size, grid_size), dtype=bool)
    # Ensure closed
    if not np.allclose(poly_norm[0], poly_norm[-1]):
        poly_norm = np.vstack([poly_norm, poly_norm[0]])
    Path = mpath.Path
    path = Path(poly_norm)
    X, Y = grid_lin(grid_size)
    pts = np.column_stack([X.ravel(), Y.ravel()])
    inside = path.contains_points(pts)
    return inside.reshape(grid_size, grid_size)


def target_polygon_mask(poly_norm: np.ndarray, grid_size: int) -> np.ndarray:
    """Create target mask using the same centering method as GPS."""
    return polygon_mask(poly_norm, grid_size)


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


def region_signed_score(mask_gps_poly: np.ndarray, mask_target: np.ndarray) -> float:
    """Custom scoring algorithm:
    Raw Score = (Overlap Area) - (1.0 × Missing Mask Area) - (0.3 × Extra Route Area)
    Final Similarity = (Raw Score / Total Mask Area) × 100
    
    Where:
    - Overlap Area: intersection of GPS and target
    - Missing Mask Area: target area not covered by GPS (under-coverage)
    - Extra Route Area: GPS area outside target (over-extension)
    - Total Mask Area: total target area
    """
    overlap_area = np.logical_and(mask_gps_poly, mask_target).sum()
    missing_mask_area = np.logical_and(mask_target, np.logical_not(mask_gps_poly)).sum()  # target not covered
    extra_route_area = np.logical_and(mask_gps_poly, np.logical_not(mask_target)).sum()   # GPS outside target
    total_mask_area = mask_target.sum()
    
    if total_mask_area == 0:
        return 0.0  # Cannot calculate if target has no area
    
    # Raw Score = Overlap - 1.0×Missing - 0.3×Extra
    raw_score = overlap_area - (1.0 * missing_mask_area) - (0.3 * extra_route_area)
    
    # Final Similarity = (Raw Score / Total Mask Area) × 100
    final_similarity = (raw_score / total_mask_area) * 100.0
    
    return final_similarity




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

    # Precompute target mask once (filled polygon)
    tgt_mask = target_polygon_mask(target_norm, grid_size)

    # Coarse rotation search (maximize region-signed score)
    best_score = -1e9
    best_angle = 0
    for ang in range(0, 360, coarse_step):
        a = math.radians(ang)
        c, s = math.cos(a), math.sin(a)
        R = np.array([[c, -s], [s, c]])
        gps_rot = gps_norm @ R.T
        # Build GPS enclosed region mask from polygon
        gps_poly_mask = polygon_mask(gps_rot, grid_size)
        val = region_signed_score(gps_poly_mask, tgt_mask)
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
        gps_poly_mask = polygon_mask(gps_rot, grid_size)
        val = region_signed_score(gps_poly_mask, tgt_mask)
        if val > best_score:
            best_score = val
            best_angle = (ang + 360) % 360

    # Coverage diagnostics at best angle
    a = math.radians(best_angle)
    c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s], [s, c]])
    gps_rot = gps_norm @ R.T
    gps_mask_line = gps_path_mask(gps_rot, grid_size, stroke_width_norm)
    gps_mask_poly = polygon_mask(gps_rot, grid_size)
    inter = np.logical_and(gps_mask_poly, tgt_mask).sum()
    gps_only_poly = np.logical_and(gps_mask_poly, np.logical_not(tgt_mask)).sum()
    tgt_only = np.logical_and(tgt_mask, np.logical_not(gps_mask_poly)).sum()
    tgt_area = tgt_mask.sum()
    gps_area_line = gps_mask_line.sum()
    cov_target = (inter / tgt_area) * 100 if tgt_area > 0 else 0.0
    cov_gps = (inter / gps_area_line) * 100 if gps_area_line > 0 else 0.0
    signed_score = region_signed_score(gps_mask_poly, tgt_mask)
    iou_score = iou(gps_mask_poly, tgt_mask)

    return {
        "region_signed_pct": round(np.clip(signed_score, -1.0, 1.0) * 100, 1),
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
        print(f"  Overlap (IoU): {result['overlap_iou_pct']:.1f}%")
        print(f"  Coverage of Target: {result['coverage_of_target_pct']:.1f}%")
        print(f"  Coverage of GPS: {result['coverage_of_gps_pct']:.1f}%")
        print(f"  Best Rotation: {result['best_rotation_deg']}°")

        # Final single number as requested
        print(f"\nFINAL SCORE: {result['overlap_iou_pct']:.1f}%")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nPlease check that:")
        print("  1) GPS_ROUTE is a list of [lat, lng] with ≥ 2 points")
        print("  2) TARGET_SVG is a valid SVG path string (M/L/H/V/C/Q/Z)")
        print("  3) Shapes are non-degenerate (not all points equal)")


# Compatibility functions for Flask app integration
def parse_strava_data(strava_file):
    """Parse Strava data from JSON file (compatibility with existing interface)."""
    import json
    with open(strava_file, 'r') as f:
        data = json.load(f)
    
    if 'coordinates' in data:
        # Strava coordinates are in [lat, lon] format
        return data['coordinates']
    return [[0, 0]]  # fallback


def grade_shape_similarity_iou(strava_file, svg_file):
    """
    Grade similarity between Strava run data and SVG shape using IoU-based algorithm.
    
    Parameters:
    - strava_file: Path to Strava JSON file
    - svg_file: Path to SVG shape file
    
    Returns:
    - Similarity percentage (0-100) based on IoU overlap
    """
    try:
        # Parse GPS data from JSON file
        gps_coords = parse_strava_data(strava_file)
        
        # Read SVG file content
        with open(svg_file, 'r') as f:
            svg_content = f.read()
        
        # Use the IoU-based algorithm
        result = best_overlap_iou(
            gps_latlng=gps_coords,
            svg_path=svg_content,
            grid_size=256,
            stroke_width_norm=0.02,
            coarse_step=5,
            fine_step=1
        )
        
        # Return the IoU overlap percentage as the main similarity score
        return result['overlap_iou_pct']
        
    except Exception as e:
        print(f"Error in grade_shape_similarity_iou: {e}")
        return 0.0


def grade_shape_similarity_with_transform_iou(strava_file, svg_file):
    """
    Grade similarity and return IoU-based metrics for visualization.
    
    Parameters:
    - strava_file: Path to Strava JSON file  
    - svg_file: Path to SVG shape file
    
    Returns:
    - Dictionary with:
        - similarity: Similarity percentage (0-100) based on IoU overlap
        - coverage_of_target_pct: How much of target shape is covered by GPS
        - coverage_of_gps_pct: How much of GPS route overlaps with target
        - best_rotation_deg: Optimal rotation angle found
        - algorithm: "iou" to identify the algorithm used
        - strava_transformed: Transformed GPS coordinates for visualization
        - svg_normalized: Normalized SVG coordinates for visualization
    """
    try:
        # Parse GPS data from JSON file
        gps_coords = parse_strava_data(strava_file)
        
        # Read SVG file content
        with open(svg_file, 'r') as f:
            svg_content = f.read()
        
        # Use the IoU-based algorithm
        result = best_overlap_iou(
            gps_latlng=gps_coords,
            svg_path=svg_content,
            grid_size=256,
            stroke_width_norm=0.02,
            coarse_step=5,
            fine_step=1
        )
        
        # Generate visualization coordinates using same logic as visualizer.py
        best_angle = result['best_rotation_deg']
        
        # Prepare normalized shapes (same as visualizer.py)
        gps_xy = latlng_to_xy(gps_coords)
        gps_norm = center_and_scale(gps_xy)
        svg_pts = parse_svg_input(svg_content)
        target_norm = center_and_scale(svg_pts)
        
        # Apply best rotation to GPS coordinates
        import math
        a = math.radians(best_angle)
        c, s = math.cos(a), math.sin(a)
        R = np.array([[c, -s], [s, c]])
        gps_rot = gps_norm @ R.T
        
        # Align GPS route to target center (same as visualizer.py)
        tgt_mask = target_polygon_mask(target_norm, 256)
        gps_aligned = align_shapes_to_target_center(gps_rot, tgt_mask, 256)
        
        # Return in format compatible with existing interface + visualization coordinates
        return {
            'similarity': result['overlap_iou_pct'],
            'coverage_of_target_pct': result['coverage_of_target_pct'],
            'coverage_of_gps_pct': result['coverage_of_gps_pct'], 
            'best_rotation_deg': result['best_rotation_deg'],
            'algorithm': 'iou',
            'full_metrics': result,  # Include all original metrics
            # Visualization coordinates (same format as old procrustes algorithm)
            'strava_transformed': gps_aligned.tolist(),
            'svg_normalized': target_norm.tolist()
        }
        
    except Exception as e:
        print(f"Error in grade_shape_similarity_with_transform_iou: {e}")
        return {
            'similarity': 0.0,
            'coverage_of_target_pct': 0.0,
            'coverage_of_gps_pct': 0.0,
            'best_rotation_deg': 0,
            'algorithm': 'iou',
            'error': str(e)
        }


if __name__ == "__main__":
    main()


