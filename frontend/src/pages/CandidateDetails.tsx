import { useParams, Link } from 'react-router-dom'
import { FiArrowLeft, FiUser, FiBriefcase, FiBook, FiStar, FiTrendingUp, FiAward, FiMapPin, FiClock } from 'react-icons/fi'
import { useCandidateDetail } from '../hooks/useCandidates'
import { getScoreColor, getScoreBadgeColor, getSeniorityColor } from '../utils/helpers'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'

export default function CandidateDetails() {
  const { id } = useParams<{ id: string }>()
  const { candidate, loading, error } = useCandidateDetail(id)

  if (loading) {
    return (
      <div className="card">
        <LoadingSpinner text="Loading candidate profile..." size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700">
          <FiArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
        <ErrorMessage message={error} />
      </div>
    )
  }

  if (!candidate) return null

  const { profile, skills, domains } = candidate

  return (
    <div className="space-y-6">
      <Link to="/" className="inline-flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700">
        <FiArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      <div className="card">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 bg-gradient-to-br from-primary-100 to-primary-200 rounded-full flex items-center justify-center flex-shrink-0">
            <FiUser className="w-8 h-8 text-primary-600" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-gray-900">{profile.name || candidate.candidate_id}</h1>
              {candidate.seniority && (
                <span className={`text-sm px-3 py-1 rounded-full font-medium ${getSeniorityColor(candidate.seniority)}`}>
                  {candidate.seniority}
                </span>
              )}
            </div>
            {profile.headline && (
              <p className="text-gray-600 mt-1">{profile.headline}</p>
            )}
            <div className="flex items-center gap-4 mt-3 flex-wrap">
              {profile.experience && (
                <div className="flex items-center gap-1.5 text-sm text-gray-500">
                  <FiBriefcase className="w-4 h-4" />
                  {profile.experience}
                </div>
              )}
              {profile.location && (
                <div className="flex items-center gap-1.5 text-sm text-gray-500">
                  <FiMapPin className="w-4 h-4" />
                  {profile.location}
                </div>
              )}
              {candidate.total_experience_years > 0 && (
                <div className="flex items-center gap-1.5 text-sm text-gray-500">
                  <FiClock className="w-4 h-4" />
                  {candidate.total_experience_years} years total
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-2 mb-3">
            <FiTrendingUp className="w-5 h-5 text-blue-500" />
            <h3 className="text-sm font-semibold text-gray-900">Leadership</h3>
          </div>
          <div className={`text-2xl font-bold ${getScoreColor(candidate.leadership_score)}`}>
            {candidate.leadership_score.toFixed(1)}
          </div>
          <div className="mt-2 w-full bg-gray-100 rounded-full h-2">
            <div
              className="h-full bg-blue-500 rounded-full"
              style={{ width: `${Math.min(candidate.leadership_score, 100)}%` }}
            />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 mb-3">
            <FiAward className="w-5 h-5 text-amber-500" />
            <h3 className="text-sm font-semibold text-gray-900">Impact</h3>
          </div>
          <div className={`text-2xl font-bold ${getScoreColor(candidate.impact_score)}`}>
            {candidate.impact_score.toFixed(1)}
          </div>
          <div className="mt-2 w-full bg-gray-100 rounded-full h-2">
            <div
              className="h-full bg-amber-500 rounded-full"
              style={{ width: `${Math.min(candidate.impact_score, 100)}%` }}
            />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 mb-3">
            <FiTrendingUp className="w-5 h-5 text-emerald-500" />
            <h3 className="text-sm font-semibold text-gray-900">Career Growth</h3>
          </div>
          <div className={`text-2xl font-bold ${getScoreColor(candidate.career_growth_score)}`}>
            {candidate.career_growth_score.toFixed(1)}
          </div>
          <div className="mt-2 w-full bg-gray-100 rounded-full h-2">
            <div
              className="h-full bg-emerald-500 rounded-full"
              style={{ width: `${Math.min(candidate.career_growth_score, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {candidate.profile_summary && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Profile Summary</h3>
          <p className="text-sm text-gray-700 leading-relaxed">{candidate.profile_summary}</p>
        </div>
      )}

      {skills.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <FiStar className="w-5 h-5 text-primary-500" />
            <h3 className="text-sm font-semibold text-gray-900">Skills ({skills.length})</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {skills
              .sort((a, b) => b.score - a.score)
              .map((skill, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-lg border border-gray-100"
                >
                  <span className="text-sm text-gray-700">{skill.name}</span>
                  {skill.score > 0 && (
                    <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${getScoreBadgeColor(skill.score)}`}>
                      {skill.score.toFixed(0)}
                    </span>
                  )}
                </div>
              ))}
          </div>
        </div>
      )}

      {domains.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <FiBook className="w-5 h-5 text-purple-500" />
            <h3 className="text-sm font-semibold text-gray-900">Domains ({domains.length})</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {domains
              .sort((a, b) => b.score - a.score)
              .map((domain, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 px-3 py-1.5 bg-purple-50 rounded-lg border border-purple-100"
                >
                  <span className="text-sm text-purple-700">{domain.name}</span>
                  {domain.score > 0 && (
                    <span className="text-xs font-medium text-purple-500">
                      {domain.score.toFixed(0)}
                    </span>
                  )}
                </div>
              ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card text-center">
          <p className="text-xs text-gray-500 mb-1">Promotions</p>
          <p className="text-2xl font-bold text-gray-900">{candidate.promotion_count}</p>
        </div>
        <div className="card text-center">
          <p className="text-xs text-gray-500 mb-1">Education Score</p>
          <p className={`text-2xl font-bold ${getScoreColor(candidate.education_score)}`}>
            {candidate.education_score.toFixed(1)}
          </p>
        </div>
        <div className="card text-center">
          <p className="text-xs text-gray-500 mb-1">Current Role</p>
          <p className="text-2xl font-bold text-gray-900">{candidate.years_in_current_role}y</p>
        </div>
        <div className="card text-center">
          <p className="text-xs text-gray-500 mb-1">Total Experience</p>
          <p className="text-2xl font-bold text-gray-900">{candidate.total_experience_years}y</p>
        </div>
      </div>
    </div>
  )
}
