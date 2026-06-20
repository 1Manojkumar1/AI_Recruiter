import axios from 'axios'
import type {
  SearchResponse,
  RankResponse,
  ExplanationResponse,
  ComparisonResponse,
  HealthResponse,
  CandidateDetail,
} from '../types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'API error'
    console.error('API Error:', message)
    return Promise.reject(new Error(message))
  }
)

export async function searchCandidates(query: string, topK: number = 100): Promise<SearchResponse> {
  const { data } = await api.post<SearchResponse>('/search', { query, top_k: topK })
  return data
}

export async function rankCandidates(
  jobDescription: string,
  topN: number = 100,
  weights?: Record<string, number>
): Promise<RankResponse> {
  const { data } = await api.post<RankResponse>('/rank', {
    job_description: jobDescription,
    top_n: topN,
    weights,
  })
  return data
}

export async function explainCandidate(
  candidateId: string,
  jobDescription: string
): Promise<ExplanationResponse> {
  const { data } = await api.post<ExplanationResponse>('/explain', {
    candidate_id: candidateId,
    job_description: jobDescription,
  })
  return data
}

export async function compareCandidates(
  candidateAId: string,
  candidateBId: string,
  jobDescription: string
): Promise<ComparisonResponse> {
  const { data } = await api.post<ComparisonResponse>('/explain/compare', {
    candidate_a_id: candidateAId,
    candidate_b_id: candidateBId,
    job_description: jobDescription,
  })
  return data
}

export async function getCandidate(candidateId: string): Promise<CandidateDetail> {
  const { data } = await api.get<CandidateDetail>(`/candidate/${candidateId}`)
  return data
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/health')
  return data
}

export default api
