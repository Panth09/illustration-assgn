import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://illustration-assgn-1.onrender.com';

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

export interface DetectionResult {
  success: boolean;
  file_id: string;
  file_path: string;
  detection_results: {
    detected: boolean;
    faces: Array<{
      bbox: number[];
      embedding: number[];
      gender: string;
      age: number;
    }>;
    image_shape: number[];
  };
}

export interface PersonalizationResult {
  success: boolean;
  output_file_id: string;
  output_path: string;
  message: string;
}

export const detectFace = async (file: File): Promise<DetectionResult> => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await apiClient.post<DetectionResult>('/detect-face', formData);
    return response.data;
  } catch (error) {
    console.error('Face detection error:', error);
    throw error;
  }
};

export const personalizeIllustration = async (
  childPhoto: File,
  illustrationTemplate: File
): Promise<PersonalizationResult> => {
  const formData = new FormData();
  formData.append('child_photo', childPhoto);
  formData.append('illustration', illustrationTemplate);

  try {
    const response = await apiClient.post<PersonalizationResult>('/personalize', formData);
    return response.data;
  } catch (error) {
    console.error('Personalization error:', error);
    throw error;
  }
};

export const downloadResult = (fileId: string): string => {
  return `${API_URL}/download/${fileId}`;
};

export const uploadTemplate = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await apiClient.post('/upload-illustration-template', formData);
    return response.data;
  } catch (error) {
    console.error('Template upload error:', error);
    throw error;
  }
};

export const healthCheck = async (): Promise<boolean> => {
  try {
    await apiClient.get('/health');
    return true;
  } catch {
    return false;
  }
};
