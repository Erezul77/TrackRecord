// src/app/predictions/page.tsx
import { api, PredictionWithPundit } from "@/lib/api"
import Link from "next/link"
import { formatDate, cn } from "@/lib/utils"
import { ExternalLink, User, CheckCircle, XCircle, Clock } from "lucide-react"

async function getRecentPredictions() {
  try {
    return await api.getRecentPredictions(50)
  } catch (e) {
    console.error(e)
    return []
  }
}

// Get status display based on outcome - GREEN for right, RED for wrong
function getStatusDisplay(status: string, outcome?: string) {
  if (status === 'resolved') {
    if (outcome === 'YES') {
      return { color: 'bg-emerald-500 text-white', label: 'CORRECT', icon: CheckCircle }
    } else {
      return { color: 'bg-rose-500 text-white', label: 'WRONG', icon: XCircle }
    }
  }
  if (status === 'matched') {
    return { color: 'bg-blue-600 text-white', label: 'OPEN', icon: Clock }
  }
  return { color: 'bg-amber-500 text-white', label: 'PENDING', icon: Clock }
}

export default async function PredictionsPage() {
  const predictions: PredictionWithPundit[] = await getRecentPredictions()

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="mb-12">
        <h1 className="text-4xl font-black text-slate-900 tracking-tighter mb-2">Recent Predictions</h1>
        <p className="text-slate-500 font-medium text-lg">The latest verifiable claims captured from across the web.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {predictions.length > 0 ? (
          predictions.map((pred) => {
            const statusDisplay = getStatusDisplay(pred.status, (pred as any).outcome)
            const StatusIcon = statusDisplay.icon
            const isResolved = pred.status === 'resolved'
            const isCorrect = (pred as any).outcome === 'YES'
            
            return (
              <div key={pred.id} className={cn(
                "bg-white border rounded-xl overflow-hidden hover:shadow-md transition-shadow",
                isResolved && isCorrect && "ring-2 ring-emerald-200",
                isResolved && !isCorrect && "ring-2 ring-rose-200"
              )}>
                {/* Status Banner */}
                <div className={cn("px-4 py-2 flex items-center justify-between", statusDisplay.color)}>
                  <div className="flex items-center gap-2">
                    <StatusIcon className="h-4 w-4" />
                    <span className="text-xs font-black uppercase tracking-wider">{statusDisplay.label}</span>
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-wider opacity-80">{pred.category}</span>
                </div>
                
                <div className="p-4">
                  {/* Pundit Header */}
                  <Link href={`/pundits/${pred.pundit.id}`} className="flex items-center gap-3 mb-3">
                    <div className="h-8 w-8 rounded-full bg-slate-100 overflow-hidden flex items-center justify-center flex-shrink-0">
                      {pred.pundit.avatar_url ? (
                        <img src={pred.pundit.avatar_url} alt={pred.pundit.name} className="h-full w-full object-cover" />
                      ) : (
                        <User className="h-4 w-4 text-slate-400" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="font-bold text-slate-900 text-sm truncate">{pred.pundit.name}</p>
                      <p className="text-xs text-slate-500">@{pred.pundit.username}</p>
                    </div>
                  </Link>

                  {/* Claim */}
                  <p className="font-bold text-slate-900 mb-3 line-clamp-2">{pred.claim}</p>
                  
                  {/* Quote */}
                  <div className="bg-slate-50 rounded-lg p-3 mb-3 border-l-4 border-slate-300 italic text-sm text-slate-600 line-clamp-2">
                    "{pred.quote}"
                  </div>

                  {/* Footer */}
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>{pred.captured_at ? formatDate(pred.captured_at) : 'Unknown date'}</span>
                    {pred.source_url && pred.source_url !== 'https://example.com/test' && (
                      <a href={pred.source_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-blue-600 hover:underline font-bold">
                        Source <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            )
          })
        ) : (
          <div className="col-span-full bg-white border rounded-xl p-12 sm:p-20 text-center">
            <Clock className="h-12 w-12 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-400 font-bold text-xl">No recent predictions found.</p>
            <p className="text-slate-400 mt-2">Check back later as our AI processes more content.</p>
          </div>
        )}
      </div>
    </div>
  )
}
