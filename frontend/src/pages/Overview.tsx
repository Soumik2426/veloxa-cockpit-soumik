
import { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Users,
  MessageSquare,
  ArrowRight,
  Database,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import { agentApi } from '../api/agentApi';

export default function Overview() {
  const [agentCount, setAgentCount] = useState<number | null>(null);
  const [loadingAgents, setLoadingAgents] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadAgents() {
      try {
        const agents = await agentApi.getAllAgents();

        if (active) {
          setAgentCount(agents.length);
        }
      } catch (error) {
        console.error('[Overview] Failed to load agents:', error);
      } finally {
        if (active) {
          setLoadingAgents(false);
        }
      }
    }

    void loadAgents();

    return () => {
      active = false;
    };
  }, []);

  const metrics = [
    {
      label: 'Business Health',
      value: '—',
      note: 'Awaiting verified business metrics',
      icon: Activity,
    },
    {
      label: 'Open Concerns',
      value: '—',
      note: 'Awaiting risk intelligence',
      icon: AlertTriangle,
    },
    {
      label: 'Employee Agents',
      value: loadingAgents ? '...' : agentCount === null ? '—' : String(agentCount),
      note: 'Registered employee agents',
      icon: Users,
    },
    {
      label: 'Pending Decisions',
      value: '—',
      note: 'Awaiting decision data',
      icon: MessageSquare,
    },
  ];

  const shortcuts = [
    {
      title: 'Ask your company',
      description:
        'Get answers grounded in structured records and company documents.',
      path: '/ask-company',
      icon: MessageSquare,
    },
    {
      title: 'Employee intelligence',
      description:
        'Explore employee agents and their individual knowledge.',
      path: '/agents',
      icon: Users,
    },
    {
      title: 'Monitor business risks',
      description:
        'Review emerging concerns, conflicting evidence and unresolved issues.',
      path: '/risks',
      icon: ShieldCheck,
    },
    {
      title: 'Review voice notes',
      description:
        'Inspect CEO instructions, resulting changes and written pushbacks.',
      path: '/voice-notes',
      icon: Activity,
    },
  ];

  return (
    <div className="page-content">
      <div className="page-heading overview-heading">
        <div>
          <div className="eyebrow">EXECUTIVE WORKSPACE</div>
          <h1>Company overview</h1>
          <p>Your company intelligence, brought together in one place.</p>
        </div>

        <div className="overview-date">
          <span className="status-dot" />
          Executive view
        </div>
      </div>

      <section className="metrics-grid">
        {metrics.map(({ label, value, note, icon: Icon }) => (
          <article className="metric-card" key={label}>
            <div className="metric-top">
              <span>{label}</span>
              <Icon size={19} />
            </div>
            <div className="metric-value">{value}</div>
            <p>{note}</p>
          </article>
        ))}
      </section>

      {agentCount !== null && (
        <p className="overview-data-note">
          <RefreshCw size={13} />
          Employee count retrieved from the live employee-agent API.
        </p>
      )}

      <section className="section-block">
        <div className="section-heading">
          <div>
            <h2>Executive workspace</h2>
            <p>Choose where you want to focus your attention.</p>
          </div>
        </div>

        <div className="shortcut-grid">
          {shortcuts.map(({ title, description, path, icon: Icon }) => (
            <Link to={path} className="shortcut-card" key={path}>
              <div className="shortcut-icon">
                <Icon size={20} />
              </div>
              <h3>{title}</h3>
              <p>{description}</p>
              <span className="shortcut-link">
                Open workspace <ArrowRight size={15} />
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="section-block">
        <div className="section-heading">
          <div>
            <h2>Intelligence infrastructure</h2>
            <p>Core components of the company simulation.</p>
          </div>
        </div>

        <div className="infrastructure-card">
          <div className="infrastructure-item">
            <div className="infrastructure-icon">
              <Database size={20} />
            </div>
            <div>
              <h3>Company data</h3>
              <p>Structured records and ingested documents</p>
            </div>
          </div>

          <div className="infrastructure-item">
            <div className="infrastructure-icon">
              <Users size={20} />
            </div>
            <div>
              <h3>Employee simulation</h3>
              <p>Role-specific employee agents</p>
            </div>
          </div>

          <div className="infrastructure-item">
            <div className="infrastructure-icon">
              <ShieldCheck size={20} />
            </div>
            <div>
              <h3>Evidence-based intelligence</h3>
              <p>Retrieval, citations and confidence assessment</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
