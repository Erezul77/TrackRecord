// src/components/leaderboard/PunditCard.tsx
'use client'
import Link from 'next/link'
import { Pundit } from '@/lib/api'
import { formatPercent, cn } from '@/lib/utils'
import { CheckCircle, User, Star, AlertCircle, DollarSign } from 'lucide-react'
import { useState } from 'react'

// Format net worth for display
function formatNetWorth(netWorth: number): string {
  if (netWorth >= 1000) {
    return `$${(netWorth / 1000).toFixed(1)}B`
  }
  return `$${netWorth}M`
}

interface PunditCardProps {
  pundit: Pundit
  rank: number
}

// Minimum predictions for meaningful ranking
const MIN_PREDICTIONS = 3

// Calculate star rating (1-5) based on win rate
function getStarRating(winRate: number): number {
  if (winRate >= 0.8) return 5
  if (winRate >= 0.6) return 4
  if (winRate >= 0.4) return 3
  if (winRate >= 0.2) return 2
  return 1
}

// Get rating color
function getRatingColor(winRate: number): string {
  if (winRate >= 0.6) return 'text-emerald-500'
  if (winRate >= 0.4) return 'text-amber-500'
  return 'text-rose-500'
}

export function PunditCard({ pundit, rank }: PunditCardProps) {
  const [imgError, setImgError] = useState(false)
  const hasEnoughData = pundit.metrics.resolved_predictions >= MIN_PREDICTIONS
  const stars = getStarRating(pundit.metrics.paper_win_rate)
  const ratingColor = hasEnoughData ? getRatingColor(pundit.metrics.paper_win_rate) : 'text-slate-400'
  
  return (
    <Link href={`/pundits/${pundit.id}`} className="block">
      <div className="flex items-center gap-3 sm:gap-6 p-4 sm:p-6 bg-white border rounded-xl hover:shadow-md transition-all hover:border-blue-200">
        {/* Rank */}
        <div className="text-2xl sm:text-3xl font-bold text-slate-300 w-8 sm:w-12 text-center flex-shrink-0">
          {rank}
        </div>
        
        {/* Avatar */}
        <div className="relative h-12 w-12 sm:h-16 sm:w-16 flex-shrink-0 rounded-full border-2 border-slate-100 overflow-hidden bg-slate-100 flex items-center justify-center">
          {!imgError && pundit.avatar_url ? (
            <img
              src={pundit.avatar_url}
              alt={pundit.name}
              className="h-full w-full object-cover"
              onError={() => setImgError(true)}
            />
          ) : (
            <User className="h-6 w-6 sm:h-8 sm:w-8 text-slate-400" />
          )}
        </div>
        
        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm sm:text-lg font-bold text-slate-900 truncate">{pundit.name}</h3>
            {pundit.verified && (
              <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 fill-blue-50 flex-shrink-0" />
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-500 truncate mb-2">
            @{pundit.username}
          </p>
          
          {/* Stats - Hidden on mobile, shown on desktop */}
          <div className="hidden sm:flex flex-wrap gap-4 text-xs font-medium text-slate-600">
            <div className="flex flex-col">
              <span className="text-slate-400 font-normal uppercase tracking-wider">Total</span>
              <span>{pundit.metrics.total_predictions} predictions</span>
            </div>
            <div className="flex flex-col">
              <span className="text-slate-400 font-normal uppercase tracking-wider">Resolved</span>
              <span>{pundit.metrics.resolved_predictions} closed</span>
            </div>
            {pundit.net_worth && (
              <div className="flex flex-col">
                <span className="text-slate-400 font-normal uppercase tracking-wider">Net Worth</span>
                <span className="flex items-center gap-1">
                  <DollarSign className="h-3 w-3 text-emerald-500" />
                  <span className="text-emerald-600 font-bold">{formatNetWorth(pundit.net_worth)}</span>
                  {pundit.net_worth_source && (
                    <span className="text-slate-400 text-[10px]">({pundit.net_worth_source})</span>
                  )}
                </span>
              </div>
            )}
          </div>
        </div>
        
        {/* Rating */}
        <div className="text-right flex-shrink-0">
          {hasEnoughData ? (
            <>
              {/* Star Rating */}
              <div className="flex items-center justify-end gap-0.5 mb-1">
                {[1, 2, 3, 4, 5].map((s) => (
                  <Star 
                    key={s} 
                    className={cn(
                      "h-4 w-4 sm:h-5 sm:w-5",
                      s <= stars ? `${ratingColor} fill-current` : "text-slate-200"
                    )} 
                  />
                ))}
              </div>
              
              {/* Win Rate */}
              <div className={cn("text-lg sm:text-2xl font-black", ratingColor)}>
                {formatPercent(pundit.metrics.paper_win_rate)}
              </div>
              <div className="text-[10px] sm:text-xs font-semibold text-slate-400 uppercase tracking-widest">
                {pundit.metrics.resolved_predictions} resolved
              </div>
            </>
          ) : (
            <div className="flex flex-col items-end bg-slate-100 px-3 py-2 rounded-lg">
              <div className="text-xs font-bold text-slate-500 mb-0.5">
                Awaiting Results
              </div>
              <div className="text-[10px] text-slate-400">
                {pundit.metrics.resolved_predictions} of {MIN_PREDICTIONS} min
              </div>
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}
