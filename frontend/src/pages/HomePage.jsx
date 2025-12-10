import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ticketService } from '../services/api';
import './HomePage.css';

function HomePage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_email: '',
    subject: '',
    message: '',
    order_id: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [ticketNumber, setTicketNumber] = useState(null);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const submitData = {
        ...formData,
        order_id: formData.order_id || null,
      };

      const response = await ticketService.createTicket(submitData);
      setTicketNumber(response.ticket_number);

      // Reset form
      setFormData({
        customer_name: '',
        customer_email: '',
        subject: '',
        message: '',
        order_id: '',
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit ticket. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const viewTicket = () => {
    if (ticketNumber) {
      navigate(`/admin`);
    }
  };

  return (
    <div className="home-page">
      <div className="hero-section">
        <h1>Welcome to SupportFlow</h1>
        <p className="hero-subtitle">
          Get instant AI-powered support for your questions. Our multi-agent system
          analyzes your request and provides accurate, policy-compliant responses.
        </p>
      </div>

      {ticketNumber ? (
        <div className="success-card">
          <div className="success-icon">✓</div>
          <h2>Ticket Submitted Successfully!</h2>
          <p className="ticket-number">
            Your ticket number: <strong>{ticketNumber}</strong>
          </p>
          <p className="success-message">
            Our AI agents have processed your request. You can view the response in the admin dashboard.
          </p>
          <div className="success-actions">
            <button onClick={viewTicket} className="btn btn-primary">
              View All Tickets
            </button>
            <button onClick={() => setTicketNumber(null)} className="btn btn-secondary">
              Submit Another Ticket
            </button>
          </div>
        </div>
      ) : (
        <div className="ticket-form-card">
          <h2>Submit a Support Ticket</h2>
          <form onSubmit={handleSubmit} className="ticket-form">
            <div className="form-group">
              <label htmlFor="customer_name">Your Name *</label>
              <input
                type="text"
                id="customer_name"
                name="customer_name"
                value={formData.customer_name}
                onChange={handleChange}
                required
                placeholder="John Doe"
              />
            </div>

            <div className="form-group">
              <label htmlFor="customer_email">Email Address *</label>
              <input
                type="email"
                id="customer_email"
                name="customer_email"
                value={formData.customer_email}
                onChange={handleChange}
                required
                placeholder="john@example.com"
              />
            </div>

            <div className="form-group">
              <label htmlFor="order_id">Order ID (Optional)</label>
              <input
                type="text"
                id="order_id"
                name="order_id"
                value={formData.order_id}
                onChange={handleChange}
                placeholder="ORD-001"
              />
              <small className="form-hint">
                Provide your order ID for faster assistance with order-related issues
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="subject">Subject *</label>
              <input
                type="text"
                id="subject"
                name="subject"
                value={formData.subject}
                onChange={handleChange}
                required
                placeholder="Brief description of your issue"
              />
            </div>

            <div className="form-group">
              <label htmlFor="message">Message *</label>
              <textarea
                id="message"
                name="message"
                value={formData.message}
                onChange={handleChange}
                required
                rows="6"
                placeholder="Please describe your issue in detail..."
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="btn btn-submit" disabled={loading}>
              {loading ? 'Processing...' : 'Submit Ticket'}
            </button>
          </form>

          <div className="info-box">
            <h3>🤖 AI-Powered Support</h3>
            <p>
              Your ticket will be analyzed by our multi-agent AI system which includes:
            </p>
            <ul>
              <li><strong>Triage Agent:</strong> Classifies intent and priority</li>
              <li><strong>Research Agent:</strong> Searches our knowledge base</li>
              <li><strong>Policy Agent:</strong> Checks eligibility and policies</li>
              <li><strong>Response Agent:</strong> Drafts personalized response</li>
              <li><strong>Escalation Agent:</strong> Determines if human review needed</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default HomePage;
