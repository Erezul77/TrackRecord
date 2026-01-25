// src/app/disclaimer/page.tsx
export default function DisclaimerPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-3xl">
      <h1 className="text-4xl font-black text-slate-900 mb-8">Disclaimer</h1>
      
      <div className="prose prose-slate max-w-none">
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 mb-8">
          <p className="text-amber-800 font-bold text-lg">
            Important: TrackRecord is NOT financial advice. Do not make investment decisions based on information from this platform.
          </p>
        </div>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">General Disclaimer</h2>
        <p className="text-slate-600 mb-4">
          TrackRecord tracks publicly available predictions made by pundits, analysts, and public figures. The information presented is for educational and entertainment purposes only.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">No Investment Advice</h2>
        <p className="text-slate-600 mb-4">
          Nothing on TrackRecord constitutes investment advice, financial advice, trading advice, or any other sort of advice. You should not treat any of the platform's content as such.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">Accuracy of Information</h2>
        <p className="text-slate-600 mb-4">
          While we strive for accuracy in tracking predictions and their outcomes:
        </p>
        <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
          <li>Prediction attributions may contain errors</li>
          <li>Outcome determinations involve judgment calls</li>
          <li>Historical data may be incomplete</li>
          <li>We rely on public sources that may themselves contain errors</li>
        </ul>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">Third-Party Content</h2>
        <p className="text-slate-600 mb-4">
          TrackRecord aggregates content from various sources including news articles, social media, and prediction markets. We do not control or endorse third-party content.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">Limitation of Liability</h2>
        <p className="text-slate-600 mb-4">
          TrackRecord and its creators shall not be liable for any damages arising from the use of this platform, including but not limited to financial losses from investment decisions.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">Fair Use</h2>
        <p className="text-slate-600 mb-4">
          We believe our use of quotations and predictions constitutes fair use for purposes of commentary, criticism, and education. If you believe your content has been used incorrectly, please contact us.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">Contact</h2>
        <p className="text-slate-600 mb-4">
          For questions or concerns: legal@trackrecord.io
        </p>
      </div>
    </div>
  )
}
