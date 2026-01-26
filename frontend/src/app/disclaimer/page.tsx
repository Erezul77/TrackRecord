// src/app/disclaimer/page.tsx
import { AlertTriangle } from 'lucide-react'

export default function DisclaimerPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-3xl">
      <h1 className="text-4xl font-black text-black dark:text-white tracking-tighter mb-4">Disclaimer</h1>
      <p className="text-neutral-500 mb-8">Important information about TrackRecord</p>

      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800  p-6 mb-8">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-6 w-6 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
          <p className="text-amber-800 dark:text-amber-300 font-medium">
            TrackRecord is for informational and entertainment purposes only. Nothing on this platform constitutes financial, investment, legal, or professional advice.
          </p>
        </div>
      </div>

      <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800  p-6 space-y-6">
        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">Not Financial Advice</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            The predictions, scores, rankings, and simulated trading results displayed on TrackRecord are not recommendations to buy, sell, or hold any securities, cryptocurrencies, or other financial instruments. Always consult a qualified financial advisor before making investment decisions.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">Accuracy of Information</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            While we strive for accuracy, we cannot guarantee that all predictions, quotes, or outcomes displayed are complete, accurate, or up-to-date. Predictions are sourced from publicly available information and may contain errors or omissions.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">Simulated Results</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            All PnL (Profit & Loss) figures shown are based on paper trading simulations and do not represent actual trading results. Simulated results have inherent limitations and should not be relied upon as indicators of future performance.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">Third-Party Content</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            TrackRecord aggregates predictions and statements from third-party sources. We do not endorse, verify, or take responsibility for the accuracy of any third-party content or the views expressed by the pundits tracked on our platform.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">Fair Use</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            Quotes and excerpts from public figures are used under fair use principles for the purpose of commentary, criticism, and news reporting. All original sources are linked where available.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">No Liability</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            TrackRecord, its operators, and contributors shall not be held liable for any losses, damages, or other consequences arising from the use of information on this platform. Use at your own risk.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">Changes</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            This disclaimer may be updated at any time. Please review periodically for changes.
          </p>
        </section>
      </div>

      <div className="mt-8 text-center text-neutral-500 text-sm">
        Questions about this disclaimer? Contact{' '}
        <a href="mailto:legal@trackrecord.life" className="text-black dark:text-white hover:underline">
          legal@trackrecord.life
        </a>
      </div>
    </div>
  )
}
