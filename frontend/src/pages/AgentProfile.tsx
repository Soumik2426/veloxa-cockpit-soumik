
import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  BriefcaseBusiness,
  Building2,
  MessageSquare,
  RefreshCw,
  UserRound,
  AlertCircle,
  Activity,
} from 'lucide-react';

import { agentApi } from '../api/agentApi';
import type { EmployeeAgent } from '../types/agent';

export default function AgentProfile() {
  const { employeeCode } = useParams<{ employeeCode: string }>();
  const navigate = useNavigate();

  const [agent, setAgent] = useState<EmployeeAgent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadAgent = useCallback(async () => {
    if (!employeeCode) {
      setError('Employee code is missing.');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError('');

      const result = await agentApi.getAgentByCode(employeeCode);

      console.log('[AgentProfile] Profile received:', result);

      setAgent(result);
    } catch (err) {
      console.error('[AgentProfile] Failed to load profile:', err);
      setError('Unable to load this employee profile.');
    } finally {
      setLoading(false);
    }
  }, [employeeCode]);

  useEffect(() => {
    void loadAgent();
  }, [loadAgent]);

  if (loading) {
    return (
      <div className="page-content loading-state">
        <RefreshCw size={22} className="animate-spin" />
        <p>Loading employee profile...</p>
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="page-content">
        <Link to="/agents" className="back-link">
          <ArrowLeft size={16} />
          Back to employee agents
        </Link>

        <div className="error-banner">
          <AlertCircle size={19} />
          {error || 'Employee profile not found.'}
          <button type="button" onClick={() => void loadAgent()}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  const enabled = agent.enabled === true;

  return (
    <div className="page-content">
      <Link to="/agents" className="back-link">
        <ArrowLeft size={16} />
        Back to employee agents
      </Link>

      <section className="profile-header">
        <div className="profile-identity">
          <div className="profile-avatar">
            {agent.fullName.charAt(0).toUpperCase()}
          </div>

          <div>
            <div className="eyebrow">EMPLOYEE AGENT PROFILE</div>
            <h1>{agent.fullName}</h1>
            <p>{agent.designation}</p>

            <span className="profile-code">
              {agent.employeeCode}
            </span>
          </div>
        </div>

        <button
          className="primary-button"
          type="button"
          onClick={() =>
            navigate(`/agents/${agent.employeeCode}/conversations`)
          }
        >
          <MessageSquare size={17} />
          Open conversations
        </button>
      </section>

      <section className="section-block">
        <div className="section-heading">
          <div>
            <h2>Employee information</h2>
            <p>Profile information retrieved from the company records.</p>
          </div>
        </div>

        <div className="profile-details-grid">
          <article className="profile-detail-card">
            <div className="profile-detail-icon">
              <UserRound size={19} />
            </div>
            <span>Full name</span>
            <strong>{agent.fullName}</strong>
          </article>

          <article className="profile-detail-card">
            <div className="profile-detail-icon">
              <BriefcaseBusiness size={19} />
            </div>
            <span>Designation</span>
            <strong>{agent.designation}</strong>
          </article>

          <article className="profile-detail-card">
            <div className="profile-detail-icon">
              <Building2 size={19} />
            </div>
            <span>Department</span>
            <strong>{agent.department}</strong>
          </article>

          <article className="profile-detail-card">
            <div className="profile-detail-icon">
              <Activity size={19} />
            </div>
            <span>Employment status</span>
            <strong>{agent.employmentStatus}</strong>
          </article>
        </div>
      </section>

      <section className="section-block">
        <div className="section-heading">
          <div>
            <h2>AI agent information</h2>
            <p>Agent identity and availability.</p>
          </div>
        </div>

        <div className="profile-agent-card">
          <div>
            <span className="profile-info-label">Agent key</span>
            <strong>{agent.agentKey}</strong>
          </div>

          <div>
            <span className="profile-info-label">Agent availability</span>
            <span className={`profile-status ${enabled ? 'enabled' : 'disabled'}`}>
              <span className="agent-status-dot" />
              {enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}
