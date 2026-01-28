// src/components/predictions/PredictionCard.tsx
import { formatDate, cn } from '@/lib/utils'
import { Calendar, Quote, ExternalLink, CheckCircle, XCircle, Clock, Target } from 'lucide-react'

// TR Index tier based on score
function getTRTier(score: number | null | undefined) {
  if (!score) return null
  if (score >= 80) return { label: 'Gold', color: 'bg-yellow-500 text-black' }
  if (score >= 60) return { label: 'Silver', color: 'bg-neutral-400 text-black' }
  if (score >= 40) return { label: 'Bronze', color: 'bg-amber-700 text-white' }
  return null
}

// Horizon display - time until resolution
function getHorizonDisplay(horizon: string | null | undefined) {
  switch (horizon) {
    case 'ST': return { label: 'Short', full: 'Short-term (<6mo)', color: 'bg-blue-500 text-white' }
    case 'MT': return { label: 'Med', full: 'Medium-term (6-24mo)', color: 'bg-purple-500 text-white' }
    case 'LT': return { label: 'Long', full: 'Long-term (2-5yr)', color: 'bg-orange-500 text-white' }
    case 'V': return { label: 'Vision', full: 'Visionary (5+yr)', color: 'bg-amber-400 text-black' }
    default: return null
  }
}

interface PredictionCardProps {
  prediction: {
    id: string
    claim: string
    timeframe: string
    quote: string
    category: string
    source_url: string
    status: string
    outcome?: string // 'YES' | 'NO' | null
    tr_index_score?: number | null
    horizon?: string | null
  }
}

// Get outcome display - NO CONFIDENCE, a prediction is 100% owned
function getOutcomeDisplay(status: string, outcome?: string) {
  if (status === 'resolved' && outcome === 'YES') {
    return { label: 'CORRECT', color: 'bg-green-500 text-white', icon: CheckCircle }
  }
  if (status === 'resolved' && outcome === 'NO') {
    return { label: 'WRONG', color: 'bg-red-500 text-white', icon: XCircle }
  }
  if (status === 'matched') {
    return { label: 'OPEN', color: 'bg-black dark:bg-white text-white dark:text-black', icon: Clock }
  }
  return { label: 'PENDING', color: 'bg-amber-500 text-white', icon: Clock }
}

export function PredictionCard({ prediction }: PredictionCardProps) {
  const outcomeDisplay = getOutcomeDisplay(prediction.status, prediction.outcome)
  const OutcomeIcon = outcomeDisplay.icon

  return (
    <div className={cn(
      "bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 overflow-hidden transition-all",
      prediction.outcome === 'YES' && "border-green-400 dark:border-green-700",
      prediction.outcome === 'NO' && "border-red-400 dark:border-red-700"
    )}>
      {/* Outcome Banner */}
      <div className={cn("px-4 py-2 flex items-center justify-between", outcomeDisplay.color)}>
        <div className="flex items-center gap-2">
          <OutcomeIcon className="h-4 w-4" />
          <span className="text-xs font-black uppercase tracking-wider">{outcomeDisplay.label}</span>
          {/* Horizon Badge */}
          {prediction.horizon && getHorizonDisplay(prediction.horizon) && (
            <span 
              className={cn(
                "px-1.5 py-0.5 text-[9px] font-bold uppercase rounded",
                getHorizonDisplay(prediction.horizon)?.color
              )}
              title={getHorizonDisplay(prediction.horizon)?.full}
            >
              {getHorizonDisplay(prediction.horizon)?.label}
            </span>
          )}
        </div>
        <span className="text-xs font-semibold uppercase tracking-wider opacity-80">
          {prediction.category}
        </span>
      </div>

      <div className="p-4">
        {/* Claim */}
        <h4 className="text-base font-bold text-black dark:text-white mb-3 leading-snug">
          {prediction.claim}
        </h4>

        {/* Quote - the exact words they said */}
        <div className="bg-neutral-50 dark:bg-neutral-800 p-3 mb-3 border-l-4 border-neutral-300 dark:border-neutral-600 italic text-sm text-neutral-600 dark:text-neutral-400">
          <Quote className="h-3 w-3 text-neutral-400 inline mr-1" />
          "{prediction.quote}"
        </div>

        {/* Deadline & TR Index */}
        <div className="flex items-center justify-between text-xs text-neutral-500">
          <div className="flex items-center gap-2">
            <Calendar className="h-3 w-3" />
            <span>Resolves: {formatDate(prediction.timeframe)}</span>
          </div>
          {prediction.tr_index_score && getTRTier(prediction.tr_index_score) && (
            <div className={cn(
              "flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold uppercase",
              getTRTier(prediction.tr_index_score)?.color
            )}>
              <Target className="h-3 w-3" />
              TR {Math.round(prediction.tr_index_score)}
            </div>
          )}
        </div>
      </div>
      
      {/* Footer - Source Link */}
      {prediction.source_url && prediction.source_url !== 'https://example.com/test' && (
        <div className="px-4 py-2 bg-neutral-50 dark:bg-neutral-800 border-t border-neutral-200 dark:border-neutral-800">
          <a 
            href={prediction.source_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white flex items-center gap-1"
          >
            View Source <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      )}
    </div>
  )
}
