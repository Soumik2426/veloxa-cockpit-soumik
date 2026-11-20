
import apiClient from './client';
import type { EmployeeAgent } from '../types/agent';

export const agentApi = {
  async getAllAgents(): Promise<EmployeeAgent[]> {
    const response = await apiClient.get<EmployeeAgent[]>(
      '/api/v1/employee-agents'
    );

    return response.data;
  },

  async getAgentByCode(employeeCode: string): Promise<EmployeeAgent> {
    const response = await apiClient.get<EmployeeAgent>(
      `/api/v1/employee-agents/${encodeURIComponent(employeeCode)}`
    );

    return response.data;
  },
};
