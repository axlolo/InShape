import { useState, useEffect } from 'react';

interface RunTotals {
  count: number;
  distance: number;
  moving_time: number;
  elapsed_time: number;
  elevation_gain: number;
}

interface AthleteStats {
  recent_run_totals: RunTotals;
  all_run_totals: RunTotals;
  ytd_run_totals: RunTotals;
  this_week_run_totals: RunTotals;
  this_month_run_totals: RunTotals;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export function useAthleteStats() {
  const [stats, setStats] = useState<AthleteStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingMessage, setLoadingMessage] = useState<string>('Loading stats...');

  useEffect(() => {
    const fetchStats = async () => {
      const token = localStorage.getItem('authToken');
      if (!token) {
        setError('No authentication token');
        setLoading(false);
        return;
      }

      try {
        // First check the status to see if we need to fetch
        setLoadingMessage('Checking cache status...');
        
        const statusResponse = await fetch(`${API_BASE_URL}/api/athlete/stats/status`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          
          if (statusData.needs_initial_fetch) {
            setLoadingMessage('First time setup - fetching all your activities from Strava...');
          } else if (statusData.cache_stale) {
            setLoadingMessage('Refreshing your latest activities...');
          } else {
            setLoadingMessage('Loading cached stats...');
          }
        }

        // Now fetch the actual stats
        const response = await fetch(`${API_BASE_URL}/api/athlete/stats/enhanced`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setStats(data.stats);
          setError(null);
          
          // Show completion message based on source
          if (data.source === 'calculated_and_cached') {
            setLoadingMessage('Stats updated successfully!');
          } else {
            setLoadingMessage('Stats loaded from cache');
          }
        } else {
          setError('Failed to fetch athlete stats');
        }
      } catch (err) {
        setError('Network error fetching stats');
        console.error('Error fetching athlete stats:', err);
      } finally {
        setTimeout(() => setLoading(false), 500); // Brief delay to show completion message
      }
    };

    fetchStats();
  }, []);

  // Helper function to convert meters to miles
  const metersToMiles = (meters: number): number => {
    return meters * 0.000621371;
  };

  // Helper function to format distance
  const formatDistance = (meters: number): string => {
    const miles = metersToMiles(meters);
    return `${miles.toFixed(1)} mi`;
  };

  // Helper function to format time
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  return {
    stats,
    loading,
    error,
    loadingMessage,
    formatDistance,
    formatTime,
    metersToMiles,
  };
}
