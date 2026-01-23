// src/app/predictions/page.tsx
import { api, PredictionWithPundit } from "@/lib/api"
import { Clock } from "lucide-react"
import { PredictionCardWithVotes } from "@/components/predictions/PredictionCardWithVotes"

async function getRecentPredictions() {
  try {
    return await api.getRecentPredictions(50)
  } catch (e) {
    console.error(e)
    return []
  }
}

export default async function PredictionsPage() {
  const predictions: PredictionWithPundit[] = await getRecentPredictions()

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="mb-12">
        <h1 className="text-4xl font-black text-slate-900 tracking-tighter mb-2">Recent Predictions</h1>
        <p className="text-slate-500 font-medium text-lg">The latest verifiable claims captured from across the web. Vote on predictions you agree or disagree with!</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {predictions.length > 0 ? (
          predictions.map((pred) => (
            <PredictionCardWithVotes key={pred.id} prediction={pred} />
          ))
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
