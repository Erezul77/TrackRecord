// src/app/pundits/[id]/page.tsx
import { api } from "@/lib/api"
import { PredictionCard } from "@/components/predictions/PredictionCard"
import { formatPercent, cn } from "@/lib/utils"
import Link from "next/link"
import { CheckCircle, Info, ExternalLink, Target, TrendingUp, User, Star } from "lucide-react"

async function getPunditData(id: string) {
  try {
    const [pundit, predictions] = await Promise.all([
      api.getPundit(id),
      api.getPunditPredictions(id)
    ])
    return { pundit, predictions }
  } catch (e) {
    console.error(e)
    return null
  }
}

export default async function PunditPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const data = await getPunditData(id)
  
  if (!data) {
    return (
      <div className="container mx-auto px-4 py-24 text-center">
        <h1 className="text-2xl font-bold text-slate-900">Pundit not found</h1>
        <p className="text-slate-500 mt-2">The pundit you are looking for does not exist in our database.</p>
      </div>
    )
  }

  const { pundit, predictions } = data
  
  // Calculate stats
  const correctCount = predictions.filter((p: any) => p.outcome === 'YES').length
  const wrongCount = predictions.filter((p: any) => p.outcome === 'NO').length
  const openCount = predictions.filter((p: any) => !p.outcome).length
  
  // Star rating based on win rate
  const getStars = (rate: number) => {
    if (rate >= 0.8) return 5
    if (rate >= 0.6) return 4
    if (rate >= 0.4) return 3
    if (rate >= 0.2) return 2
    return 1
  }
  const stars = getStars(pundit.metrics.paper_win_rate)

  return (
    <div className="container mx-auto px-4 py-12">
      {/* Pundit Header Card */}
      <div className="bg-white border rounded-3xl p-8 mb-8 shadow-sm">
        <div className="flex flex-col md:flex-row gap-8 items-start">
          <div className="relative h-32 w-32 flex-shrink-0 rounded-3xl border-4 border-slate-50 shadow-inner overflow-hidden bg-slate-100 flex items-center justify-center">
            {pundit.avatar_url ? (
              <img
                src={pundit.avatar_url}
                alt={pundit.name}
                className="h-full w-full object-cover"
              />
            ) : (
              <User className="h-16 w-16 text-slate-400" />
            )}
          </div>
          
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <h1 className="text-4xl font-black text-slate-900 tracking-tighter">{pundit.name}</h1>
              {pundit.verified && (
                <div className="bg-blue-600 text-white text-[10px] font-black px-2 py-1 rounded-md flex items-center gap-1 uppercase tracking-widest">
                  <CheckCircle className="h-3 w-3" /> Verified
                </div>
              )}
            </div>
            
            <p className="text-lg text-slate-500 font-medium mb-4">
              @{pundit.username} {pundit.affiliation && `• ${pundit.affiliation}`}
            </p>
            
            <p className="text-slate-600 leading-relaxed max-w-2xl mb-6">
              {pundit.bio}
            </p>

            <div className="flex flex-wrap gap-2">
              {pundit.domains.map((domain: string) => (
                <span key={domain} className="bg-slate-100 text-slate-600 text-xs font-bold px-3 py-1.5 rounded-full uppercase tracking-wider">
                  {domain}
                </span>
              ))}
            </div>
          </div>

          <div className="w-full md:w-auto grid grid-cols-2 md:grid-cols-3 gap-3">
            <div className="bg-slate-900 text-white p-6 rounded-2xl flex flex-col justify-between h-32 w-full">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Accuracy</span>
              <div>
                <span className="text-4xl font-black tracking-tighter">{formatPercent(pundit.metrics.paper_win_rate)}</span>
                <div className="flex gap-0.5 mt-1">
                  {[1,2,3,4,5].map(s => (
                    <Star key={s} className={cn("h-4 w-4", s <= stars ? "text-yellow-400 fill-yellow-400" : "text-slate-600")} />
                  ))}
                </div>
              </div>
            </div>
            <div className="bg-blue-600 text-white p-6 rounded-2xl flex flex-col justify-between h-32 w-full">
              <span className="text-[10px] font-black text-blue-200 uppercase tracking-widest">Record</span>
              <div>
                <span className="text-2xl font-black tracking-tighter text-emerald-300">{correctCount}W</span>
                <span className="text-xl font-bold mx-1">-</span>
                <span className="text-2xl font-black tracking-tighter text-rose-300">{wrongCount}L</span>
                {openCount > 0 && (
                  <span className="text-lg font-bold text-blue-200 ml-2">({openCount} open)</span>
                )}
              </div>
            </div>
            {pundit.net_worth && (
              <div className="bg-emerald-600 text-white p-6 rounded-2xl flex flex-col justify-between h-32 w-full col-span-2 md:col-span-1">
                <span className="text-[10px] font-black text-emerald-200 uppercase tracking-widest">Net Worth</span>
                <div>
                  <span className="text-3xl font-black tracking-tighter">
                    ${pundit.net_worth >= 1000 ? `${(pundit.net_worth / 1000).toFixed(1)}B` : `${pundit.net_worth}M`}
                  </span>
                  {pundit.net_worth_source && (
                    <div className="text-xs text-emerald-200 mt-1">
                      {pundit.net_worth_source} ({pundit.net_worth_year})
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Predictions */}
        <div className="lg:col-span-2 space-y-8">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-black text-slate-900 tracking-tight">Predictions History</h2>
              <div className="flex gap-2 text-xs font-bold uppercase tracking-widest text-slate-400">
                <span className="text-slate-900 border-b-2 border-slate-900 pb-1">All</span>
                <span className="hover:text-slate-600 cursor-pointer">Matched</span>
                <span className="hover:text-slate-600 cursor-pointer">Pending</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {predictions.length > 0 ? (
                predictions.map((pred: any) => (
                  <PredictionCard key={pred.id} prediction={pred} />
                ))
              ) : (
                <div className="col-span-2 bg-white border rounded-xl p-12 text-center text-slate-400 font-bold">
                  No predictions recorded for this pundit.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column - Metrics & Details */}
        <div className="space-y-8">
          <div className="bg-white border rounded-2xl p-6">
            <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-6">Stats</h3>
            <div className="space-y-4">
              {[
                { label: 'Total Predictions', value: pundit.metrics.total_predictions, icon: Target },
                { label: 'Resolved', value: pundit.metrics.resolved_predictions, icon: CheckCircle },
                { label: 'Correct', value: correctCount, icon: TrendingUp, color: 'text-emerald-600' },
                { label: 'Wrong', value: wrongCount, icon: Target, color: 'text-rose-600' },
                { label: 'Open', value: openCount, icon: Target, color: 'text-blue-600' },
              ].map((m: any, i: number) => (
                <div key={i} className="flex items-center justify-between py-3 border-b border-slate-50 last:border-0">
                  <div className="flex items-center gap-3">
                    <m.icon className="h-4 w-4 text-slate-400" />
                    <span className="text-sm font-bold text-slate-600">{m.label}</span>
                  </div>
                  <span className={cn("text-sm font-black text-slate-900", m.color)}>{m.value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-100 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Info className="h-5 w-5 text-blue-600" />
              <h3 className="text-sm font-black text-blue-900 uppercase tracking-widest">How we track</h3>
            </div>
            <p className="text-xs text-blue-800 leading-relaxed mb-4">
              TrackRecord uses natural language processing to extract verifiable predictions from public statements. These are then matched with Polymarket questions to simulate actual trading performance.
            </p>
            <Link href="/methodology" className="text-xs font-black text-blue-600 flex items-center gap-1 uppercase tracking-widest hover:underline">
              Full Methodology <ExternalLink className="h-3 w-3" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
