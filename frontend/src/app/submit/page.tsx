// src/app/submit/page.tsx
'use client'
import { useState } from 'react'
import { Send, CheckCircle, AlertCircle, History, Link as LinkIcon } from 'lucide-react'
import { KNOWN_PUNDITS, searchKnownPundits } from '@/data/knownPundits'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function SubmitPage() {
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  
  // Form state
  const [formData, setFormData] = useState({
    pundit_name: '',
    pundit_username: '',
    claim: '',
    quote: '',
    source_url: '',
    prediction_date: '',
    resolution_date: '',
    outcome: 'unknown',
    outcome_notes: '',
    category: 'markets',
    submitter_email: ''
  })
  
  // Pundit autocomplete
  const [showSuggestions, setShowSuggestions] = useState(false)
  const suggestions = searchKnownPundits(formData.pundit_name).slice(0, 5)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)
    
    try {
      const res = await fetch(`${API_URL}/api/submit-prediction`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      if (res.ok) {
        setMessage({ type: 'success', text: 'Thank you! Your submission has been received and will be reviewed.' })
        setFormData({
          pundit_name: '',
          pundit_username: '',
          claim: '',
          quote: '',
          source_url: '',
          prediction_date: '',
          resolution_date: '',
          outcome: 'unknown',
          outcome_notes: '',
          category: 'markets',
          submitter_email: ''
        })
      } else {
        const data = await res.json()
        setMessage({ type: 'error', text: data.detail || 'Submission failed. Please try again.' })
      }
    } catch (err) {
      // Store locally if API fails
      const submissions = JSON.parse(localStorage.getItem('pending_submissions') || '[]')
      submissions.push({ ...formData, submitted_at: new Date().toISOString() })
      localStorage.setItem('pending_submissions', JSON.stringify(submissions))
      setMessage({ type: 'success', text: 'Saved locally! Will sync when connection restored.' })
    }
    
    setLoading(false)
  }

  return (
    <div className="container mx-auto px-4 py-12 max-w-2xl">
      <div className="mb-8">
        <h1 className="text-3xl font-black text-slate-900 mb-2 flex items-center gap-3">
          <History className="h-8 w-8 text-blue-600" />
          Submit Historical Prediction
        </h1>
        <p className="text-slate-500">
          Help us build the most comprehensive pundit accountability database. 
          Submit predictions from any public figure with a verifiable source.
        </p>
      </div>

      {/* Guidelines */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-8">
        <h3 className="font-bold text-blue-900 mb-2">Submission Guidelines</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Must be a <strong>specific, measurable prediction</strong> (not vague opinions)</li>
          <li>• Must have a <strong>clear timeframe</strong> (when it should resolve)</li>
          <li>• Must include <strong>source URL</strong> (article, tweet, video, etc.)</li>
          <li>• Must be from a <strong>public figure</strong> (investor, analyst, politician, etc.)</li>
        </ul>
      </div>

      {/* Message */}
      {message && (
        <div className={`mb-6 p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
        }`}>
          {message.type === 'success' ? <CheckCircle className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
          {message.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white border rounded-xl p-6 space-y-6">
        {/* Pundit Info */}
        <div className="border-b pb-4 mb-4">
          <h3 className="font-bold text-slate-900 mb-4">Who made the prediction?</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="relative">
              <label className="block text-sm font-bold text-slate-700 mb-2">Pundit Name *</label>
              <input
                type="text"
                value={formData.pundit_name}
                onChange={(e) => {
                  setFormData({...formData, pundit_name: e.target.value})
                  setShowSuggestions(true)
                }}
                onFocus={() => setShowSuggestions(true)}
                placeholder="e.g., Jim Cramer"
                className="w-full border rounded-lg px-4 py-2 text-slate-900"
                required
              />
              
              {/* Autocomplete */}
              {showSuggestions && formData.pundit_name.length >= 2 && suggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-40 overflow-y-auto">
                  {suggestions.map(s => (
                    <button
                      key={s.username}
                      type="button"
                      onClick={() => {
                        setFormData({
                          ...formData,
                          pundit_name: s.name,
                          pundit_username: s.username
                        })
                        setShowSuggestions(false)
                      }}
                      className="w-full px-4 py-2 text-left hover:bg-blue-50 text-sm"
                    >
                      <span className="font-bold">{s.name}</span>
                      <span className="text-slate-500 ml-2">@{s.username}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Twitter/X Username</label>
              <input
                type="text"
                value={formData.pundit_username}
                onChange={(e) => setFormData({...formData, pundit_username: e.target.value})}
                placeholder="e.g., jimcramer (optional)"
                className="w-full border rounded-lg px-4 py-2 text-slate-900"
              />
            </div>
          </div>
        </div>

        {/* Prediction Details */}
        <div className="border-b pb-4 mb-4">
          <h3 className="font-bold text-slate-900 mb-4">What did they predict?</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Prediction Claim *</label>
              <input
                type="text"
                value={formData.claim}
                onChange={(e) => setFormData({...formData, claim: e.target.value})}
                placeholder="e.g., Bitcoin will reach $100,000 by end of 2024"
                className="w-full border rounded-lg px-4 py-2 text-slate-900"
                required
              />
              <p className="text-xs text-slate-400 mt-1">Be specific: include target price/event and deadline</p>
            </div>
            
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Original Quote *</label>
              <textarea
                value={formData.quote}
                onChange={(e) => setFormData({...formData, quote: e.target.value})}
                placeholder="Paste the exact words they said..."
                className="w-full border rounded-lg px-4 py-2 text-slate-900 h-24"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">
                <LinkIcon className="h-4 w-4 inline mr-1" />
                Source URL *
              </label>
              <input
                type="url"
                value={formData.source_url}
                onChange={(e) => setFormData({...formData, source_url: e.target.value})}
                placeholder="https://twitter.com/... or https://youtube.com/..."
                className="w-full border rounded-lg px-4 py-2 text-slate-900"
                required
              />
              <p className="text-xs text-slate-400 mt-1">Tweet, article, video, podcast - any verifiable source</p>
            </div>
          </div>
        </div>

        {/* Dates & Outcome */}
        <div className="border-b pb-4 mb-4">
          <h3 className="font-bold text-slate-900 mb-4">When and how did it resolve?</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Date Prediction Made *</label>
              <input
                type="date"
                value={formData.prediction_date}
                onChange={(e) => setFormData({...formData, prediction_date: e.target.value})}
                className="w-full border rounded-lg px-4 py-2 text-slate-900"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Resolution Deadline</label>
              <input
                type="date"
                value={formData.resolution_date}
                onChange={(e) => setFormData({...formData, resolution_date: e.target.value})}
                className="w-full border rounded-lg px-4 py-2 text-slate-900"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Outcome</label>
              <select
                value={formData.outcome}
                onChange={(e) => setFormData({...formData, outcome: e.target.value})}
                className="w-full border rounded-lg px-4 py-2 text-slate-900"
              >
                <option value="unknown">Unknown / Still Open</option>
                <option value="right">Correct (Pundit was RIGHT)</option>
                <option value="wrong">Wrong (Pundit was WRONG)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
                className="w-full border rounded-lg px-4 py-2 text-slate-900"
              >
                <option value="markets">Markets / Stocks</option>
                <option value="crypto">Crypto</option>
                <option value="economy">Economy</option>
                <option value="politics">Politics</option>
                <option value="tech">Tech</option>
                <option value="macro">Macro</option>
                <option value="sports">Sports</option>
                <option value="entertainment">Entertainment</option>
                <option value="religion">Religion</option>
                <option value="science">Science</option>
                <option value="health">Health</option>
                <option value="climate">Climate</option>
                <option value="geopolitics">Geopolitics</option>
              </select>
            </div>
          </div>
          
          <div className="mt-4">
            <label className="block text-sm font-bold text-slate-700 mb-2">Outcome Notes</label>
            <input
              type="text"
              value={formData.outcome_notes}
              onChange={(e) => setFormData({...formData, outcome_notes: e.target.value})}
              placeholder="e.g., Bitcoin reached $73k but not $100k target"
              className="w-full border rounded-lg px-4 py-2 text-slate-900"
            />
          </div>
        </div>

        {/* Contact (optional) */}
        <div>
          <label className="block text-sm font-bold text-slate-700 mb-2">Your Email (optional)</label>
          <input
            type="email"
            value={formData.submitter_email}
            onChange={(e) => setFormData({...formData, submitter_email: e.target.value})}
            placeholder="Get notified when your submission is reviewed"
            className="w-full border rounded-lg px-4 py-2 text-slate-900"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white font-bold py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <Send className="h-5 w-5" />
          {loading ? 'Submitting...' : 'Submit Prediction'}
        </button>
        
        <p className="text-xs text-slate-400 text-center">
          All submissions are reviewed before being added to the database.
          We verify sources and check for accuracy.
        </p>
      </form>

      {/* Examples */}
      <div className="mt-8 bg-slate-50 border rounded-xl p-6">
        <h3 className="font-bold text-slate-900 mb-4">Example Good Submissions</h3>
        <div className="space-y-4 text-sm">
          <div className="bg-white border rounded-lg p-3">
            <p className="font-bold text-emerald-600">✓ Good Prediction</p>
            <p className="text-slate-700">"Bitcoin will reach $100,000 by December 31, 2024"</p>
            <p className="text-slate-500">Clear target + clear deadline = measurable</p>
          </div>
          <div className="bg-white border rounded-lg p-3">
            <p className="font-bold text-rose-600">✗ Bad Prediction</p>
            <p className="text-slate-700">"Bitcoin is going to the moon"</p>
            <p className="text-slate-500">No target + no deadline = unmeasurable</p>
          </div>
        </div>
      </div>
    </div>
  )
}
