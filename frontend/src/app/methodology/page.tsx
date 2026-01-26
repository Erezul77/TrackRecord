// src/app/methodology/page.tsx
import { BarChart3, Target, Scale, Clock } from 'lucide-react'

export default function MethodologyPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-3xl">
      <h1 className="text-4xl font-black text-black dark:text-white tracking-tighter mb-4">Methodology</h1>
      <p className="text-neutral-500 text-lg mb-12">
        How we track, score, and rank predictions from public figures.
      </p>

      <div className="space-y-12">
        {/* Section 1 */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-black dark:bg-white rounded-lg">
              <Target className="h-5 w-5 text-white dark:text-black" />
            </div>
            <h2 className="text-2xl font-bold text-black dark:text-white">What We Track</h2>
          </div>
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl p-6">
            <ul className="space-y-3 text-neutral-600 dark:text-neutral-400">
              <li><strong className="text-black dark:text-white">Specific predictions</strong> — Not vague opinions, but measurable claims with clear outcomes</li>
              <li><strong className="text-black dark:text-white">Clear timeframes</strong> — Every prediction must have a deadline for resolution</li>
              <li><strong className="text-black dark:text-white">Verifiable sources</strong> — All predictions are linked to public statements (articles, tweets, videos)</li>
              <li><strong className="text-black dark:text-white">Binary outcomes</strong> — Predictions are scored as CORRECT or WRONG, no partial credit</li>
            </ul>
          </div>
        </section>

        {/* Section 2 */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-black dark:bg-white rounded-lg">
              <BarChart3 className="h-5 w-5 text-white dark:text-black" />
            </div>
            <h2 className="text-2xl font-bold text-black dark:text-white">Scoring System</h2>
          </div>
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl p-6">
            <p className="text-neutral-600 dark:text-neutral-400 mb-4">
              We use a paper trading simulation to calculate PnL (Profit & Loss) for each prediction:
            </p>
            <ul className="space-y-3 text-neutral-600 dark:text-neutral-400">
              <li><strong className="text-black dark:text-white">Position sizing</strong> — $100 virtual stake per prediction</li>
              <li><strong className="text-black dark:text-white">Market odds</strong> — When available, we use Polymarket odds to determine potential returns</li>
              <li><strong className="text-black dark:text-white">Win rate</strong> — Simple percentage of correct predictions</li>
              <li><strong className="text-black dark:text-white">ROI</strong> — Return on investment based on simulated trades</li>
            </ul>
          </div>
        </section>

        {/* Section 3 */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-black dark:bg-white rounded-lg">
              <Scale className="h-5 w-5 text-white dark:text-black" />
            </div>
            <h2 className="text-2xl font-bold text-black dark:text-white">Ranking Criteria</h2>
          </div>
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl p-6">
            <p className="text-neutral-600 dark:text-neutral-400 mb-4">
              Pundits are ranked by their paper PnL. To appear on the leaderboard:
            </p>
            <ul className="space-y-3 text-neutral-600 dark:text-neutral-400">
              <li><strong className="text-black dark:text-white">Minimum 3 resolved predictions</strong> — Ensures statistical relevance</li>
              <li><strong className="text-black dark:text-white">Primary sort: Total PnL</strong> — Who's made the most (or lost the least)</li>
              <li><strong className="text-black dark:text-white">Secondary: Win rate</strong> — Consistency matters</li>
            </ul>
          </div>
        </section>

        {/* Section 4 */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-black dark:bg-white rounded-lg">
              <Clock className="h-5 w-5 text-white dark:text-black" />
            </div>
            <h2 className="text-2xl font-bold text-black dark:text-white">Resolution Process</h2>
          </div>
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl p-6">
            <p className="text-neutral-600 dark:text-neutral-400 mb-4">
              Predictions are resolved through a transparent process:
            </p>
            <ul className="space-y-3 text-neutral-600 dark:text-neutral-400">
              <li><strong className="text-black dark:text-white">Automatic matching</strong> — AI matches predictions to Polymarket outcomes when possible</li>
              <li><strong className="text-black dark:text-white">Manual review</strong> — Our team reviews edge cases and ambiguous outcomes</li>
              <li><strong className="text-black dark:text-white">Community input</strong> — Users can vote on prediction accuracy</li>
              <li><strong className="text-black dark:text-white">Appeal process</strong> — Disputed resolutions can be reviewed</li>
            </ul>
          </div>
        </section>
      </div>

      <div className="mt-12 p-6 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl">
        <p className="text-sm text-neutral-500 text-center">
          Our methodology is constantly evolving. Have suggestions? Contact us at{' '}
          <a href="mailto:feedback@trackrecord.life" className="text-black dark:text-white hover:underline">
            feedback@trackrecord.life
          </a>
        </p>
      </div>
    </div>
  )
}
