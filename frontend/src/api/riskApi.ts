import apiClient from './client';

export type RiskAssessmentStatus =
  | 'NOT_STARTED'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED';

export interface RiskAssessmentSnapshot {
  id: string | null;
  assessmentDate: string | null;
  generatedAt: string | null;
  updatedAt: string | null;
  status: RiskAssessmentStatus;
  assessment: Record<string, unknown> | null;
  dataVersion: string | null;
  errorMessage: string | null;
}

export const riskApi = {
  async latest(): Promise<RiskAssessmentSnapshot> {
    const response = await apiClient.get<RiskAssessmentSnapshot>(
      '/api/v1/risk-assessments/latest'
    );
    return response.data;
  },

  async refresh(): Promise<RiskAssessmentSnapshot> {
    const response = await apiClient.post<RiskAssessmentSnapshot>(
      '/api/v1/risk-assessments/refresh'
    );
    return response.data;
  },
};
