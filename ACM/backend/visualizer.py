#!/usr/bin/env python3
"""
Visualizer for GPS vs SVG similarity and overlap (IoU) used by algorithm.py

It renders:
- Target mask (filled shape)
- GPS mask at best rotation (thick path)
- Overlay (target vs GPS vs intersection)
- Normalized outlines for quick sanity check

Usage:
  python visualizer.py
  (uses TARGET_SVG and GPS_ROUTE defined in algorithm.py)
"""

import math
import numpy as np
import matplotlib.pyplot as plt

# Reuse the same helpers from algorithm.py to ensure identical processing
from algorithm import (
    TARGET_SVG, GPS_ROUTE,
    parse_svg_input,
    latlng_to_xy,
    center_and_scale,
    grid_lin,
    target_polygon_mask,
    gps_path_mask,
    best_overlap_iou,
)


def rotate_points(pts: np.ndarray, angle_deg: float) -> np.ndarray:
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s], [s, c]])
    return pts @ R.T


def visualize_comparison(
    svg_text: str,
    gps_latlng: list,
    grid_size: int = 256,
    stroke_width_norm: float = 0.02,
    coarse_step: int = 5,
    fine_step: int = 1,
    outfile: str = "comparison.png",
):
    # Compute best rotation and masks
    result = best_overlap_iou(
        gps_latlng=gps_latlng,
        svg_path=svg_text,
        grid_size=grid_size,
        stroke_width_norm=stroke_width_norm,
        coarse_step=coarse_step,
        fine_step=fine_step,
    )

    best_angle = result["best_rotation_deg"]

    # Prepare normalized shapes again for visualization
    gps_xy = latlng_to_xy(gps_latlng)
    gps_norm = center_and_scale(gps_xy)
    svg_pts = parse_svg_input(svg_text)
    target_norm = center_and_scale(svg_pts)

    # Build masks at best angle
    tgt_mask = target_polygon_mask(target_norm, grid_size)
    gps_rot = rotate_points(gps_norm, best_angle)
    gps_mask = gps_path_mask(gps_rot, grid_size, stroke_width_norm)

    # Intersection map for overlay
    intersection = np.logical_and(tgt_mask, gps_mask)

    # Create figure
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))

    # Row 1: masks
    im0 = axes[0, 0].imshow(tgt_mask, cmap="Reds", origin="lower")
    axes[0, 0].set_title("Target Mask")
    axes[0, 0].axis("off")

    im1 = axes[0, 1].imshow(gps_mask, cmap="Blues", origin="lower")
    axes[0, 1].set_title(f"GPS Mask (rot {best_angle}°)")
    axes[0, 1].axis("off")

    # Overlay: R=target, B=gps, Purple=intersection
    overlay = np.zeros((grid_size, grid_size, 3), dtype=float)
    overlay[:, :, 0] = tgt_mask.astype(float)  # red
    overlay[:, :, 2] = gps_mask.astype(float)  # blue
    overlay[:, :, 1] = intersection.astype(float) * 0.6  # a bit of green to show intersection as purple
    axes[0, 2].imshow(overlay, origin="lower")
    axes[0, 2].set_title("Overlay (purple = intersection)")
    axes[0, 2].axis("off")

    # Prominent similarity score overlay (safe fallback if field missing)
    sim_pct = result.get("similarity_score_pct", result.get("overlap_signed_pct", None))
    sim_txt = f"Similarity: {sim_pct:.1f}%" if isinstance(sim_pct, (int, float)) else "Similarity: N/A"
    axes[0, 2].text(
        0.02, 0.98, sim_txt,
        transform=axes[0, 2].transAxes,
        va="top", ha="left",
        fontsize=14, color="white",
        bbox=dict(facecolor="black", alpha=0.6, boxstyle="round,pad=0.3")
    )

    # Row 2: normalized outlines (quick sanity check)
    # Target polygon outline
    axes[1, 0].plot(target_norm[:, 0], target_norm[:, 1], "r-", lw=2)
    axes[1, 0].set_title("Target (normalized outline)")
    axes[1, 0].set_aspect("equal")
    axes[1, 0].grid(True, alpha=0.3)

    # GPS path normalized and rotated
    axes[1, 1].plot(gps_rot[:, 0], gps_rot[:, 1], "b-", lw=2)
    axes[1, 1].set_title(f"GPS (normalized, rot {best_angle}°)")
    axes[1, 1].set_aspect("equal")
    axes[1, 1].grid(True, alpha=0.3)

    # Combined outlines
    axes[1, 2].plot(target_norm[:, 0], target_norm[:, 1], "r-", lw=2, label="Target")
    axes[1, 2].plot(gps_rot[:, 0], gps_rot[:, 1], "b-", lw=2, label="GPS")
    axes[1, 2].set_title("Outlines (normalized)")
    axes[1, 2].set_aspect("equal")
    axes[1, 2].grid(True, alpha=0.3)
    axes[1, 2].legend()

    fig.suptitle(
        f"{sim_txt} | IoU {result['overlap_iou_pct']}% | TargetCov {result['coverage_of_target_pct']}% | GPSCov {result['coverage_of_gps_pct']}% | Rot {best_angle}°",
        fontsize=12,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(outfile, dpi=150)
    # Console message includes similarity for clarity
    print(sim_txt)
    print(f"Saved visualization to '{outfile}'")
    plt.show()


if __name__ == "__main__":
    visualize_comparison(
        svg_text=TARGET_SVG,
        gps_latlng=GPS_ROUTE,
        grid_size=256,
        stroke_width_norm=0.02,
        coarse_step=5,
        fine_step=1,
        outfile="comparison.png",
    )

import matplotlib.pyplot as plt
import numpy as np

def visualize_shapes(route_points, svg_points, aligned_route, aligned_svg, similarity_score):
    """
    Visualize original shapes and final aligned shapes
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # Original shapes (normalized but not aligned)
    ax1.plot(route_points[:, 0], route_points[:, 1], 'b-o', markersize=3, label='GPS Route', linewidth=2)
    ax1.plot(svg_points[:, 0], svg_points[:, 1], 'r-s', markersize=3, label='SVG Shape', linewidth=2)
    ax1.set_title('Original Normalized Shapes')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.axis('equal')
    
    # Just the GPS route
    ax2.plot(route_points[:, 0], route_points[:, 1], 'b-o', markersize=4, linewidth=2)
    ax2.set_title('GPS Route (Normalized)')
    ax2.grid(True, alpha=0.3)
    ax2.axis('equal')
    
    # Just the SVG shape
    ax3.plot(svg_points[:, 0], svg_points[:, 1], 'r-s', markersize=4, linewidth=2)
    ax3.set_title('SVG Shape (Normalized)')
    ax3.grid(True, alpha=0.3)
    ax3.axis('equal')
    
    # Final aligned shapes
    ax4.plot(aligned_route[:, 0], aligned_route[:, 1], 'b-o', markersize=3, label='Aligned GPS Route', linewidth=2)
    ax4.plot(aligned_svg[:, 0], aligned_svg[:, 1], 'r-s', markersize=3, label='SVG Shape', linewidth=2)
    ax4.set_title(f'Final Aligned Shapes\nSimilarity: {similarity_score:.1f}%')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.axis('equal')
    
    plt.tight_layout()
    plt.show()

def visualize_comparison(aligned_route, aligned_svg, similarity_score):
    """
    Simple side-by-side comparison of final aligned shapes
    """
    plt.figure(figsize=(10, 5))
    
    plt.subplot(1, 2, 1)
    plt.plot(aligned_route[:, 0], aligned_route[:, 1], 'b-o', markersize=4, linewidth=2)
    plt.title('GPS Route (Final)')
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    
    plt.subplot(1, 2, 2)
    plt.plot(aligned_svg[:, 0], aligned_svg[:, 1], 'r-s', markersize=4, linewidth=2)
    plt.title('SVG Shape')
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    
    plt.suptitle(f'Shape Comparison - Similarity: {similarity_score:.1f}%', fontsize=14)
    plt.tight_layout()
    plt.show()

def visualize_overlay(aligned_route, aligned_svg, similarity_score):
    """
    Overlay both shapes to see the match quality
    """
    plt.figure(figsize=(8, 8))
    
    plt.plot(aligned_route[:, 0], aligned_route[:, 1], 'b-o', markersize=5, 
             label='GPS Route', linewidth=3, alpha=0.7)
    plt.plot(aligned_svg[:, 0], aligned_svg[:, 1], 'r-s', markersize=5, 
             label='SVG Shape', linewidth=3, alpha=0.7)
    
    # Draw lines between corresponding points to show distances
    for i in range(min(len(aligned_route), len(aligned_svg))):
        plt.plot([aligned_route[i, 0], aligned_svg[i, 0]], 
                [aligned_route[i, 1], aligned_svg[i, 1]], 
                'gray', alpha=0.3, linewidth=1)
    
    plt.title(f'Shape Overlay - Similarity: {similarity_score:.1f}%', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    plt.show()