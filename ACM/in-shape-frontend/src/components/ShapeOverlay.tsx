'use client';

import React, { useEffect, useRef, useState } from 'react';

interface VisualizationData {
  strava_transformed: number[][];
  svg_normalized: number[][];
  transform_info: {
    rotation_matrix: number[][];
    best_shift: number;
    best_direction: number;
    strava_center: number[];
    svg_center: number[];
    strava_scale: number;
    svg_scale: number;
  };
}

interface ShapeOverlayProps {
  visualizationData?: VisualizationData;
  width?: number;
  height?: number;
  showTargetShape?: boolean;
  showUserPath?: boolean;
}

export default function ShapeOverlay({
  visualizationData,
  width = 400,
  height = 400,
  showTargetShape = true,
  showUserPath = true
}: ShapeOverlayProps) {
  console.log('ShapeOverlay received data:', visualizationData);
  
  if (!visualizationData) {
    console.log('No visualization data provided');
    return null;
  }

  const { strava_transformed, svg_normalized } = visualizationData;
  console.log('Strava transformed points:', strava_transformed?.length);
  console.log('SVG normalized points:', svg_normalized?.length);

  const containerRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState<{ width: number; height: number }>({ width, height });

  useEffect(() => {
    const measure = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        // Fallback to provided props if measurement fails
        setDims({
          width: Math.max(1, Math.floor(rect.width || width)),
          height: Math.max(1, Math.floor(rect.height || height)),
        });
      }
    };
    measure();
    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, [width, height]);

  // Convert normalized coordinates to SVG coordinates with intelligent scaling, centering, and optimal orientation
  const coordinatesToSVGPath = (coords: number[][], targetWidth: number = 300, targetHeight: number = 300, isStravaPath: boolean = false, forcedScalePx?: number) => {
    if (!coords || coords.length === 0) return '';
    
    let processedCoords = [...coords];
    
    // For Strava path, find the optimal orientation (rotation only preference)
    if (isStravaPath) {
      processedCoords = findOptimalOrientation(coords, targetWidth, targetHeight);
      // Neutralize any internal optimalScale usage; we'll supply a common forced scale below
      (processedCoords as any).optimalScale = undefined;
    }
    
    // Find bounding box of the (possibly rotated) coordinates
    const xs = processedCoords.map(p => p[0]);
    const ys = processedCoords.map(p => p[1]);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    
    // Calculate dimensions and center
    const coordWidth = maxX - minX;
    const coordHeight = maxY - minY;
    const coordCenterX = (minX + maxX) / 2;
    const coordCenterY = (minY + maxY) / 2;
    
    // Calculate scale to fit target area
    // If a common forced pixel scale is provided, use it for perfect alignment
    let scale: number;
    if (forcedScalePx && forcedScalePx > 0) {
      scale = forcedScalePx;
    } else {
      // Use optimal scale if available, otherwise default to 80%
      const optimalScaleFactor = (processedCoords as any).optimalScale || 0.8;
      const scaleX = coordWidth > 0 ? (targetWidth * optimalScaleFactor) / coordWidth : 1;
      const scaleY = coordHeight > 0 ? (targetHeight * optimalScaleFactor) / coordHeight : 1;
      scale = Math.min(scaleX, scaleY); // Use uniform scaling
    }
    
    // Calculate SVG center (center of the SVG viewbox)
    const svgCenterX = dims.width / 2;
    const svgCenterY = dims.height / 2;
    
    const pathData = processedCoords.map((point, index) => {
      // Translate to origin, scale, then translate to SVG center
      const x = (point[0] - coordCenterX) * scale + svgCenterX;
      const y = (point[1] - coordCenterY) * scale + svgCenterY;
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(2)} ${y.toFixed(2)}`;
    }).join(' ');
    
    return { path: `${pathData} Z`, transformedCoords: processedCoords, scalePx: scale, center: { x: svgCenterX, y: svgCenterY }, bbox: { width: coordWidth, height: coordHeight } };
  };

  // Function to find the optimal orientation and scale for best fit using multiple strategies
  const findOptimalOrientation = (coords: number[][], targetWidth: number, targetHeight: number) => {
    // Strategy 1: Principal Component Analysis - find the main axis of the shape
    const pca = findPrincipalAxis(coords);
    
    // Strategy 2: Test many rotation angles (every 5 degrees)
    const center = coords.reduce((acc, point) => [acc[0] + point[0], acc[1] + point[1]], [0, 0]);
    center[0] /= coords.length;
    center[1] /= coords.length;
    
    let bestRotation = 0;
    let bestScale = 0.8; // Default scale
    let bestFitScore = -1;
    let bestStrategy = 'default';
    
    // Test different scale factors (from 50% to 100% of available space)
    const scaleFactors = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0];
    
    scaleFactors.forEach(scaleFactor => {
      // Test fine-grained rotations with this scale
      for (let degrees = 0; degrees < 360; degrees += 10) { // Reduced to 10° steps for performance
        const angle = (degrees * Math.PI) / 180;
        const result = testRotationWithScale(coords, center, angle, targetWidth, targetHeight, scaleFactor);
        
        if (result.finalScore > bestFitScore) {
          bestFitScore = result.finalScore;
          bestRotation = angle;
          bestScale = scaleFactor;
          bestStrategy = `fine-rotation-${(scaleFactor * 100).toFixed(0)}%`;
        }
      }
      
      // Test PCA-based orientation with this scale
      const pcaAngles = [
        pca.angle,                    // Align main axis horizontally
        pca.angle + Math.PI/2,        // Align main axis vertically
        pca.angle + Math.PI,          // Flip horizontally
        pca.angle + 3*Math.PI/2       // Flip vertically
      ];
      
      pcaAngles.forEach(angle => {
        const result = testRotationWithScale(coords, center, angle, targetWidth, targetHeight, scaleFactor);
        
        if (result.finalScore > bestFitScore) {
          bestFitScore = result.finalScore;
          bestRotation = angle;
          bestScale = scaleFactor;
          bestStrategy = `pca-${(scaleFactor * 100).toFixed(0)}%`;
        }
      });
      
      // Test edge-based alignment with this scale
      const edgeBasedAngles = findOptimalEdgeAlignment(coords, targetWidth, targetHeight);
      edgeBasedAngles.forEach(angle => {
        const result = testRotationWithScale(coords, center, angle, targetWidth, targetHeight, scaleFactor);
        
        if (result.finalScore > bestFitScore) {
          bestFitScore = result.finalScore;
          bestRotation = angle;
          bestScale = scaleFactor;
          bestStrategy = `edge-alignment-${(scaleFactor * 100).toFixed(0)}%`;
        }
      });
    });
    
    console.log(`Best orientation: ${(bestRotation * 180 / Math.PI).toFixed(1)}° at ${(bestScale * 100).toFixed(0)}% scale using ${bestStrategy} strategy`);
    
    // Apply the best rotation and store the scale for later use
    const rotatedCoords = coords.map(point => {
      const dx = point[0] - center[0];
      const dy = point[1] - center[1];
      const cos = Math.cos(bestRotation);
      const sin = Math.sin(bestRotation);
      const rotX = dx * cos - dy * sin;
      const rotY = dx * sin + dy * cos;
      return [rotX + center[0], rotY + center[1]];
    });
    
    // Store the optimal scale factor for use in coordinatesToSVGPath
    (rotatedCoords as any).optimalScale = bestScale;
    
    return rotatedCoords;
  };

  // Helper function to test a specific rotation with scale factor and size penalty
  const testRotationWithScale = (coords: number[][], center: number[], angle: number, targetWidth: number, targetHeight: number, scaleFactor: number) => {
    const rotatedCoords = coords.map(point => {
      const dx = point[0] - center[0];
      const dy = point[1] - center[1];
      const cos = Math.cos(angle);
      const sin = Math.sin(angle);
      const rotX = dx * cos - dy * sin;
      const rotY = dx * sin + dy * cos;
      return [rotX + center[0], rotY + center[1]];
    });
    
    const xs = rotatedCoords.map(p => p[0]);
    const ys = rotatedCoords.map(p => p[1]);
    const width = Math.max(...xs) - Math.min(...xs);
    const height = Math.max(...ys) - Math.min(...ys);
    
    // Calculate what the actual display size would be with this scale factor
    const displayWidth = width * scaleFactor * (targetWidth / width);
    const displayHeight = height * scaleFactor * (targetHeight / height);
    const effectiveScale = Math.min(targetWidth / width, targetHeight / height) * scaleFactor;
    
    // Aspect ratio matching
    const targetAspectRatio = targetWidth / targetHeight;
    const shapeAspectRatio = width / height;
    const aspectRatioMatch = 1 - Math.abs(targetAspectRatio - shapeAspectRatio) / Math.max(targetAspectRatio, shapeAspectRatio);
    
    // Size appropriateness penalty
    // Calculate how much larger the overlay would be compared to a "reasonable" size
    const baseSize = Math.min(targetWidth, targetHeight);
    const overlaySize = Math.max(displayWidth, displayHeight);
    const sizeRatio = overlaySize / baseSize;
    
    // Penalty for being too large (starts at 1.2x base size, gets severe at 2x)
    let sizePenalty = 1.0;
    if (sizeRatio > 1.2) {
      sizePenalty = Math.max(0.1, 1.0 - Math.pow((sizeRatio - 1.2) / 0.8, 2));
    }
    
    // Bonus for being closer to ideal size (around 80% of target)
    const idealSizeRatio = 0.8;
    const sizeFitness = 1.0 - Math.abs(sizeRatio - idealSizeRatio) / idealSizeRatio;
    
    // Visibility score - ensure the shape is large enough to be meaningful
    const minVisibleRatio = 0.3;
    const visibilityBonus = sizeRatio > minVisibleRatio ? 1.0 : sizeRatio / minVisibleRatio;
    
    // Final score combines multiple factors
    const baseScore = effectiveScale * (0.7 + 0.3 * aspectRatioMatch);
    const finalScore = baseScore * sizePenalty * sizeFitness * visibilityBonus;
    
    return { 
      finalScore, 
      effectiveScale, 
      aspectRatioMatch, 
      sizePenalty, 
      sizeFitness, 
      visibilityBonus,
      sizeRatio 
    };
  };

  // Legacy function for compatibility
  const testRotation = (coords: number[][], center: number[], angle: number, targetWidth: number, targetHeight: number) => {
    return testRotationWithScale(coords, center, angle, targetWidth, targetHeight, 0.8);
  };

  // Find the principal axis of the shape using covariance matrix
  const findPrincipalAxis = (coords: number[][]) => {
    const center = coords.reduce((acc, point) => [acc[0] + point[0], acc[1] + point[1]], [0, 0]);
    center[0] /= coords.length;
    center[1] /= coords.length;
    
    // Calculate covariance matrix
    let cov_xx = 0, cov_xy = 0, cov_yy = 0;
    
    coords.forEach(point => {
      const dx = point[0] - center[0];
      const dy = point[1] - center[1];
      cov_xx += dx * dx;
      cov_xy += dx * dy;
      cov_yy += dy * dy;
    });
    
    cov_xx /= coords.length;
    cov_xy /= coords.length;
    cov_yy /= coords.length;
    
    // Find the principal axis angle
    const angle = Math.atan2(2 * cov_xy, cov_xx - cov_yy) / 2;
    
    return { angle, center };
  };

  // Find angles that align longest edges with target dimensions
  const findOptimalEdgeAlignment = (coords: number[][], targetWidth: number, targetHeight: number) => {
    const angles: number[] = [];
    
    // Find the longest segments in the path
    const segments: { length: number; angle: number }[] = [];
    
    for (let i = 0; i < coords.length; i++) {
      const current = coords[i];
      const next = coords[(i + 1) % coords.length];
      
      const dx = next[0] - current[0];
      const dy = next[1] - current[1];
      const length = Math.sqrt(dx * dx + dy * dy);
      const angle = Math.atan2(dy, dx);
      
      segments.push({ length, angle });
    }
    
    // Sort by length and take the top segments
    segments.sort((a, b) => b.length - a.length);
    const topSegments = segments.slice(0, Math.min(4, segments.length));
    
    // For each top segment, try aligning it with horizontal and vertical
    topSegments.forEach(segment => {
      angles.push(-segment.angle);                    // Align with horizontal
      angles.push(-segment.angle + Math.PI/2);       // Align with vertical
    });
    
    return angles;
  };

  // Use the container's measured size for layout
  const baseFactor = 0.8; // 80% of the smaller dimension to leave padding
  const targetSize = Math.min(dims.width, dims.height) * baseFactor;

  // First, compute the target shape's scale so we can match it
  const svgProbe = coordinatesToSVGPath(svg_normalized, targetSize, targetSize, false);
  // Derive a common pixel scale from the target SVG shape
  const commonScalePx = svgProbe.scalePx;

  // Now render both paths using the same pixel scale so sizes match
  const svgResult = coordinatesToSVGPath(svg_normalized, targetSize, targetSize, false, commonScalePx);
  const stravaResult = coordinatesToSVGPath(strava_transformed, targetSize, targetSize, true, commonScalePx);
  
  const svgPath = svgResult.path;
  const stravaPath = stravaResult.path;
  const optimizedStravaCoords = stravaResult.transformedCoords;
  
  console.log('SVG Path:', svgPath.substring(0, 100) + '...');
  console.log('Strava Path:', stravaPath.substring(0, 100) + '...');

  return (
    <div ref={containerRef} className="absolute inset-0 pointer-events-none">
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${dims.width} ${dims.height}`}
        className="absolute inset-0 pointer-events-none"
      >
        {/* User's run path (Strava) */}
        {showUserPath && (
          <path
            d={stravaPath}
            fill="none"
            stroke="#ff6600" // Bright orange
            strokeWidth="5"
            opacity="1"
          />
        )}
        
        {/* Optional: Add dots to show direction */}
        {showUserPath && optimizedStravaCoords.length > 0 && (() => {
          // Calculate the same transformation as used for the path (using common scale)
          const xs = optimizedStravaCoords.map(p => p[0]);
          const ys = optimizedStravaCoords.map(p => p[1]);
          const minX = Math.min(...xs);
          const maxX = Math.max(...xs);
          const minY = Math.min(...ys);
          const maxY = Math.max(...ys);
          const coordCenterX = (minX + maxX) / 2;
          const coordCenterY = (minY + maxY) / 2;
          const scale = commonScalePx;
          const svgCenterX = dims.width / 2;
          const svgCenterY = dims.height / 2;
          
          const transformPoint = (point: number[]) => {
            return {
              x: (point[0] - coordCenterX) * scale + svgCenterX,
              y: (point[1] - coordCenterY) * scale + svgCenterY
            };
          };
          
          const startPoint = transformPoint(optimizedStravaCoords[0]);
          const endPoint = transformPoint(optimizedStravaCoords[optimizedStravaCoords.length - 1]);
          
          return (
            <>
              {/* Start point */}
              <circle
                cx={startPoint.x}
                cy={startPoint.y}
                r="6"
                fill="rgba(0, 255, 0, 0.9)"
                stroke="white"
                strokeWidth="2"
              />
              {/* End point */}
              <circle
                cx={endPoint.x}
                cy={endPoint.y}
                r="6"
                fill="rgba(255, 0, 0, 0.9)"
                stroke="white"
                strokeWidth="2"
              />
            </>
          );
        })()}
      </svg>
    </div>
  );
}
