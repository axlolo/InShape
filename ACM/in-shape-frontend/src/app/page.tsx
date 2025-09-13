'use client';

import Link from "next/link";
import { useState } from "react";
import { getTodaysShape } from "../utils/shapes";
import ProtectedRoute from "../components/ProtectedRoute";
import ChallengeModal from "../components/ChallengeModal";
import ShapeOverlay from "../components/ShapeOverlay";
import { useChallenge } from "../contexts/ChallengeContext";

// Get today's shape dynamically
const todaysShape = getTodaysShape();

const mockGroups = [
  {
    id: 1,
    name: "Downtown Runners",
    bestAccuracy: 94.8,
    members: 24,
  },
  {
    id: 2,
    name: "Shape Masters",
    bestAccuracy: 91.2,
    members: 156,
  },
  {
    id: 3,
    name: "Weekend Warriors",
    bestAccuracy: 88.7,
    members: 89,
  },
  {
    id: 4,
    name: "City Runners Club",
    bestAccuracy: 87.3,
    members: 324,
  },
  {
    id: 5,
    name: "Marathon Shapers",
    bestAccuracy: 85.9,
    members: 67,
  },
];

export default function Home() {
  const [isChallengeModalOpen, setIsChallengeModalOpen] = useState(false);
  const { challengeResult, selectedRun } = useChallenge();
  
  console.log('Homepage - challengeResult:', challengeResult);
  console.log('Homepage - selectedRun:', selectedRun);
  console.log('Homepage - has visualization_data:', !!challengeResult?.visualization_data);

  // Derive dynamic leaderboard data: override bestAccuracy with user's current score if higher
  const userScore = typeof challengeResult?.score === 'number' ? Number(challengeResult.score.toFixed(1)) : null;
  const computedGroups = mockGroups.map(g => {
    const original = g.bestAccuracy;
    const bestAccuracy = userScore !== null ? Math.max(original, userScore) : original;
    const topIsYou = userScore !== null && userScore >= bestAccuracy && userScore >= original;
    return { ...g, bestAccuracy, topIsYou } as typeof g & { topIsYou?: boolean };
  });

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[#0f0f0f]">
        <div className="max-w-5xl mx-auto px-6 py-16">
          
          {/* Today's Shape Section */}
          <div className="mb-14">
            <h1 className="text-5xl font-bold text-white mb-6 text-center" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
              Today's Shape
            </h1>
            
            <div className="flex flex-col items-center">
              <div className="mb-6 relative w-full h-[520px] mx-auto flex items-center justify-center">
                {/* Map background with low opacity */}
                <div 
                  className="absolute bg-center bg-no-repeat opacity-10"
                  style={{
                    backgroundImage: 'url(/map.png)',
                    backgroundSize: 'contain',
                    width: '100%',
                    height: '100%',
                    left: '50%',
                    top: '50%',
                    transform: 'translate(-50%, -50%)',
                    zIndex: 1
                  }}
                />
                {/* Shape on top (scaled to match overlay target) */}
                <div className="absolute inset-0 flex items-center justify-center z-10">
                  <img 
                    src={todaysShape.image} 
                    alt={todaysShape.name}
                    className="h-[70%] w-auto object-contain filter invert"
                  />
                </div>
                {/* Shape overlay with user's run path */}
                {challengeResult?.visualization_data && (
                  <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 20 }}>
                    <ShapeOverlay
                      visualizationData={challengeResult.visualization_data}
                      width={900}
                      height={520}
                    />
                  </div>
                )}
              </div>
              <h2 className="text-3xl font-bold text-white mb-4" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
                {todaysShape.name}
              </h2>
              <p className="text-gray-400 text-lg mb-4 text-center max-w-md">
                {todaysShape.description}
              </p>
              {challengeResult && selectedRun && (
                <div className="mb-4 text-center">
                  <p className="text-[var(--primary-orange)] font-semibold mb-2">
                    📍 Showing: {selectedRun.name}
                  </p>
                  {challengeResult.visualization_data ? (
                    <p className="text-sm text-gray-400">
                      Your run is overlaid in <span className="text-[var(--primary-orange)]">orange</span> on the target shape
                    </p>
                  ) : (
                    <p className="text-sm text-red-400">
                      Visualization data not available (cached result)
                    </p>
                  )}
                  <p className="text-lg font-bold text-white mt-2">
                    Score: {challengeResult.score}%
                  </p>
                </div>
              )}
              <button 
                onClick={() => setIsChallengeModalOpen(true)}
                className="bg-[var(--primary-orange)] text-white px-8 py-3 font-semibold hover:bg-[var(--orange-dark)] transition-colors"
              >
                Start Challenge
              </button>
            </div>
          </div>

          {/* Groups Section */}
          <div>
            <h2 className="text-4xl font-bold text-white mb-12 text-center" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
              Leaderboard
            </h2>
            
            <div className="space-y-1">
              {computedGroups.map((group, index) => (
                <Link key={group.id} href={`/leaderboard/${group.id}`}>
                  <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-6 hover:bg-[#222] transition-colors cursor-pointer">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-6">
                        <div className="text-2xl font-bold text-gray-500 w-8">
                          {index + 1}
                        </div>
                        <div>
                          <h3 className="text-xl font-semibold text-white flex items-center space-x-2" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
                            <span>{group.name}</span>
                          </h3>
                          <p className="text-gray-400">
                            {group.members} members
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        {group.topIsYou && (
                          <span className="px-2 py-0.5 text-xs font-semibold text-[var(--primary-orange)] border border-[var(--primary-orange)]">
                            You
                          </span>
                        )}
                        <div className="text-right">
                          <div className="text-3xl font-bold text-[var(--primary-orange)]" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
                            {group.bestAccuracy}%
                          </div>
                          <div className="text-sm text-gray-400">
                            Best Score
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            
            <div className="text-center mt-12">
              <Link href="/groups">
                <button className="border border-[var(--primary-orange)] text-[var(--primary-orange)] px-8 py-3 font-semibold hover:bg-[var(--primary-orange)] hover:text-white transition-colors">
                  View All Groups
                </button>
              </Link>
            </div>
          </div>
        </div>
      </div>
      
      {/* Challenge Modal */}
      <ChallengeModal 
        isOpen={isChallengeModalOpen} 
        onClose={() => setIsChallengeModalOpen(false)} 
      />
    </ProtectedRoute>
  );
}
