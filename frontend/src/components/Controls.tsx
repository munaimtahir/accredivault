import React, { useEffect, useState } from 'react';
import { api, type Control } from '../api';
import './Controls.css';

const Controls: React.FC = () => {
  const [controls, setControls] = useState<Control[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sectionFilter, setSectionFilter] = useState('');
  const [sections, setSections] = useState<string[]>([]);

  useEffect(() => {
    loadControls();
  }, []);

  const loadControls = async (section?: string, q?: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getControls({ section, q });
      setControls(data);
      
      // Extract unique sections
      const uniqueSections = Array.from(new Set(data.map(c => c.section))).sort();
      setSections(uniqueSections);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load controls');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadControls(sectionFilter || undefined, searchQuery || undefined);
  };

  const handleReset = () => {
    setSearchQuery('');
    setSectionFilter('');
    loadControls();
  };

  const getStatusBadge = (status: string) => {
    const statusClasses: Record<string, string> = {
      'NOT_STARTED': 'status-not-started',
      'IN_PROGRESS': 'status-in-progress',
      'READY': 'status-ready',
      'VERIFIED': 'status-verified',
      'OVERDUE': 'status-overdue',
    };
    return (
      <span className={`status-badge ${statusClasses[status] || ''}`}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className="controls-container">
      <header className="controls-header">
        <h1>AccrediVault - PHC Controls</h1>
        <p>Primary Healthcare Lab Licensing Checklist</p>
      </header>

      <div className="controls-filters">
        <form onSubmit={handleSearch}>
          <div className="filter-row">
            <div className="filter-group">
              <label>Section</label>
              <select
                value={sectionFilter}
                onChange={(e) => setSectionFilter(e.target.value)}
              >
                <option value="">All Sections</option>
                {sections.map(section => (
                  <option key={section} value={section}>{section}</option>
                ))}
              </select>
            </div>
            <div className="filter-group">
              <label>Search</label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search controls..."
              />
            </div>
            <div className="filter-actions">
              <button type="submit" className="btn-primary">Search</button>
              <button type="button" onClick={handleReset} className="btn-secondary">
                Reset
              </button>
            </div>
          </div>
        </form>
      </div>

      {loading && <div className="loading">Loading controls...</div>}
      {error && <div className="error">Error: {error}</div>}

      {!loading && !error && (
        <>
          <div className="controls-summary">
            <strong>Total Controls:</strong> {controls.length}
          </div>
          <div className="controls-table-wrapper">
            <table className="controls-table">
              <thead>
                <tr>
                  <th>Control Code</th>
                  <th>Section</th>
                  <th>Indicator</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {controls.map(control => (
                  <tr key={control.id}>
                    <td className="control-code">{control.control_code}</td>
                    <td>{control.section}</td>
                    <td className="indicator">{control.indicator}</td>
                    <td>{getStatusBadge(control.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

export default Controls;
