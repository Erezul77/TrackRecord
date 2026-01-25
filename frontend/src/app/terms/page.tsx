// src/app/terms/page.tsx
export default function TermsPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-3xl">
      <h1 className="text-4xl font-black text-slate-900 mb-8">Terms of Service</h1>
      
      <div className="prose prose-slate max-w-none">
        <p className="text-lg text-slate-600 mb-6">
          Last updated: January 2026
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">1. Acceptance of Terms</h2>
        <p className="text-slate-600 mb-4">
          By using TrackRecord, you agree to these terms of service. If you do not agree, please do not use our service.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">2. Description of Service</h2>
        <p className="text-slate-600 mb-4">
          TrackRecord is a platform that tracks predictions made by public figures and community members. We aggregate publicly available statements and track their accuracy over time.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">3. User Content</h2>
        <p className="text-slate-600 mb-4">
          When you submit predictions or votes, you grant TrackRecord a license to display and use this content. You are responsible for ensuring your submissions are accurate and do not violate any laws.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">4. Accuracy Disclaimer</h2>
        <p className="text-slate-600 mb-4">
          While we strive for accuracy, TrackRecord cannot guarantee the accuracy of all information displayed. Prediction outcomes are determined by our verification process and may be subject to interpretation.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">5. Not Financial Advice</h2>
        <p className="text-slate-600 mb-4">
          TrackRecord is for informational and entertainment purposes only. Nothing on this platform constitutes financial, investment, or trading advice. Always do your own research.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">6. Prohibited Uses</h2>
        <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
          <li>Submitting false or misleading information</li>
          <li>Impersonating others</li>
          <li>Automated scraping without permission</li>
          <li>Harassment or abuse of other users</li>
        </ul>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">7. Modifications</h2>
        <p className="text-slate-600 mb-4">
          We reserve the right to modify these terms at any time. Continued use after changes constitutes acceptance.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">8. Contact</h2>
        <p className="text-slate-600 mb-4">
          For questions about these terms, contact us at: legal@trackrecord.io
        </p>
      </div>
    </div>
  )
}
