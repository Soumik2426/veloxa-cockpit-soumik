
import { useCallback, useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Send,
  RefreshCw,
  MessageSquare,
  AlertCircle,
  UserRound,
  Bot,
  FileText,
} from 'lucide-react';

import { agentApi } from '../api/agentApi';
import type { AgentMessage, ConversationDetails } from '../types/message';
import { readableEvidence } from '../utils/evidence';

function getMessageRole(message: AgentMessage): string {
  return (message.role || message.senderType || '').toLowerCase();
}

function isUserMessage(message: AgentMessage): boolean {
  const role = getMessageRole(message);
  return role === 'user' || role === 'human';
}

function getMessageDate(value?: string): string {
  if (!value) return '';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';

  return date.toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

function getCitations(message: AgentMessage): unknown[] {
  if (Array.isArray(message.citations)) {
    return message.citations;
  }

  const metadata = message.metadata;

  if (metadata && Array.isArray(metadata.citations)) {
    return metadata.citations;
  }

  if (metadata && Array.isArray(metadata.evidence)) {
    return metadata.evidence;
  }

  return [];
}

export default function AgentChat() {
  const { conversationId } = useParams<{ conversationId: string }>();

  const [conversation, setConversation] =
    useState<ConversationDetails | null>(null);

  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const bottomRef = useRef<HTMLDivElement>(null);

  const loadConversation = useCallback(async () => {
    if (!conversationId) {
      setError('Conversation ID is missing.');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError('');

      const [details, history] = await Promise.all([
        agentApi.getConversation(conversationId),
        agentApi.getMessages(conversationId),
      ]);

      console.log('[AgentChat] Conversation:', details);
      console.log('[AgentChat] Message history:', history);

      setConversation(details);
      setMessages(history);
    } catch (err) {
      console.error('[AgentChat] Failed to load conversation:', err);
      setError('Unable to load this conversation. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  useEffect(() => {
    void loadConversation();
  }, [loadConversation]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  async function handleSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const content = input.trim();

    if (!content || !conversationId || sending) return;

    try {
      setSending(true);
      setError('');
      setInput('');

      const request = { content };

      const response = await agentApi.sendMessage(
        conversationId,
        request
      );

      console.log('[AgentChat] Send response:', response);

      // Reload persisted messages to preserve the backend's
      // authoritative message order and response structure.
      const updatedMessages = await agentApi.getMessages(conversationId);
      setMessages(updatedMessages);
    } catch (err) {
      console.error('[AgentChat] Message sending failed:', err);

      setError(
        'Your message could not be sent. Please check the connection and retry.'
      );

      setInput(content);
    } finally {
      setSending(false);
    }
  }

  if (loading) {
    return (
      <div className="page-content loading-state">
        <RefreshCw size={22} className="animate-spin" />
        <p>Loading conversation...</p>
      </div>
    );
  }

  if (error && !conversation) {
    return (
      <div className="page-content">
        <div className="error-banner">
          <AlertCircle size={19} />
          {error}
          <button type="button" onClick={() => void loadConversation()}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  const conversationsUrl = conversation?.employeeCode
    ? `/agents/${conversation.employeeCode}/conversations`
    : '/agents';

  return (
    <div className="chat-page">
      <div className="chat-header">
        <div>
          <Link to={conversationsUrl} className="back-link">
            <ArrowLeft size={15} />
            Back to conversations
          </Link>

          <h1>{conversation?.title || 'Agent conversation'}</h1>

          <p>
            Employee agent conversation
            {conversation?.status ? ` · ${conversation.status}` : ''}
          </p>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={() => void loadConversation()}
          disabled={loading || sending}
        >
          <RefreshCw size={15} />
          Refresh
        </button>
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">
              <MessageSquare size={26} />
            </div>

            <h3>Start the conversation</h3>

            <p>
              Ask a question about the employee's work, responsibilities,
              commitments or company knowledge.
            </p>
          </div>
        ) : (
          messages.map((message, index) => {
            const userMessage = isUserMessage(message);
            const citations = readableEvidence(getCitations(message));

            return (
              <div
                key={message.id || message.messageId || index}
                className={`message-row ${
                  userMessage ? 'message-user' : 'message-assistant'
                }`}
              >
                <div className="message-avatar">
                  {userMessage ? (
                    <UserRound size={17} />
                  ) : (
                    <Bot size={18} />
                  )}
                </div>

                <div className="message-content">
                  <div className="message-meta">
                    <strong>{userMessage ? 'You' : 'Employee Agent'}</strong>
                    <span>{getMessageDate(message.createdAt)}</span>
                  </div>

                  <div className="message-bubble">
                    {message.content}
                  </div>

                  {citations.length > 0 && (
                    <div className="message-citations">
                      <div className="citation-heading">
                        <FileText size={14} />
                        Evidence and citations
                      </div>

                      {citations.map((citation, citationIndex) => (
                        <div
                          className="citation-item"
                          key={citationIndex}
                        >
                          <strong>{citation.fileName}</strong>
                          {citation.location && <span>{citation.location}</span>}
                          {citation.supports && (
                            <small>Supports: {citation.supports}</small>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}

        {sending && (
          <div className="message-row message-assistant">
            <div className="message-avatar">
              <Bot size={18} />
            </div>

            <div className="message-content">
              <div className="message-meta">
                <strong>Employee Agent</strong>
              </div>

              <div className="message-bubble typing-indicator">
                Thinking and retrieving company knowledge...
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="error-banner chat-error">
          <AlertCircle size={17} />
          {error}
        </div>
      )}

      <div className="chat-composer">
        <form onSubmit={handleSend}>
          <div className="chat-input-wrapper">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask this employee agent a question..."
              rows={2}
              maxLength={2000}
              disabled={sending}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
            />

            <button
              type="submit"
              className="send-button"
              disabled={!input.trim() || sending}
              aria-label="Send message"
            >
              <Send size={18} />
            </button>
          </div>

          <div className="chat-composer-footer">
            <span>{input.length}/2000 characters</span>
          </div>
        </form>
      </div>
    </div>
  );
}
