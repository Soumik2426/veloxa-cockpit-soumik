
import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import {
  MessageSquare,
  Send,
  RefreshCw,
  AlertCircle,
  FileText,
  Bot,
  UserRound,
} from 'lucide-react';

import { agentApi } from '../api/agentApi';

type ApiResponse = Record<string, unknown>;

interface CompanyTurn {
  id: number;
  question: string;
  response?: ApiResponse;
  error?: string;
  loading: boolean;
  createdAt: string;
}

function getValue(
  data: ApiResponse,
  keys: string[]
): unknown {
  for (const key of keys) {
    if (data[key] !== undefined && data[key] !== null) {
      return data[key];
    }
  }

  return undefined;
}

function getAnswer(data: ApiResponse): unknown {
  const answer = getValue(data, [
    'answer',
    'response',
    'message',
    'output',
    'content',
  ]);

  if (answer !== undefined) return answer;

  for (const key of ['data', 'result', 'agent_response']) {
    const nested = data[key];

    if (nested && typeof nested === 'object' && !Array.isArray(nested)) {
      const nestedAnswer = getValue(nested as ApiResponse, [
        'answer',
        'response',
        'message',
        'output',
        'content',
      ]);

      if (nestedAnswer !== undefined) return nestedAnswer;
    }

    if (typeof nested === 'string' && nested.trim()) {
      return nested;
    }
  }

  return undefined;
}

function formatValue(value: unknown): string {
  if (typeof value === 'string') return value;

  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  if (value === null || value === undefined) return '';

  return JSON.stringify(value, null, 2);
}

function AnswerContent({ value }: { value: unknown }) {
  const content = formatValue(value);

  if (!content) {
    return <p>The AI service returned an empty answer.</p>;
  }

  return (
    <div className="company-chat-answer">
      {content.split('\n').map((line, index) => {
        const trimmed = line.trim();

        if (!trimmed) {
          return <div className="answer-spacer" key={index} />;
        }

        if (/^#{1,3}\s/.test(trimmed)) {
          return (
            <h3 key={index}>
              {trimmed.replace(/^#{1,3}\s/, '')}
            </h3>
          );
        }

        if (/^[-*]\s/.test(trimmed)) {
          return (
            <div className="answer-bullet" key={index}>
              <span>•</span>
              <span>{trimmed.replace(/^[-*]\s/, '')}</span>
            </div>
          );
        }

        if (/^\d+\.\s/.test(trimmed)) {
          return (
            <div className="answer-bullet" key={index}>
              <span>{trimmed.match(/^\d+\./)?.[0]}</span>
              <span>{trimmed.replace(/^\d+\.\s/, '')}</span>
            </div>
          );
        }

        return <p key={index}>{trimmed}</p>;
      })}
    </div>
  );
}

function Evidence({ value }: { value: unknown }) {
  if (!Array.isArray(value) || value.length === 0) return null;

  return (
    <details className="company-chat-evidence">
      <summary>
        <FileText size={14} />
        Supporting sources ({value.length})
      </summary>

      <div className="company-chat-evidence-list">
        {value.map((item, index) => (
          <div className="company-chat-evidence-item" key={index}>
            {typeof item === 'string'
              ? item
              : formatValue(item)}
          </div>
        ))}
      </div>
    </details>
  );
}

function ChatTimestamp({ value }: { value: string }) {
  return (
    <span>
      {new Date(value).toLocaleTimeString('en-IN', {
        hour: 'numeric',
        minute: '2-digit',
      })}
    </span>
  );
}

export default function AskCompany() {
  const [question, setQuestion] = useState('');
  const [turns, setTurns] = useState<CompanyTurn[]>([]);
  const [sending, setSending] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const content = question.trim();

    if (!content || sending) return;

    const turnId = Date.now();

    const newTurn: CompanyTurn = {
      id: turnId,
      question: content,
      loading: true,
      createdAt: new Date().toISOString(),
    };

    setTurns((previous) => [...previous, newTurn]);
    setQuestion('');
    setSending(true);

    try {
      const response = await agentApi.askCompany(content);

      console.log('[AskCompany] API response:', response);

      setTurns((previous) =>
        previous.map((turn) =>
          turn.id === turnId
            ? { ...turn, response, loading: false }
            : turn
        )
      );
    } catch (err) {
      console.error('[AskCompany] Request failed:', err);

      const errorMessage =
        err instanceof Error
          ? err.message
          : 'Unable to generate an answer.';

      setTurns((previous) =>
        previous.map((turn) =>
          turn.id === turnId
            ? {
                ...turn,
                loading: false,
                error: errorMessage,
              }
            : turn
        )
      );
    } finally {
      setSending(false);
      textareaRef.current?.focus();
    }
  }

  return (
    <div className="company-chat-page">
      <header className="company-chat-header">
        <div className="company-chat-heading-icon">
          <MessageSquare size={19} />
        </div>

        <div>
          <h1>Ask your company</h1>
          <p>Company-wide intelligence and evidence-based answers</p>
        </div>

        <span className="company-chat-status">
          <span className="status-dot" />
          AI assistant
        </span>
      </header>

      <div className="company-chat-messages">
        {turns.length === 0 && (
          <div className="company-chat-welcome">
            <div className="company-chat-welcome-icon">
              <Bot size={30} />
            </div>

            <h2>Company intelligence, at your fingertips.</h2>

            <p>
              Ask questions about company performance, employees,
              projects, finances and business risks.
            </p>

            <div className="company-chat-suggestions">
              <button
                type="button"
                onClick={() =>
                  setQuestion('What are the biggest business risks facing the company?')
                }
              >
                What are the biggest business risks?
              </button>

              <button
                type="button"
                onClick={() =>
                  setQuestion('What are the major engineering and product delivery concerns?')
                }
              >
                What are the engineering concerns?
              </button>

              <button
                type="button"
                onClick={() =>
                  setQuestion('What should the CEO be most worried about right now?')
                }
              >
                What should the CEO worry about?
              </button>
            </div>
          </div>
        )}

        {turns.map((turn) => {
          const response = turn.response;
          const answer = response ? getAnswer(response) : undefined;

          const citations = response
            ? getValue(response, [
                'citations',
                'evidence',
                'sources',
                'references',
              ])
            : undefined;

          const worry = response
            ? getValue(response, [
                'what_should_i_worry_about',
                'concerns',
                'priority_concerns',
              ])
            : undefined;

          const confidence = response
            ? getValue(response, [
                'confidence',
                'confidence_score',
              ])
            : undefined;

          return (
            <div className="company-chat-turn" key={turn.id}>
              <div className="company-chat-user-row">
                <div className="company-chat-user-bubble">
                  <div>{turn.question}</div>
                  <ChatTimestamp value={turn.createdAt} />
                </div>

                <div className="company-chat-user-avatar">
                  <UserRound size={17} />
                </div>
              </div>

              <div className="company-chat-assistant-row">
                <div className="company-chat-bot-avatar">
                  <Bot size={19} />
                </div>

                <div className="company-chat-assistant-content">
                  <div className="company-chat-agent-label">
                    Company Intelligence
                    <ChatTimestamp value={turn.createdAt} />
                  </div>

                  {turn.loading && (
                    <div className="company-chat-bubble">
                      <div className="company-chat-thinking">
                        <RefreshCw
                          size={16}
                          className="animate-spin"
                        />
                        Analysing company knowledge...
                      </div>
                    </div>
                  )}

                  {turn.error && (
                    <div className="company-chat-bubble company-chat-error">
                      <AlertCircle size={17} />
                      <div>
                        <strong>Unable to generate an answer</strong>
                        <p>{turn.error}</p>
                      </div>
                    </div>
                  )}

                  {response && (
                    <div className="company-chat-bubble">
                      {answer !== undefined ? (
                        <AnswerContent value={answer} />
                      ) : (
                        <>
                          <p>
                            The AI service returned a response in an
                            unexpected format. Raw response:
                          </p>
                          <pre className="company-raw-response">
                            {JSON.stringify(response, null, 2)}
                          </pre>
                        </>
                      )}

                      {worry !== undefined && (
                        <div className="company-chat-worry">
                          <strong>What should I worry about?</strong>
                          <AnswerContent value={worry} />
                        </div>
                      )}

                      {confidence !== undefined && (
                        <div className="company-chat-confidence">
                          Confidence: {formatValue(confidence)}
                        </div>
                      )}

                      <Evidence value={citations} />
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        <div ref={bottomRef} />
      </div>

      <div className="company-chat-composer">
        <form onSubmit={handleSubmit}>
          <textarea
            ref={textareaRef}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask anything about your company..."
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
            disabled={!question.trim() || sending}
            aria-label="Send question"
          >
            {sending ? (
              <RefreshCw size={18} className="animate-spin" />
            ) : (
              <Send size={18} />
            )}
          </button>
        </form>

        <div className="company-chat-composer-note">
          Company answers are generated from available evidence.
          Press Enter to send · Shift + Enter for a new line.
        </div>
      </div>
    </div>
  );
}
