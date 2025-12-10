import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import HomePage from './pages/HomePage';
import AdminPage from './pages/AdminPage';
import TicketDetailPage from './pages/TicketDetailPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="navbar-container">
            <Link to="/" className="navbar-brand">
              <span className="brand-icon">🤖</span>
              SupportFlow
            </Link>
            <div className="navbar-links">
              <Link to="/" className="nav-link">Submit Ticket</Link>
              <Link to="/admin" className="nav-link">Admin Dashboard</Link>
            </div>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/ticket/:ticketId" element={<TicketDetailPage />} />
          </Routes>
        </main>

        <footer className="footer">
          <p>SupportFlow - AI-Native Customer Support Automation</p>
          <p className="footer-subtitle">Powered by Multi-Agent AI System</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
