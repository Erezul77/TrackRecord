// src/components/leaderboard/PunditCard.tsx
import Link from 'next/link'
import Image from 'next/image'
import { Pundit } from '@/lib/api'
import { formatCurrency, formatPercent, cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, CheckCircle } from 'lucide-react'

interface PunditCardProps {
  pundit: Pundit
  rank: number
}

export function PunditCard({ pundit, rank }: PunditCardProps) {
  const isProfit = pundit.metrics.paper_total_pnl >= 0
  
  return (
    <Link href={`/pundits/${pundit.id}`} className="block">
      <div className="flex items-center gap-6 p-6 bg-white border rounded-xl hover:shadow-md transition-all hover:border-blue-200">
        {/* Rank */}
        <div className="text-3xl font-bold text-slate-300 w-12 text-center">
          {rank}
        </div>
        
        {/* Avatar */}
        <div className="relative h-16 w-16 flex-shrink-0">
          <Image
            src={pundit.avatar_url || '/default-avatar.png'}
            alt={pundit.name}
            fill
            className="rounded-full object-cover border-2 border-slate-100"
          />
        </div>
        
        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-bold text-slate-900 truncate">{pundit.name}</h3>
            {pundit.verified && (
              <CheckCircle className="h-5 w-5 text-blue-500 fill-blue-50" />
            )}
          </div>
          <p className="text-sm text-slate-500 truncate mb-2">
            @{pundit.username} {pundit.affiliation && `• ${pundit.affiliation}`}
          </p>
          <div className="flex flex-wrap gap-4 text-xs font-medium text-slate-600">
            <div className="flex flex-col">
              <span className="text-slate-400 font-normal uppercase tracking-wider">Predictions</span>
              <span>{pundit.metrics.total_predictions}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-slate-400 font-normal uppercase tracking-wider">Win Rate</span>
              <span>{formatPercent(pundit.metrics.paper_win_rate)}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-slate-400 font-normal uppercase tracking-wider">ROI</span>
              <span>{formatPercent(pundit.metrics.paper_roi)}</span>
            </div>
          </div>
        </div>
        
        {/* P&L */}
        <div className="text-right flex-shrink-0">
          <div className={cn(
            "text-2xl font-black flex items-center justify-end gap-1",
            isProfit ? "text-emerald-600" : "text-rose-600"
          )}>
            {isProfit ? <TrendingUp className="h-6 w-6" /> : <TrendingDown className="h-6 w-6" />}
            {formatCurrency(pundit.metrics.paper_total_pnl)}
          </div>
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-widest mt-1">
            All-Time P&L
          </div>
        </div>
      </div>
    </Link>
  )
}
