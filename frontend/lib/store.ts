import { create } from 'zustand';

interface UploadState {
  childPhoto: File | null;
  illustrationTemplate: File | null;
  isProcessing: boolean;
  result: string | null;
  error: string | null;
  detectionResults: any;

  setChildPhoto: (file: File) => void;
  setIllustrationTemplate: (file: File) => void;
  setIsProcessing: (value: boolean) => void;
  setResult: (value: string | null) => void;
  setError: (value: string | null) => void;
  setDetectionResults: (value: any) => void;
  reset: () => void;
}

export const useUploadStore = create<UploadState>((set) => ({
  childPhoto: null,
  illustrationTemplate: null,
  isProcessing: false,
  result: null,
  error: null,
  detectionResults: null,

  setChildPhoto: (file) => set({ childPhoto: file }),
  setIllustrationTemplate: (file) => set({ illustrationTemplate: file }),
  setIsProcessing: (value) => set({ isProcessing: value }),
  setResult: (value) => set({ result: value }),
  setError: (value) => set({ error: value }),
  setDetectionResults: (value) => set({ detectionResults: value }),
  reset: () =>
    set({
      childPhoto: null,
      illustrationTemplate: null,
      isProcessing: false,
      result: null,
      error: null,
      detectionResults: null,
    }),
}));
