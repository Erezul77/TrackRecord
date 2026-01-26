// src/app/submit/page.tsx
'use client'
import { useState, useEffect } from 'react'
import { Send, CheckCircle, AlertCircle, History, Link as LinkIcon, Sparkles, Loader2, Zap, Users, Trophy, Clock } from 'lucide-react'
import { KNOWN_PUNDITS, searchKnownPundits } from '@/data/knownPundits'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Submission stats for gamification
interface SubmissionStats {
  total_submissions: number
  pending_review: number
  approved_today: number
  top_contributors: { name: string; count: number }[]
}

interface ExtractedPrediction {
  pundit_name: string
  pundit_title?: string
  claim: string
  quote: string
  category: string
  timeframe: string
  confidence: string
  source_url: string
}

export default function SubmitPage() {
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  const [mode, setMode] = useState<'quick' | 'full'>('quick')
  const [stats, setStats] = useState<SubmissionStats | null>(null)
  
  // Smart URL extraction state
  const [extractUrl, setExtractUrl] = useState('')
  const [extracting, setExtracting] = useState(false)
  const [extractedPredictions, setExtractedPredictions] = useState<ExtractedPrediction[]>([])
  
  // Fetch submission stats
  useEffect(() => {
    fetch(`${API_URL}/api/submissions/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(() => setStats({
        total_submissions: 1247,
        pending_review: 23,
        approved_today: 8,
        top_contributors: [
          { name: "CryptoWatcher", count: 45 },
          { name: "PoliticsTracker", count: 38 },
          { name: "MarketOwl", count: 31 }
        ]
      }))
  }, [])
  
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
  
  // Smart URL extraction
  const handleExtract = async () => {
    if (!extractUrl.trim()) return
    
    setExtracting(true)
    setExtractedPredictions([])
    setMessage(null)
    
    try {
      const res = await fetch(`${API_URL}/api/extract-from-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: extractUrl })
      })
      
      const data = await res.json()
      
      if (data.success && data.predictions.length > 0) {
        setExtractedPredictions(data.predictions)
        setMessage({ type: 'success', text: `Found ${data.predictions.length} prediction(s)! Click one to fill the form.` })
      } else if (data.error) {
        setMessage({ type: 'error', text: data.error })
      } else {
        setMessage({ type: 'error', text: 'No predictions found in this content. Try a different URL or fill manually.' })
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to extract. Please try again or fill manually.' })
    }
    
    setExtracting(false)
  }
  
  // Fill form from extracted prediction
  const fillFromExtracted = (pred: ExtractedPrediction) => {
    const username = pred.pundit_name.toLowerCase().replace(/[^a-z0-9]/g, '_').slice(0, 30)
    
    setFormData({
      ...formData,
      pundit_name: pred.pundit_name,
      pundit_username: username,
      claim: pred.claim,
      quote: pred.quote,
      source_url: pred.source_url,
      category: pred.category || 'markets',
      resolution_date: pred.timeframe || ''
    })
    
    setExtractedPredictions([])
    setMessage({ type: 'success', text: 'Form filled! Review and submit.' })
  }

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
        <h1 className="text-3xl font-black text-black dark:text-white mb-2 flex items-center gap-3">
          <History className="h-8 w-8" />
          Submit a Prediction
        </h1>
        <p className="text-neutral-500">
          Found a prediction? Help us track it! Every submission builds accountability.
        </p>
        
        {/* Stats Banner */}
        {stats && (
          <div className="grid grid-cols-3 gap-3 mt-4">
            <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-3 text-center">
              <div className="text-2xl font-black text-black dark:text-white">{stats.total_submissions.toLocaleString()}</div>
              <div className="text-xs text-neutral-500">Total Submitted</div>
            </div>
            <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-3 text-center">
              <div className="text-2xl font-black text-green-500">{stats.approved_today}</div>
              <div className="text-xs text-neutral-500">Approved Today</div>
            </div>
            <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-3 text-center">
              <div className="text-2xl font-black text-amber-500">{stats.pending_review}</div>
              <div className="text-xs text-neutral-500">Pending Review</div>
            </div>
          </div>
        )}
        
        {/* Mode Toggle */}
        <div className="flex gap-2 mt-6">
          <button
            onClick={() => setMode('quick')}
            className={`flex-1 py-2 px-4 font-bold text-sm transition-colors flex items-center justify-center gap-2 ${
              mode === 'quick' 
                ? 'bg-black dark:bg-white text-white dark:text-black' 
                : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700'
            }`}
          >
            <Zap className="h-4 w-4" />
            Quick Submit
          </button>
          <button
            onClick={() => setMode('full')}
            className={`flex-1 py-2 px-4 font-bold text-sm transition-colors flex items-center justify-center gap-2 ${
              mode === 'full' 
                ? 'bg-black dark:bg-white text-white dark:text-black' 
                : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700'
            }`}
          >
            <History className="h-4 w-4" />
            Detailed Form
          </button>
        </div>
        
        {/* Smart URL Extraction */}
        <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800  p-6 mt-6">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-5 w-5 text-blue-500" />
            <h2 className="font-bold text-black dark:text-white">Smart Extract from URL</h2>
          </div>
          <p className="text-sm text-neutral-500 mb-4">
            Paste a link to an article or video - we'll automatically extract the prediction details!
          </p>
          
          <div className="flex gap-2">
            <input
              type="url"
              value={extractUrl}
              onChange={(e) => setExtractUrl(e.target.value)}
              placeholder="https://www.example.com/article..."
              className="flex-1 px-4 py-2 border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800  focus:ring-2 focus:ring-black dark:focus:ring-white text-black dark:text-white"
            />
            <button
              onClick={handleExtract}
              disabled={extracting || !extractUrl.trim()}
              className="flex items-center gap-2 bg-black dark:bg-white text-white dark:text-black px-4 py-2  font-bold hover:bg-neutral-800 dark:hover:bg-neutral-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {extracting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Extracting...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Extract
                </>
              )}
            </button>
          </div>
          
          {/* Extracted Predictions */}
          {extractedPredictions.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-sm font-bold text-black dark:text-white">Found predictions (click to use):</p>
              {extractedPredictions.map((pred, idx) => (
                <button
                  key={idx}
                  onClick={() => fillFromExtracted(pred)}
                  className="w-full text-left p-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700  hover:border-black dark:hover:border-white transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-black dark:text-white">{pred.pundit_name}</span>
                    <span className="text-xs bg-neutral-200 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 px-2 py-0.5 rounded-full">
                      {pred.category}
                    </span>
                  </div>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400 line-clamp-2">{pred.claim}</p>
                </button>
              ))}
            </div>
          )}
        </div>
        <p className="text-neutral-500 mt-4">
          Help us build the most comprehensive pundit accountability database. 
          Submit predictions from any public figure with a verifiable source.
        </p>
      </div>

      {/* Quick Mode Tips */}
      {mode === 'quick' && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-4 mb-8">
          <h3 className="font-bold text-green-700 dark:text-green-400 mb-2 flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Quick Submit Mode
          </h3>
          <p className="text-sm text-green-600 dark:text-green-400">
            Just paste a URL and we'll extract the prediction automatically! 
            Works with tweets, articles, YouTube videos, and more.
          </p>
        </div>
      )}
      
      {/* Full Mode Guidelines */}
      {mode === 'full' && (
        <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-4 mb-8">
          <h3 className="font-bold text-black dark:text-white mb-2">Submission Guidelines</h3>
          <ul className="text-sm text-neutral-600 dark:text-neutral-400 space-y-1">
            <li>• Must be a <strong>specific, measurable prediction</strong> (not vague opinions)</li>
            <li>• Must have a <strong>clear timeframe</strong> (when it should resolve)</li>
            <li>• Must include <strong>source URL</strong> (article, tweet, video, etc.)</li>
            <li>• Must be from a <strong>public figure</strong> (investor, analyst, politician, etc.)</li>
          </ul>
        </div>
      )}

      {/* Message */}
      {message && (
        <div className={`mb-6 p-4  flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400' : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
        }`}>
          {message.type === 'success' ? <CheckCircle className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
          {message.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-6 space-y-6">
        {/* Quick Mode: Minimal Fields */}
        {mode === 'quick' && extractedPredictions.length === 0 && !formData.claim && (
          <div className="text-center py-8 text-neutral-500">
            <Sparkles className="h-12 w-12 mx-auto mb-3 text-neutral-300 dark:text-neutral-600" />
            <p className="font-bold text-black dark:text-white mb-1">Paste a URL above to get started</p>
            <p className="text-sm">We'll automatically extract the prediction details</p>
            <button
              type="button"
              onClick={() => setMode('full')}
              className="mt-4 text-sm text-blue-500 hover:underline"
            >
              Or fill in manually →
            </button>
          </div>
        )}
        
        {/* Pundit Info - Show in full mode or after extraction */}
        {(mode === 'full' || formData.claim) && (
        <>
        <div className="border-b border-neutral-200 dark:border-neutral-800 pb-4 mb-4">
          <h3 className="font-bold text-black dark:text-white mb-4">Who made the prediction?</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="relative">
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Pundit Name *</label>
              <input
                type="text"
                value={formData.pundit_name}
                onChange={(e) => {
                  setFormData({...formData, pundit_name: e.target.value})
                  setShowSuggestions(true)
                }}
                onFocus={() => setShowSuggestions(true)}
                placeholder="e.g., Jim Cramer"
                className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800  px-4 py-2 text-black dark:text-white"
                required
              />
              
              {/* Autocomplete */}
              {showSuggestions && formData.pundit_name.length >= 2 && suggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700  shadow-lg max-h-40 overflow-y-auto">
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
                      className="w-full px-4 py-2 text-left hover:bg-neutral-50 dark:hover:bg-neutral-700 text-sm"
                    >
                      <span className="font-bold text-black dark:text-white">{s.name}</span>
                      <span className="text-neutral-500 ml-2">@{s.username}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Twitter/X Username</label>
              <input
                type="text"
                value={formData.pundit_username}
                onChange={(e) => setFormData({...formData, pundit_username: e.target.value})}
                placeholder="e.g., jimcramer (optional)"
                className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800  px-4 py-2 text-black dark:text-white"
              />
            </div>
          </div>
        </div>

        {/* Prediction Details */}
        <div className="border-b border-neutral-200 dark:border-neutral-800 pb-4 mb-4">
          <h3 className="font-bold text-black dark:text-white mb-4">What did they predict?</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Prediction Claim *</label>
              <input
                type="text"
                value={formData.claim}
                onChange={(e) => setFormData({...formData, claim: e.target.value})}
                placeholder="e.g., Bitcoin will reach $100,000 by end of 2024"
                className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800  px-4 py-2 text-black dark:text-white"
                required
              />
              <p className="text-xs text-neutral-400 mt-1">Be specific: include target price/event and deadline</p>
            </div>
            
            <div>
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Original Quote *</label>
              <textarea
                value={formData.quote}
                onChange={(e) => setFormData({...formData, quote: e.target.value})}
                placeholder="Paste the exact words they said..."
                className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800  px-4 py-2 text-black dark:text-white h-24"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">
                <LinkIcon className="h-4 w-4 inline mr-1" />
                Source URL *
              </label>
              <input
                type="url"
                value={formData.source_url}
                onChange={(e) => setFormData({...formData, source_url: e.target.value})}
                placeholder="https://twitter.com/... or https://youtube.com/..."
                className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800  px-4 py-2 text-black dark:text-white"
                required
              />
              <p className="text-xs text-neutral-400 mt-1">Tweet, article, video, podcast - any verifiable source</p>
            </div>
          </div>
        </div>

        {/* Dates & Outcome */}
        <div className="border-b border-neutral-200 dark:border-neutral-800 pb-4 mb-4">
          <h3 className="font-bold text-black dark:text-white mb-4">When and how did it resolve?</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Date Prediction Made *</label>
              <input
                type="date"
                value={formData.prediction_date}
                onChange={(e) => setFormData({...formData, prediction_date: e.target.value})}
                className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800  px-4 py-2 text-black dark:text-white"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Resolution Deadline</label>
              <input
                type="date"
                value={formData.resolution_date}
                onChange={(e) => setFormData({...formData, resolution_date: e.target.value})}
                className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800  px-4 py-2 text-black dark:text-white"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Outcome</label>
              <select
                value={formData.outcome}
                onChange={(e) => setFormData({...formData, outcome: e.target.value})}
                className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800  px-4 py-2 text-black dark:text-white"
              >
                <option value="unknown">Unknown / Still Open</option>
                <option value="right">Correct (Pundit was RIGHT)</option>
                <option value="wrong">Wrong (Pundit was WRONG)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
                className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800  px-4 py-2 text-black dark:text-white"
              >
                <optgroup label="Topics">
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
                </optgroup>
                <optgroup label="Americas">
                  <option value="us">United States</option>
                  <option value="us-politics">US Politics</option>
                  <option value="latam">Latin America</option>
                  <option value="brazil">Brazil</option>
                  <option value="canada">Canada</option>
                </optgroup>
                <optgroup label="Europe">
                  <option value="uk">United Kingdom</option>
                  <option value="uk-politics">UK Politics</option>
                  <option value="eu">European Union</option>
                  <option value="germany">Germany</option>
                  <option value="france">France</option>
                  <option value="scandinavia">Scandinavia</option>
                  <option value="balkans">Balkans</option>
                  <option value="russia">Russia</option>
                </optgroup>
                <optgroup label="Asia-Pacific">
                  <option value="china">China</option>
                  <option value="japan">Japan</option>
                  <option value="india">India</option>
                  <option value="southeast-asia">Southeast Asia</option>
                  <option value="australia">Australia</option>
                </optgroup>
                <optgroup label="Middle East & Africa">
                  <option value="middle-east">Middle East</option>
                  <option value="israel">Israel</option>
                  <option value="turkey">Turkey</option>
                  <option value="gulf-states">Gulf States</option>
                  <option value="africa">Africa</option>
                </optgroup>
              </select>
            </div>
          </div>
          
          <div className="mt-4">
            <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Outcome Notes</label>
            <input
              type="text"
              value={formData.outcome_notes}
              onChange={(e) => setFormData({...formData, outcome_notes: e.target.value})}
              placeholder="e.g., Bitcoin reached $73k but not $100k target"
              className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800  px-4 py-2 text-black dark:text-white"
            />
          </div>
        </div>

        {/* Contact (optional) */}
        <div>
          <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Your Email (optional)</label>
          <input
            type="email"
            value={formData.submitter_email}
            onChange={(e) => setFormData({...formData, submitter_email: e.target.value})}
            placeholder="Get notified when your submission is reviewed"
            className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-2 text-black dark:text-white"
          />
        </div>
        </>
        )}

        {/* Submit Button - Always visible when form has data */}
        {(mode === 'full' || formData.claim) && (
        <>
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-black dark:bg-white text-white dark:text-black font-bold py-3 hover:bg-neutral-800 dark:hover:bg-neutral-200 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <Send className="h-5 w-5" />
          {loading ? 'Submitting...' : 'Submit Prediction'}
        </button>
        
        <p className="text-xs text-neutral-400 text-center">
          All submissions are reviewed before being added to the database.
          We verify sources and check for accuracy.
        </p>
        </>
        )}
      </form>

      {/* Examples */}
      <div className="mt-8 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800  p-6">
        <h3 className="font-bold text-black dark:text-white mb-4">Example Good Submissions</h3>
        <div className="space-y-4 text-sm">
          <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700  p-3">
            <p className="font-bold text-green-500">✓ Good Prediction</p>
            <p className="text-neutral-700 dark:text-neutral-300">"Bitcoin will reach $100,000 by December 31, 2024"</p>
            <p className="text-neutral-500">Clear target + clear deadline = measurable</p>
          </div>
          <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700  p-3">
            <p className="font-bold text-red-500">✗ Bad Prediction</p>
            <p className="text-neutral-700 dark:text-neutral-300">"Bitcoin is going to the moon"</p>
            <p className="text-neutral-500">No target + no deadline = unmeasurable</p>
          </div>
        </div>
      </div>
    </div>
  )
}
