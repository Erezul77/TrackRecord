// src/app/methodology/page.tsx
export default function MethodologyPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-3xl">
      <h1 className="text-4xl font-black text-slate-900 mb-8">Our Methodology</h1>
      
      <div className="prose prose-slate max-w-none">
        <p className="text-lg text-slate-600 mb-6">
          How we track predictions and calculate accuracy scores.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">1. What Counts as a Prediction?</h2>
        <p className="text-slate-600 mb-4">
          A valid prediction must have:
        </p>
        <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
          <li><strong>Specific Claim:</strong> A clear statement about what will happen</li>
          <li><strong>Timeframe:</strong> When the prediction can be verified (explicit or implicit)</li>
          <li><strong>Verifiability:</strong> Can be objectively determined as right or wrong</li>
          <li><strong>Attribution:</strong> Clearly stated by a specific person</li>
        </ul>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">2. How We Score Predictions</h2>
        <div className="bg-slate-100 rounded-xl p-6 mb-6">
          <p className="text-slate-700 font-bold mb-2">Binary Outcomes:</p>
          <p className="text-slate-600">Each prediction is resolved as either <span className="text-emerald-600 font-bold">CORRECT</span> or <span className="text-rose-600 font-bold">WRONG</span>.</p>
          <p className="text-slate-600 mt-2">Win Rate = Correct Predictions / Total Resolved Predictions</p>
        </div>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">3. TR Prediction Index</h2>
        <p className="text-slate-600 mb-4">
          Each prediction is scored on multiple dimensions:
        </p>
        <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
          <li><strong>Specificity (1-5):</strong> How precise is the prediction?</li>
          <li><strong>Verifiability (1-5):</strong> How easy to verify objectively?</li>
          <li><strong>Boldness (1-5):</strong> How contrarian vs. consensus?</li>
          <li><strong>Stakes (1-5):</strong> How significant if true?</li>
        </ul>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">4. Data Sources</h2>
        <p className="text-slate-600 mb-4">
          We collect predictions from:
        </p>
        <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
          <li>News articles (via RSS feeds from major outlets)</li>
          <li>Social media posts (Twitter/X)</li>
          <li>TV appearances and interviews</li>
          <li>Podcasts and videos</li>
          <li>Official statements and press releases</li>
          <li>Community submissions (verified before inclusion)</li>
        </ul>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">5. Resolution Process</h2>
        <p className="text-slate-600 mb-4">
          Predictions are resolved through:
        </p>
        <ul className="list-disc pl-6 text-slate-600 space-y-2 mb-6">
          <li><strong>Prediction Markets:</strong> Using Polymarket outcomes when available</li>
          <li><strong>Manual Verification:</strong> Admin review with evidence links</li>
          <li><strong>Community Input:</strong> Votes inform but don't determine outcomes</li>
        </ul>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">6. Minimum Requirements</h2>
        <p className="text-slate-600 mb-4">
          A pundit needs at least <strong>3 resolved predictions</strong> to appear in official rankings. This ensures statistical significance.
        </p>
        
        <h2 className="text-2xl font-bold text-slate-900 mt-8 mb-4">7. Dispute Process</h2>
        <p className="text-slate-600 mb-4">
          If you believe a prediction was incorrectly attributed or resolved, contact us with evidence at: disputes@trackrecord.io
        </p>
      </div>
    </div>
  )
}
