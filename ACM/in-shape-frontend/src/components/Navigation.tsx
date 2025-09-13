'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { UserIcon, UserGroupIcon, TrophyIcon, StarIcon } from '@heroicons/react/24/outline';
import { UserIcon as UserIconSolid, UserGroupIcon as UserGroupIconSolid, TrophyIcon as TrophyIconSolid, StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

const Navigation = () => {
  const pathname = usePathname();

  const navItems = [
    {
      name: 'Missions',
      href: '/missions',
      icon: StarIcon,
      activeIcon: StarIconSolid,
    },
    {
      name: 'Groups',
      href: '/groups',
      icon: UserGroupIcon,
      activeIcon: UserGroupIconSolid,
    },
  ];

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/">
              <img 
                src="/InShape.png" 
                alt="In Shape Logo" 
                className="h-10 w-auto"
              />
            </Link>
          </div>

          <div className="flex items-center space-x-6">
            {navItems.map((item) => {
              const isActive = pathname.startsWith(item.href);
              const Icon = isActive ? item.activeIcon : item.icon;
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'text-[var(--primary-orange)] bg-orange-50'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
            
            <div className="h-6 w-px bg-gray-300"></div>
            <Link
              href="/profile"
              className="flex items-center space-x-3 hover:opacity-80 transition-opacity"
            >
              <img
                className="h-8 w-8 rounded-full"
                src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
                alt="User profile"
              />
              <span className="text-sm font-medium text-gray-700">John Doe</span>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
