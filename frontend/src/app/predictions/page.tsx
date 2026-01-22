// src/app/predictions/page.tsx
import { api, PredictionWithPundit } from "@/lib/api"
import Link from "next/link"
import { formatDate, cn } from "@/lib/utils"
import { ExternalLink, User } from "lucide-react"

async function getRecentPredictions() {
  try {
    return await api.getRecentPredictions(50)
  } catch (e) {
    console.error(e)
    return []
  }
}

function getConfidenceColor(confidence: number) {
  if (confidence >= 0.8) return 'bg-emerald-100 text-emerald-700'
  if (confidence >= 0.6) return 'bg-blue-100 text-blue-700'
  if (confidence >= 0.4) return 'bg-amber-100 text-amber-700'
  return 'bg-slate-100 text-slate-700'
}

function getStatusColor(status: string) {
  switch (status) {
    case 'resolved': return 'bg-emerald-100 text-emerald-700'
    case 'matched': return 'bg-blue-100 text-blue-700'
    case 'pending': return 'bg-amber-100 text-amber-700'
    default: return 'bg-slate-100 text-slate-700'
  }
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
          predictions.map((pred) => (
            <div key={pred.id} className="bg-white border rounded-xl p-6 hover:shadow-md transition-shadow">
              {/* Pundit Header */}
              <Link href={`/pundits/${pred.pundit.id}`} className="flex items-center gap-3 mb-4">
                <div className="h-10 w-10 rounded-full bg-slate-100 overflow-hidden flex items-center justify-center">
                  {pred.pundit.avatar_url ? (
                    <img src={pred.pundit.avatar_url} alt={pred.pundit.name} className="h-full w-full object-cover" />
                  ) : (
                    <User className="h-5 w-5 text-slate-400" />
                  )}
                </div>
                <div>
                  <p className="font-bold text-slate-900 text-sm">{pred.pundit.name}</p>
                  <p className="text-xs text-slate-500">@{pred.pundit.username}</p>
                </div>
              </Link>

              {/* Claim */}
              <p className="font-bold text-slate-900 mb-3 line-clamp-2">{pred.claim}</p>
              
              {/* Quote */}
              <p className="text-sm text-slate-500 italic mb-4 line-clamp-2">"{pred.quote}"</p>
              
              {/* Meta */}
              <div className="flex flex-wrap gap-2 mb-4">
                <span className={cn("text-xs font-bold px-2 py-1 rounded-full uppercase", getConfidenceColor(pred.confidence))}>
                  {Math.round(pred.confidence * 100)}% conf
                </span>
                <span className={cn("text-xs font-bold px-2 py-1 rounded-full uppercase", getStatusColor(pred.status))}>
                  {pred.status}
                </span>
                <span className="text-xs font-bold px-2 py-1 rounded-full bg-slate-100 text-slate-600 uppercase">
                  {pred.category}
                </span>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>{pred.captured_at ? formatDate(pred.captured_at) : 'Unknown date'}</span>
                <a href={pred.source_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-blue-600 hover:underline font-bold">
                  Source <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full bg-white border rounded-xl p-20 text-center">
            <p className="text-slate-400 font-bold text-xl">No recent predictions found.</p>
            <p className="text-slate-400 mt-2">Check back later as our AI processes more content.</p>
          </div>
        )}
      </div>
    </div>
  )
}
