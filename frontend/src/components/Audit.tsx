import React, { useEffect, useState } from 'react';
import { api, type AuditEvent } from '../api';
import './Audit.css';

const Audit: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterQ, setFilterQ] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [filterEntityType, setFilterEntityType] = useState('');

  const loadEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: { q?: string; action?: string; entity_type?: string } = {};
      if (filterQ) params.q = filterQ;
      if (filterAction) params.action = filterAction;
      if (filterEntityType) params.entity_type = filterEntityType;
      const data = await api.getAuditEvents(params);
      setEvents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit events');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadEvents();
  };

  return (
    <div className="audit-container">
      <header className="audit-header">
        <h1>Audit Log</h1>
      </header>

      <div className="audit-filters">
        <form onSubmit={handleSearch}>
          <div className="filter-row">
            <div className="filter-group">
              <label>Search (q)</label>
              <input
                type="text"
                value={filterQ}
                onChange={(e) => setFilterQ(e.target.value)}
                placeholder="Search..."
              />
            </div>
            <div className="filter-group">
              <label>Action</label>
              <input
                type="text"
                value={filterAction}
                onChange={(e) => setFilterAction(e.target.value)}
                placeholder="e.g. EVIDENCE_CREATED"
              />
            </div>
            <div className="filter-group">
              <label>Entity Type</label>
              <input
                type="text"
                value={filterEntityType}
                onChange={(e) => setFilterEntityType(e.target.value)}
                placeholder="e.g. Control, EvidenceItem"
              />
            </div>
            <div className="filter-actions">
              <button type="submit" className="btn-primary">
                Search
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => {
                  setFilterQ('');
                  setFilterAction('');
                  setFilterEntityType('');
                  setTimeout(loadEvents, 0);
                }}
              >
                Reset
              </button>
            </div>
          </div>
        </form>
      </div>

      {loading && <div className="loading">Loading audit events...</div>}
      {error && <div className="error">Error: {error}</div>}

      {!loading && !error && (
        <div className="audit-table-wrapper">
          <table className="audit-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Entity Type</th>
                <th>Entity ID</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {events.length === 0 ? (
                <tr>
                  <td colSpan={6} className="muted">
                    No audit events found.
                  </td>
                </tr>
              ) : (
                events.map((e) => (
                  <tr key={e.id}>
                    <td className="audit-time">{e.created_at ? new Date(e.created_at).toLocaleString() : '-'}</td>
                    <td>{e.actor || '-'}</td>
                    <td>{e.action}</td>
                    <td>{e.entity_type}</td>
                    <td className="audit-entity-id">{e.entity_id}</td>
                    <td>{e.summary}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Audit;
