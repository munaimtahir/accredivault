import React from 'react';
import './Login.css';

const Login: React.FC = () => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Placeholder - no auth in Prompt 0
    alert('Authentication not implemented in MVP (Prompt 0)');
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>AccrediVault</h1>
        <h2>PHC Lab Licensing System</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input type="text" id="username" placeholder="Enter username" />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input type="password" id="password" placeholder="Enter password" />
          </div>
          <button type="submit" className="login-button">
            Login (Placeholder)
          </button>
        </form>
        <p className="note">
          Note: Authentication will be implemented in Prompt 1
        </p>
      </div>
    </div>
  );
};

export default Login;
