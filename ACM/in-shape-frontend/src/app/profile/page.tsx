import Link from 'next/link';
import { TrophyIcon, CalendarIcon, ClockIcon, MapPinIcon } from '@heroicons/react/24/outline';

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
  return (
    <div className="min-h-screen bg-[#0f0f0f] py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Profile Header */}
        <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-8 mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div className="flex items-center space-x-6">
              <img
                className="h-24 w-24 rounded-full object-cover"
                src={mockUser.profilePicture}
                alt={mockUser.name}
              />
              <div>
                <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>{mockUser.name}</h1>
                <p className="text-gray-400 flex items-center mt-1">
                  <CalendarIcon className="w-4 h-4 mr-1" />
                  Member since {mockUser.memberSince}
                </p>
              </div>
            </div>
            
            <div className="mt-6 md:mt-0 flex flex-col md:flex-row md:space-x-8">
              <div className="text-center md:text-right">
                <div className="text-3xl font-bold text-[var(--primary-orange)]">
                  {mockUser.lifetimePoints.toLocaleString()}
                </div>
                <div className="text-sm text-gray-400">Lifetime Points</div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Stats Cards */}
          <div className="lg:col-span-2 space-y-6">
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-6">
                <div className="flex items-center">
                  <MapPinIcon className="w-8 h-8 text-[var(--primary-orange)]" />
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-white">{mockUser.totalRuns}</div>
                    <div className="text-sm text-gray-400">Total Runs</div>
                  </div>
                </div>
              </div>
              
              <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-6">
                <div className="flex items-center">
                  <TrophyIcon className="w-8 h-8 text-yellow-500" />
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-white">{mockUser.bestScore}%</div>
                    <div className="text-sm text-gray-400">Best Score</div>
                  </div>
                </div>
              </div>
              
              <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-6">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-[var(--primary-orange)] rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-xs">⬜</span>
                  </div>
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-white">{mockUser.bestShape}</div>
                    <div className="text-sm text-gray-400">Best Shape</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Runs */}
            <div className="bg-[#1a1a1a] border border-[#2a2a2a]">
              <div className="p-6 border-b border-[#2a2a2a]">
                <h2 className="text-xl font-semibold text-white" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>Recent Runs</h2>
              </div>
              <div className="divide-y divide-[#2a2a2a]">
                {mockUser.recentRuns.map((run) => (
                  <div key={run.id} className="p-6 hover:bg-[#222]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                          <span className="text-[var(--primary-orange)] font-bold">
                            {run.shape[0]}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium text-white">{run.shape}</div>
                          <div className="text-sm text-gray-400">{run.date}</div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-6 text-sm">
                        <div className="text-center">
                          <div className="font-medium text-white">{run.score}%</div>
                          <div className="text-gray-400">Score</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium text-white">{run.distance}</div>
                          <div className="text-gray-400">Distance</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium text-white">{run.time}</div>
                          <div className="text-gray-400">Time</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
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
  );
}
