'use client';

import { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon, GiftIcon, CalendarIcon, UsersIcon } from '@heroicons/react/24/outline';

// Mock data for missions and group rankings
const mockMissions = [
  {
    id: 1,
    company: 'Nike',
    logo: 'https://logos-world.net/wp-content/uploads/2020/04/Nike-Logo.png',
    title: 'Run the Swoosh Challenge',
    description: 'Create Nike\'s iconic swoosh logo with your running route',
    reward: 'Nike Air Zoom Pegasus 40 Running Shoes',
    rewardValue: '$130',
    deadline: '2024-10-15',
    participants: 1247,
    targetShape: 'Nike Swoosh',
    shapeImage: '/shapes/star-1.svg', // Using star as placeholder for swoosh
    requirements: [
      'Route must be at least 2 miles long',
      'Accuracy score of 75% or higher',
      'Complete within 45 minutes',
      'Upload to social media with #NikeSwooshRun'
    ],
    groupRankings: [
      { groupName: 'Shape Masters', accuracy: 89.2, rank: 1 },
      { groupName: 'Downtown Runners', accuracy: 84.7, rank: 2 },
      { groupName: 'City Runners Club', accuracy: 78.3, rank: 3 },
      { groupName: 'Weekend Warriors', accuracy: 72.1, rank: 4 },
      { groupName: 'Marathon Shapers', accuracy: 68.9, rank: 5 },
    ]
  },
  {
    id: 2,
    company: 'Alo Yoga',
    logo: 'https://logos-world.net/wp-content/uploads/2023/01/Alo-Yoga-Logo.png',
    title: 'Mindful Movement Circle',
    description: 'Run a perfect circle to embody Alo\'s philosophy of mindful movement',
    reward: 'Alo Yoga Shine Long Sleeve + Leggings Set',
    rewardValue: '$180',
    deadline: '2024-09-30',
    participants: 892,
    targetShape: 'Perfect Circle',
    shapeImage: '/shapes/circle-1.svg',
    requirements: [
      'Perfect circular route (85%+ accuracy)',
      'Minimum 3 mile distance',
      'Maintain steady pace throughout',
      'Share mindfulness moment post-run'
    ],
    groupRankings: [
      { groupName: 'Downtown Runners', accuracy: 91.5, rank: 1 },
      { groupName: 'Shape Masters', accuracy: 87.8, rank: 2 },
      { groupName: 'Weekend Warriors', accuracy: 81.2, rank: 3 },
      { groupName: 'Marathon Shapers', accuracy: 76.4, rank: 4 },
      { groupName: 'City Runners Club', accuracy: 73.9, rank: 5 },
    ]
  },
  {
    id: 3,
    company: 'Adidas',
    logo: 'https://logos-world.net/wp-content/uploads/2020/04/Adidas-Logo.png',
    title: 'Three Stripes Triangle',
    description: 'Honor the three stripes legacy by running a perfect triangle',
    reward: 'Adidas Ultraboost 23 + Training Gear',
    rewardValue: '$220',
    deadline: '2024-11-01',
    participants: 1456,
    targetShape: 'Equilateral Triangle',
    shapeImage: '/shapes/triangle-1.svg',
    requirements: [
      'Equilateral triangle shape (80%+ accuracy)',
      'Each side minimum 1.5 miles',
      'Complete in under 35 minutes',
      'Tag @adidas in completion post'
    ],
    groupRankings: [
      { groupName: 'City Runners Club', accuracy: 86.7, rank: 1 },
      { groupName: 'Shape Masters', accuracy: 85.1, rank: 2 },
      { groupName: 'Marathon Shapers', accuracy: 79.8, rank: 3 },
      { groupName: 'Downtown Runners', accuracy: 77.2, rank: 4 },
      { groupName: 'Weekend Warriors', accuracy: 74.6, rank: 5 },
    ]
  },
  {
    id: 4,
    company: 'Lululemon',
    logo: 'https://logos-world.net/wp-content/uploads/2020/11/Lululemon-Logo.png',
    title: 'Omega Mindfulness Run',
    description: 'Channel inner peace by running Lululemon\'s omega symbol',
    reward: 'Lululemon Fast & Free Tights + Define Jacket',
    rewardValue: '$298',
    deadline: '2024-10-20',
    participants: 743,
    targetShape: 'Omega Symbol',
    shapeImage: '/shapes/heart-1.svg', // Using heart as placeholder for omega
    requirements: [
      'Omega-shaped route (75%+ accuracy)',
      'Minimum 4 mile total distance',
      'Include 5-minute meditation stops',
      'Share wellness journey story'
    ],
    groupRankings: [
      { groupName: 'Weekend Warriors', accuracy: 88.3, rank: 1 },
      { groupName: 'Shape Masters', accuracy: 83.9, rank: 2 },
      { groupName: 'Downtown Runners', accuracy: 80.1, rank: 3 },
      { groupName: 'City Runners Club', accuracy: 75.7, rank: 4 },
      { groupName: 'Marathon Shapers', accuracy: 71.2, rank: 5 },
    ]
  }
];

export default function MissionsPage() {
  const [expandedMissions, setExpandedMissions] = useState<number[]>([]);

  const toggleMission = (missionId: number) => {
    setExpandedMissions(prev => 
      prev.includes(missionId)
        ? prev.filter(id => id !== missionId)
        : [...prev, missionId]
    );
  };

  const getRankColor = (rank: number) => {
    switch (rank) {
      case 1: return 'text-yellow-500 font-bold';
      case 2: return 'text-gray-400 font-bold';
      case 3: return 'text-orange-500 font-bold';
      default: return 'text-gray-300';
    }
  };

  const getDaysLeft = (deadline: string) => {
    const today = new Date();
    const endDate = new Date(deadline);
    const diffTime = endDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  return (
    <div className="min-h-screen bg-[#0f0f0f] py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-white mb-4" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
            Brand Missions
          </h1>
          <p className="text-gray-400 text-lg">
            Complete sponsored challenges from top brands and earn exclusive rewards
          </p>
        </div>

        {/* Missions List */}
        <div className="space-y-6">
          {mockMissions.map((mission) => {
            const isExpanded = expandedMissions.includes(mission.id);
            const daysLeft = getDaysLeft(mission.deadline);
            
            return (
              <div key={mission.id} className="bg-[#1a1a1a] border border-[#2a2a2a] overflow-hidden">
                <div 
                  className="p-6 cursor-pointer hover:bg-[#222] transition-colors"
                  onClick={() => toggleMission(mission.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-6">
                      <img 
                        src={mission.logo} 
                        alt={`${mission.company} logo`}
                        className="w-16 h-16 object-contain bg-white rounded-lg p-2"
                      />
                      
                      <div>
                        <h3 className="text-xl font-bold text-white mb-1" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
                          {mission.title}
                        </h3>
                        <p className="text-gray-400 mb-2">
                          {mission.description}
                        </p>
                        
                        <div className="flex items-center space-x-6 text-sm">
                          <div className="flex items-center text-[var(--primary-orange)]">
                            <GiftIcon className="w-4 h-4 mr-1" />
                            <span className="font-semibold">{mission.rewardValue}</span>
                          </div>
                          
                          <div className="flex items-center text-gray-400">
                            <CalendarIcon className="w-4 h-4 mr-1" />
                            <span>{daysLeft} days left</span>
                          </div>
                          
                          <div className="flex items-center text-gray-400">
                            <UsersIcon className="w-4 h-4 mr-1" />
                            <span>{mission.participants.toLocaleString()} participants</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <div className="text-white font-semibold">{mission.reward}</div>
                        <div className="text-gray-400 text-sm">Reward</div>
                      </div>
                      
                      {isExpanded ? (
                        <ChevronUpIcon className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDownIcon className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                  </div>
                </div>
                
                {isExpanded && (
                  <div className="border-t border-[#2a2a2a] bg-[#111]">
                    <div className="p-6 grid gap-8 lg:grid-cols-2">
                      {/* Mission Details */}
                      <div>
                        <h4 className="text-lg font-semibold text-white mb-4" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
                          Mission Requirements
                        </h4>
                        
                        <div className="mb-6">
                          <div className="flex items-center justify-center w-32 h-32 bg-[#1a1a1a] border border-[#2a2a2a] mx-auto mb-4">
                            <img 
                              src={mission.shapeImage} 
                              alt={mission.targetShape}
                              className="w-24 h-24 object-contain filter invert"
                            />
                          </div>
                          <p className="text-center text-gray-400 font-medium">{mission.targetShape}</p>
                        </div>
                        
                        <ul className="space-y-3">
                          {mission.requirements.map((req, index) => (
                            <li key={index} className="flex items-start space-x-3">
                              <div className="w-2 h-2 bg-[var(--primary-orange)] rounded-full mt-2 flex-shrink-0"></div>
                              <span className="text-gray-300 text-sm">{req}</span>
                            </li>
                          ))}
                        </ul>
                        
                        <button className="w-full mt-6 bg-[var(--primary-orange)] text-white py-3 px-6 font-semibold hover:bg-[var(--orange-dark)] transition-colors">
                          Accept Mission
                        </button>
                      </div>
                      
                      {/* Group Rankings */}
                      <div>
                        <h4 className="text-lg font-semibold text-white mb-4" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
                          Group Performance Rankings
                        </h4>
                        
                        <div className="space-y-3">
                          {mission.groupRankings.map((group) => (
                            <div key={group.groupName} className="flex items-center justify-between p-3 bg-[#1a1a1a] border border-[#2a2a2a]">
                              <div className="flex items-center space-x-3">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                  group.rank <= 3 ? 'bg-[#2a2a2a]' : 'bg-[#1a1a1a]'
                                }`}>
                                  <span className={getRankColor(group.rank)}>#{group.rank}</span>
                                </div>
                                <span className="text-white font-medium">{group.groupName}</span>
                              </div>
                              
                              <div className="text-right">
                                <div className="text-[var(--primary-orange)] font-bold">
                                  {group.accuracy}%
                                </div>
                                <div className="text-gray-400 text-xs">accuracy</div>
                              </div>
                            </div>
                          ))}
                        </div>
                        
                        <div className="mt-4 p-3 bg-[#2a2a2a] border border-[#3a3a3a]">
                          <p className="text-gray-300 text-sm">
                            <span className="text-[var(--primary-orange)] font-semibold">Your groups</span> are competing 
                            for the top spots. Higher accuracy increases your chances of winning!
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        
        {/* Footer Info */}
        <div className="mt-12 text-center">
          <p className="text-gray-400">
            New missions are added weekly. Check back regularly for exclusive brand partnerships!
          </p>
        </div>
      </div>
    </div>
  );
}
