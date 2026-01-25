// src/app/privacy/page.tsx
export default function PrivacyPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-3xl">
      <h1 className="text-4xl font-black text-slate-900 mb-8">Privacy Policy</h1>
      
      <div className="prose prose-slate max-w-none">
        <p className="text-lg text-slate-600 mb-6">
          Last updated: January 2026
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">1. Information We Collect</h2>
        <p className="text-slate-600 mb-4">
          TrackRecord collects minimal personal information:
        </p>
        <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
          <li>Display name (chosen by you when registering)</li>
          <li>Predictions you submit</li>
          <li>Votes on predictions</li>
          <li>Usage data (page views, interactions)</li>
        </ul>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">2. How We Use Your Information</h2>
        <p className="text-slate-600 mb-4">
          We use your information to:
        </p>
        <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
          <li>Display your predictions and track record</li>
          <li>Calculate accuracy scores</li>
          <li>Show community votes</li>
          <li>Improve our service</li>
        </ul>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">3. Data Storage</h2>
        <p className="text-slate-600 mb-4">
          Your data is stored securely on our servers. We do not sell your personal information to third parties.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">4. Cookies</h2>
        <p className="text-slate-600 mb-4">
          We use localStorage to remember your preferences and login status. No third-party tracking cookies are used.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">5. Contact</h2>
        <p className="text-slate-600 mb-4">
          For privacy questions, contact us at: privacy@trackrecord.io
        </p>
      </div>
    </div>
  )
}
