'use client';

import React from 'react';

interface ErrorMessageProps {
  error: string;
  onDismiss: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ error, onDismiss }) => {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-red-800 font-semibold">Error</h3>
          <p className="text-red-700 text-sm mt-1">{error}</p>
        </div>
        <button
          onClick={onDismiss}
          className="text-red-600 hover:text-red-800"
        >
          ✕
        </button>
      </div>
    </div>
  );
};
