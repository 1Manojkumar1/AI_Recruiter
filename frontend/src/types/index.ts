export interface SearchHit {
  candidate_id: string
  score: number
  profile_summary: string
  seniority: string
  total_experience_years: number
}

export interface SearchResponse {
  results: SearchHit[]
  total: number
  query_time_ms: number
}

export interface CandidateScore {
  candidate_id: string
  rank: number
  final_score: number
  skill_score: number
  experience_score: number
  education_score: number
  semantic_score: number
  achievement_score: number
  strengths: string[]
  weaknesses: string[]
  explanation: string
  profile_summary: string
  seniority: string
  total_experience_years: number
}

export interface RankResponse {
  candidates: CandidateScore[]
  total_scored: number
  query_time_ms: number
  weights_used: Record<string, number>
}

export interface ExplanationResponse {
  candidate_id: string
  strengths: string[]
  weaknesses: string[]
  summary: string
  recommendation: string
  scores: Record<string, number>
}

export interface ComparisonResponse {
  candidate_A_id: string
  candidate_B_id: string
  candidate_A_advantage: string[]
  candidate_B_advantage: string[]
  final_reason: string
}

export interface HealthResponse {
  status: string
  version: string
  candidates_loaded: number
}

export interface SkillItem {
  name: string
  score: number
}

export interface DomainItem {
  name: string
  score: number
}

export interface CandidateProfile {
  name: string
  headline: string
  experience: string
  location: string
}

export interface CandidateDetail {
  candidate_id: string
  profile: CandidateProfile
  skills: SkillItem[]
  domains: DomainItem[]
  seniority: string
  total_experience_years: number
  leadership_score: number
  impact_score: number
  career_growth_score: number
  promotion_count: number
  education_score: number
  years_in_current_role: number
  profile_summary: string
}
