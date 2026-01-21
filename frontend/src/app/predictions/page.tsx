// src/app/predictions/page.tsx
import { api } from "@/lib/api"
import { PredictionCard } from "@/components/predictions/PredictionCard"

async function getRecentPredictions() {
  try {
    // We don't have a global recent predictions endpoint yet in our simplified backend, 
    // but we can mock it or just fetch from a few pundits.
    // In a real app, we'd add @app.get("/api/predictions/recent")
    const pundits = await api.getLeaderboard()
    if (pundits.length === 0) return []
    
    // For now, let's just get predictions from the top pundit
    const predictions = await api.getPunditPredictions(pundits[0].id)
    return predictions
  } catch (e) {
    console.error(e)
    return []
  }
}

export default async function PredictionsPage() {
  const predictions = await getRecentPredictions()

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="mb-12">
        <h1 className="text-4xl font-black text-slate-900 tracking-tighter mb-2">Recent Predictions</h1>
        <p className="text-slate-500 font-medium text-lg">The latest verifiable claims captured from across the web.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {predictions.length > 0 ? (
          predictions.map((pred: any) => (
            <PredictionCard key={pred.id} prediction={pred} />
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
