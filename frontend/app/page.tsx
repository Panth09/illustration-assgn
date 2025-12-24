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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex flex-col">
        <div className="container flex-grow">
          <div className="card max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold mb-2 text-transparent bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text">
                ✓ Personalization Complete!
              </h1>
              <p className="text-gray-600">Your personalized illustration is ready to download</p>
            </div>

            <div className="mb-8 rounded-2xl overflow-hidden shadow-2xl hover:shadow-3xl transition">
              <img
                src={downloadResult(result)}
                alt="Personalized illustration"
                className="w-full"
              />
            </div>

            <div className="flex gap-4 flex-col sm:flex-row">
              <a
                href={downloadResult(result)}
                download
                className="button-primary text-center flex-1 flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download Image
              </a>
              <button onClick={handleReset} className="button-secondary flex-1">
                ✨ Create Another
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 py-8 border-t border-gray-200 bg-white/50 backdrop-blur">
          <div className="max-w-6xl mx-auto px-4 text-center">
            <p className="text-gray-600 mb-2">
              Built with ❤️ by <span className="font-semibold text-gray-800">Panth Maheshwari</span>
            </p>
            <a
              href="https://www.linkedin.com/in/panthmaheshwari"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium transition"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z" />
              </svg>
              Connect on LinkedIn
            </a>
            <p className="text-sm text-gray-500 mt-4">
              Powered by FastAPI, Next.js, InsightFace & OpenCV
            </p>
          </div>
        </footer>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex flex-col">
      <div className="container flex-grow">
        <div className="card max-w-3xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-3">
              ✨ Illustration Personalizer
            </h1>
            <p className="text-lg text-gray-600">
              Transform your child&apos;s photo into personalized art with AI magic
            </p>
          </div>

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
                      label="Upload Child&apos;s Photo"
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

              <div className="mt-10 pt-10 border-t border-gray-200">
                <h3 className="text-xl font-bold mb-4 text-gray-800">🎨 How It Works:</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="font-semibold text-blue-900 mb-1">📸 Step 1-2</p>
                    <p className="text-sm text-gray-600">Upload your child&apos;s photo and an illustration template</p>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <p className="font-semibold text-purple-900 mb-1">🤖 Step 3-4</p>
                    <p className="text-sm text-gray-600">Our AI detects faces, applies stylization, and blends them seamlessly</p>
                  </div>
                  <div className="bg-pink-50 p-4 rounded-lg">
                    <p className="font-semibold text-pink-900 mb-1">⚡ Step 5</p>
                    <p className="text-sm text-gray-600">Download your unique personalized illustration instantly</p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <p className="font-semibold text-green-900 mb-1">✨ Features</p>
                    <p className="text-sm text-gray-600">Fast processing, high quality, fully automated</p>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-12 py-8 border-t border-gray-200 bg-white/50 backdrop-blur">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p className="text-gray-600 mb-2">
            Built with ❤️ by <span className="font-semibold text-gray-800">Panth Maheshwari</span>
          </p>
          <a
            href="https://www.linkedin.com/in/panthmaheshwari"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium transition"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z" />
            </svg>
            Connect on LinkedIn
          </a>
          <p className="text-sm text-gray-500 mt-4">
            Powered by FastAPI, Next.js, InsightFace & OpenCV
          </p>
        </div>
      </footer>
    </div>
  );
}
