import Link from "next/link";
import { getTodaysShape } from "../utils/shapes";

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
  return (
    <div className="min-h-screen bg-[#0f0f0f]">
      <div className="max-w-5xl mx-auto px-6 py-16">
        
        {/* Today's Shape Section */}
        <div className="mb-20">
          <h1 className="text-5xl font-bold text-white mb-16 text-center" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
            Today's Shape
          </h1>
          
          <div className="flex flex-col items-center">
            <div className="mb-8">
              <img 
                src={todaysShape.image} 
                alt={todaysShape.name}
                className="w-64 h-64 object-contain filter invert"
              />
            </div>
            <h2 className="text-3xl font-bold text-white mb-4" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
              {todaysShape.name}
            </h2>
            <p className="text-gray-400 text-lg mb-8 text-center max-w-md">
              {todaysShape.description}
            </p>
            <button className="bg-[var(--primary-orange)] text-white px-8 py-3 font-semibold hover:bg-[var(--orange-dark)] transition-colors">
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
            {mockGroups.map((group, index) => (
              <Link key={group.id} href={`/leaderboard/${group.id}`}>
                <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-6 hover:bg-[#222] transition-colors cursor-pointer">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-6">
                      <div className="text-2xl font-bold text-gray-500 w-8">
                        {index + 1}
                      </div>
                      <div>
                        <h3 className="text-xl font-semibold text-white" style={{ fontFamily: 'Alliance No.2, sans-serif' }}>
                          {group.name}
                        </h3>
                        <p className="text-gray-400">
                          {group.members} members
                        </p>
                      </div>
                    </div>
                    
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
  );
}
