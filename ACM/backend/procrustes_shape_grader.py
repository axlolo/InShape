#!/usr/bin/env python3
"""
Closed-loop Procrustes with cyclic shift (no reflection)
Implementation of shape similarity calculation using Procrustes analysis
Author: ACM Project
"""

import numpy as np
import json
import os
import xml.etree.ElementTree as ET
import re

def parse_svg_to_points(svg_file):
    """Extract points from SVG shapes and convert to coordinate list."""
    tree = ET.parse(svg_file)
    root = tree.getroot()
    points = []
    
    # Handle different SVG elements
    for elem in root:
        if elem.tag.endswith('circle'):
            cx, cy, r = float(elem.get('cx')), float(elem.get('cy')), float(elem.get('r'))
            # Generate points around circle
            angles = np.linspace(0, 2*np.pi, 100, endpoint=False)
            points = [(cx + r*np.cos(a), cy + r*np.sin(a)) for a in angles]
            
        elif elem.tag.endswith('rect'):
            x, y = float(elem.get('x')), float(elem.get('y'))
            w, h = float(elem.get('width')), float(elem.get('height'))
            # Generate points around rectangle perimeter
            # Top edge
            points.extend([(x + i*w/20, y) for i in range(21)])
            # Right edge
            points.extend([(x + w, y + i*h/20) for i in range(1, 21)])
            # Bottom edge
            points.extend([(x + w - i*w/20, y + h) for i in range(1, 21)])
            # Left edge
            points.extend([(x, y + h - i*h/20) for i in range(1, 20)])
            
        elif elem.tag.endswith('polygon'):
            points_str = elem.get('points')
            coords = [float(x) for x in re.findall(r'-?\d+\.?\d*', points_str)]
            points = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
            
            # Interpolate between polygon vertices
            interpolated = []
            for i in range(len(points)):
                start = points[i]
                end = points[(i + 1) % len(points)]
                for t in np.linspace(0, 1, 20, endpoint=False):
                    interpolated.append((
                        start[0] + t * (end[0] - start[0]),
                        start[1] + t * (end[1] - start[1])
                    ))
            points = interpolated
    
    return np.array(points) if points else np.array([[0, 0]])

def parse_strava_data(file_path):
    """Parse Strava data from JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if 'coordinates' in data:
        # Strava coordinates are in [lat, lon] format
        return np.array(data['coordinates'])
    return np.array([[0, 0]])

def calculate_arc_length_distances(points):
    """Calculate cumulative arc-length distances along the polyline."""
    if len(points) < 2:
        return np.array([0])
    
    # Calculate distances between consecutive points
    diffs = np.diff(points, axis=0)
    segment_lengths = np.linalg.norm(diffs, axis=1)
    
    # Add distance from last to first point (to close the loop)
    last_to_first = np.linalg.norm(points[0] - points[-1])
    segment_lengths = np.append(segment_lengths, last_to_first)
    
    # Calculate cumulative distances
    cumulative_distances = np.zeros(len(points) + 1)
    cumulative_distances[1:] = np.cumsum(segment_lengths)
    
    return cumulative_distances

def resample_closed_by_arclength(points, K=512):
    """
    Resample a polyline to K points uniformly spaced by arc-length.
    Forces closed loop by adding segment from last to first if needed.
    """
    if len(points) < 2:
        return np.zeros((K, 2))
    
    points = np.array(points)
    
    # Calculate cumulative arc-length distances
    cumulative_distances = calculate_arc_length_distances(points)
    total_length = cumulative_distances[-1]
    
    if total_length == 0:
        return np.tile(points[0], (K, 1))
    
    # Create K equally spaced target distances
    target_distances = np.linspace(0, total_length, K, endpoint=False)
    
    # Resample points
    resampled = np.zeros((K, 2))
    
    for i, target_dist in enumerate(target_distances):
        # Find the segment containing this distance
        segment_idx = np.searchsorted(cumulative_distances[1:], target_dist)
        
        # Get the start and end points of the segment
        if segment_idx < len(points) - 1:
            start_point = points[segment_idx]
            end_point = points[segment_idx + 1]
        else:
            # Last segment (from last to first point)
            start_point = points[-1]
            end_point = points[0]
        
        # Interpolate within the segment
        segment_start_dist = cumulative_distances[segment_idx]
        segment_end_dist = cumulative_distances[segment_idx + 1]
        segment_length = segment_end_dist - segment_start_dist
        
        if segment_length > 0:
            t = (target_dist - segment_start_dist) / segment_length
            resampled[i] = start_point + t * (end_point - start_point)
        else:
            resampled[i] = start_point
    
    return resampled

def shape_similarity(A_pts, B_pts, K=512):
    """
    Calculate shape similarity using closed-loop Procrustes with cyclic shift.
    
    Parameters:
    - A_pts: First shape points (Nx2 array)
    - B_pts: Second shape points (Mx2 array)
    - K: Number of points to resample to (default 512)
    
    Returns:
    - Similarity score in [0, 1]
    """
    # Step 0: Close and resample
    A = resample_closed_by_arclength(A_pts, K)
    B = resample_closed_by_arclength(B_pts, K)
    
    # Step 1: Center and scale
    # Center at origin
    A = A - A.mean(axis=0)
    B = B - B.mean(axis=0)
    
    # Normalize by Frobenius norm
    nA = np.linalg.norm(A, 'fro')
    nB = np.linalg.norm(B, 'fro')
    
    if nA == 0 or nB == 0:
        return 0.0
    
    A = A / nA
    B = B / nB
    
    # Step 2 & 3: Try all cyclic shifts and directions
    best = 0.0
    
    for direction in [1, -1]:  # Forward and reverse traversal
        Bdir = B if direction == 1 else B[::-1]
        
        for k in range(K):  # Try all cyclic start points
            # Cyclic shift
            Bk = np.roll(Bdir, shift=k, axis=0)
            
            # Calculate optimal rotation using SVD
            C = A.T @ Bk  # 2x2 matrix
            U, S, Vt = np.linalg.svd(C)
            
            # Ensure proper rotation (no reflection)
            det_UV = np.linalg.det(U @ Vt)
            D = np.diag([1, np.sign(det_UV)])
            
            # Calculate similarity score
            sim = np.trace(D @ np.diag(S))
            
            if sim > best:
                best = sim
    
    # Clamp to [0, 1] for numerical stability
    return float(np.clip(best, 0, 1))

def shape_distance(A_pts, B_pts, K=512):
    """
    Calculate shape distance based on similarity score.
    
    Returns:
    - Distance in [0, sqrt(2)]
    """
    sim = shape_similarity(A_pts, B_pts, K)
    return np.sqrt(2 - 2 * sim)

def grade_shape_similarity_procrustes(strava_file, svg_file, K=512):
    """
    Grade similarity between Strava run data and SVG shape using Procrustes analysis.
    
    Parameters:
    - strava_file: Path to Strava JSON file
    - svg_file: Path to SVG shape file
    - K: Number of resampling points
    
    Returns:
    - Similarity percentage (0-100)
    """
    # Parse input data
    strava_points = parse_strava_data(strava_file)
    svg_points = parse_svg_to_points(svg_file)
    
    # Calculate similarity
    similarity = shape_similarity(strava_points, svg_points, K)
    
    # Convert to percentage
    return similarity * 100

def test_procrustes_grader():
    """Test the Procrustes shape grader with various shapes."""
    print("🔬 Testing Procrustes Shape Grader")
    print("=" * 50)
    
    # Test basic shapes
    print("\n1. Testing identical shapes:")
    square1 = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
    square2 = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
    sim = shape_similarity(square1, square2)
    print(f"   Same square: {sim*100:.1f}% (expected: ~100%)")
    
    # Test rotated rectangle
    print("\n2. Testing rotation invariance:")
    rect1 = np.array([[0, 0], [2, 0], [2, 1], [0, 1]])  # 2x1 rectangle
    rect2 = np.array([[0, 0], [0, 2], [1, 2], [1, 0]])  # 1x2 rectangle (90° rotated)
    sim = shape_similarity(rect1, rect2)
    print(f"   2x1 vs 1x2 rectangle: {sim*100:.1f}% (expected: ~100%)")
    
    # Test different starting points
    print("\n3. Testing cyclic shift invariance:")
    square_shifted = np.array([[1, 0], [1, 1], [0, 1], [0, 0]])  # Same square, different start
    sim = shape_similarity(square1, square_shifted)
    print(f"   Square vs shifted square: {sim*100:.1f}% (expected: ~100%)")
    
    # Test reversed direction
    print("\n4. Testing direction invariance:")
    square_reversed = np.array([[0, 0], [0, 1], [1, 1], [1, 0]])  # Counter-clockwise
    sim = shape_similarity(square1, square_reversed)
    print(f"   Clockwise vs counter-clockwise: {sim*100:.1f}% (expected: ~100%)")
    
    # Test with real Strava data if available
    strava_dir = "/Users/axeledin/Desktop/ACM_Folder/ACM/StravaDataTxt"
    shapes_dir = "/Users/axeledin/Desktop/ACM_Folder/ACM/shapes"
    
    if os.path.exists(strava_dir) and os.path.exists(shapes_dir):
        print("\n5. Testing with real Strava data:")
        
        strava_files = [f for f in os.listdir(strava_dir) if f.endswith('.txt') and f != 'requirements.txt' and 'Strava' in f]
        svg_files = [f for f in os.listdir(shapes_dir) if f.endswith('.svg')]
        
        for strava_file in strava_files[:2]:  # Test first 2 Strava files
            print(f"\n   {strava_file}:")
            strava_path = os.path.join(strava_dir, strava_file)
            
            best_match = ("", 0)
            for svg_file in svg_files:
                svg_path = os.path.join(shapes_dir, svg_file)
                try:
                    similarity = grade_shape_similarity_procrustes(strava_path, svg_path)
                    if similarity > best_match[1]:
                        best_match = (svg_file, similarity)
                except Exception as e:
                    print(f"      Error processing {svg_file}: {e}")
            
            print(f"      Best match: {best_match[0]} ({best_match[1]:.1f}%)")

def example_usage():
    """Example of how to use the Procrustes shape grader."""
    print("\n📚 Example Usage:")
    print("=" * 30)
    
    # Example with direct coordinates
    print("1. Direct coordinate comparison:")
    circle_points = [(np.cos(t), np.sin(t)) for t in np.linspace(0, 2*np.pi, 50)]
    square_points = [(0, 0), (1, 0), (1, 1), (0, 1)]
    
    sim = shape_similarity(circle_points, square_points)
    print(f"   Circle vs Square: {sim*100:.1f}%")
    
    # Example with files
    strava_file = "/Users/axeledin/Desktop/ACM_Folder/ACM/StravaDataTxt/RectangleStrava.txt"
    svg_file = "/Users/axeledin/Desktop/ACM_Folder/ACM/shapes/rectangle-1.svg"
    
    if os.path.exists(strava_file) and os.path.exists(svg_file):
        print("\n2. File-based comparison:")
        similarity = grade_shape_similarity_procrustes(strava_file, svg_file)
        print(f"   RectangleStrava vs rectangle-1.svg: {similarity:.1f}%")

def compare_with_existing_algorithms():
    """Compare Procrustes algorithm with existing shape graders."""
    print("\n🔍 Algorithm Comparison")
    print("=" * 50)
    
    strava_dir = "/Users/axeledin/Desktop/ACM_Folder/ACM/StravaDataTxt"
    shapes_dir = "/Users/axeledin/Desktop/ACM_Folder/ACM/shapes"
    
    # Import existing graders
    import sys
    sys.path.append("/Users/axeledin/Desktop/ACM_Folder/ACM/backend")
    
    try:
        from shape_grader import grade_shape_similarity
        from rotation_invariant_shape_grader import grade_shape_similarity_rotation_invariant
        
        strava_files = [f for f in os.listdir(strava_dir) if f.endswith('.txt') and 'Strava' in f]
        
        for strava_file in strava_files:
            print(f"\n{strava_file}:")
            strava_path = os.path.join(strava_dir, strava_file)
            
            # Parse Strava data once
            strava_data = parse_strava_data(strava_path)
            
            # Test against rectangle
            svg_path = os.path.join(shapes_dir, "rectangle-1.svg")
            
            # Standard algorithm
            standard_score = grade_shape_similarity(strava_data, svg_path)
            
            # Rotation invariant algorithm
            rotation_score = grade_shape_similarity_rotation_invariant(strava_data, svg_path)
            
            # Procrustes algorithm
            procrustes_score = grade_shape_similarity_procrustes(strava_path, svg_path)
            
            print(f"  Standard algorithm:         {standard_score:.1f}%")
            print(f"  Rotation-invariant:         {rotation_score:.1f}%")
            print(f"  Procrustes (this script):   {procrustes_score:.1f}%")
            
    except ImportError as e:
        print(f"Could not import existing algorithms: {e}")
        print("Running only Procrustes algorithm...")

if __name__ == "__main__":
    test_procrustes_grader()
    example_usage()
    compare_with_existing_algorithms()
