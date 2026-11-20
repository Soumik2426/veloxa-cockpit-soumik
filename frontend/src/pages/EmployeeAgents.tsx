import { Link } from 'react-router-dom';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Search,
  Users,
  RefreshCw,
  AlertCircle,
  UserRound,
} from 'lucide-react';

import { agentApi } from '../api/agentApi';
import type { EmployeeAgent } from '../types/agent';

export default function EmployeeAgents() {
  const [agents, setAgents] = useState<EmployeeAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');

  const loadAgents = useCallback(async () => {
    try {
      setLoading(true);
      setError('');

      console.log('[EmployeeAgents] Fetching employee agents...');

      const result = await agentApi.getAllAgents();

      console.log('[EmployeeAgents] API RESULT:', result);
      console.log('[EmployeeAgents] IS ARRAY:', Array.isArray(result));
      console.log('[EmployeeAgents] AGENT COUNT:', result.length);

      if (!Array.isArray(result)) {
        throw new Error('API response is not an array.');
      }

      const validAgents = result.filter(
        (agent) =>
          agent &&
          typeof agent === 'object' &&
          typeof agent.employeeCode === 'string' &&
          typeof agent.fullName === 'string'
      );

      console.log('[EmployeeAgents] VALID AGENTS:', validAgents.length);

      setAgents(validAgents);

      if (validAgents.length === 0) {
        setError('No valid employee records were received from the API.');
      }
    } catch (err: unknown) {
      console.error('[EmployeeAgents] Failed to load agents:', err);

      setAgents([]);

      setError(
        err instanceof Error
          ? err.message
          : 'Unable to retrieve employee agents.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAgents();
  }, [loadAgents]);

  const filteredAgents = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) {
      return agents;
    }

    return agents.filter((agent) => {
      const searchText = [
        agent.employeeCode,
        agent.fullName,
        agent.designation,
        agent.department,
        agent.employmentStatus,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      return searchText.includes(query);
    });
  }, [agents, search]);

  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <div className="eyebrow">COMPANY INTELLIGENCE</div>

          <h1>Employee agents</h1>

          <p>
            Explore the people behind your company's intelligence.
          </p>
        </div>

        <button
          className="secondary-button"
          onClick={() => void loadAgents()}
          type="button"
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={loading ? 'animate-spin' : ''}
          />
          Refresh
        </button>
      </div>

      <div className="agent-toolbar">
        <div className="search-field">
          <Search size={18} />

          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by name, employee code or department..."
          />
        </div>

        <div className="agent-count">
          <Users size={17} />

          {loading
            ? 'Loading agents...'
            : `${filteredAgents.length} of ${agents.length} agents`}
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <AlertCircle size={19} />

          <span>{error}</span>

          <button
            type="button"
            onClick={() => void loadAgents()}
          >
            Retry
          </button>
        </div>
      )}

      {loading ? (
        <div className="loading-state">
          <RefreshCw size={22} className="animate-spin" />
          <p>Loading employee agents...</p>
        </div>
      ) : filteredAgents.length === 0 ? (
        <div className="empty-state">
          <Users size={28} />

          <h3>No employee agents found</h3>

          <p>
            {agents.length === 0
              ? 'No employee records are currently available.'
              : 'No employees match your search. Try another name or department.'}
          </p>
        </div>
      ) : (
        <div className="agents-grid">
          {filteredAgents.map((agent) => {
            const enabled = agent.enabled === true;

            return (
              <Link
                to={`/agents/${agent.employeeCode}`}
                className="agent-card"
                key={agent.id || agent.employeeCode}
              >
                <div className="agent-card-top">
                  <div className="agent-avatar">
                    {agent.fullName?.charAt(0).toUpperCase() || (
                      <UserRound size={20} />
                    )}
                  </div>

                  <span className="agent-code">
                    {agent.employeeCode}
                  </span>
                </div>

                <h3>{agent.fullName || 'Unknown employee'}</h3>

                <p className="agent-designation">
                  {agent.designation || 'Designation unavailable'}
                </p>

                <p className="agent-department">
                  {agent.department || 'Department unavailable'}
                </p>

                <div className="agent-card-footer">
                  <span>
                    {agent.employmentStatus || 'Status unavailable'}
                  </span>

                  <span
                    className="agent-status-dot"
                    title={enabled ? 'Agent enabled' : 'Agent disabled'}
                    style={{
                      background: enabled ? '#38a783' : '#d97757',
                    }}
                  />
                </div>

                <span className="profile-card-link">
                  View profile →
                </span>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
