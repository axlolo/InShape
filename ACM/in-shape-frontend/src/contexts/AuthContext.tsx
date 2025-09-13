'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  firstname: string;
  lastname: string;
  profile: string;
  city?: string;
  country?: string;
  created_at?: string;
  sex?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => void;
  logout: () => void;
  verifyAuth: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  const verifyAuth = async (): Promise<boolean> => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      setIsLoading(false);
      return false;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUser({
          id: data.user_id,
          firstname: data.athlete.firstname,
          lastname: data.athlete.lastname,
          profile: data.athlete.profile,
          city: data.athlete.city,
          country: data.athlete.country,
          created_at: data.athlete.created_at,
          sex: data.athlete.sex,
        });
        setIsLoading(false);
        return true;
      } else {
        // Token invalid or expired
        localStorage.removeItem('authToken');
        setUser(null);
        setIsLoading(false);
        return false;
      }
    } catch (error) {
      console.error('Auth verification failed:', error);
      // Don't remove token on network errors, only on auth errors
      setUser(null);
      setIsLoading(false);
      return false;
    }
  };

  const login = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/strava`);
      const data = await response.json();
      
      if (data.auth_url) {
        // Store state for verification
        localStorage.setItem('oauthState', data.state);
        // Redirect to Strava OAuth
        window.location.href = data.auth_url;
      }
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const logout = async () => {
    const token = localStorage.getItem('authToken');
    
    if (token) {
      try {
        await fetch(`${API_BASE_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      } catch (error) {
        console.error('Logout request failed:', error);
      }
    }
    
    localStorage.removeItem('authToken');
    localStorage.removeItem('oauthState');
    setUser(null);
  };

  useEffect(() => {
    verifyAuth();
  }, []);

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated,
      isLoading,
      login,
      logout,
      verifyAuth,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
