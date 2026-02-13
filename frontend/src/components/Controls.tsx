import React, { useEffect, useRef, useState } from 'react';
import { api, type Control, type ControlNote, type ControlStatus, type ControlTimeline, type ExportJob } from '../api';
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

  const [controlStatus, setControlStatus] = useState<ControlStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);

  const [exports, setExports] = useState<ExportJob[]>([]);
  const [exportsLoading, setExportsLoading] = useState(false);
  const [exportsError, setExportsError] = useState<string | null>(null);
  const [lastDownloadUrl, setLastDownloadUrl] = useState<string | null>(null);

  const [verificationRemarks, setVerificationRemarks] = useState('');
  const [actionBusy, setActionBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const [evidenceTitle, setEvidenceTitle] = useState('');
  const [evidenceCategory, setEvidenceCategory] = useState('');
  const [evidenceDate, setEvidenceDate] = useState('');
  const [evidenceNotes, setEvidenceNotes] = useState('');
  const [evidenceFiles, setEvidenceFiles] = useState<File[]>([]);
  const [evidenceSubmitting, setEvidenceSubmitting] = useState(false);
  const [evidenceSubmitError, setEvidenceSubmitError] = useState<string | null>(null);
  const [evidenceSubmitSuccess, setEvidenceSubmitSuccess] = useState<string | null>(null);
  const [notes, setNotes] = useState<ControlNote[]>([]);
  const [notesLoading, setNotesLoading] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [noteType, setNoteType] = useState<'INTERNAL' | 'INSPECTION' | 'CORRECTIVE_ACTION'>('INTERNAL');
  const [notesError, setNotesError] = useState<string | null>(null);
  const [noteModalOpen, setNoteModalOpen] = useState(false);
  const noteModalRef = useRef<HTMLDivElement | null>(null);
  const addNoteButtonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    loadControls();
  }, []);

  useEffect(() => {
    if (!noteModalOpen) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const focusables = noteModalRef.current?.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    );
    focusables?.[0]?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        setNoteModalOpen(false);
      }
      if (event.key === 'Tab' && focusables && focusables.length > 0) {
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      (previouslyFocused || addNoteButtonRef.current)?.focus();
    };
  }, [noteModalOpen]);

  const getStatusBadge = (status: string) => {
    const statusClasses: Record<string, string> = {
      NOT_STARTED: 'status-not-started',
      IN_PROGRESS: 'status-in-progress',
      READY: 'status-ready',
      VERIFIED: 'status-verified',
      OVERDUE: 'status-overdue',
    };
    return <span className={`status-badge ${statusClasses[status] || ''}`}>{status.replace('_', ' ')}</span>;
  };

  const loadControls = async (section?: string, q?: string): Promise<Control[]> => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getControls({ section, q });
      setControls(data);

      const uniqueSections = Array.from(new Set(data.map((c) => c.section))).sort();
      setSections(uniqueSections);

      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load controls');
      return [];
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

  const loadControlStatus = async (controlId: number) => {
    try {
      setStatusLoading(true);
      setStatusError(null);
      const data = await api.getControlStatus(controlId);
      setControlStatus(data);
    } catch (err) {
      setStatusError(err instanceof Error ? err.message : 'Failed to load control status');
    } finally {
      setStatusLoading(false);
    }
  };

  const loadControlExports = async (controlId: number) => {
    try {
      setExportsLoading(true);
      setExportsError(null);
      const data = await api.listControlExports(controlId);
      setExports(data.slice(0, 5));
    } catch (err) {
      setExportsError(err instanceof Error ? err.message : 'Failed to load exports');
    } finally {
      setExportsLoading(false);
    }
  };

  const loadControlNotes = async (controlId: number) => {
    try {
      setNotesLoading(true);
      setNotesError(null);
      const data = await api.getControlNotes(controlId);
      setNotes(data);
    } catch (err) {
      setNotesError(err instanceof Error ? err.message : 'Failed to load notes');
    } finally {
      setNotesLoading(false);
    }
  };

  const refreshSelectedControlRow = async (controlId: number) => {
    const data = await loadControls(sectionFilter || undefined, searchQuery || undefined);
    const match = data.find((c) => c.id === controlId);
    if (match) {
      setSelectedControl(match);
    }
  };

  const refreshSelectedControlData = async (controlId: number) => {
    await Promise.all([
      loadTimeline(controlId),
      loadControlStatus(controlId),
      loadControlExports(controlId),
      loadControlNotes(controlId),
      refreshSelectedControlRow(controlId),
    ]);
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
    setActionError(null);
    setActionSuccess(null);
    setLastDownloadUrl(null);
    refreshSelectedControlData(control.id);
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

      await refreshSelectedControlData(selectedControl.id);
    } catch (err) {
      setEvidenceSubmitError(err instanceof Error ? err.message : 'Failed to create evidence');
    } finally {
      setEvidenceSubmitting(false);
    }
  };

  const handleVerify = async (kind: 'verify' | 'reject') => {
    if (!selectedControl) return;

    try {
      setActionBusy(true);
      setActionError(null);
      setActionSuccess(null);

      if (kind === 'verify') {
        await api.verifyControl(selectedControl.id, verificationRemarks || undefined);
        setActionSuccess('Control marked as VERIFIED.');
      } else {
        await api.rejectControl(selectedControl.id, verificationRemarks || undefined);
        setActionSuccess('Control marked as REJECTED.');
      }

      await refreshSelectedControlData(selectedControl.id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Verification action failed');
    } finally {
      setActionBusy(false);
    }
  };

  const handleCreateExport = async () => {
    if (!selectedControl) return;

    try {
      setActionBusy(true);
      setActionError(null);
      setActionSuccess(null);

      const response = await api.createControlExport(selectedControl.id);
      setLastDownloadUrl(response.download.url);
      setActionSuccess('Control PDF export generated successfully.');
      await refreshSelectedControlData(selectedControl.id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setActionBusy(false);
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

  const handleDownloadExport = async (jobId: string) => {
    try {
      const data = await api.downloadExport(jobId);
      window.open(data.url, '_blank', 'noopener,noreferrer');
    } catch (err) {
      setExportsError(err instanceof Error ? err.message : 'Failed to download export');
    }
  };

  const handleCreateNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedControl) return;
    if (!noteText.trim()) {
      setNotesError('Note text is required.');
      return;
    }

    try {
      setNotesError(null);
      await api.createControlNote(selectedControl.id, { note_type: noteType, text: noteText.trim() });
      setNoteText('');
      setNoteModalOpen(false);
      await loadControlNotes(selectedControl.id);
    } catch (err) {
      setNotesError(err instanceof Error ? err.message : 'Failed to create note');
    }
  };

  const handleToggleResolved = async (note: ControlNote) => {
    if (!selectedControl) return;
    try {
      setNotesError(null);
      await api.updateControlNote(selectedControl.id, note.id, { resolved: !note.resolved });
      await loadControlNotes(selectedControl.id);
    } catch (err) {
      setNotesError(err instanceof Error ? err.message : 'Failed to update note');
    }
  };

  const handleDeleteNote = async (noteId: string) => {
    if (!selectedControl) return;
    try {
      setNotesError(null);
      await api.deleteControlNote(selectedControl.id, noteId);
      await loadControlNotes(selectedControl.id);
    } catch (err) {
      setNotesError(err instanceof Error ? err.message : 'Failed to delete note');
    }
  };

  const statusLabel = controlStatus?.computed_status || selectedControl?.status || 'NOT_STARTED';
  const noteTypeLabel = (type: ControlNote['note_type']) => {
    if (type === 'CORRECTIVE_ACTION') return 'Corrective Action';
    if (type === 'INSPECTION') return 'Inspection';
    return 'Internal';
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
              <select value={sectionFilter} onChange={(e) => setSectionFilter(e.target.value)}>
                <option value="">All Sections</option>
                {sections.map((section) => (
                  <option key={section} value={section}>
                    {section}
                  </option>
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
              <button type="submit" className="btn-primary">
                Search
              </button>
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
                {controls.map((control) => (
                  <tr
                    key={control.id}
                    className={selectedControl?.id === control.id ? 'selected-row' : ''}
                    role="button"
                    tabIndex={0}
                    aria-label={`Open ${control.control_code}`}
                    onClick={() => handleSelectControl(control)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleSelectControl(control);
                      }
                    }}
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
                setControlStatus(null);
                setExports([]);
                setActionError(null);
                setActionSuccess(null);
                setLastDownloadUrl(null);
                setNotes([]);
                setNotesError(null);
                setNoteModalOpen(false);
              }}
            >
              Close
            </button>
          </div>

          <div className="control-status-row">
            <div>
              <strong>Status:</strong> {getStatusBadge(statusLabel)}
            </div>
            <div>
              <strong>Last evidence:</strong> {controlStatus?.last_evidence_date || selectedControl.last_evidence_date || '-'}
            </div>
            <div>
              <strong>Next due:</strong> {controlStatus?.next_due_date || selectedControl.next_due_date || '-'}
            </div>
          </div>
          {statusLoading && <div className="loading">Refreshing status...</div>}
          {statusError && <div className="error-banner">{statusError}</div>}

          <div className="action-panel">
            <h4 className="panel-title">Verification Actions</h4>
            <div className="form-group">
              <label>Verification Remarks (optional)</label>
              <textarea
                value={verificationRemarks}
                onChange={(e) => setVerificationRemarks(e.target.value)}
                placeholder="Remarks for verification or rejection"
              />
            </div>
            <div className="action-buttons">
              <button type="button" className="btn-primary" disabled={actionBusy} onClick={() => handleVerify('verify')}>
                Mark Verified
              </button>
              <button type="button" className="btn-secondary" disabled={actionBusy} onClick={() => handleVerify('reject')}>
                Reject
              </button>
              <button type="button" className="btn-primary" disabled={actionBusy} onClick={handleCreateExport}>
                Generate Control PDF
              </button>
              {lastDownloadUrl && (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => window.open(lastDownloadUrl, '_blank', 'noopener,noreferrer')}
                >
                  Download PDF
                </button>
              )}
            </div>
            {actionError && <div className="error-banner">{actionError}</div>}
            {actionSuccess && <div className="success-banner">{actionSuccess}</div>}
          </div>

          <div className="exports-panel">
            <h3>Recent Exports</h3>
            {exportsLoading && <div className="loading">Loading exports...</div>}
            {exportsError && <div className="error-banner">{exportsError}</div>}
            {!exportsLoading && !exportsError && (
              <ul className="export-list">
                {exports.length > 0 ? (
                  exports.map((job) => (
                    <li key={job.id}>
                      <span>
                        {new Date(job.created_at).toLocaleString()} - {job.status}
                      </span>
                      <button type="button" className="btn-secondary btn-small" onClick={() => handleDownloadExport(job.id)}>
                        Download
                      </button>
                    </li>
                  ))
                ) : (
                  <li className="muted">No exports yet.</li>
                )}
              </ul>
            )}
          </div>

          <div className="exports-panel">
            <h3>Control Notes</h3>
            <button
              type="button"
              className="btn-primary"
              ref={addNoteButtonRef}
              onClick={() => setNoteModalOpen(true)}
              style={{ marginBottom: '1rem' }}
            >
              Add Note
            </button>
            {notesLoading && <div className="loading">Loading notes...</div>}
            {notesError && <div className="error-banner">{notesError}</div>}
            {!notesLoading && (
              <ul className="export-list">
                {notes.length ? (
                  notes.map((note) => (
                    <li key={note.id}>
                      <span className="note-copy">
                        <span className="note-meta">
                          <span className="note-type">{noteTypeLabel(note.note_type)}</span>
                          <span className={`note-state ${note.resolved ? 'resolved' : 'open'}`}>
                            {note.resolved ? 'Resolved' : 'Open'}
                          </span>
                          <span>{new Date(note.created_at).toLocaleString()}</span>
                        </span>
                        <span>{note.text}</span>
                      </span>
                      <div>
                        <button type="button" className="btn-secondary btn-small" onClick={() => handleToggleResolved(note)}>
                          {note.resolved ? 'Reopen' : 'Resolve'}
                        </button>
                        <button
                          type="button"
                          className="btn-secondary btn-small"
                          onClick={() => handleDeleteNote(note.id)}
                          style={{ marginLeft: '0.35rem' }}
                        >
                          Delete
                        </button>
                      </div>
                    </li>
                  ))
                ) : (
                  <li className="muted">No notes added.</li>
                )}
              </ul>
            )}
          </div>

          {noteModalOpen && (
            <div className="modal-overlay">
              <div className="modal-card" ref={noteModalRef} role="dialog" aria-modal="true" aria-labelledby="note-dialog-title">
                <h3 id="note-dialog-title">Add Note</h3>
                <form onSubmit={handleCreateNote} className="form-group">
                  <label>Note Type</label>
                  <select
                    value={noteType}
                    onChange={(e) => setNoteType(e.target.value as 'INTERNAL' | 'INSPECTION' | 'CORRECTIVE_ACTION')}
                  >
                    <option value="INTERNAL">Internal</option>
                    <option value="INSPECTION">Inspection</option>
                    <option value="CORRECTIVE_ACTION">Corrective Action</option>
                  </select>
                  <label style={{ marginTop: '0.5rem' }}>Note Text</label>
                  <textarea
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    placeholder="Add control-level note"
                  />
                  <div className="action-buttons" style={{ marginTop: '0.75rem' }}>
                    <button type="submit" className="btn-primary">Save Note</button>
                    <button type="button" className="btn-secondary" onClick={() => setNoteModalOpen(false)}>
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

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
                  <select value={evidenceCategory} onChange={(e) => setEvidenceCategory(e.target.value)}>
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
                  <input type="date" value={evidenceDate} onChange={(e) => setEvidenceDate(e.target.value)} />
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
                  <input type="file" multiple onChange={(e) => setEvidenceFiles(Array.from(e.target.files || []))} />
                </div>
                <button type="submit" className="btn-primary" disabled={evidenceSubmitting} style={{ width: '100%', marginTop: '1rem' }}>
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
                      {timeline.evidence_items.map((link) => (
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
                          {link.evidence_item.notes && <p className="evidence-notes">{link.evidence_item.notes}</p>}
                          <div className="evidence-files">
                            {link.evidence_item.files?.length ? (
                              <ul>
                                {link.evidence_item.files.map((file) => (
                                  <li key={file.id}>
                                    <span style={{ fontSize: '0.875rem', color: 'var(--text)' }}>{file.filename}</span>
                                    <button type="button" className="btn-secondary btn-small" onClick={() => handleDownloadFile(file.id)}>
                                      Download
                                    </button>
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <div className="muted" style={{ fontSize: '0.875rem' }}>
                                No files uploaded.
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="muted" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
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
