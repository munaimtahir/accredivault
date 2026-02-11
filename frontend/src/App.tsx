import { useState } from 'react'
import Login from './components/Login'
import Controls from './components/Controls'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState<'login' | 'controls'>('controls');

  return (
    <>
      <nav className="app-nav">
        <div className="nav-brand">
          <span style={{ fontSize: '1.5rem' }}>🛡️</span> AccrediVault
        </div>
        <div className="nav-links">
          <button
            className={currentPage === 'controls' ? 'active' : ''}
            onClick={() => setCurrentPage('controls')}
          >
            Dashboard
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
        {currentPage === 'controls' && <Controls />}
      </main>
    </>
  )
}

export default App
