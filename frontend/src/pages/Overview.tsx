
import { useEffect, useState } from 'react';
import {
  Activity,
  Users,
  MessageSquare,
  ArrowRight,
  Database,
  ShieldCheck,
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

      <section className="workspace-summary" aria-label="Executive workspace summary">
        <div className="workspace-summary-main">
          <div className="workspace-summary-icon">
            <Users size={21} />
          </div>
          <div>
            <div className="workspace-summary-eyebrow">WORKSPACE COVERAGE</div>
            <h2>Employee intelligence</h2>
            <p>
              Explore role-specific perspectives across the company&apos;s
              employee agents.
            </p>
          </div>
        </div>

        {(loadingAgents || agentCount !== null) && (
          <div className="workspace-summary-stat">
            {loadingAgents && <span>Loading agents...</span>}
            {agentCount !== null && (
              <>
                <strong>{agentCount}</strong>
                <span>registered agents</span>
              </>
            )}
          </div>
        )}

        <Link to="/agents" className="workspace-summary-link">
          Explore agents <ArrowRight size={15} />
        </Link>
      </section>

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
