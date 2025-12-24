'use client';

import React, { useState, useEffect } from 'react';
import { UploadDropzone } from '@/components/UploadDropzone';
import { FilePreview } from '@/components/FilePreview';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { useUploadStore } from '@/lib/store';
import { personalizeIllustration, downloadResult, healthCheck } from '@/lib/api';

export default function Home() {
  const {
    childPhoto,
    illustrationTemplate,
    isProcessing,
    result,
    error,
    setChildPhoto,
    setIllustrationTemplate,
    setIsProcessing,
    setResult,
    setError,
    reset,
  } = useUploadStore();

  const [apiHealthy, setApiHealthy] = useState(false);

  useEffect(() => {
    const checkHealth = async () => {
      const healthy = await healthCheck();
      setApiHealthy(healthy);
      if (!healthy) {
        setError('Backend API is not available. Please ensure the server is running.');
      }
    };

    checkHealth();
  }, [setError]);

  const handlePersonalize = async () => {
    if (!childPhoto || !illustrationTemplate) {
      setError('Please upload both a child photo and an illustration template');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const response = await personalizeIllustration(childPhoto, illustrationTemplate);

      if (response.success) {
        setResult(response.output_file_id);
      } else {
        setError('Personalization failed. Please try again.');
      }
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'An error occurred during personalization';
      setError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    reset();
    setResult(null);
  };

  if (!apiHealthy && error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center p-4">
        <div className="card max-w-md">
          <h1 className="text-2xl font-bold text-gray-800 mb-4">Connection Error</h1>
          <p className="text-gray-600 mb-4">
            The backend API is not available. Please ensure the FastAPI server is running at{' '}
            <code className="bg-gray-100 px-2 py-1 rounded">http://localhost:8000</code>
          </p>
          <p className="text-gray-600">
            To start the backend, run:
            <code className="block bg-gray-100 p-2 rounded mt-2">python main.py</code>
          </p>
        </div>
      </div>
    );
  }

  if (result) {
    return (
      <div className="container">
        <div className="card max-w-2xl mx-auto">
          <h1 className="text-3xl font-bold text-center text-gray-800 mb-6">
            ✓ Personalization Complete!
          </h1>

          <div className="mb-6">
            <img
              src={downloadResult(result)}
              alt="Personalized illustration"
              className="w-full rounded-lg shadow-lg"
            />
          </div>

          <div className="flex gap-4">
            <a
              href={downloadResult(result)}
              download
              className="button-primary flex-1 text-center"
            >
              Download Image
            </a>
            <button onClick={handleReset} className="button-secondary flex-1">
              Create Another
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="card max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-2 text-gray-800">
          Illustration Personalizer
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Upload your child's photo and an illustration template to create a personalized version
        </p>

        {error && (
          <ErrorMessage
            error={error}
            onDismiss={() => setError(null)}
          />
        )}

        {isProcessing ? (
          <Loading />
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              {/* Child Photo Upload */}
              <div>
                <h2 className="text-lg font-semibold mb-4 text-gray-800">Step 1: Child Photo</h2>
                {childPhoto ? (
                  <FilePreview
                    file={childPhoto}
                    onRemove={() => setChildPhoto(null as any)}
                  />
                ) : (
                  <UploadDropzone
                    label="Upload Child's Photo"
                    onFile={setChildPhoto}
                  />
                )}
              </div>

              {/* Illustration Template Upload */}
              <div>
                <h2 className="text-lg font-semibold mb-4 text-gray-800">Step 2: Illustration</h2>
                {illustrationTemplate ? (
                  <FilePreview
                    file={illustrationTemplate}
                    onRemove={() => setIllustrationTemplate(null as any)}
                  />
                ) : (
                  <UploadDropzone
                    label="Upload Illustration Template"
                    onFile={setIllustrationTemplate}
                  />
                )}
              </div>
            </div>

            <button
              onClick={handlePersonalize}
              disabled={!childPhoto || !illustrationTemplate}
              className={`w-full ${
                childPhoto && illustrationTemplate
                  ? 'button-primary'
                  : 'px-6 py-3 bg-gray-300 text-gray-600 rounded-lg font-semibold cursor-not-allowed'
              }`}
            >
              Personalize Illustration
            </button>

            <div className="mt-8 pt-8 border-t">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">How it works:</h3>
              <ol className="list-decimal list-inside space-y-2 text-gray-600">
                <li>Upload a clear photo of your child's face</li>
                <li>Upload an illustration or template image</li>
                <li>Our AI will detect the child's face and stylize it</li>
                <li>The stylized face will be inserted into the illustration</li>
                <li>Download your personalized illustration</li>
              </ol>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
