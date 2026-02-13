import React, { useEffect, useState } from 'react';
import { api, type ComplianceAlert, type DashboardSummary } from '../api';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [alerts, setAlerts] = useState<ComplianceAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionBusy, setActionBusy] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionMessageKind, setActionMessageKind] = useState<'success' | 'error'>('success');

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const [summaryData, alertsData] = await Promise.all([api.getDashboardSummary(), api.getAlerts()]);
      setSummary(summaryData);
      setAlerts(alertsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const handleFullExport = async () => {
    try {
      setActionBusy(true);
      setActionMessage(null);
      const result = await api.createFullExport();
      window.open(result.download.url, '_blank', 'noopener,noreferrer');
      setActionMessage('Full pack export generated.');
      setActionMessageKind('success');
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Failed to export full pack');
      setActionMessageKind('error');
    } finally {
      setActionBusy(false);
    }
  };

  const handleSectionExport = async (sectionCode: string) => {
    try {
      setActionBusy(true);
      setActionMessage(null);
      const result = await api.createSectionExport(sectionCode);
      window.open(result.download.url, '_blank', 'noopener,noreferrer');
      setActionMessage(`Section ${sectionCode} export generated.`);
      setActionMessageKind('success');
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Failed to export section');
      setActionMessageKind('error');
    } finally {
      setActionBusy(false);
    }
  };

  if (loading) {
    return <div className="dashboard-shell">Loading dashboard...</div>;
  }

  if (error || !summary) {
    return (
      <div className="dashboard-shell">
        <div className="dashboard-error">{error || 'No dashboard data available.'}</div>
      </div>
    );
  }

  const counters = [
    ['Total', summary.totals.total_controls],
    ['Not Started', summary.totals.NOT_STARTED],
    ['In Progress', summary.totals.IN_PROGRESS],
    ['Ready', summary.totals.READY],
    ['Verified', summary.totals.VERIFIED],
    ['Overdue', summary.totals.OVERDUE],
    ['Near Due', summary.totals.NEAR_DUE],
  ];

  return (
    <div className="dashboard-shell">
      <div className="dashboard-header">
        <div>
          <h1>Compliance Dashboard</h1>
          <p>Pack v{summary.pack_version}</p>
        </div>
        <div className="dashboard-actions">
          <button className="btn-secondary" onClick={loadDashboard} disabled={actionBusy}>Refresh</button>
          <button className="btn-primary" onClick={handleFullExport} disabled={actionBusy}>Export Full Pack</button>
        </div>
      </div>

      {actionMessage && <div className={`dashboard-message ${actionMessageKind}`}>{actionMessage}</div>}

      <div className="counter-grid">
        {counters.map(([label, value]) => (
          <div key={label} className="counter-card">
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>

      <div className="dashboard-grid">
        <section className="dashboard-card">
          <h2>Section Breakdown</h2>
          <div className="dashboard-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Section</th>
                  <th>Total</th>
                  <th>Ready</th>
                  <th>Verified</th>
                  <th>Overdue</th>
                  <th>Export</th>
                </tr>
              </thead>
              <tbody>
                {summary.sections.map((row) => (
                  <tr key={row.section_code}>
                    <td>{row.section_code}</td>
                    <td>{row.total}</td>
                    <td>{row.READY}</td>
                    <td>{row.VERIFIED}</td>
                    <td><span className="alert-pill overdue-count">{row.OVERDUE}</span></td>
                    <td>
                      <button className="btn-secondary btn-small" onClick={() => handleSectionExport(row.section_code)} disabled={actionBusy}>
                        Export Section
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="dashboard-card">
          <h2>Upcoming Due</h2>
          <ul className="simple-list">
            {summary.upcoming_due.length === 0 && <li>No upcoming due controls.</li>}
            {summary.upcoming_due.map((item) => (
              <li key={item.control_id}>
                <strong>{item.control_code}</strong> - {item.section_code} - {item.next_due_date}
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="dashboard-card">
        <h2>Active Alerts</h2>
        <ul className="simple-list">
          {alerts.length === 0 && <li>No active alerts.</li>}
          {alerts.map((alert) => (
            <li key={alert.id}>
              <span className={`alert-pill ${alert.alert_type === 'OVERDUE' ? 'overdue' : 'near-due'}`}>{alert.alert_type}</span>{' '}
              <strong>{alert.control_code}</strong> - {new Date(alert.triggered_at).toLocaleString()}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};

export default Dashboard;
