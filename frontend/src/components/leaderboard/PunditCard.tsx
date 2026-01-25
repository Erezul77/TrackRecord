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

// Get rating color - Clean accent colors
function getRatingColor(winRate: number): string {
  if (winRate >= 0.6) return 'text-green-600'  // Good = Green
  if (winRate >= 0.4) return 'text-amber-500'  // OK = Amber
  return 'text-red-600'                         // Bad = Red
}

export function PunditCard({ pundit, rank }: PunditCardProps) {
  const [imgError, setImgError] = useState(false)
  const hasEnoughData = pundit.metrics.resolved_predictions >= MIN_PREDICTIONS
  const stars = getStarRating(pundit.metrics.paper_win_rate)
  const ratingColor = hasEnoughData ? getRatingColor(pundit.metrics.paper_win_rate) : 'text-neutral-400'
  
  return (
    <Link href={`/pundits/${pundit.id}`} className="block group">
      <div className="flex items-center gap-3 sm:gap-6 p-4 sm:p-5 bg-white border border-neutral-200 hover:border-black transition-all">
        {/* Rank */}
        <div className="text-2xl sm:text-3xl font-black text-neutral-200 w-8 sm:w-12 text-center flex-shrink-0 group-hover:text-black transition-colors">
          {rank}
        </div>
        
        {/* Avatar */}
        <div className="relative h-12 w-12 sm:h-14 sm:w-14 flex-shrink-0 rounded-full border-2 border-neutral-100 overflow-hidden bg-neutral-100 flex items-center justify-center">
          {!imgError && pundit.avatar_url ? (
            <img
              src={pundit.avatar_url}
              alt={pundit.name}
              className="h-full w-full object-cover grayscale group-hover:grayscale-0 transition-all"
              onError={() => setImgError(true)}
            />
          ) : (
            <User className="h-6 w-6 sm:h-7 sm:w-7 text-neutral-400" />
          )}
        </div>
        
        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <h3 className="text-sm sm:text-base font-bold text-black truncate">{pundit.name}</h3>
            {pundit.verified && (
              <CheckCircle className="h-4 w-4 text-blue-500 flex-shrink-0" />
            )}
          </div>
          <p className="text-xs text-neutral-400 truncate">
            @{pundit.username}
          </p>
          
          {/* Stats - Hidden on mobile, shown on desktop */}
          <div className="hidden sm:flex flex-wrap gap-4 text-xs mt-2">
            <span className="text-neutral-500">
              <span className="font-semibold text-black">{pundit.metrics.total_predictions}</span> predictions
            </span>
            <span className="text-neutral-500">
              <span className="font-semibold text-black">{pundit.metrics.resolved_predictions}</span> resolved
            </span>
            {pundit.net_worth && (
              <span className="text-neutral-500">
                <span className="font-semibold text-green-600">{formatNetWorth(pundit.net_worth)}</span>
              </span>
            )}
          </div>
        </div>
        
        {/* Rating */}
        <div className="text-right flex-shrink-0">
          {hasEnoughData ? (
            <>
              {/* Win Rate - Big number */}
              <div className={cn("text-2xl sm:text-3xl font-black tracking-tight", ratingColor)}>
                {formatPercent(pundit.metrics.paper_win_rate)}
              </div>
              <div className="text-[10px] font-medium text-neutral-400 uppercase tracking-wider">
                accuracy
              </div>
            </>
          ) : (
            <div className="text-right">
              <div className="text-xs font-medium text-neutral-400">
                Pending
              </div>
              <div className="text-[10px] text-neutral-300">
                {pundit.metrics.resolved_predictions}/{MIN_PREDICTIONS}
              </div>
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}
