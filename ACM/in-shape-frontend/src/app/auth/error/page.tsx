'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

const errorMessages: { [key: string]: string } = {
  'access_denied': 'You denied access to your Strava account. We need access to sync your activities.',
  'no_code': 'No authorization code received from Strava. Please try again.',
  'token_exchange_failed': 'Failed to exchange authorization code for access token.',
  'server_error': 'A server error occurred during authentication. Please try again.',
  'no_token': 'No authentication token received. Please try again.',
  'token_verification_failed': 'Token verification failed. Please try again.',
  'default': 'An unexpected error occurred during authentication. Please try again.'
};

export default function AuthErrorPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [errorType, setErrorType] = useState<string>('default');

  useEffect(() => {
    const error = searchParams?.get('error') || 'default';
    setErrorType(error);
  }, [searchParams]);

  const handleTryAgain = () => {
    router.push('/auth');
  };

  const handleGoHome = () => {
    router.push('/');
  };

  const errorMessage = errorMessages[errorType] || errorMessages.default;

  return (
    <div className="min-h-screen bg-[#0f0f0f] flex items-center justify-center">
      <div className="max-w-md w-full px-6 text-center">
        <div className="space-y-6">
          {/* Error Icon */}
          <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center mx-auto">
            <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>

          {/* Error Title */}
          <div>
            <h1 
              className="text-2xl font-bold text-white mb-4" 
              style={{ fontFamily: 'Alliance No.2, sans-serif' }}
            >
              Authentication Failed
            </h1>
            <p className="text-gray-400 mb-6">
              {errorMessage}
            </p>
          </div>

          {/* Error Details (for debugging) */}
          {process.env.NODE_ENV === 'development' && (
            <div className="bg-[#1a1a1a] border border-[#2a2a2a] p-4 rounded-lg">
              <p className="text-gray-500 text-sm">
                <strong>Error Code:</strong> {errorType}
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={handleTryAgain}
              className="w-full bg-[var(--primary-orange)] hover:bg-[var(--orange-dark)] text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
              style={{ fontFamily: 'Alliance No.2, sans-serif' }}
            >
              Try Again
            </button>
            
            <button
              onClick={handleGoHome}
              className="w-full border border-gray-600 text-gray-300 hover:bg-gray-800 font-bold py-3 px-6 rounded-lg transition-colors duration-200"
              style={{ fontFamily: 'Alliance No.2, sans-serif' }}
            >
              Go to Homepage
            </button>
          </div>

          {/* Help Text */}
          <div className="text-gray-500 text-sm">
            <p>Still having trouble? Make sure you:</p>
            <ul className="mt-2 space-y-1">
              <li>• Allow access when prompted by Strava</li>
              <li>• Have a stable internet connection</li>
              <li>• Are using a supported browser</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
