'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { UserIcon, UserGroupIcon, TrophyIcon, StarIcon, ChevronDownIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline';
import { UserIcon as UserIconSolid, UserGroupIcon as UserGroupIconSolid, TrophyIcon as TrophyIconSolid, StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { useAuth } from '../contexts/AuthContext';

const Navigation = () => {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);

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

  // Don't show navigation on auth pages
  if (pathname?.startsWith('/auth')) {
    return null;
  }

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

          {isAuthenticated && user ? (
            <div className="flex items-center space-x-6">
              {navItems.map((item) => {
                const isActive = pathname?.startsWith(item.href);
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
              
              {/* User Profile Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowDropdown(!showDropdown)}
                  className="flex items-center space-x-3 hover:opacity-80 transition-opacity"
                >
                  <img
                    className="h-8 w-8 rounded-full"
                    src={user.profile || '/default-avatar.svg'}
                    alt="User profile"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = '/default-avatar.svg';
                    }}
                  />
                  <span className="text-sm font-medium text-gray-700">
                    {user.firstname} {user.lastname}
                  </span>
                  <ChevronDownIcon className="w-4 h-4 text-gray-400" />
                </button>

                {showDropdown && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                    <Link
                      href="/profile"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setShowDropdown(false)}
                    >
                      <div className="flex items-center space-x-2">
                        <UserIcon className="w-4 h-4" />
                        <span>Profile</span>
                      </div>
                    </Link>
                    <button
                      onClick={() => {
                        logout();
                        setShowDropdown(false);
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <div className="flex items-center space-x-2">
                        <ArrowRightOnRectangleIcon className="w-4 h-4" />
                        <span>Sign Out</span>
                      </div>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center">
              <Link
                href="/auth"
                className="bg-[var(--primary-orange)] hover:bg-[var(--orange-dark)] text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Connect with Strava
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Click outside to close dropdown */}
      {showDropdown && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowDropdown(false)}
        />
      )}
    </nav>
  );
};

export default Navigation;
