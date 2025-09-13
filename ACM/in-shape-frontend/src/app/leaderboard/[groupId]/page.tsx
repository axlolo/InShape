'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { 
  ChevronLeftIcon, 
  TrophyIcon, 
  ClockIcon, 
  MapPinIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';

// Mock data - replace with actual API calls later
const mockGroupData: { [key: string]: any } = {
  '1': {
    name: "Downtown Runners",
    currentChallenge: "Perfect Rectangle",
    challengeEndDate: "September 20, 2024",
    description: "Run a route that forms a perfect rectangle shape",
  },
  '2': {
    name: "Shape Masters",
    currentChallenge: "Star Pattern",
    challengeEndDate: "September 22, 2024",
    description: "Create a 5-pointed star with your running route",
  },
  '3': {
    name: "Weekend Warriors",
    currentChallenge: "Heart Shape",
    challengeEndDate: "September 25, 2024",
    description: "Run a heart-shaped route for the romantic challenge",
  },
};

const mockLeaderboardData = [
  {
    id: 1,
    rank: 1,
    name: "Sarah Johnson",
    avatar: "https://images.unsplash.com/photo-1494790108755-2616b612c05e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
    score: 94.8,
    distance: "3.4 miles",
    time: "29:15",
    date: "2024-09-12",
    isExpanded: false,
  },
  {
    id: 2,
    rank: 2,
    name: "Mike Chen",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
    score: 91.2,
    distance: "3.1 miles",
    time: "27:43",
    date: "2024-09-12",
    isExpanded: false,
  },
  {
    id: 3,
    rank: 3,
    name: "Emma Rodriguez",
    avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
    score: 88.7,
    distance: "2.9 miles",
    time: "26:11",
    date: "2024-09-11",
    isExpanded: false,
  },
  {
    id: 4,
    rank: 4,
    name: "John Doe",
    avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
    score: 87.5,
    distance: "3.2 miles",
    time: "28:15",
    date: "2024-09-10",
    isExpanded: false,
    isCurrentUser: true,
  },
  {
    id: 5,
    rank: 5,
    name: "Lisa Wang",
    avatar: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
    score: 85.3,
    distance: "3.0 miles",
    time: "30:22",
    date: "2024-09-10",
    isExpanded: false,
  },
];

export default function LeaderboardPage() {
  const params = useParams();
  const groupId = params.groupId as string;
  const [leaderboardData, setLeaderboardData] = useState(mockLeaderboardData);
  
  const groupInfo = mockGroupData[groupId] || mockGroupData['1'];

  const toggleExpand = (userId: number) => {
    setLeaderboardData(prev => 
      prev.map(user => 
        user.id === userId 
          ? { ...user, isExpanded: !user.isExpanded }
          : user
      )
    );
  };

  const getRankColor = (rank: number) => {
    switch (rank) {
      case 1: return 'text-yellow-600 bg-yellow-50';
      case 2: return 'text-gray-400 bg-[#222]';
      case 3: return 'text-orange-600 bg-orange-50';
      default: return 'text-gray-300 bg-gray-100';
    }
  };

  const getRankIcon = (rank: number) => {
    if (rank <= 3) {
      return <TrophyIcon className="w-5 h-5" />;
    }
    return <span className="font-bold text-sm">#{rank}</span>;
  };

  return (
    <div className="min-h-screen bg-[#0f0f0f] py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link href="/groups" className="inline-flex items-center text-[var(--primary-orange)] hover:text-[var(--orange-dark)] mb-4">
            <ChevronLeftIcon className="w-4 h-4 mr-1" />
            Back to Groups
          </Link>
          
          <div className="bg-[#1a1a1a] rounded-xl shadow-sm border border-[#2a2a2a] p-6">
            <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>{groupInfo.name}</h1>
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <div>
                <h3 className="font-medium text-white">Current Challenge</h3>
                <p className="text-[var(--primary-orange)] font-semibold">{groupInfo.currentChallenge}</p>
              </div>
              <div>
                <h3 className="font-medium text-white">Challenge Ends</h3>
                <p className="text-gray-400">{groupInfo.challengeEndDate}</p>
              </div>
              <div>
                <h3 className="font-medium text-white">Description</h3>
                <p className="text-gray-400">{groupInfo.description}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Leaderboard */}
        <div className="bg-[#1a1a1a] rounded-xl shadow-sm border border-[#2a2a2a]">
          <div className="p-6 border-b border-[#2a2a2a]">
            <h2 className="text-xl font-semibold text-white" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>Leaderboard</h2>
            <p className="text-gray-400 mt-1">Click on any user to see their detailed stats</p>
          </div>
          
          <div className="divide-y divide-gray-200">
            {leaderboardData.map((user) => (
              <div key={user.id} className="hover:bg-[#222] transition-colors">
                <div 
                  className="p-6 cursor-pointer"
                  onClick={() => toggleExpand(user.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${getRankColor(user.rank)}`}>
                        {getRankIcon(user.rank)}
                      </div>
                      
                      <img
                        className="h-12 w-12 rounded-full object-cover"
                        src={user.avatar}
                        alt={user.name}
                      />
                      
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className={`font-medium ${user.isCurrentUser ? 'text-[var(--primary-orange)]' : 'text-white'}`}>
                            {user.name}
                          </span>
                          {user.isCurrentUser && (
                            <span className="px-2 py-1 bg-orange-100 text-[var(--primary-orange)] text-xs rounded-full">
                              You
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-400">{user.date}</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-[var(--primary-orange)]">{user.score}%</div>
                        <div className="text-xs text-gray-400">Score</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="font-medium text-white">{user.distance}</div>
                        <div className="text-xs text-gray-400">Distance</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="font-medium text-white">{user.time}</div>
                        <div className="text-xs text-gray-400">Time</div>
                      </div>
                      
                      <div className="ml-4">
                        {user.isExpanded ? (
                          <ChevronUpIcon className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronDownIcon className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                    </div>
                  </div>
                </div>
                
                {user.isExpanded && (
                  <div className="px-6 pb-6 bg-[#222]">
                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="bg-[#1a1a1a] rounded-lg p-4">
                        <div className="flex items-center mb-2">
                          <TrophyIcon className="w-5 h-5 text-[var(--primary-orange)] mr-2" />
                          <span className="font-medium text-white">Shape Analysis</span>
                        </div>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-400">Accuracy:</span>
                            <span className="font-medium">{user.score}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Corner Precision:</span>
                            <span className="font-medium">92.1%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Side Symmetry:</span>
                            <span className="font-medium">89.3%</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="bg-[#1a1a1a] rounded-lg p-4">
                        <div className="flex items-center mb-2">
                          <MapPinIcon className="w-5 h-5 text-green-600 mr-2" />
                          <span className="font-medium text-white">Route Details</span>
                        </div>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-400">Distance:</span>
                            <span className="font-medium">{user.distance}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Avg Pace:</span>
                            <span className="font-medium">8:48/mile</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Elevation:</span>
                            <span className="font-medium">124 ft</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="bg-[#1a1a1a] rounded-lg p-4">
                        <div className="flex items-center mb-2">
                          <ClockIcon className="w-5 h-5 text-blue-600 mr-2" />
                          <span className="font-medium text-white">Performance</span>
                        </div>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-400">Total Time:</span>
                            <span className="font-medium">{user.time}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Moving Time:</span>
                            <span className="font-medium">26:34</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Calories:</span>
                            <span className="font-medium">342</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
