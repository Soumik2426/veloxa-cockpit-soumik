import { NavLink } from 'react-router-dom';
import {
  Activity,
  LayoutDashboard,
  MessageSquare,
  Users,
  ShieldAlert,
  Mic,
  Database,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navigation = [
  { label: 'Overview', path: '/', icon: LayoutDashboard },
  { label: 'Ask Company', path: '/ask-company', icon: MessageSquare },
  { label: 'Employee Agents', path: '/agents', icon: Users },
  { label: 'Risk Monitor', path: '/risks', icon: ShieldAlert },
  { label: 'Voice Notes', path: '/voice-notes', icon: Mic },
  { label: 'Data Sources', path: '/data-sources', icon: Database },
];

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Activity size={21} />
        </div>

        {!collapsed && (
          <div>
            <h2>VELOXA</h2>
            <span>EXECUTIVE WORKSPACE</span>
          </div>
        )}
      </div>

      <div className="sidebar-section-label">
        {!collapsed && 'WORKSPACE'}
      </div>

      <nav className="sidebar-nav">
        {navigation.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            title={collapsed ? label : undefined}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'nav-item-active' : ''}`
            }
          >
            <Icon size={19} strokeWidth={1.8} />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <button
          className="collapse-button"
          onClick={onToggle}
          type="button"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          {!collapsed && <span>Collapse sidebar</span>}
        </button>

        {!collapsed && (
          <div className="sidebar-version">
            <span className="status-dot" />
            Veloxa CXO Cockpit
            <span>v1.0</span>
          </div>
        )}
      </div>
    </aside>
  );
}