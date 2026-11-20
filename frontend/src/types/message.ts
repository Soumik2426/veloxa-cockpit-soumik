
export interface AgentMessage {
  id: string;
  messageId?: string;
  role?: string;
  senderType?: string;
  content: string;
  citations?: unknown[];
  metadata?: Record<string, unknown>;
  createdAt?: string;
  confidence?: string;
}

export interface SendMessageRequest {
  content: string;
  asOfDate?: string;
}

export interface ConversationDetails {
  id: string;
  conversationId?: string;
  title?: string;
  status?: string;
  employeeCode?: string;
}
