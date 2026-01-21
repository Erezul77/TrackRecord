// src/components/predictions/PredictionCard.tsx
import { formatDate, formatPercent, cn } from '@/lib/utils'
import { Calendar, Quote, ExternalLink, Target } from 'lucide-react'

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
  }
}

export function PredictionCard({ prediction }: PredictionCardProps) {
  const statusColors: Record<string, string> = {
    'pending_match': 'bg-amber-100 text-amber-700 border-amber-200',
    'matched': 'bg-blue-100 text-blue-700 border-blue-200',
    'resolved': 'bg-emerald-100 text-emerald-700 border-emerald-200',
    'no_match': 'bg-slate-100 text-slate-700 border-slate-200',
  }

  return (
    <div className="bg-white border rounded-xl overflow-hidden hover:border-blue-200 transition-colors">
      <div className="p-5">
        <div className="flex justify-between items-start mb-4">
          <span className={cn(
            "text-xs font-bold px-2.5 py-1 rounded-full border uppercase tracking-wider",
            statusColors[prediction.status] || statusColors.pending_match
          )}>
            {prediction.status.replace('_', ' ')}
          </span>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest flex items-center gap-1">
            <Target className="h-3 w-3" /> {prediction.category}
          </span>
        </div>

        <h4 className="text-lg font-bold text-slate-900 mb-3 leading-snug">
          {prediction.claim}
        </h4>

        <div className="bg-slate-50 rounded-lg p-4 mb-4 border-l-4 border-slate-200 italic text-sm text-slate-600 relative">
          <Quote className="h-4 w-4 text-slate-300 absolute -top-2 -left-2 fill-slate-300" />
          "{prediction.quote}"
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-2 text-slate-500 text-sm">
            <Calendar className="h-4 w-4" />
            <span>Resolves: {formatDate(prediction.timeframe)}</span>
          </div>
          <div className="flex items-center gap-2 text-slate-500 text-sm">
            <div className="h-4 w-4 rounded-full border-2 border-slate-300 flex items-center justify-center text-[10px] font-bold">
              %
            </div>
            <span>Confidence: {formatPercent(prediction.confidence)}</span>
          </div>
        </div>
      </div>
      
      <div className="px-5 py-3 bg-slate-50 border-t flex justify-between items-center">
        <a 
          href={prediction.source_url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
        >
          View Source <ExternalLink className="h-3 w-3" />
        </a>
        <button className="text-xs font-semibold text-slate-400 hover:text-rose-500 transition-colors">
          Report Inaccurate
        </button>
      </div>
    </div>
  )
}
