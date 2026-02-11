import React, { useEffect, useState } from 'react';
import { api, type Control, type ControlTimeline } from '../api';
import './Controls.css';

const Controls: React.FC = () => {
  const [controls, setControls] = useState<Control[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sectionFilter, setSectionFilter] = useState('');
  const [sections, setSections] = useState<string[]>([]);
  const [selectedControl, setSelectedControl] = useState<Control | null>(null);
  const [timeline, setTimeline] = useState<ControlTimeline | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineError, setTimelineError] = useState<string | null>(null);

  const [evidenceTitle, setEvidenceTitle] = useState('');
  const [evidenceCategory, setEvidenceCategory] = useState('');
  const [evidenceDate, setEvidenceDate] = useState('');
  const [evidenceNotes, setEvidenceNotes] = useState('');
  const [evidenceFiles, setEvidenceFiles] = useState<File[]>([]);
  const [evidenceSubmitting, setEvidenceSubmitting] = useState(false);
  const [evidenceSubmitError, setEvidenceSubmitError] = useState<string | null>(null);
  const [evidenceSubmitSuccess, setEvidenceSubmitSuccess] = useState<string | null>(null);

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

  const loadTimeline = async (controlId: number) => {
    try {
      setTimelineLoading(true);
      setTimelineError(null);
      const data = await api.getControlTimeline(controlId);
      setTimeline(data);
    } catch (err) {
      setTimelineError(err instanceof Error ? err.message : 'Failed to load evidence timeline');
    } finally {
      setTimelineLoading(false);
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

  const handleSelectControl = (control: Control) => {
    setSelectedControl(control);
    loadTimeline(control.id);
  };

  const handleCreateEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedControl) return;
    if (!evidenceTitle || !evidenceCategory || !evidenceDate) {
      setEvidenceSubmitError('Title, category, and date are required.');
      return;
    }

    try {
      setEvidenceSubmitting(true);
      setEvidenceSubmitError(null);
      setEvidenceSubmitSuccess(null);

      const evidence = await api.createEvidenceItem({
        title: evidenceTitle,
        category: evidenceCategory,
        event_date: evidenceDate,
        notes: evidenceNotes || undefined,
      });

      await api.linkEvidenceToControl(selectedControl.id, evidence.id);

      if (evidenceFiles.length > 0) {
        await api.uploadEvidenceFiles(evidence.id, evidenceFiles);
      }

      setEvidenceTitle('');
      setEvidenceCategory('');
      setEvidenceDate('');
      setEvidenceNotes('');
      setEvidenceFiles([]);
      setEvidenceSubmitSuccess('Evidence created and linked.');

      await loadTimeline(selectedControl.id);
    } catch (err) {
      setEvidenceSubmitError(err instanceof Error ? err.message : 'Failed to create evidence');
    } finally {
      setEvidenceSubmitting(false);
    }
  };

  const handleDownloadFile = async (fileId: string) => {
    try {
      const data = await api.downloadEvidenceFile(fileId);
      window.open(data.url, '_blank', 'noopener,noreferrer');
    } catch (err) {
      setTimelineError(err instanceof Error ? err.message : 'Failed to download file');
    }
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
                  <tr
                    key={control.id}
                    className={selectedControl?.id === control.id ? 'selected-row' : ''}
                    onClick={() => handleSelectControl(control)}
                  >
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

      {selectedControl && (
        <div className="control-detail">
          <div className="control-detail-header">
            <div>
              <h2>{selectedControl.control_code} Evidence</h2>
              <p>{selectedControl.indicator}</p>
            </div>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => {
                setSelectedControl(null);
                setTimeline(null);
                setTimelineError(null);
              }}
            >
              Close
            </button>
          </div>

          <div className="evidence-grid">
            <div className="evidence-form">
              <h3>Create Evidence</h3>
              <form onSubmit={handleCreateEvidence}>
                <div className="form-group">
                  <label>Title</label>
                  <input
                    type="text"
                    value={evidenceTitle}
                    onChange={(e) => setEvidenceTitle(e.target.value)}
                    placeholder="e.g., Calibration Certificate"
                  />
                </div>
                <div className="form-group">
                  <label>Category</label>
                  <select
                    value={evidenceCategory}
                    onChange={(e) => setEvidenceCategory(e.target.value)}
                  >
                    <option value="">Select Category</option>
                    <option value="policy">Policy</option>
                    <option value="procedure">Procedure</option>
                    <option value="certificate">Certificate</option>
                    <option value="log">Log</option>
                    <option value="photo">Photo</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Event Date</label>
                  <input
                    type="date"
                    value={evidenceDate}
                    onChange={(e) => setEvidenceDate(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Notes</label>
                  <textarea
                    value={evidenceNotes}
                    onChange={(e) => setEvidenceNotes(e.target.value)}
                    placeholder="Optional notes"
                  />
                </div>
                <div className="form-group">
                  <label>Files</label>
                  <input
                    type="file"
                    multiple
                    onChange={(e) => setEvidenceFiles(Array.from(e.target.files || []))}
                  />
                </div>
                <button 
                  type="submit" 
                  className="btn-primary" 
                  disabled={evidenceSubmitting}
                  style={{ width: '100%', marginTop: '1rem' }}
                >
                  {evidenceSubmitting ? 'Creating...' : 'Create Evidence'}
                </button>
                {evidenceSubmitError && <div className="error-banner">{evidenceSubmitError}</div>}
                {evidenceSubmitSuccess && <div className="success-banner">{evidenceSubmitSuccess}</div>}
              </form>
            </div>

            <div className="evidence-list">
              <h3>Evidence Timeline</h3>
              {timelineLoading && <div className="loading">Loading timeline...</div>}
              {timelineError && <div className="error-banner">{timelineError}</div>}

              {!timelineLoading && !timelineError && (
                <>
                  {timeline?.evidence_items?.length ? (
                    <div className="evidence-cards">
                      {timeline.evidence_items.map(link => (
                        <div key={link.id} className="evidence-card animate-fade-in">
                          <div className="evidence-card-header">
                            <div>
                              <div className="evidence-title">{link.evidence_item.title}</div>
                              <div className="evidence-meta">
                                <span className="status-badge" style={{ padding: '2px 8px', fontSize: '0.7rem', marginRight: '8px' }}>
                                  {link.evidence_item.category}
                                </span>
                                <span>{link.evidence_item.event_date}</span>
                              </div>
                            </div>
                          </div>
                          {link.evidence_item.notes && (
                            <p className="evidence-notes">{link.evidence_item.notes}</p>
                          )}
                          <div className="evidence-files">
                            {link.evidence_item.files?.length ? (
                              <ul>
                                {link.evidence_item.files.map(file => (
                                  <li key={file.id}>
                                    <span style={{ fontSize: '0.875rem', color: 'var(--text)' }}>
                                      📄 {file.filename}
                                    </span>
                                    <button
                                      type="button"
                                      className="btn-secondary btn-small"
                                      onClick={() => handleDownloadFile(file.id)}
                                    >
                                      Download
                                    </button>
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <div className="muted" style={{ fontSize: '0.875rem' }}>No files uploaded.</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="muted" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                      <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📂</div>
                      <p>No evidence linked yet.</p>
                      <p style={{ fontSize: '0.875rem' }}>Upload your first piece of evidence using the form.</p>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Controls;
