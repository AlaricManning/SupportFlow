import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ticketService } from '../services/api';
import { format } from 'date-fns';
import './TicketDetailPage.css';

function TicketDetailPage() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedTrace, setExpandedTrace] = useState(null);

  useEffect(() => {
    loadTicket();
  }, [ticketId]);

  const loadTicket = async () => {
    try {
      setLoading(true);
      const data = await ticketService.getTicket(ticketId);
      setTicket(data);
      setError(null);
    } catch (err) {
      setError('Failed to load ticket. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const approveResponse = async () => {
    try {
      await ticketService.updateTicket(ticketId, {
        response_approved: true,
        status: 'resolved',
      });
      await loadTicket();
    } catch (err) {
      alert('Failed to approve response');
    }
  };

  const toggleTrace = (traceId) => {
    setExpandedTrace(expandedTrace === traceId ? null : traceId);
  };

  if (loading) {
    return (
      <div className="ticket-detail-page">
        <div className="loading">Loading ticket...</div>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="ticket-detail-page">
        <div className="error-message">{error || 'Ticket not found'}</div>
        <button onClick={() => navigate('/admin')} className="btn btn-back">
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="ticket-detail-page">
      <button onClick={() => navigate('/admin')} className="btn btn-back">
        ← Back to Dashboard
      </button>

      <div className="ticket-header">
        <div>
          <h1>Ticket {ticket.ticket_number}</h1>
          <p className="ticket-meta">
            Created {format(new Date(ticket.created_at), 'PPpp')}
          </p>
        </div>
        <div className="header-badges">
          <span className={`badge status-${ticket.status}`}>
            {ticket.status.replace('_', ' ').toUpperCase()}
          </span>
          <span className={`badge priority-${ticket.priority}`}>
            {ticket.priority.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="content-grid">
        <div className="main-column">
          <div className="card">
            <h2>Customer Information</h2>
            <div className="info-row">
              <span className="label">Name:</span>
              <span className="value">{ticket.customer_name}</span>
            </div>
            <div className="info-row">
              <span className="label">Email:</span>
              <span className="value">{ticket.customer_email}</span>
            </div>
            {ticket.order_id && (
              <div className="info-row">
                <span className="label">Order ID:</span>
                <span className="value">{ticket.order_id}</span>
              </div>
            )}
          </div>

          <div className="card">
            <h2>Ticket Details</h2>
            <div className="info-row">
              <span className="label">Subject:</span>
              <span className="value">{ticket.subject}</span>
            </div>
            <div className="message-box">
              <strong>Message:</strong>
              <p>{ticket.message}</p>
            </div>
            {ticket.intent && (
              <div className="info-row">
                <span className="label">Detected Intent:</span>
                <span className="value intent-value">{ticket.intent.replace('_', ' ')}</span>
              </div>
            )}
            {ticket.confidence !== null && (
              <div className="info-row">
                <span className="label">Confidence:</span>
                <span className="value">
                  <div className="confidence-display">
                    <div className="confidence-bar-large">
                      <div
                        className="confidence-fill"
                        style={{ width: `${ticket.confidence * 100}%` }}
                      />
                    </div>
                    <span className="confidence-percent">
                      {(ticket.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </span>
              </div>
            )}
          </div>

          {ticket.ai_response && (
            <div className="card response-card">
              <h2>AI-Generated Response</h2>
              <div className="response-box">
                <p>{ticket.ai_response}</p>
              </div>
              {!ticket.response_approved && ticket.status === 'waiting_human' && (
                <div className="response-actions">
                  <button onClick={approveResponse} className="btn btn-approve">
                    ✓ Approve & Send Response
                  </button>
                  <p className="action-note">
                    This ticket requires human review before sending the response.
                  </p>
                </div>
              )}
              {ticket.response_approved && (
                <div className="approved-badge">
                  ✓ Response Approved
                </div>
              )}
            </div>
          )}
        </div>

        <div className="sidebar-column">
          <div className="card traces-card">
            <h2>Agent Execution Traces</h2>
            <p className="traces-subtitle">
              View how each AI agent processed this ticket
            </p>

            {ticket.agent_traces && ticket.agent_traces.length > 0 ? (
              <div className="traces-list">
                {ticket.agent_traces.map((trace) => (
                  <div key={trace.id} className="trace-item">
                    <div
                      className="trace-header"
                      onClick={() => toggleTrace(trace.id)}
                    >
                      <div className="trace-title">
                        <span className="trace-step">{trace.step_number}</span>
                        <span className="trace-agent">{trace.agent_name}</span>
                      </div>
                      <div className="trace-time">{trace.execution_time_ms}ms</div>
                    </div>

                    {expandedTrace === trace.id && (
                      <div className="trace-details">
                        {trace.reasoning && (
                          <div className="trace-section">
                            <strong>Reasoning:</strong>
                            <p>{trace.reasoning}</p>
                          </div>
                        )}

                        {trace.confidence !== null && (
                          <div className="trace-section">
                            <strong>Confidence:</strong>
                            <span className="confidence-value">
                              {(trace.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        )}

                        {trace.tools_used && trace.tools_used.length > 0 && (
                          <div className="trace-section">
                            <strong>Tools Used:</strong>
                            <div className="tools-list">
                              {trace.tools_used.map((tool, idx) => (
                                <span key={idx} className="tool-badge">
                                  {tool}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {trace.output_data && (
                          <div className="trace-section">
                            <strong>Output:</strong>
                            <pre className="json-output">
                              {JSON.stringify(trace.output_data, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-traces">No agent traces available.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default TicketDetailPage;
