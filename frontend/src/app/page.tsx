// src/app/page.tsx
import { api, Pundit } from "@/lib/api"
import { PunditCard } from "@/components/leaderboard/PunditCard"
import { TrendingUp, Users, Target, BarChart3 } from "lucide-react"
import { cn } from "@/lib/utils"

async function getPundits() {
  try {
    const data = await api.getLeaderboard()
    return data as Pundit[]
  } catch (e) {
    console.error(e)
    return []
  }
}

export default async function Home() {
  const pundits = await getPundits()

  return (
    <div className="container mx-auto px-4 py-12">
      {/* Hero Section */}
      <section className="text-center mb-20">
        <h1 className="text-5xl md:text-7xl font-black text-slate-900 tracking-tighter mb-6 leading-tight">
          Public Accountability for <br />
          <span className="text-blue-600">Public Predictions.</span>
        </h1>
        <p className="text-xl text-slate-500 max-w-2xl mx-auto leading-relaxed">
          We use AI to extract predictions from pundits across all media channels and track their financial performance via Polymarket integration.
        </p>
      </section>

      {/* Stats Section */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-20">
        {[
          { label: 'Pundits Tracked', value: '150+', icon: Users },
          { label: 'Predictions Captured', value: '12.4k', icon: Target },
          { label: 'Avg Win Rate', value: '42.1%', icon: BarChart3 },
          { label: 'Market Matches', value: '8.2k', icon: TrendingUp },
        ].map((stat: any, i: number) => (
          <div key={i} className="bg-white p-6 rounded-2xl border flex flex-col items-center text-center">
            <stat.icon className="h-6 w-6 text-blue-600 mb-2" />
            <div className="text-3xl font-black text-slate-900 tracking-tight">{stat.value}</div>
            <div className="text-xs font-bold text-slate-400 uppercase tracking-widest">{stat.label}</div>
          </div>
        ))}
      </section>

      {/* Leaderboard Section */}
      <section>
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-black text-slate-900 tracking-tight">Pundit Leaderboard</h2>
            <p className="text-slate-500 font-medium">Ranked by All-Time Paper Trading P&L</p>
          </div>
          <div className="flex gap-2">
            {/* Simple Category Filter Mockup */}
            {['All', 'Politics', 'Economy', 'Crypto'].map((cat: string) => (
              <button key={cat} className={cn(
                "text-sm font-bold px-4 py-2 rounded-lg transition-colors",
                cat === 'All' ? "bg-blue-600 text-white shadow-sm" : "bg-white text-slate-600 border hover:bg-slate-50"
              )}>
                {cat}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          {pundits.length > 0 ? (
            pundits.map((pundit: Pundit, index: number) => (
              <PunditCard key={pundit.id} pundit={pundit} rank={index + 1} />
            ))
          ) : (
            <div className="bg-white border rounded-xl p-12 text-center">
              <p className="text-slate-500 font-medium">No pundit data found. Start by populating the database!</p>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
