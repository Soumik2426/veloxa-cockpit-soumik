import { useEffect, useMemo, useState } from 'react';
import { Database, ExternalLink, RefreshCw, Search } from 'lucide-react';

import { dataApi } from '../api/dataApi';
import type { DataFile } from '../api/dataApi';

export default function DataSources() {
  const [files, setFiles] = useState<DataFile[]>([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadFiles() {
    try {
      setLoading(true);
      setError('');
      setFiles(await dataApi.listFiles());
    } catch (requestError) {
      console.error('[DataSources] Failed to load files:', requestError);
      setError('Unable to load source files. Check the backend connection.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadFiles();
  }, []);

  const categories = useMemo(
    () => ['All', ...Array.from(new Set(files.map((file) => file.category))).sort()],
    [files]
  );

  const filteredFiles = files.filter((file) => {
    const query = search.trim().toLowerCase();
    const matchesSearch =
      !query ||
      [file.fileName, file.category, file.fileType]
        .join(' ')
        .toLowerCase()
        .includes(query);
    return matchesSearch && (category === 'All' || file.category === category);
  });

  return (
    <div className="page-content data-sources-page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">SOURCE RECORDS</div>
          <h1>Data sources</h1>
          <p>Original assessment files indexed by the ingestion pipeline.</p>
        </div>
        <button type="button" className="secondary-button" onClick={() => void loadFiles()}>
          <RefreshCw size={15} />
          Refresh
        </button>
      </div>

      <div className="data-source-toolbar">
        <label>
          <Search size={16} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search files"
          />
        </label>
        <select value={category} onChange={(event) => setCategory(event.target.value)}>
          {categories.map((item) => <option key={item}>{item}</option>)}
        </select>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && <div className="loading-state"><RefreshCw size={20} className="animate-spin" /> Loading source files...</div>}
      {!loading && !error && (
        <section className="data-source-card">
          <div className="data-source-count">
            <Database size={17} />
            {filteredFiles.length} of {files.length} files
          </div>
          {filteredFiles.length === 0 ? (
            <div className="empty-state"><p>No matching source files.</p></div>
          ) : (
            <div className="data-source-list">
              {filteredFiles.map((file) => (
                <article className="data-source-row" key={file.id}>
                  <div className="data-source-icon"><Database size={17} /></div>
                  <div className="data-source-details">
                    <strong>{file.fileName}</strong>
                    <span>{file.category} · {file.fileType} · {file.status}</span>
                  </div>
                  <a
                    href={dataApi.contentUrl(file.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="secondary-button"
                  >
                    <ExternalLink size={14} />
                    Open
                  </a>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
