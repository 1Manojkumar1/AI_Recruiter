import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { CandidateProvider } from './context/CandidateContext'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import CandidateDetails from './pages/CandidateDetails'

function App() {
  return (
    <CandidateProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/candidate/:id" element={<CandidateDetails />} />
            </Routes>
          </main>
        </div>
      </Router>
    </CandidateProvider>
  )
}

export default App
