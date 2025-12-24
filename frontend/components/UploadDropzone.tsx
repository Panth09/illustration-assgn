'use client';

import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface UploadDropzoneProps {
  onFile: (file: File) => void;
  accept?: Record<string, string[]>;
  label: string;
  maxSize?: number;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({
  onFile,
  accept = { 'image/*': ['.jpeg', '.jpg', '.png'] },
  label,
  maxSize = 50 * 1024 * 1024,
}) => {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFile(acceptedFiles[0]);
      }
    },
    [onFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple: false,
  });

  return (
    <div
      {...getRootProps()}
      className={`upload-zone ${isDragActive ? 'dragover' : ''}`}
    >
      <input {...getInputProps()} />
      {isDragActive ? (
        <p className="text-purple-600 font-semibold">Drop the file here...</p>
      ) : (
        <div>
          <p className="text-gray-700 font-semibold mb-2">{label}</p>
          <p className="text-gray-500 text-sm">
            Drag and drop an image, or click to select
          </p>
        </div>
      )}
    </div>
  );
};
