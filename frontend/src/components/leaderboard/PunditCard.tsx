// src/components/leaderboard/PunditCard.tsx
'use client'
import Link from 'next/link'
import { Pundit } from '@/lib/api'
import { formatPercent, cn } from '@/lib/utils'
import { CheckCircle, User, Star } from 'lucide-react'
import { useState } from 'react'

interface PunditCardProps {
  pundit: Pundit
  rank: number
}

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
  const stars = getStarRating(pundit.metrics.paper_win_rate)
  const ratingColor = getRatingColor(pundit.metrics.paper_win_rate)
  
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
              <span className="text-slate-400 font-normal uppercase tracking-wider">Predictions</span>
              <span>{pundit.metrics.total_predictions}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-slate-400 font-normal uppercase tracking-wider">Win Rate</span>
              <span>{formatPercent(pundit.metrics.paper_win_rate)}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-slate-400 font-normal uppercase tracking-wider">Accuracy</span>
              <span>{pundit.metrics.resolved_predictions > 0 
                ? `${pundit.metrics.resolved_predictions} resolved`
                : 'No resolved yet'}</span>
            </div>
          </div>
        </div>
        
        {/* Rating */}
        <div className="text-right flex-shrink-0">
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
            Win Rate
          </div>
        </div>
      </div>
    </Link>
  )
}
