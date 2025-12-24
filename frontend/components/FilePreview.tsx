'use client';

import React from 'react';

interface FilePreviewProps {
  file: File;
  onRemove: () => void;
}

export const FilePreview: React.FC<FilePreviewProps> = ({ file, onRemove }) => {
  const preview = URL.createObjectURL(file);

  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      <div className="flex gap-4">
        <img
          src={preview}
          alt="Preview"
          className="w-32 h-32 object-cover rounded"
        />
        <div className="flex flex-col justify-between flex-1">
          <div>
            <p className="font-semibold text-gray-800">{file.name}</p>
            <p className="text-sm text-gray-600">
              {(file.size / 1024).toFixed(2)} KB
            </p>
          </div>
          <button
            onClick={onRemove}
            className="text-red-600 hover:text-red-800 font-semibold text-sm"
          >
            Remove
          </button>
        </div>
      </div>
    </div>
  );
};
