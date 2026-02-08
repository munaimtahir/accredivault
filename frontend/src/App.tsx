import { useState } from 'react'
import Login from './components/Login'
import Controls from './components/Controls'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState<'login' | 'controls'>('controls');

  return (
    <>
      <nav className="app-nav">
        <button onClick={() => setCurrentPage('login')}>Login (Placeholder)</button>
        <button onClick={() => setCurrentPage('controls')}>Controls</button>
      </nav>
      
      {currentPage === 'login' && <Login />}
      {currentPage === 'controls' && <Controls />}
    </>
  )
}

export default App
