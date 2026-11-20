export interface AgentConversation {
  id: string;
  conversationId?: string;
  employeeCode: string;
  employeeName?: string;
  agentKey?: string;
  title: string;
  status: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface CreateConversationRequest {
  title: string;
}