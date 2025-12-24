'use client';

import React from 'react';

interface LoadingProps {
  message?: string;
}

export const Loading: React.FC<LoadingProps> = ({
  message = 'Processing your personalization...',
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="spinner mb-4">
        <svg
          className="w-12 h-12 text-purple-600"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
      </div>
      <p className="text-gray-700 font-semibold">{message}</p>
      <p className="text-gray-500 text-sm mt-2">
        This may take a minute or two...
      </p>
    </div>
  );
};
