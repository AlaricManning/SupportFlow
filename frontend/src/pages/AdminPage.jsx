import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ticketService, statsService } from '../services/api';
import { formatDistanceToNow } from 'date-fns';
import './AdminPage.css';

function AdminPage() {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState(null);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [ticketsData, statsData] = await Promise.all([
        ticketService.getTickets(statusFilter),
        statsService.getStats(),
      ]);
      setTickets(ticketsData);
      setStats(statsData);
      setError(null);
    } catch (err) {
      setError('Failed to load data. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadgeClass = (status) => {
    const classes = {
      new: 'badge-new',
      in_progress: 'badge-progress',
      waiting_human: 'badge-waiting',
      resolved: 'badge-resolved',
      closed: 'badge-closed',
    };
    return classes[status] || 'badge-default';
  };

  const getPriorityBadgeClass = (priority) => {
    const classes = {
      low: 'badge-priority-low',
      medium: 'badge-priority-medium',
      high: 'badge-priority-high',
      urgent: 'badge-priority-urgent',
    };
    return classes[priority] || 'badge-default';
  };

  const formatStatus = (status) => {
    return status.replace('_', ' ').toUpperCase();
  };

  if (loading && !tickets.length) {
    return (
      <div className="admin-page">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Admin Dashboard</h1>
        <button onClick={loadData} className="btn btn-refresh">
          Refresh
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.total_tickets}</div>
            <div className="stat-label">Total Tickets</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.average_confidence.toFixed(2)}</div>
            <div className="stat-label">Avg Confidence</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.escalation_rate_percent.toFixed(1)}%</div>
            <div className="stat-label">Escalation Rate</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">
              {Object.keys(stats.top_intents).length}
            </div>
            <div className="stat-label">Intent Types</div>
          </div>
        </div>
      )}

      <div className="filters">
        <label>Filter by Status:</label>
        <select
          value={statusFilter || ''}
          onChange={(e) => setStatusFilter(e.target.value || null)}
          className="filter-select"
        >
          <option value="">All Statuses</option>
          <option value="new">New</option>
          <option value="in_progress">In Progress</option>
          <option value="waiting_human">Waiting Human</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      <div className="tickets-section">
        <h2>Support Tickets ({tickets.length})</h2>

        {tickets.length === 0 ? (
          <div className="empty-state">
            <p>No tickets found.</p>
          </div>
        ) : (
          <div className="tickets-table">
            <table>
              <thead>
                <tr>
                  <th>Ticket #</th>
                  <th>Customer</th>
                  <th>Subject</th>
                  <th>Intent</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Confidence</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((ticket) => (
                  <tr key={ticket.id}>
                    <td className="ticket-number">{ticket.ticket_number}</td>
                    <td>
                      <div className="customer-info">
                        <div className="customer-name">{ticket.customer_name}</div>
                        <div className="customer-email">{ticket.customer_email}</div>
                      </div>
                    </td>
                    <td className="ticket-subject">{ticket.subject}</td>
                    <td>
                      {ticket.intent ? (
                        <span className="intent-badge">
                          {ticket.intent.replace('_', ' ')}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td>
                      <span className={`badge ${getPriorityBadgeClass(ticket.priority)}`}>
                        {ticket.priority}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${getStatusBadgeClass(ticket.status)}`}>
                        {formatStatus(ticket.status)}
                      </span>
                    </td>
                    <td>
                      <div className="confidence-score">
                        {ticket.confidence ? (
                          <>
                            <div className="confidence-bar">
                              <div
                                className="confidence-fill"
                                style={{ width: `${ticket.confidence * 100}%` }}
                              />
                            </div>
                            <span>{(ticket.confidence * 100).toFixed(0)}%</span>
                          </>
                        ) : (
                          '-'
                        )}
                      </div>
                    </td>
                    <td className="ticket-date">
                      {formatDistanceToNow(new Date(ticket.created_at), {
                        addSuffix: true,
                      })}
                    </td>
                    <td>
                      <button
                        onClick={() => navigate(`/ticket/${ticket.id}`)}
                        className="btn btn-small btn-view"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {stats && stats.agent_performance && (
        <div className="agent-performance">
          <h2>Agent Performance</h2>
          <div className="performance-grid">
            {Object.entries(stats.agent_performance).map(([agent, perf]) => (
              <div key={agent} className="performance-card">
                <h3>{agent}</h3>
                <div className="perf-stat">
                  <span className="perf-label">Avg Execution:</span>
                  <span className="perf-value">{perf.avg_execution_time_ms}ms</span>
                </div>
                <div className="perf-stat">
                  <span className="perf-label">Total Runs:</span>
                  <span className="perf-value">{perf.total_executions}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminPage;
