import { useState } from 'react'
import Login from './components/Login'
import Controls from './components/Controls'
import Dashboard from './components/Dashboard'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState<'login' | 'controls' | 'dashboard'>('dashboard');

  return (
    <>
      <nav className="app-nav">
        <div className="nav-brand">
          AccrediVault
        </div>
        <div className="nav-links">
          <button
            className={currentPage === 'dashboard' ? 'active' : ''}
            onClick={() => setCurrentPage('dashboard')}
          >
            Dashboard
          </button>
          <button
            className={currentPage === 'controls' ? 'active' : ''}
            onClick={() => setCurrentPage('controls')}
          >
            Controls
          </button>
          <button
            className={currentPage === 'login' ? 'active' : ''}
            onClick={() => setCurrentPage('login')}
          >
            Settings
          </button>
        </div>
      </nav>

      <main className="animate-fade-in">
        {currentPage === 'login' && <Login />}
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'controls' && <Controls />}
      </main>
    </>
  )
}

export default App
