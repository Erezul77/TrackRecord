// src/app/privacy/page.tsx
export default function PrivacyPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-3xl">
      <h1 className="text-4xl font-black text-black dark:text-white tracking-tighter mb-4">Privacy Policy</h1>
      <p className="text-neutral-500 mb-8">Last updated: January 2026</p>

      <div className="prose prose-neutral dark:prose-invert max-w-none">
        <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl p-6 space-y-6">
          <section>
            <h2 className="text-xl font-bold text-black dark:text-white mb-3">Information We Collect</h2>
            <p className="text-neutral-600 dark:text-neutral-400">
              TrackRecord collects minimal personal information:
            </p>
            <ul className="list-disc list-inside text-neutral-600 dark:text-neutral-400 mt-2 space-y-1">
              <li>Email address (if you register for the community competition)</li>
              <li>Username and display name (for leaderboard)</li>
              <li>Predictions you submit (public by default)</li>
              <li>Basic analytics data (page views, anonymized)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-black dark:text-white mb-3">How We Use Your Data</h2>
            <ul className="list-disc list-inside text-neutral-600 dark:text-neutral-400 space-y-1">
              <li>To display your predictions and track record on the platform</li>
              <li>To send occasional updates about your predictions (if opted in)</li>
              <li>To improve our service and user experience</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-black dark:text-white mb-3">Data Sharing</h2>
            <p className="text-neutral-600 dark:text-neutral-400">
              We do not sell your personal data. Predictions and public profile information are visible to all users. We may share anonymized, aggregated data for research purposes.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-black dark:text-white mb-3">Cookies</h2>
            <p className="text-neutral-600 dark:text-neutral-400">
              We use essential cookies for authentication and preferences (like dark mode). We do not use advertising cookies.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-black dark:text-white mb-3">Your Rights</h2>
            <p className="text-neutral-600 dark:text-neutral-400">
              You can request deletion of your account and associated data by contacting us at{' '}
              <a href="mailto:privacy@trackrecord.life" className="text-black dark:text-white hover:underline">
                privacy@trackrecord.life
              </a>
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-black dark:text-white mb-3">Contact</h2>
            <p className="text-neutral-600 dark:text-neutral-400">
              Questions about this policy? Email{' '}
              <a href="mailto:privacy@trackrecord.life" className="text-black dark:text-white hover:underline">
                privacy@trackrecord.life
              </a>
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
