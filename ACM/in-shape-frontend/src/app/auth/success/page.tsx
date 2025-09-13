'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '../../../contexts/AuthContext';

export default function AuthSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { verifyAuth } = useAuth();
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const handleAuthSuccess = async () => {
      const token = searchParams?.get('token');
      
      if (token) {
        // Store the token
        localStorage.setItem('authToken', token);
        
        // Verify the authentication
        const isValid = await verifyAuth();
        
        if (isValid) {
          // Redirect to home after a brief success display
          setTimeout(() => {
            router.push('/');
          }, 2000);
        } else {
          // Token verification failed
          router.push('/auth/error?error=token_verification_failed');
        }
      } else {
        router.push('/auth/error?error=no_token');
      }
      
      setIsProcessing(false);
    };

    handleAuthSuccess();
  }, [searchParams, router, verifyAuth]);

  return (
    <div className="min-h-screen bg-[#0f0f0f] flex items-center justify-center">
      <div className="max-w-md w-full px-6 text-center">
        {isProcessing ? (
          <div className="space-y-6">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[var(--primary-orange)] mx-auto"></div>
            <div>
              <h1 
                className="text-2xl font-bold text-white mb-2" 
                style={{ fontFamily: 'Alliance No.2, sans-serif' }}
              >
                Connecting to Strava...
              </h1>
              <p className="text-gray-400">
                We're setting up your account, this will just take a moment.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h1 
                className="text-2xl font-bold text-white mb-2" 
                style={{ fontFamily: 'Alliance No.2, sans-serif' }}
              >
                Successfully Connected!
              </h1>
              <p className="text-gray-400">
                Welcome to InShape! You'll be redirected to the dashboard shortly.
              </p>
            </div>
            <div className="text-[var(--primary-orange)] text-sm">
              Redirecting to dashboard...
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
