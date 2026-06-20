import { Link, useLocation } from 'react-router-dom'
import { FiCpu, FiHome, FiActivity } from 'react-icons/fi'
import { useHealthCheck } from '../hooks/useCandidates'

export default function Navbar() {
  const location = useLocation()
  const { health } = useHealthCheck()

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center shadow-sm group-hover:shadow-md transition-shadow">
              <FiCpu className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900 leading-tight">AI Candidate Ranking</h1>
              <p className="text-xs text-gray-500 leading-tight">Intelligent Hiring</p>
            </div>
          </Link>

          <div className="flex items-center gap-6">
            <Link
              to="/"
              className={`flex items-center gap-2 text-sm font-medium transition-colors ${
                location.pathname === '/'
                  ? 'text-primary-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <FiHome className="w-4 h-4" />
              Dashboard
            </Link>

            {health && (
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <FiActivity className="w-3 h-3 text-emerald-500" />
                <span>{health.candidates_loaded.toLocaleString()} candidates</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
