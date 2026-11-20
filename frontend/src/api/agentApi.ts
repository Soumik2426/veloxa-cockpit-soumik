import apiClient from './client';
import type { EmployeeAgent } from '../types/agent';
import type {
  AgentConversation,
  CreateConversationRequest,
} from '../types/conversation';
import type {
  AgentMessage,
  ConversationDetails,
  SendMessageRequest,
} from '../types/message';

function extractList<T>(payload: unknown): T[] {
  if (Array.isArray(payload)) {
    return payload as T[];
  }

  if (!payload || typeof payload !== 'object') {
    return [];
  }

  const response = payload as Record<string, unknown>;

  for (const key of ['data', 'content', 'conversations', 'messages', 'result']) {
    const value = response[key];

    if (Array.isArray(value)) {
      return value as T[];
    }

    if (value && typeof value === 'object') {
      const nested = value as Record<string, unknown>;

      for (const nestedKey of [
        'data',
        'content',
        'conversations',
        'messages',
      ]) {
        if (Array.isArray(nested[nestedKey])) {
          return nested[nestedKey] as T[];
        }
      }
    }
  }

  return [];
}

function unwrapObject<T>(payload: unknown): T {
  if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
    const response = payload as Record<string, unknown>;

    if (response.data && typeof response.data === 'object') {
      return response.data as T;
    }
  }

  return payload as T;
}

export const agentApi = {
  async getAllAgents(): Promise<EmployeeAgent[]> {
    const response = await apiClient.get<EmployeeAgent[]>(
      '/api/v1/employee-agents'
    );
    return response.data;
  },

  async getAgentByCode(employeeCode: string): Promise<EmployeeAgent> {
    const response = await apiClient.get(
      `/api/v1/employee-agents/${encodeURIComponent(employeeCode)}`
    );
    return unwrapObject<EmployeeAgent>(response.data);
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
    return unwrapObject<AgentConversation>(response.data);
  },

  async getConversation(
    conversationId: string
  ): Promise<ConversationDetails> {
    const response = await apiClient.get(
      `/api/v1/conversations/${encodeURIComponent(conversationId)}`
    );
    return unwrapObject<ConversationDetails>(response.data);
  },

  async getMessages(conversationId: string): Promise<AgentMessage[]> {
    const response = await apiClient.get(
      `/api/v1/conversations/${encodeURIComponent(conversationId)}/messages`
    );
    return extractList<AgentMessage>(response.data);
  },

  async sendMessage(
    conversationId: string,
    request: SendMessageRequest
  ): Promise<AgentMessage> {
    const response = await apiClient.post(
      `/api/v1/conversations/${encodeURIComponent(conversationId)}/messages`,
      request
    );
    return unwrapObject<AgentMessage>(response.data);
  },

    async askCompany(question: string): Promise<Record<string, unknown>> {
    const response = await apiClient.post<Record<string, unknown>>(
        '/api/v1/agent/ask',
            { question }
        );

        return unwrapObject<Record<string, unknown>>(response.data);
    },

};
