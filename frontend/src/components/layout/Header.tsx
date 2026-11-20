import { Bell, Search } from 'lucide-react';
import { useLocation } from 'react-router-dom';

const pageTitles: Record<string, string> = {
  '/': 'Overview',
  '/ask-company': 'Ask Company',
  '/agents': 'Employee Agents',
  '/risks': 'Risk Monitor',
  '/voice-notes': 'Voice Notes',
  '/data-sources': 'Data Sources',
};

export default function Header() {
  const location = useLocation();
  const title = pageTitles[location.pathname] || 'Executive Workspace';

  return (
    <header className="topbar">
      <div className="breadcrumb">
        <span>VELOXA</span>
        <span className="breadcrumb-divider">/</span>
        <strong>{title}</strong>
      </div>

      <div className="topbar-actions">
        <button
          className="icon-button"
          type="button"
          aria-label="Search"
          title="Search"
        >
          <Search size={19} />
        </button>

        <button
          className="icon-button"
          type="button"
          aria-label="Notifications"
          title="Notifications"
        >
          <Bell size={19} />
        </button>

        <div className="user-avatar" title="Ananya Rao">
          AR
        </div>
      </div>
    </header>
  );
}