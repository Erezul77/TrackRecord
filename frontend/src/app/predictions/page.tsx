// src/app/predictions/page.tsx
import { PredictionsList } from "@/components/predictions/PredictionsList"

export default function PredictionsPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl sm:text-4xl font-black text-black dark:text-white tracking-tighter mb-1">Predictions</h1>
        <p className="text-neutral-500 text-sm sm:text-base">Browse and vote on verifiable predictions from pundits across the web.</p>
      </div>

      <PredictionsList />
    </div>
  )
}
