import { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, FileText, Mic, ShieldCheck } from 'lucide-react';

import { dataApi } from '../api/dataApi';
import type { VoiceNote } from '../api/dataApi';

export default function VoiceNotes() {
  const [voiceNotes, setVoiceNotes] = useState<VoiceNote[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    void dataApi.listVoiceNotes()
      .then(setVoiceNotes)
      .catch((requestError) => {
        console.error('[VoiceNotes] Failed to load notes:', requestError);
        setError('Unable to load CEO voice notes from the backend.');
      });
  }, []);

  return (
    <div className="page-content voice-notes-page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">DECISION TRACEABILITY</div>
          <h1>CEO voice notes</h1>
          <p>Original notes and their recorded decisions from the source system.</p>
        </div>
        <div className="voice-notes-summary">
          <Mic size={18} />
          <strong>{voiceNotes.length} notes loaded</strong>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {!error && voiceNotes.length === 0 && (
        <div className="loading-state">Loading CEO voice notes...</div>
      )}

      <div className="voice-notes-list">
        {voiceNotes.map((note) => {
          const implemented = note.outcome.kind === 'implemented';
          const StatusIcon = implemented ? CheckCircle2 : AlertTriangle;

          return (
            <article className="voice-note-card" key={note.id}>
              <div className="voice-note-card-header">
                <div>
                  <span className="voice-note-id">{note.noteId}</span>
                  <h2>{note.outcome.summary}</h2>
                  <span className="voice-note-date">
                    {note.discoveredAt
                      ? new Date(note.discoveredAt).toLocaleDateString('en-IN')
                      : 'Date unavailable'}
                  </span>
                </div>
                <span className={`voice-note-status ${implemented ? 'voice-note-status-implemented' : 'voice-note-status-pushback'}`}>
                  <StatusIcon size={15} />
                  {note.outcome.label}
                </span>
              </div>

              <section className="voice-note-section">
                <h3>Original transcript</h3>
                <p className="voice-note-transcript">“{note.transcript}”</p>
                <p className="voice-note-source">
                  <FileText size={14} />
                  {note.sourceFile}
                </p>
              </section>

              <section className="voice-note-outcome">
                <h3>
                  {implemented ? <ShieldCheck size={16} /> : <AlertTriangle size={16} />}
                  Decision
                </h3>
                <p>{note.outcome.decision}</p>
              </section>
            </article>
          );
        })}
      </div>
    </div>
  );
}
