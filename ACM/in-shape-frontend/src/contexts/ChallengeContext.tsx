'use client';

import React, { createContext, useContext, useState } from 'react';

interface VisualizationData {
  // Old procrustes format (for backwards compatibility)
  strava_transformed?: number[][];
  svg_normalized?: number[][];
  transform_info?: {
    rotation_matrix: number[][];
    best_shift: number;
    best_direction: number;
    strava_center: number[];
    svg_center: number[];
    strava_scale: number;
    svg_scale: number;
  };
  
  // New IoU format
  coverage_of_target_pct?: number;
  coverage_of_gps_pct?: number;
  best_rotation_deg?: number;
  algorithm?: string;
  full_metrics?: any;
}

interface ChallengeResult {
  activity_id: number;
  shape: string;
  score: number;
  grade: string; // kept in type for backend payload compatibility, but not displayed
  message: string;
  cached: boolean;
  visualization_data?: VisualizationData;
}

interface ChallengeContextType {
  selectedRun: any | null;
  challengeResult: ChallengeResult | null;
  isLoading: boolean;
  setSelectedRun: (run: any) => void;
  setChallengeResult: (result: ChallengeResult) => void;
  setIsLoading: (loading: boolean) => void;
  clearChallenge: () => void;
  clearChallengeResult: () => void; // Clear result but keep selected run
}

const ChallengeContext = createContext<ChallengeContextType | undefined>(undefined);

export function ChallengeProvider({ children }: { children: React.ReactNode }) {
  const [selectedRun, setSelectedRun] = useState<any | null>(null);
  const [challengeResult, setChallengeResult] = useState<ChallengeResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const clearChallenge = () => {
    setSelectedRun(null);
    setChallengeResult(null);
    setIsLoading(false);
  };

  const clearChallengeResult = () => {
    setChallengeResult(null);
    setIsLoading(false);
    // Keep selectedRun intact
  };

  return (
    <ChallengeContext.Provider
      value={{
        selectedRun,
        challengeResult,
        isLoading,
        setSelectedRun,
        setChallengeResult,
        setIsLoading,
        clearChallenge,
        clearChallengeResult,
      }}
    >
      {children}
    </ChallengeContext.Provider>
  );
}

export function useChallenge() {
  const context = useContext(ChallengeContext);
  if (context === undefined) {
    throw new Error('useChallenge must be used within a ChallengeProvider');
  }
  return context;
}
