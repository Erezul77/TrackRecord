// src/app/terms/page.tsx
export default function TermsPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-3xl">
      <h1 className="text-4xl font-black text-black dark:text-white tracking-tighter mb-4">Terms of Service</h1>
      <p className="text-neutral-500 mb-8">Last updated: January 2026</p>

      <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl p-6 space-y-6">
        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">1. Acceptance of Terms</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            By accessing or using TrackRecord, you agree to be bound by these Terms of Service. If you do not agree, please do not use the service.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">2. Description of Service</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            TrackRecord is a platform that tracks and scores public predictions made by pundits, analysts, and other public figures. We aggregate publicly available statements and evaluate their accuracy over time.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">3. User Accounts</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            You may create an account to participate in the community prediction competition. You are responsible for maintaining the confidentiality of your account credentials and for all activities under your account.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">4. User Submissions</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            When you submit predictions or content, you grant TrackRecord a non-exclusive, royalty-free license to display, distribute, and use that content on the platform. You retain ownership of your submissions.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">5. Prohibited Conduct</h2>
          <ul className="list-disc list-inside text-neutral-600 dark:text-neutral-400 space-y-1">
            <li>Submitting false or misleading information</li>
            <li>Attempting to manipulate rankings or scores</li>
            <li>Impersonating other users or public figures</li>
            <li>Using automated tools to spam or abuse the platform</li>
            <li>Violating any applicable laws or regulations</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">6. Intellectual Property</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            All content, design, and code on TrackRecord is owned by us or our licensors. You may not copy, modify, or distribute our content without permission.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">7. Disclaimers</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            TrackRecord is provided "as is" without warranties of any kind. We do not guarantee the accuracy of prediction scores or rankings. See our Disclaimer page for more details.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">8. Limitation of Liability</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            TrackRecord shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of the service.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">9. Changes to Terms</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            We may update these terms from time to time. Continued use of the service constitutes acceptance of the updated terms.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-black dark:text-white mb-3">10. Contact</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            Questions? Contact us at{' '}
            <a href="mailto:legal@trackrecord.life" className="text-black dark:text-white hover:underline">
              legal@trackrecord.life
            </a>
          </p>
        </section>
      </div>
    </div>
  )
}
