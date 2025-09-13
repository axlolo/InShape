'use client';

import { useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { TrophyIcon } from '@heroicons/react/24/outline';

export default function AuthPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0f0f0f] flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-[var(--primary-orange)]"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f0f0f] flex items-center justify-center">
      <div className="max-w-md w-full px-6">
        <div className="text-center">
          {/* Logo/Brand */}
          <div className="mb-8">
            <img 
              src="/InShapeWhite.png" 
              alt="InShape" 
              className="w-32 h-auto mx-auto mb-6"
            />
            <h1 
              className="text-4xl font-bold text-white mb-2" 
              style={{ fontFamily: 'Alliance No.2, sans-serif' }}
            >
              Running -- The <span className="text-[var(--primary-orange)]">Game</span>
            </h1>
            <p className="text-gray-400 text-lg">
              Link your strava account to get in shape
            </p>
          </div>

          {/* Features Preview */}
          <div className="mb-8 space-y-4">
            <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-4 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-[var(--primary-orange)] rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="text-left">
                  <h3 className="text-white font-semibold" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>Track Your Runs</h3>
                  <p className="text-gray-400 text-sm">Automatically sync your activities</p>
                </div>
              </div>
            </div>

            <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-4 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-[var(--primary-orange)] rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 4a1 1 0 011-1h4a1 1 0 010 2H6.414l2.293 2.293a1 1 0 01-1.414 1.414L5 6.414V8a1 1 0 01-2 0V4zm9 1a1 1 0 010-2h4a1 1 0 011 1v4a1 1 0 01-2 0V6.414l-2.293 2.293a1 1 0 11-1.414-1.414L13.586 5H12zm-9 7a1 1 0 012 0v1.586l2.293-2.293a1 1 0 111.414 1.414L6.414 15H8a1 1 0 010 2H4a1 1 0 01-1-1v-4zm13-1a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 010-2h1.586l-2.293-2.293a1 1 0 111.414-1.414L15.586 13H14a1 1 0 01-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="text-left">
                  <h3 className="text-white font-semibold" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>Shape Challenges</h3>
                  <p className="text-gray-400 text-sm">Draw shapes with your running routes</p>
                </div>
              </div>
            </div>

            <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-4 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-[var(--primary-orange)] rounded-full flex items-center justify-center">
                  <TrophyIcon className="w-4 h-4 text-white" />
                </div>
                <div className="text-left">
                  <h3 className="text-white font-semibold" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>Compete & Compare</h3>
                  <p className="text-gray-400 text-sm">Join groups and climb leaderboards</p>
                </div>
              </div>
            </div>
          </div>

          {/* Connect Button */}
          <button
            onClick={login}
            className="w-full bg-[#FC4C02] hover:bg-[#E8440B] text-white font-bold py-4 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-3"
            style={{ fontFamily: 'Alliance No.2, sans-serif' }}
          >
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.387 17.944l-2.089-4.116h-3.065L15.387 24l5.15-10.172h-3.066m-7.008-5.599l2.836 5.599h4.172L10.463 0l-7.009 13.828h4.172"/>
            </svg>
            <span>Connect with Strava</span>
          </button>

          <p className="text-gray-500 text-sm mt-4">
            We'll redirect you to Strava to authorize the connection. 
            We only access your activity data to power your shape challenges.
          </p>
        </div>
      </div>
    </div>
  );
}
