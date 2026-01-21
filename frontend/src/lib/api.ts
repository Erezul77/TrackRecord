// src/lib/api.ts

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Pundit {
  id: string
  name: string
  username?: string
  affiliation?: string
  bio?: string
  avatar_url?: string
  domains: string[]
  verified: boolean
  metrics: PunditMetrics
}

export interface PunditMetrics {
  total_predictions: number
  resolved_predictions: number
  paper_total_pnl: number
  paper_win_rate: number
  paper_roi: number
  real_total_pnl?: number
  pnl_30d: number
  global_rank: number
}

export const api = {
  async getLeaderboard(filters?: {
    category?: string | null
    timeframe?: string
    limit?: number
    offset?: number
  }) {
    const params = new URLSearchParams()
    if (filters?.category) params.append('category', filters.category)
    if (filters?.timeframe) params.append('timeframe', filters.timeframe)
    if (filters?.limit) params.append('limit', String(filters.limit))
    if (filters?.offset) params.append('offset', String(filters.offset))
    
    const res = await fetch(`${API_BASE_URL}/api/leaderboard?${params}`)
    if (!res.ok) throw new Error('Failed to fetch leaderboard')
    return res.json()
  },
  
  async getPundit(id: string) {
    const res = await fetch(`${API_BASE_URL}/api/pundits/${id}`)
    if (!res.ok) throw new Error('Failed to fetch pundit')
    return res.json()
  },
  
  async getPunditPredictions(id: string) {
    const res = await fetch(`${API_BASE_URL}/api/pundits/${id}/predictions`)
    if (!res.ok) throw new Error('Failed to fetch predictions')
    return res.json()
  }
}
