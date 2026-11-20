import AgentChat from './pages/AgentChat';
import AgentConversations from './pages/AgentConversations';
import AgentProfile from './pages/AgentProfile';
import { useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import {
  MessageSquare,
  ShieldAlert,
  Mic,
  Database,
} from 'lucide-react';

import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import PagePlaceholder from './components/common/PagePlaceholder';

import Overview from './pages/Overview';
import EmployeeAgents from './pages/EmployeeAgents';

import './App.css';

function AppContent() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={`app-shell ${collapsed ? 'app-shell-collapsed' : ''}`}>
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed((value) => !value)}
      />

      <div className="app-main">
        <Header />

        <main>
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/agents" element={<EmployeeAgents />} />
            <Route path="/agents/:employeeCode" element={<AgentProfile />} />
            <Route
              path="/agents/:employeeCode/conversations"
              element={<AgentConversations />}
            />
            <Route
              path="/conversations/:conversationId/messages"
              element={<AgentChat />}
            />
            <Route
              path="/ask-company"
              element={
                <PagePlaceholder
                  title="Ask Company"
                  description="Ask questions across company records, documents and employee knowledge."
                  icon={MessageSquare}
                />
              }
            />

            <Route
              path="/risks"
              element={
                <PagePlaceholder
                  title="Risk monitor"
                  description="Identify business risks, contradictions and unresolved concerns."
                  icon={ShieldAlert}
                />
              }
            />

            <Route
              path="/voice-notes"
              element={
                <PagePlaceholder
                  title="CEO voice notes"
                  description="Submit CEO instructions and review changes or written pushbacks."
                  icon={Mic}
                />
              }
            />

            <Route
              path="/data-sources"
              element={
                <PagePlaceholder
                  title="Data sources"
                  description="Review ingested files, data sources and pipeline activity."
                  icon={Database}
                />
              }
            />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        <footer className="app-footer">
          <span>VELOXA CXO COCKPIT</span>
          <span>Evidence-led company intelligence</span>
        </footer>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}