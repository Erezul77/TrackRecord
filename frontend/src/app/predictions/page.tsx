// src/app/predictions/page.tsx
import { PredictionsList } from "@/components/predictions/PredictionsList"
import { Sparkles, Clock, CheckCircle, XCircle, Hourglass } from "lucide-react"

export default function PredictionsPage() {
  return (
    <div className="container mx-auto px-4 py-12">
      <div className="mb-8">
        <h1 className="text-4xl font-black text-black dark:text-white tracking-tighter mb-2">Recent Predictions</h1>
        <p className="text-neutral-500 font-medium text-lg">The latest verifiable claims captured from across the web. Vote on predictions you agree or disagree with!</p>
      </div>

      {/* Legend / Guide */}
      <div className="mb-8 p-4 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg">
        <h3 className="font-bold text-sm text-black dark:text-white mb-3">How to Read Predictions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {/* Status Labels */}
          <div>
            <p className="font-semibold text-neutral-600 dark:text-neutral-400 mb-2">Status Labels:</p>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1 px-2 py-0.5 bg-blue-600 text-white rounded text-[10px] font-bold">
                  <Clock className="h-3 w-3" /> TRACKING
                </span>
                <span className="text-neutral-500">Still waiting for deadline</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1 px-2 py-0.5 bg-amber-500 text-white rounded text-[10px] font-bold">
                  <Hourglass className="h-3 w-3" /> AWAITING
                </span>
                <span className="text-neutral-500">Past deadline, pending resolution</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1 px-2 py-0.5 bg-green-500 text-white rounded text-[10px] font-bold">
                  <CheckCircle className="h-3 w-3" /> CORRECT
                </span>
                <span className="text-neutral-500">Prediction came true</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1 px-2 py-0.5 bg-red-500 text-white rounded text-[10px] font-bold">
                  <XCircle className="h-3 w-3" /> WRONG
                </span>
                <span className="text-neutral-500">Prediction was incorrect</span>
              </div>
            </div>
          </div>
          
          {/* TR Index */}
          <div>
            <p className="font-semibold text-neutral-600 dark:text-neutral-400 mb-2">TR Index (Quality Score):</p>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1 px-2 py-0.5 bg-yellow-400 text-yellow-900 rounded-full text-[10px] font-bold">
                  <Sparkles className="h-3 w-3" /> 80+
                </span>
                <span className="text-neutral-500">Gold - Exceptional quality</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1 px-2 py-0.5 bg-neutral-300 text-neutral-800 rounded-full text-[10px] font-bold">
                  <Sparkles className="h-3 w-3" /> 60-79
                </span>
                <span className="text-neutral-500">Silver - Good quality</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1 px-2 py-0.5 bg-orange-300 text-orange-900 rounded-full text-[10px] font-bold">
                  <Sparkles className="h-3 w-3" /> 40-59
                </span>
                <span className="text-neutral-500">Bronze - Acceptable</span>
              </div>
              <p className="text-neutral-400 mt-2 text-[10px]">
                Score based on: Specificity, Verifiability, Boldness, Relevance, Stakes
              </p>
            </div>
          </div>
        </div>
      </div>

      <PredictionsList />
    </div>
  )
}
