
import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  MessageSquare,
  Plus,
  RefreshCw,
  AlertCircle,
  Clock,
  X,
} from 'lucide-react';

import { agentApi } from '../api/agentApi';
import type { AgentConversation } from '../types/conversation';
import type { EmployeeAgent } from '../types/agent';

function getConversationId(conversation: AgentConversation): string {
  return conversation.id || conversation.conversationId || '';
}

function formatDate(value?: string): string {
  if (!value) return 'Date unavailable';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return 'Date unavailable';

  return date.toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

export default function AgentConversations() {
  const { employeeCode } = useParams<{ employeeCode: string }>();
  const navigate = useNavigate();

  const [agent, setAgent] = useState<EmployeeAgent | null>(null);
  const [conversations, setConversations] = useState<AgentConversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [title, setTitle] = useState('');

  const loadConversations = useCallback(async () => {
    if (!employeeCode) return;

    try {
      setLoading(true);
      setError('');

      const [agentResult, conversationResult] = await Promise.all([
        agentApi.getAgentByCode(employeeCode),
        agentApi.getConversations(employeeCode),
      ]);

      console.log('[Conversations] Employee:', agentResult);
      console.log('[Conversations] Conversations:', conversationResult);

      setAgent(agentResult);
      setConversations(conversationResult);
    } catch (err) {
      console.error('[Conversations] Failed to load:', err);
      setError('Unable to load this employee’s conversations.');
    } finally {
      setLoading(false);
    }
  }, [employeeCode]);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  async function handleCreateConversation(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!employeeCode || !title.trim()) return;

    try {
      setCreating(true);
      setError('');

      const created = await agentApi.createConversation(employeeCode, {
        title: title.trim(),
      });

      console.log('[Conversations] Created:', created);

      const conversationId = getConversationId(created);

      if (!conversationId) {
        throw new Error(
          'Conversation was created, but its ID was not found in the response.'
        );
      }

      navigate(`/conversations/${conversationId}/messages`);
    } catch (err) {
      console.error('[Conversations] Creation failed:', err);

      setError(
        err instanceof Error
          ? err.message
          : 'Unable to create the conversation.'
      );

      await loadConversations();
    } finally {
      setCreating(false);
    }
  }

  if (loading) {
    return (
      <div className="page-content loading-state">
        <RefreshCw size={22} className="animate-spin" />
        <p>Loading conversations...</p>
      </div>
    );
  }

  return (
    <div className="page-content">
      <Link
        to={`/agents/${employeeCode}`}
        className="back-link"
      >
        <ArrowLeft size={16} />
        Back to employee profile
      </Link>

      <div className="page-heading">
        <div>
          <div className="eyebrow">EMPLOYEE INTELLIGENCE</div>
          <h1>Conversations</h1>
          <p>
            {agent?.fullName || employeeCode} ·{' '}
            {agent?.designation || 'Employee agent'}
          </p>
        </div>

        <button
          className="primary-button"
          type="button"
          onClick={() => setShowCreateForm(true)}
        >
          <Plus size={17} />
          New conversation
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <AlertCircle size={19} />
          <span>{error}</span>
          <button type="button" onClick={() => void loadConversations()}>
            Retry
          </button>
        </div>
      )}

      {showCreateForm && (
        <div className="conversation-form-card">
          <div className="conversation-form-heading">
            <div>
              <h3>Create a conversation</h3>
              <p>Start a new discussion with this employee agent.</p>
            </div>

            <button
              className="icon-button"
              type="button"
              aria-label="Close"
              onClick={() => setShowCreateForm(false)}
            >
              <X size={18} />
            </button>
          </div>

          <form onSubmit={handleCreateConversation}>
            <label htmlFor="conversation-title">
              Conversation title
            </label>

            <input
              id="conversation-title"
              className="conversation-title-input"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="e.g. Sales performance discussion"
              maxLength={150}
              required
            />

            <div className="conversation-form-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() => setShowCreateForm(false)}
              >
                Cancel
              </button>

              <button
                type="submit"
                className="primary-button"
                disabled={creating || !title.trim()}
              >
                {creating ? 'Creating...' : 'Create conversation'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="section-block">
        <div className="section-heading">
          <div>
            <h2>Conversation history</h2>
            <p>
              {conversations.length} conversation
              {conversations.length === 1 ? '' : 's'} available
            </p>
          </div>

          <button
            className="secondary-button"
            type="button"
            onClick={() => void loadConversations()}
          >
            <RefreshCw size={15} />
            Refresh
          </button>
        </div>

        {conversations.length === 0 ? (
          <div className="empty-state">
            <MessageSquare size={28} />
            <h3>No conversations yet</h3>
            <p>
              Start a new conversation to interact with this employee's
              AI agent.
            </p>
            <button
              className="primary-button"
              type="button"
              onClick={() => setShowCreateForm(true)}
            >
              <Plus size={16} />
              Start first conversation
            </button>
          </div>
        ) : (
          <div className="conversation-list">
            {conversations.map((conversation) => {
              const id = getConversationId(conversation);

              return (
                <button
                  type="button"
                  className="conversation-item"
                  key={id}
                  onClick={() =>
                    navigate(`/conversations/${id}/messages`)
                  }
                >
                  <div className="conversation-item-icon">
                    <MessageSquare size={19} />
                  </div>

                  <div className="conversation-item-content">
                    <h3>{conversation.title || 'Untitled conversation'}</h3>

                    <p>
                      <Clock size={13} />
                      {formatDate(
                        conversation.updatedAt || conversation.createdAt
                      )}
                    </p>
                  </div>

                  <span className="conversation-status">
                    {conversation.status || 'ACTIVE'}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
