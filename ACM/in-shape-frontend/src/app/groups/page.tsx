import Link from 'next/link';
import { UserGroupIcon, UsersIcon, CalendarIcon, TrophyIcon, PlusIcon } from '@heroicons/react/24/outline';

// Mock data - replace with actual API calls later
const mockGroups = [
  {
    id: 1,
    name: "Downtown Runners",
    description: "A community of runners exploring downtown routes and geometric challenges",
    members: 24,
    memberRole: "member",
    joinedDate: "January 2024",
    avatar: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=200&q=80",
    recentActivity: "3 members completed Rectangle challenge",
    weeklyChallenge: "Perfect Square",
  },
  {
    id: 2,
    name: "Shape Masters",
    description: "Elite group focused on achieving perfect geometric running patterns",
    members: 156,
    memberRole: "admin",
    joinedDate: "February 2024",
    avatar: "https://images.unsplash.com/photo-1594736797933-d0c7ad21d5ad?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=200&q=80",
    recentActivity: "New weekly leaderboard posted",
    weeklyChallenge: "Star Pattern",
  },
  {
    id: 3,
    name: "Weekend Warriors",
    description: "Casual group for weekend running adventures and fun shape challenges",
    members: 89,
    memberRole: "member",
    joinedDate: "March 2024",
    avatar: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=200&q=80",
    recentActivity: "Saturday group run scheduled",
    weeklyChallenge: "Heart Shape",
  },
];

const discoveredGroups = [
  {
    id: 4,
    name: "City Runners Club",
    description: "Large community of urban runners with daily challenges",
    members: 324,
    avatar: "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=200&q=80",
    weeklyChallenge: "Triangle Sprint",
  },
  {
    id: 5,
    name: "Marathon Shapers",
    description: "For runners who want to combine long distance with geometric precision",
    members: 67,
    avatar: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=200&q=80",
    weeklyChallenge: "Diamond Route",
  },
];

export default function GroupsPage() {
  return (
    <div className="min-h-screen bg-[#0f0f0f] py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>Your Groups</h1>
          <p className="mt-2 text-gray-400">
            Manage your running groups and discover new communities
          </p>
        </div>

        {/* Your Groups */}
        <div className="mb-12">
          <h2 className="text-xl font-semibold text-white mb-6" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>Your Groups</h2>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {mockGroups.map((group) => (
              <div key={group.id} className="bg-[#1a1a1a] rounded-xl border border-[#2a2a2a] overflow-hidden hover:bg-[#222] transition-colors">
                <div className="p-6">
                  <div className="flex items-center space-x-4 mb-4">
                    <img
                      className="w-12 h-12 rounded-lg object-cover"
                      src={group.avatar}
                      alt={group.name}
                    />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-white truncate">{group.name}</h3>
                      <div className="flex items-center text-sm text-gray-400">
                        <UsersIcon className="w-4 h-4 mr-1" />
                        {group.members} members
                        {group.memberRole === 'admin' && (
                          <span className="ml-2 px-2 py-1 bg-orange-100 text-[var(--primary-orange)] text-xs rounded-full">
                            Admin
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                    {group.description}
                  </p>

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center text-sm text-gray-400">
                      <CalendarIcon className="w-4 h-4 mr-2" />
                      Joined {group.joinedDate}
                    </div>
                    <div className="flex items-center text-sm text-gray-400">
                      <TrophyIcon className="w-4 h-4 mr-2" />
                      Weekly: {group.weeklyChallenge}
                    </div>
                  </div>

                  <div className="text-sm text-gray-400 mb-4 p-3 bg-[#222] rounded-lg">
                    {group.recentActivity}
                  </div>

                  <Link href={`/leaderboard/${group.id}`}>
                    <button className="w-full bg-[var(--primary-orange)] text-white py-2 px-4 rounded-lg hover:bg-[var(--orange-dark)] transition-colors">
                      View Leaderboard
                    </button>
                  </Link>
                </div>
              </div>
            ))}

            {/* Create New Group Card */}
            <div className="bg-[#1a1a1a] rounded-xl border border-dashed border-[#2a2a2a] overflow-hidden hover:border-[var(--primary-orange)] transition-colors">
              <div className="p-6 text-center">
                <div className="w-12 h-12 mx-auto mb-4 bg-orange-100 rounded-lg flex items-center justify-center">
                  <PlusIcon className="w-6 h-6 text-[var(--primary-orange)]" />
                </div>
                <h3 className="font-semibold text-white mb-2">Create New Group</h3>
                <p className="text-gray-400 text-sm mb-4">
                  Start your own running group and invite friends
                </p>
                <button className="bg-[var(--primary-orange)] text-white py-2 px-4 rounded-lg hover:bg-[var(--orange-dark)] transition-colors">
                  Create Group
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Discover Groups */}
        <div>
          <h2 className="text-xl font-semibold text-white mb-6" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>Discover Groups</h2>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {discoveredGroups.map((group) => (
              <div key={group.id} className="bg-[#1a1a1a] rounded-xl border border-[#2a2a2a] overflow-hidden hover:bg-[#222] transition-colors">
                <div className="p-6">
                  <div className="flex items-center space-x-4 mb-4">
                    <img
                      className="w-12 h-12 rounded-lg object-cover"
                      src={group.avatar}
                      alt={group.name}
                    />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-white truncate">{group.name}</h3>
                      <div className="flex items-center text-sm text-gray-400">
                        <UsersIcon className="w-4 h-4 mr-1" />
                        {group.members} members
                      </div>
                    </div>
                  </div>

                  <p className="text-gray-400 text-sm mb-4">
                    {group.description}
                  </p>

                  <div className="flex items-center text-sm text-gray-400 mb-4">
                    <TrophyIcon className="w-4 h-4 mr-2" />
                    Weekly: {group.weeklyChallenge}
                  </div>

                  <button className="w-full border border-[var(--primary-orange)] text-[var(--primary-orange)] py-2 px-4 rounded-lg hover:bg-[var(--primary-orange)] hover:text-white transition-colors">
                    Join Group
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
