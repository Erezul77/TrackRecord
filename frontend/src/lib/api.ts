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
  // Net worth data from verified sources
  net_worth?: number  // In USD millions
  net_worth_source?: string
  net_worth_year?: number
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

export interface TRIndex {
  score: number
  tier: 'gold' | 'silver' | 'bronze' | null
  specificity?: number
  verifiability?: number
  boldness?: number
  relevance?: number
  stakes?: number
}

export interface PredictionWithPundit {
  id: string
  claim: string
  quote: string
  confidence: number
  category: string
  status: string
  outcome?: string | null  // YES = correct, NO = wrong, null = open
  source_url: string
  source_type: string
  timeframe: string
  captured_at: string
  tr_index?: TRIndex | null  // TR Prediction Index score
  // Hash chain verification
  chain_hash?: string | null  // Truncated hash for display
  chain_index?: number | null  // Position in the chain
  pundit: {
    id: string
    name: string
    username: string
    avatar_url?: string
  }
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
    
    const res = await fetch(`${API_BASE_URL}/api/leaderboard?${params}`, {
      cache: 'no-store'
    })
    if (!res.ok) throw new Error('Failed to fetch leaderboard')
    return res.json()
  },
  
  async getPundit(id: string) {
    const res = await fetch(`${API_BASE_URL}/api/pundits/${id}`, {
      cache: 'no-store'
    })
    if (!res.ok) throw new Error('Failed to fetch pundit')
    return res.json()
  },
  
  async getPunditPredictions(id: string) {
    const res = await fetch(`${API_BASE_URL}/api/pundits/${id}/predictions`, {
      cache: 'no-store'
    })
    if (!res.ok) throw new Error('Failed to fetch predictions')
    return res.json()
  },

  async getRecentPredictions(limit: number = 50, category?: string, sort?: string) {
    const params = new URLSearchParams()
    params.append('limit', String(limit))
    if (category) params.append('category', category)
    if (sort) params.append('sort', sort)
    
    const res = await fetch(`${API_BASE_URL}/api/predictions/recent?${params}`, {
      cache: 'no-store'  // Always fetch fresh data
    })
    if (!res.ok) throw new Error('Failed to fetch recent predictions')
    return res.json()
  }
}
