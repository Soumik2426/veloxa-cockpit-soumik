import apiClient from './client';
import type { EmployeeAgent } from '../types/agent';
import type {
  AgentConversation,
  CreateConversationRequest,
} from '../types/conversation';

function extractList<T>(payload: unknown): T[] {
  if (Array.isArray(payload)) {
    return payload as T[];
  }

  if (!payload || typeof payload !== 'object') {
    return [];
  }

  const response = payload as Record<string, unknown>;

  for (const key of ['data', 'content', 'conversations', 'result']) {
    const value = response[key];

    if (Array.isArray(value)) {
      return value as T[];
    }

    if (value && typeof value === 'object') {
      const nested = value as Record<string, unknown>;

      for (const nestedKey of ['data', 'content', 'conversations']) {
        if (Array.isArray(nested[nestedKey])) {
          return nested[nestedKey] as T[];
        }
      }
    }
  }

  return [];
}

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

  async getConversations(
    employeeCode: string
  ): Promise<AgentConversation[]> {
    const response = await apiClient.get(
      `/api/v1/employee-agents/${encodeURIComponent(employeeCode)}/conversations`
    );

    return extractList<AgentConversation>(response.data);
  },

  async createConversation(
    employeeCode: string,
    request: CreateConversationRequest
  ): Promise<AgentConversation> {
    const response = await apiClient.post(
      `/api/v1/employee-agents/${encodeURIComponent(employeeCode)}/conversations`,
      request
    );

    const payload = response.data;

    if (payload && typeof payload === 'object') {
      const result = payload as Record<string, unknown>;

      if (result.data && typeof result.data === 'object') {
        return result.data as AgentConversation;
      }
    }

    return payload as AgentConversation;
  },
};
