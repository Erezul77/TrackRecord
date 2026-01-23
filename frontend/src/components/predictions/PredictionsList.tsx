// src/components/predictions/PredictionsList.tsx
'use client'
import { useState, useEffect } from 'react'
import { Clock, ArrowUpDown, Flame, Star, Calendar, SortAsc } from 'lucide-react'
import { PredictionCardWithVotes } from './PredictionCardWithVotes'
import { PredictionWithPundit } from '@/lib/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const SORT_OPTIONS = [
  { value: 'default', label: 'Open First', icon: Clock, description: 'Open predictions first, then resolved' },
  { value: 'newest', label: 'Newest', icon: SortAsc, description: 'Most recent first' },
  { value: 'oldest', label: 'Oldest', icon: SortAsc, description: 'Oldest first' },
  { value: 'resolving_soon', label: 'Resolving Soon', icon: Calendar, description: 'About to resolve first' },
  { value: 'boldest', label: 'Boldest', icon: Flame, description: 'Most contrarian first' },
  { value: 'highest_score', label: 'Highest Rated', icon: Star, description: 'Best TR Index first' },
]

export function PredictionsList() {
  const [predictions, setPredictions] = useState<PredictionWithPundit[]>([])
  const [loading, setLoading] = useState(true)
  const [sort, setSort] = useState('default')

  useEffect(() => {
    loadPredictions()
  }, [sort])

  const loadPredictions = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/predictions/recent?limit=50&sort=${sort}`, {
        cache: 'no-store'
      })
      if (res.ok) {
        const data = await res.json()
        setPredictions(data)
      }
    } catch (err) {
      console.error('Failed to load predictions:', err)
    }
    setLoading(false)
  }

  const currentSort = SORT_OPTIONS.find(o => o.value === sort) || SORT_OPTIONS[0]

  return (
    <div>
      {/* Sort Controls */}
      <div className="flex flex-wrap items-center gap-3 mb-8">
        <span className="text-sm font-bold text-slate-500 flex items-center gap-2">
          <ArrowUpDown className="h-4 w-4" />
          Sort by:
        </span>
        <div className="flex flex-wrap gap-2">
          {SORT_OPTIONS.map(option => {
            const Icon = option.icon
            return (
              <button
                key={option.value}
                onClick={() => setSort(option.value)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  sort === option.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border text-slate-600 hover:bg-slate-50'
                }`}
                title={option.description}
              >
                <Icon className="h-3.5 w-3.5" />
                {option.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Predictions Grid */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin h-10 w-10 border-4 border-blue-600 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {predictions.length > 0 ? (
            predictions.map((pred) => (
              <PredictionCardWithVotes key={pred.id} prediction={pred} />
            ))
          ) : (
            <div className="col-span-full bg-white border rounded-xl p-12 sm:p-20 text-center">
              <Clock className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-400 font-bold text-xl">No predictions found.</p>
              <p className="text-slate-400 mt-2">Check back later as our AI processes more content.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
