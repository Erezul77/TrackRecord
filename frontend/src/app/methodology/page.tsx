// src/app/methodology/page.tsx
import { BarChart3, Target, Scale, Clock, Shield, Link } from 'lucide-react'

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
            <div className="p-2 bg-black dark:bg-white ">
              <Target className="h-5 w-5 text-white dark:text-black" />
            </div>
            <h2 className="text-2xl font-bold text-black dark:text-white">What We Track</h2>
          </div>
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800  p-6">
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
            <div className="p-2 bg-black dark:bg-white ">
              <BarChart3 className="h-5 w-5 text-white dark:text-black" />
            </div>
            <h2 className="text-2xl font-bold text-black dark:text-white">Scoring System</h2>
          </div>
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800  p-6">
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
            <div className="p-2 bg-black dark:bg-white ">
              <Scale className="h-5 w-5 text-white dark:text-black" />
            </div>
            <h2 className="text-2xl font-bold text-black dark:text-white">Ranking Criteria</h2>
          </div>
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800  p-6">
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
            <div className="p-2 bg-black dark:bg-white ">
              <Clock className="h-5 w-5 text-white dark:text-black" />
            </div>
            <h2 className="text-2xl font-bold text-black dark:text-white">Resolution Process</h2>
          </div>
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800  p-6">
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

        {/* Section 5 - Hash Chain */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-green-600">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-black dark:text-white">Cryptographic Verification</h2>
          </div>
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-6">
            <p className="text-neutral-600 dark:text-neutral-400 mb-4">
              Every prediction is cryptographically sealed and linked in a tamper-evident chain:
            </p>
            <ul className="space-y-3 text-neutral-600 dark:text-neutral-400">
              <li><strong className="text-black dark:text-white">Content Hash</strong> — Each prediction's claim, quote, source, and timestamp are hashed using SHA-256</li>
              <li><strong className="text-black dark:text-white">Chain Link</strong> — Each prediction links to the previous one, creating an unbreakable chain</li>
              <li><strong className="text-black dark:text-white">Tamper-Evident</strong> — Any modification to past predictions breaks the chain and is immediately detectable</li>
              <li><strong className="text-black dark:text-white">Public Verification</strong> — Anyone can verify a prediction's authenticity using its hash</li>
            </ul>
            
            <div className="mt-6 p-4 bg-neutral-50 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700">
              <div className="flex items-center gap-2 mb-3">
                <Link className="h-4 w-4 text-green-600 dark:text-green-400" />
                <span className="text-sm font-bold text-black dark:text-white">How It Works</span>
              </div>
              <div className="text-xs font-mono text-neutral-500 dark:text-neutral-400 space-y-1">
                <p>content_hash = SHA256(claim + quote + source + timestamp)</p>
                <p>chain_hash = SHA256(content_hash + previous_chain_hash + index)</p>
              </div>
              <p className="text-xs text-neutral-500 mt-3">
                Look for the <Shield className="h-3 w-3 inline text-green-600" /> Verified badge on prediction cards to see the hash.
              </p>
            </div>
          </div>
        </section>
      </div>

      <div className="mt-12 p-6 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 ">
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
