'use client';

import Link from 'next/link';
import { TrophyIcon, CalendarIcon, ClockIcon, MapPinIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import ProtectedRoute from '../../components/ProtectedRoute';
import { useAthleteStats } from '../../hooks/useAthleteStats';
import { useEffect, useState } from 'react';

// Mock data - replace with actual API calls later
const mockUser = {
  name: "John Doe",
  profilePicture: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
  lifetimePoints: 2847,
  memberSince: "January 2024",
  totalRuns: 43,
  bestShape: "Rectangle",
  bestScore: 94.2,
  groups: [
    { id: 1, name: "Downtown Runners", members: 24, joinedDate: "Jan 2024" },
    { id: 2, name: "Shape Masters", members: 156, joinedDate: "Feb 2024" },
    { id: 3, name: "Weekend Warriors", members: 89, joinedDate: "Mar 2024" },
  ],
  recentRuns: [
    { id: 1, date: "2024-09-10", shape: "Rectangle", score: 87.5, distance: "3.2 miles", time: "28:15" },
    { id: 2, date: "2024-09-08", shape: "Circle", score: 72.1, distance: "2.8 miles", time: "25:43" },
    { id: 3, date: "2024-09-06", shape: "Triangle", score: 91.3, distance: "4.1 miles", time: "35:20" },
  ]
};

export default function ProfilePage() {
  const { user } = useAuth();
  const { stats, loading: statsLoading, loadingMessage, formatDistance, formatTime } = useAthleteStats();
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

  type Activity = {
    id: number;
    name: string;
    start_date: string;
    distance: number;
    moving_time: number;
    type: string;
  };

  const [recentActivities, setRecentActivities] = useState<Activity[]>([]);
  const [recentLoading, setRecentLoading] = useState<boolean>(false);
  const [recentError, setRecentError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecent = async () => {
      setRecentLoading(true);
      setRecentError(null);
      const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;
      if (!token) {
        setRecentError('No authentication token');
        setRecentLoading(false);
        return;
      }
      try {
        const resp = await fetch(`${API_BASE_URL}/api/activities/recent?days=14`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!resp.ok) {
          setRecentError('Failed to fetch recent runs');
        } else {
          const data = await resp.json();
          const runs: Activity[] = (data.activities || []).filter((a: any) => a.type === 'Run');
          setRecentActivities(runs);
        }
      } catch (e) {
        setRecentError('Network error');
      } finally {
        setRecentLoading(false);
      }
    };
    fetchRecent();
  }, []);

  // Format the user's full name
  const fullName = user ? `${user.firstname} ${user.lastname}` : 'Loading...';
  
  // Use user's profile picture or fallback to default
  const profilePicture = user?.profile || '/default-avatar.svg';
  
  // Format location if available
  const location = user?.city && user?.country ? `${user.city}, ${user.country}` : user?.country || 'Location not set';
  
  // Format member since date from Strava creation date
  const formatMemberSince = (created_at?: string) => {
    if (!created_at) return "Connected via Strava";
    
    const date = new Date(created_at);
    const options: Intl.DateTimeFormatOptions = { 
      year: 'numeric', 
      month: 'long' 
    };
    return `Member since ${date.toLocaleDateString('en-US', options)}`;
  };
  
  const memberSince = formatMemberSince(user?.created_at);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[#0f0f0f] py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          {/* Loading Status Banner */}
          {statsLoading && (
            <div className="bg-[#1a1a1a] border border-[var(--primary-orange)] p-4 mb-6 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-[var(--primary-orange)]"></div>
                <div>
                  <div className="text-white font-medium">Fetching Your Running Data</div>
                  <div className="text-gray-400 text-sm">{loadingMessage}</div>
                </div>
              </div>
            </div>
          )}
          {/* Profile Header */}
          <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-8 mb-8">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between">
              <div className="flex items-center space-x-6">
                <img
                  className="h-24 w-24 rounded-full object-cover"
                  src={profilePicture}
                  alt={fullName}
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/default-avatar.svg';
                  }}
                />
                <div>
                  <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
                    {fullName}
                  </h1>
                  <p className="text-gray-400 flex items-center mt-1">
                    <CalendarIcon className="w-4 h-4 mr-1" />
                    {memberSince}
                  </p>
                  {location !== 'Location not set' && (
                    <p className="text-gray-400 flex items-center mt-1">
                      <MapPinIcon className="w-4 h-4 mr-1" />
                      {location}
                    </p>
                  )}
                </div>
              </div>
              
              <div className="mt-6 md:mt-0 flex flex-col md:flex-row md:space-x-8">
                <div className="text-center md:text-right">
                  <div className="text-3xl font-bold text-[var(--primary-orange)]">
                    {statsLoading ? '...' : stats?.this_week_run_totals?.count ? `${stats.this_week_run_totals.count}` : '0'}
                  </div>
                  <div className="text-sm text-gray-400">Runs This Week</div>
                </div>
                <div className="text-center md:text-right mt-4 md:mt-0">
                  <div className="text-3xl font-bold text-green-500">
                    {statsLoading ? '...' : stats?.this_week_run_totals?.moving_time ? formatTime(stats.this_week_run_totals.moving_time) : '0m'}
                  </div>
                  <div className="text-sm text-gray-400">Time This Week</div>
                </div>
              </div>
            </div>
          </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Stats Cards */}
          <div className="lg:col-span-2 space-y-6">
            <div className="grid gap-4 sm:grid-cols-4">
              <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-6">
                <div className="flex items-center">
                  <MapPinIcon className="w-8 h-8 text-[var(--primary-orange)]" />
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-white">
                      {statsLoading ? '...' : stats?.all_run_totals?.count || 0}
                    </div>
                    <div className="text-sm text-gray-400">Total Runs</div>
                  </div>
                </div>
              </div>
              
              <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-6">
                <div className="flex items-center">
                  <ClockIcon className="w-8 h-8 text-blue-500" />
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-white">
                      {statsLoading ? '...' : stats?.this_week_run_totals?.distance ? formatDistance(stats.this_week_run_totals.distance) : '0 mi'}
                    </div>
                    <div className="text-sm text-gray-400">Distance This Week</div>
                  </div>
                </div>
              </div>
              
              <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-6">
                <div className="flex items-center">
                  <TrophyIcon className="w-8 h-8 text-yellow-500" />
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-white">
                      {statsLoading ? '...' : stats?.all_run_totals?.distance ? formatDistance(stats.all_run_totals.distance) : '0 mi'}
                    </div>
                    <div className="text-sm text-gray-400">All Time Distance</div>
                  </div>
                </div>
              </div>
              
              <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-6">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-xs">YTD</span>
                  </div>
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-white">
                      {statsLoading ? '...' : stats?.ytd_run_totals?.distance ? formatDistance(stats.ytd_run_totals.distance) : '0 mi'}
                    </div>
                    <div className="text-sm text-gray-400">Year to Date</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Runs (last 14 days) */}
            <div className="bg-[#1a1a1a] border border-[#2a2a2a]">
              <div className="p-6 border-b border-[#2a2a2a]">
                <h2 className="text-xl font-semibold text-white" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>Recent Runs</h2>
              </div>
              {recentLoading ? (
                <div className="p-6 text-gray-400">Loading recent runs...</div>
              ) : recentError ? (
                <div className="p-6 text-red-400">{recentError}</div>
              ) : recentActivities.length === 0 ? (
                <div className="p-6 text-gray-400">No runs in the last 14 days.</div>
              ) : (
                <div className="divide-y divide-[#2a2a2a]">
                  {recentActivities.map((a) => (
                    <div key={a.id} className="p-6 hover:bg-[#222]">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                            <span className="text-[var(--primary-orange)] font-bold">{(a.name || 'Run').charAt(0).toUpperCase()}</span>
                          </div>
                          <div>
                            <div className="font-medium text-white truncate max-w-xs">{a.name || 'Run'}</div>
                            <div className="text-sm text-gray-400">{new Date(a.start_date).toLocaleString()}</div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-6 text-sm">
                          <div className="text-center">
                            <div className="font-medium text-white">{formatDistance(a.distance)}</div>
                            <div className="text-gray-400">Distance</div>
                          </div>
                          <div className="text-center">
                            <div className="font-medium text-white">{formatTime(a.moving_time)}</div>
                            <div className="text-gray-400">Time</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Groups Sidebar */}
          <div className="bg-[#1a1a1a] border border-[#2a2a2a]">
            <div className="p-6 border-b border-[#2a2a2a]">
              <h2 className="text-xl font-semibold text-white" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>Your Groups</h2>
            </div>
            <div className="p-6 space-y-4">
              {mockUser.groups.map((group) => (
                <Link key={group.id} href={`/leaderboard/${group.id}`} className="block">
                  <div className="p-4 border border-[#2a2a2a] hover:border-[var(--primary-orange)] hover:bg-[#222] transition-colors">
                    <div className="font-medium text-white">{group.name}</div>
                    <div className="text-sm text-gray-400 mt-1">
                      {group.members} members • Joined {group.joinedDate}
                    </div>
                  </div>
                </Link>
              ))}
              
              <Link href="/groups" className="block">
                <div className="p-4 border border-dashed border-[#2a2a2a] hover:border-[var(--primary-orange)] text-center transition-colors">
                  <div className="text-[var(--primary-orange)] font-medium">+ Join More Groups</div>
                </div>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
    </ProtectedRoute>
  );
}
