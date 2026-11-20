import apiClient from './client';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export interface DataFile {
  id: string;
  fileName: string;
  relativePath: string;
  extension: string;
  fileType: string;
  category: string;
  status: string;
  fileSize: number;
  discoveredAt?: string;
  processedAt?: string;
}

export interface VoiceNote {
  id: string;
  noteId: string;
  sourceFile: string;
  relativePath: string;
  discoveredAt?: string;
  transcript: string;
  outcome: {
    kind: 'implemented' | 'pushback' | 'pending';
    label: string;
    summary: string;
    decision: string;
  };
}

export const dataApi = {
  async listFiles(): Promise<DataFile[]> {
    const response = await apiClient.get<DataFile[]>('/api/v1/data-files');
    return response.data;
  },

  contentUrl(fileId: string): string {
    return `${API_BASE_URL}/api/v1/data-files/${encodeURIComponent(fileId)}/content`;
  },

  async listVoiceNotes(): Promise<VoiceNote[]> {
    const response = await apiClient.get<VoiceNote[]>('/api/v1/voice-notes');
    return response.data;
  },
};
