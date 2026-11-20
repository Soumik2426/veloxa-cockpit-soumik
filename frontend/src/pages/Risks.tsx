
import { useCallback, useEffect, useState } from 'react';
import {
  AlertTriangle,
  RefreshCw,
  ShieldAlert,
  FileText,
  Activity,
} from 'lucide-react';

import { agentApi } from '../api/agentApi';

type ApiResponse = Record<string, unknown>;

const RISK_QUESTION = `
Analyse the company's current business risks using the available company records
and documents.

Identify:
1. Major business risks.
2. Personnel and employee attrition risks.
3. Engineering and product delivery risks.
4. Financial, hiring and operational risks.
5. Supporting evidence and source references for each risk.
6. What should the CEO worry about most?
7. Any information gaps or uncertainties.

For every finding:
- Explain the risk clearly.
- State its potential business impact.
- Cite the supporting source documents.
- Distinguish confirmed evidence from assumptions.
- Do not invent risk scores, dates, facts or evidence.

Present the answer in clearly separated sections with concise bullet points.
`;

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

function formatValue(value: unknown): string {
  if (typeof value === 'string') return value;

  if (
    typeof value === 'number' ||
    typeof value === 'boolean'
  ) {
    return String(value);
  }

  if (value === null || value === undefined) return '';

  return JSON.stringify(value, null, 2);
}

function asRecord(
  value: unknown
): Record<string, unknown> | null {
  if (
    typeof value === 'object' &&
    value !== null &&
    !Array.isArray(value)
  ) {
    return value as Record<string, unknown>;
  }

  return null;
}

function getText(
  value: unknown,
  fallback = ''
): string {
  if (
    typeof value === 'string' ||
    typeof value === 'number'
  ) {
    return String(value);
  }

  return fallback;
}

function ResponseContent({ value }: { value: unknown }) {
  const content = formatValue(value);

  if (!content) {
    return <p>No information was returned.</p>;
  }

  return (
    <div className="risk-response-content">
      {content.split('\n').map((line, index) => {
        const trimmed = line.trim();

        if (!trimmed) {
          return (
            <div className="risk-spacer" key={index} />
          );
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
            <div className="risk-bullet" key={index}>
              <span>•</span>
              <span>{trimmed.replace(/^[-*]\s/, '')}</span>
            </div>
          );
        }

        if (/^\d+\.\s/.test(trimmed)) {
          return (
            <div className="risk-bullet" key={index}>
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

function getEvidenceExcerpt(content: unknown): string {
  if (typeof content === 'string') {
    return content;
  }

  const contentRecord = asRecord(content);

  if (!contentRecord) {
    return content == null ? '' : formatValue(content);
  }

  const results = contentRecord.results;

  if (Array.isArray(results)) {
    return results
      .slice(0, 3)
      .map((item) => {
        const record = asRecord(item);

        if (!record) {
          return formatValue(item);
        }

        const extracted = asRecord(record.extracted_data);
        const data = asRecord(extracted?.data);

        if (data) {
          return Object.entries(data)
            .map(([key, value]) => {
              const readableValue =
                typeof value === 'object' && value !== null
                  ? JSON.stringify(value)
                  : String(value ?? '');

              return `${key}: ${readableValue}`;
            })
            .join(' · ');
        }

        if (typeof record.content === 'string') {
          return record.content;
        }

        return formatValue(item);
      })
      .filter(Boolean)
      .join('\n');
  }

  if (typeof contentRecord.content === 'string') {
    return contentRecord.content;
  }

  return formatValue(content);
}

function getEvidenceLocation(
  content: unknown,
  sourceReference: Record<string, unknown> | null
): string[] {
  const locations: string[] = [];

  const contentRecord = asRecord(content);

  const results = Array.isArray(contentRecord?.results)
    ? contentRecord.results
    : [];

  const firstResult = asRecord(results[0]);
  const locator = asRecord(firstResult?.source_locator);

  const sheet =
    sourceReference?.sheet ??
    sourceReference?.sheet_name ??
    locator?.sheet_name;

  const row = locator?.row_number;

  const explicitPage =
    sourceReference?.page ??
    sourceReference?.page_number;

  const contentText =
    typeof content === 'string' ? content : '';

  const pageMatch = contentText.match(
    /\bPage\s+(\d+)\b/i
  );

  const page = explicitPage ?? pageMatch?.[1];

  if (sheet) {
    locations.push(`Sheet: ${String(sheet)}`);
  }

  if (row) {
    locations.push(`Row: ${String(row)}`);
  }

  if (page) {
    locations.push(`Page: ${String(page)}`);
  }

  return locations;
}

function Evidence({ value }: { value: unknown }) {
  if (!Array.isArray(value) || value.length === 0) {
    return null;
  }

  return (
    <section className="risk-evidence">
      <div className="risk-evidence-heading">
        <div>
          <h3>
            <FileText size={17} />
            Supporting evidence
          </h3>

          <p>
            Source documents and records used to generate this assessment.
          </p>
        </div>

        <span className="risk-evidence-count">
          {value.length}{' '}
          {value.length === 1 ? 'source' : 'sources'}
        </span>
      </div>

      <div className="risk-evidence-list">
        {value.map((item, index) => {
          const evidence = asRecord(item);

          if (!evidence) {
            return (
              <article
                className="risk-evidence-card"
                key={index}
              >
                <p>{String(item)}</p>
              </article>
            );
          }

          const sourceReference = asRecord(
            evidence.source_reference
          );

          const fileName =
            getText(sourceReference?.file_name) ||
            getText(evidence.file_name) ||
            'Source document';

          const content = evidence.content;

          const excerpt = getEvidenceExcerpt(content);

          const location = getEvidenceLocation(
            content,
            sourceReference
          );

          return (
            <article
              className="risk-evidence-card"
              key={index}
            >
              <div className="risk-evidence-card-top">
                <div className="risk-evidence-file-icon">
                  <FileText size={19} />
                </div>

                <div className="risk-evidence-file-info">
                  <h4>{fileName}</h4>

                  {location.length > 0 && (
                    <span>{location.join(' · ')}</span>
                  )}
                </div>
              </div>

              {excerpt && (
                <p className="risk-evidence-excerpt">
                  {excerpt.length > 650
                    ? `${excerpt.slice(0, 650)}...`
                    : excerpt}
                </p>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default function Risks() {
  const [result, setResult] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState('');

  const loadRisks = useCallback(async () => {
    try {
      setLoading(true);
      setError('');

      const response = await agentApi.askCompany(RISK_QUESTION);

      console.log('[RiskMonitor] AI response:', response);

      setResult(response);

      setLastUpdated(
        new Date().toLocaleString('en-IN', {
          dateStyle: 'medium',
          timeStyle: 'short',
        })
      );
    } catch (err) {
      console.error('[RiskMonitor] Failed:', err);

      setError(
        'Unable to generate the risk assessment. Please check the AI service and try again.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadRisks();
  }, [loadRisks]);

  const answer = result
    ? getValue(result, [
        'answer',
        'response',
        'message',
        'output',
        'content',
      ])
    : undefined;

  const citations = result
    ? getValue(result, [
        'citations',
        'evidence',
        'sources',
        'references',
      ])
    : undefined;

  const risks = result
    ? getValue(result, [
        'risks',
        'risk_analysis',
        'riskAnalysis',
      ])
    : undefined;

  const concerns = result
    ? getValue(result, [
        'what_should_i_worry_about',
        'concerns',
        'priority_concerns',
      ])
    : undefined;

  return (
    <div className="page-content risk-page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            EXECUTIVE RISK INTELLIGENCE
          </div>

          <h1>Risk monitor</h1>

          <p>
            Identify business risks, operational concerns and potential
            threats using available company evidence.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() => void loadRisks()}
          disabled={loading}
        >
          <RefreshCw
            size={15}
            className={loading ? 'animate-spin' : ''}
          />
          Refresh analysis
        </button>
      </div>

      <div className="risk-intro-card">
        <div className="risk-intro-icon">
          <ShieldAlert size={23} />
        </div>

        <div>
          <h2>Company-wide risk assessment</h2>

          <p>
            The AI service analyses available company information and
            identifies potential areas requiring executive attention.
          </p>

          {lastUpdated && (
            <span>Last generated: {lastUpdated}</span>
          )}
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <AlertTriangle size={18} />
          {error}

          <button
            type="button"
            onClick={() => void loadRisks()}
          >
            Retry
          </button>
        </div>
      )}

      {loading && (
        <div className="risk-loading">
          <RefreshCw size={22} className="animate-spin" />

          <div>
            <strong>Analysing company risks...</strong>

            <p>
              Reviewing available evidence and identifying executive concerns.
            </p>
          </div>
        </div>
      )}

      {result && !loading && (
        <>
          <div className="risk-section-heading">
            <div>
              <div className="eyebrow">
                ASSESSMENT RESULTS
              </div>

              <h2>Identified business risks</h2>
            </div>

            <Activity size={21} />
          </div>

          {risks !== undefined && (
            <section className="risk-result-card">
              <h3>
                <AlertTriangle size={17} />
                Risk findings
              </h3>

              <ResponseContent value={risks} />
            </section>
          )}

          {answer !== undefined && (
            <section className="risk-result-card">
              <h3>Full risk assessment</h3>

              <ResponseContent value={answer} />
            </section>
          )}

          {concerns !== undefined && (
            <section className="risk-priority-card">
              <h3>
                <AlertTriangle size={17} />
                What should the CEO worry about?
              </h3>

              <ResponseContent value={concerns} />
            </section>
          )}

          {answer === undefined &&
            risks === undefined &&
            concerns === undefined && (
              <section className="risk-result-card">
                <h3>AI service response</h3>
                <pre>{JSON.stringify(result, null, 2)}</pre>
              </section>
            )}

          <Evidence value={citations} />

          <p className="risk-disclaimer">
            Risk findings are generated from available evidence. They are
            not independently verified assessments. Missing evidence does
            not imply that a risk is absent.
          </p>
        </>
      )}
    </div>
  );
}
