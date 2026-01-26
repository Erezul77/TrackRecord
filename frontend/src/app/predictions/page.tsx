// src/app/predictions/page.tsx
import { PredictionsList } from "@/components/predictions/PredictionsList"

export default function PredictionsPage() {
  return (
    <div className="container mx-auto px-4 py-12">
      <div className="mb-8">
        <h1 className="text-4xl font-black text-black dark:text-white tracking-tighter mb-2">Recent Predictions</h1>
        <p className="text-neutral-500 font-medium text-lg">The latest verifiable claims captured from across the web. Vote on predictions you agree or disagree with!</p>
      </div>

      <PredictionsList />
    </div>
  )
}
