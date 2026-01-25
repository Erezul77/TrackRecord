// src/app/page.tsx
import { api, Pundit } from "@/lib/api"
import { LeaderboardTabs } from "@/components/leaderboard/LeaderboardTabs"
import { TrendingUp, Users, Target, BarChart3 } from "lucide-react"

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
    <div>
      {/* Hero Section - Clean B&W */}
      <section className="bg-white border-b border-neutral-200">
        <div className="container mx-auto px-4 py-20 md:py-28 text-center">
          <h1 className="text-4xl sm:text-5xl md:text-7xl font-black text-black tracking-tight mb-6 leading-[1.1]">
            Everyone talks.<br />
            <span className="text-neutral-400">We keep score.</span>
          </h1>
          <p className="text-lg md:text-xl text-neutral-500 max-w-xl mx-auto leading-relaxed">
            Tracking what pundits, politicians, and experts predict—and whether they're right.
          </p>
        </div>
      </section>

      {/* Stats Section - Clean with accent colors */}
      <section className="bg-black text-white py-8">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-4">
            {[
              { label: 'Pundits Tracked', value: '150+', icon: Users, color: 'text-blue-400' },
              { label: 'Predictions', value: '12.4k', icon: Target, color: 'text-white' },
              { label: 'Avg Accuracy', value: '42%', icon: BarChart3, color: 'text-amber-400' },
              { label: 'Verified', value: '8.2k', icon: TrendingUp, color: 'text-green-400' },
            ].map((stat: any, i: number) => (
              <div key={i} className="text-center">
                <div className={`text-3xl md:text-4xl font-black tracking-tight ${stat.color}`}>{stat.value}</div>
                <div className="text-xs font-medium text-neutral-500 uppercase tracking-widest mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Leaderboard Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="mb-10">
          <h2 className="text-2xl sm:text-3xl font-black text-black tracking-tight mb-2">Leaderboard</h2>
          <p className="text-neutral-500">Who's right most often? Track the best—and worst—predictors.</p>
        </div>

        <LeaderboardTabs pundits={pundits} />
      </section>
    </div>
  )
}
