// src/components/predictions/PredictionCard.tsx
import { formatDate, cn } from '@/lib/utils'
import { Calendar, Quote, ExternalLink, Target, CheckCircle, XCircle, Clock } from 'lucide-react'

interface PredictionCardProps {
  prediction: {
    id: string
    claim: string
    confidence: number
    timeframe: string
    quote: string
    category: string
    source_url: string
    status: string
    outcome?: string // 'YES' | 'NO' | null
  }
}

// Convert confidence number to simple label
function getConfidenceLabel(confidence: number): { label: string; color: string } {
  if (confidence >= 0.7) return { label: 'High', color: 'bg-emerald-100 text-emerald-700' }
  if (confidence >= 0.4) return { label: 'Medium', color: 'bg-amber-100 text-amber-700' }
  return { label: 'Low', color: 'bg-slate-100 text-slate-600' }
}

// Get outcome display
function getOutcomeDisplay(status: string, outcome?: string) {
  if (status === 'resolved' && outcome === 'YES') {
    return { label: 'CORRECT', color: 'bg-emerald-500 text-white', icon: CheckCircle }
  }
  if (status === 'resolved' && outcome === 'NO') {
    return { label: 'WRONG', color: 'bg-rose-500 text-white', icon: XCircle }
  }
  if (status === 'matched') {
    return { label: 'OPEN', color: 'bg-blue-100 text-blue-700', icon: Clock }
  }
  return { label: 'PENDING', color: 'bg-amber-100 text-amber-700', icon: Clock }
}

export function PredictionCard({ prediction }: PredictionCardProps) {
  const confidence = getConfidenceLabel(prediction.confidence)
  const outcomeDisplay = getOutcomeDisplay(prediction.status, prediction.outcome)
  const OutcomeIcon = outcomeDisplay.icon

  return (
    <div className={cn(
      "bg-white border rounded-xl overflow-hidden transition-all",
      prediction.outcome === 'YES' && "border-emerald-300 ring-1 ring-emerald-100",
      prediction.outcome === 'NO' && "border-rose-300 ring-1 ring-rose-100"
    )}>
      {/* Outcome Banner */}
      <div className={cn("px-4 py-2 flex items-center justify-between", outcomeDisplay.color)}>
        <div className="flex items-center gap-2">
          <OutcomeIcon className="h-4 w-4" />
          <span className="text-xs font-black uppercase tracking-wider">{outcomeDisplay.label}</span>
        </div>
        <span className="text-xs font-semibold uppercase tracking-wider opacity-80">
          {prediction.category}
        </span>
      </div>

      <div className="p-4">
        {/* Claim */}
        <h4 className="text-base font-bold text-slate-900 mb-3 leading-snug">
          {prediction.claim}
        </h4>

        {/* Quote */}
        <div className="bg-slate-50 rounded-lg p-3 mb-3 border-l-4 border-slate-200 italic text-sm text-slate-600">
          <Quote className="h-3 w-3 text-slate-300 inline mr-1" />
          {prediction.quote}
        </div>

        {/* Meta row */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className={cn("font-bold px-2 py-1 rounded-full", confidence.color)}>
            {confidence.label} Confidence
          </span>
          <span className="text-slate-400 flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {formatDate(prediction.timeframe)}
          </span>
        </div>
      </div>
      
      {/* Footer */}
      {prediction.source_url && prediction.source_url !== 'https://example.com/test' && (
        <div className="px-4 py-2 bg-slate-50 border-t">
          <a 
            href={prediction.source_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            View Source <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      )}
    </div>
  )
}
