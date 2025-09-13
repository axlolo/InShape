'use client';

import React, { useState, useEffect } from 'react';
import { XMarkIcon, TrophyIcon, ClockIcon, MapPinIcon } from '@heroicons/react/24/outline';
import { useChallenge } from '../contexts/ChallengeContext';

interface Activity {
  id: number;
  name: string;
  start_date: string;
  distance: number;
  moving_time: number;
  elapsed_time: number;
  type: string;
  average_speed: number;
  // Annotations from backend
  has_map_polyline?: boolean;
  graded?: boolean;
  challenge_score?: number;
  challenge_grade?: string;
  challenge_cached?: boolean;
  challenge_error?: string;
}

interface ChallengeResult {
  activity_id: number;
  shape: string;
  score: number;
  grade: string;
  message: string;
}

interface ChallengeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export default function ChallengeModal({ isOpen, onClose }: ChallengeModalProps) {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);
  const [challengeResult, setChallengeResult] = useState<ChallengeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingActivities, setLoadingActivities] = useState(false);
  const [autoGrading, setAutoGrading] = useState(false);
  
  const { setSelectedRun, setChallengeResult: setGlobalChallengeResult } = useChallenge();

  useEffect(() => {
    if (isOpen) {
      fetchRecentActivities();
    }
  }, [isOpen]);

  const fetchRecentActivities = async () => {
    setLoadingActivities(true);
    setError(null);
    
    const token = localStorage.getItem('authToken');
    if (!token) {
      setError('No authentication token');
      setLoadingActivities(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/activities/recent?days=60&include_grades=true&shape=rectangle`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setActivities(data.activities);
        
        // Auto-select the top pregraded activity if available
        if (data.activities.length > 0) {
          const first = data.activities[0] as Activity;
          setSelectedActivity(first);
          // Kick off auto-grading for overlay coordinates
          void autoGradeForOverlay(first);
        }
      } else {
        setError('Failed to fetch recent activities');
      }
    } catch (err) {
      setError('Network error fetching activities');
      console.error('Error fetching activities:', err);
    } finally {
      setLoadingActivities(false);
    }
  };

  const autoGradeForOverlay = async (activity: Activity) => {
    if (!activity) return;
    
    setAutoGrading(true);
    setError(null);
    
    const token = localStorage.getItem('authToken');
    if (!token) {
      setError('No authentication token');
      setAutoGrading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/activities/${activity.id}/grade`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          shape: 'rectangle',
          include_coordinates: true
        }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Grade response:', result);
        console.log('Has visualization_data:', !!result.visualization_data);
        setChallengeResult(result);
        
        // Store in global context for homepage overlay
        setSelectedRun(activity);
        setGlobalChallengeResult(result);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to grade activity');
      }
    } catch (err) {
      setError('Network error grading activity');
      console.error('Error grading activity:', err);
    } finally {
      setAutoGrading(false);
    }
  };

  const handleActivitySelect = (activity: Activity) => {
    setSelectedActivity(activity);
    setChallengeResult(null); // Clear previous result
    // Auto-grade the newly selected activity for overlay
    void autoGradeForOverlay(activity);
  };


  const formatDistance = (meters: number): string => {
    const miles = meters * 0.000621371;
    return `${miles.toFixed(1)} mi`;
  };

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getScoreColor = (score: number): string => {
    if (score >= 85) return 'text-green-500';
    if (score >= 70) return 'text-yellow-500';
    if (score >= 50) return 'text-orange-500';
    return 'text-red-500';
  };

  // Removed grade-to-color UI; we keep only percentage coloring via getScoreColor

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#2a2a2a]">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-[var(--primary-orange)] rounded-lg flex items-center justify-center">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-white">
                <rect x="3" y="6" width="18" height="12" rx="2" stroke="currentColor" strokeWidth="2"/>
              </svg>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
                Rectangle Challenge
              </h2>
              <p className="text-gray-400 text-sm">Test your shape-running skills!</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          
          {/* Error Message */}
          {error && (
            <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded mb-6">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Run Selection */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">
                Select a Recent Run (Last 60 Days)
              </h3>
              
              {loadingActivities ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--primary-orange)]"></div>
                  <span className="ml-3 text-gray-400">Loading runs...</span>
                </div>
              ) : activities.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <MapPinIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No runs found in the last 60 days.</p>
                  <p className="text-sm mt-1">Go for a run and come back!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {activities.map((activity) => (
                    <div
                      key={activity.id}
                      onClick={() => handleActivitySelect(activity)}
                      className={`p-4 border rounded-lg cursor-pointer transition-all ${
                        selectedActivity?.id === activity.id
                          ? 'border-[var(--primary-orange)] bg-[#2a2a2a]'
                          : 'border-[#2a2a2a] hover:border-gray-600 hover:bg-[#222]'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium text-white truncate">
                            {activity.name}
                          </h4>
                          <div className="flex items-center space-x-4 mt-1 text-sm text-gray-400">
                            <span>{formatDate(activity.start_date)}</span>
                            <span>{formatDistance(activity.distance)}</span>
                            <span>{formatTime(activity.moving_time)}</span>
                            {activity.graded && typeof activity.challenge_score === 'number' ? (
                              <span className="inline-flex items-center space-x-2">
                                <span className="text-white">Score:</span>
                                <span className="text-[var(--primary-orange)] font-semibold">{activity.challenge_score}%</span>
                              </span>
                            ) : activity.challenge_error ? (
                              <span className="text-red-400">{activity.challenge_error}</span>
                            ) : (
                              <span className="text-gray-500">Grading...</span>
                            )}
                          </div>
                        </div>
                        {selectedActivity?.id === activity.id && (
                          <div className="w-4 h-4 rounded-full bg-[var(--primary-orange)] flex-shrink-0"></div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Challenge Results */}
            <div>
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white">
                  Challenge Results
                </h3>
              </div>
              
              {selectedActivity ? (
                <div className="space-y-4">
                  
                  {/* Selected Run Info */}
                  <div className="bg-[#222] border border-[#2a2a2a] rounded-lg p-4">
                    <h4 className="font-medium text-white mb-2">Selected Run</h4>
                    <p className="text-gray-300 text-sm truncate">{selectedActivity.name}</p>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-400">
                      <span>{formatDistance(selectedActivity.distance)}</span>
                      <span>{formatTime(selectedActivity.moving_time)}</span>
                    </div>
                  </div>

                  {/* Auto grading indicator */}
                  {autoGrading && (
                    <div className="w-full bg-[#222] border border-[#2a2a2a] rounded-lg p-3 text-center text-gray-300">
                      <div className="flex items-center justify-center space-x-2">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Preparing overlay...</span>
                      </div>
                    </div>
                  )}

                  {/* Results */}
                  {challengeResult && (
                    <div className="bg-[#222] border border-[#2a2a2a] rounded-lg p-6">
                      <div className="text-center">
                        <div className={`text-4xl font-bold mb-2 ${getScoreColor(challengeResult.score)}`}>
                          {challengeResult.score}%
                        </div>
                        
                        <p className="text-gray-300 mb-4">
                          {challengeResult.message}
                        </p>
                        
                        <div className="text-sm text-gray-400">
                          Shape similarity calculated using Procrustes analysis
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-400">
                  <TrophyIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>Select a run to see your challenge results</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
