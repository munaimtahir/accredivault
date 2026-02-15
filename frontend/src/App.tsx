import { useState, useEffect } from 'react'
import Login from './components/Login'
import Controls from './components/Controls'
import Dashboard from './components/Dashboard'
import Users from './components/Users'
import Audit from './components/Audit'
import { isAuthenticated, getStoredUser, logout as apiLogout } from './api'
import './App.css'

type Page = 'dashboard' | 'controls' | 'users' | 'audit'

function App() {
  const [authenticated, setAuthenticated] = useState(isAuthenticated())
  const [currentPage, setCurrentPage] = useState<Page>('dashboard')

  useEffect(() => {
    setAuthenticated(isAuthenticated())
  }, [])

  const handleLoginSuccess = () => {
    setAuthenticated(true)
  }

  const handleLogout = () => {
    apiLogout()
    setAuthenticated(false)
  }

  const user = getStoredUser()
  const canViewUsers = user?.roles?.includes('ADMIN') || user?.is_superuser
  const canViewAudit = user?.roles?.some((r) => ['ADMIN', 'MANAGER', 'AUDITOR'].includes(r)) || user?.is_superuser

  if (!authenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  return (
    <>
      <nav className="app-nav">
        <div className="nav-brand">AccrediVault</div>
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
          {canViewAudit && (
            <button
              className={currentPage === 'audit' ? 'active' : ''}
              onClick={() => setCurrentPage('audit')}
            >
              Audit
            </button>
          )}
          {canViewUsers && (
            <button
              className={currentPage === 'users' ? 'active' : ''}
              onClick={() => setCurrentPage('users')}
            >
              Users
            </button>
          )}
        </div>
        <div className="nav-user">
          <span className="user-chip">
            {user?.username}{' '}
            {user?.roles?.length ? (
              <span className="user-roles">[{user.roles.join(', ')}]</span>
            ) : null}
          </span>
          <button type="button" className="btn-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      <main className="animate-fade-in">
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'controls' && <Controls />}
        {currentPage === 'audit' && <Audit />}
        {currentPage === 'users' && <Users />}
      </main>
    </>
  )
}

export default App
