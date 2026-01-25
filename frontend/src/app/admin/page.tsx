// src/app/admin/page.tsx
'use client'
import { useState, useEffect, useRef } from 'react'
import { Plus, Rss, RefreshCw, CheckCircle, AlertCircle, UserPlus, Search, Sparkles, ClipboardCheck, XCircle, Check, X, Bot, Play, Square, History, Zap } from 'lucide-react'
import { KNOWN_PUNDITS, searchKnownPundits, KnownPundit } from '@/data/knownPundits'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Pundit {
  id: string
  name: string
  username: string
}

interface RSSArticle {
  title: string
  url: string
  summary: string
  source: string
  published: string
  pundits_mentioned: string[]
}

interface PendingPrediction {
  id: string
  pundit_name: string
  pundit_username: string
  claim: string
  quote: string
  category: string
  source_url: string
  timeframe: string
  captured_at: string
  status: string
  tr_index_score: number | null
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<'manual' | 'rss' | 'pundit' | 'verify' | 'bot'>('manual')
  const [pundits, setPundits] = useState<Pundit[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  
  // Verification state
  const [pendingPredictions, setPendingPredictions] = useState<PendingPrediction[]>([])
  const [verifyLoading, setVerifyLoading] = useState(false)
  
  // Bot/Scheduler state
  const [botStatus, setBotStatus] = useState<{
    is_running: boolean
    jobs: Array<{ id: string; name: string; next_run: string | null }>
    last_run_times: Record<string, string>
    stats: Record<string, { runs: number; predictions: number; errors: number; articles?: number }>
  } | null>(null)
  const [botLoading, setBotLoading] = useState(false)
  const [historicalLoading, setHistoricalLoading] = useState(false)
  const [historicalResults, setHistoricalResults] = useState<{
    status: string
    articles_collected: number
    predictions_extracted: number
    errors: string[]
  } | null>(null)
  
  // Pundit search state
  const [punditSearch, setPunditSearch] = useState('')
  const [showPunditDropdown, setShowPunditDropdown] = useState(false)
  const [selectedPundit, setSelectedPundit] = useState<Pundit | null>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  // Filter pundits based on search
  const filteredPundits = pundits.filter(p => 
    p.name.toLowerCase().includes(punditSearch.toLowerCase()) ||
    p.username.toLowerCase().includes(punditSearch.toLowerCase())
  )
  
  // Manual entry form with TR Index scoring
  const [formData, setFormData] = useState({
    pundit_username: '',
    claim: '',
    quote: '',
    source_url: '',
    category: 'general',
    timeframe_days: 90,
    // TR Index scores (1-5 scale)
    tr_specificity: 3,
    tr_verifiability: 3,
    tr_boldness: 1,
    tr_stakes: 2
  })
  
  // TR Index preview state
  const [trPreview, setTrPreview] = useState<{
    passed: boolean
    total: number
    tier: string
    rejection_reason: string | null
  } | null>(null)
  
  // New pundit form
  const [newPundit, setNewPundit] = useState({
    name: '',
    username: '',
    bio: '',
    affiliation: '',
    domains: 'markets'
  })
  
  // Known pundit suggestions
  const [punditNameSearch, setPunditNameSearch] = useState('')
  const [showKnownPundits, setShowKnownPundits] = useState(false)
  const knownPunditRef = useRef<HTMLDivElement>(null)
  
  // Get suggestions from known pundits (exclude already tracked ones)
  const trackedUsernames = pundits.map(p => p.username.toLowerCase())
  const knownPunditSuggestions = searchKnownPundits(punditNameSearch)
    .filter(kp => !trackedUsernames.includes(kp.username.toLowerCase()))
    .slice(0, 8)
  
  // RSS data
  const [rssArticles, setRssArticles] = useState<RSSArticle[]>([])
  const [rssLoading, setRssLoading] = useState(false)

  const loadPundits = () => {
    fetch(`${API_URL}/api/admin/pundits/list`)
      .then(res => res.json())
      .then(data => setPundits(data.pundits || []))
      .catch(err => console.error('Failed to load pundits:', err))
  }
  
  const loadPendingPredictions = async () => {
    setVerifyLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/admin/predictions/pending`)
      const data = await res.json()
      setPendingPredictions(data.predictions || [])
    } catch (err) {
      console.error('Failed to load pending predictions:', err)
    }
    setVerifyLoading(false)
  }
  
  const resolvePrediction = async (predictionId: string, outcome: 'correct' | 'wrong') => {
    try {
      const res = await fetch(`${API_URL}/api/admin/predictions/${predictionId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ outcome })
      })
      
      if (res.ok) {
        setMessage({ type: 'success', text: `Prediction marked as ${outcome.toUpperCase()}` })
        // Remove from list
        setPendingPredictions(prev => prev.filter(p => p.id !== predictionId))
      } else {
        const data = await res.json()
        setMessage({ type: 'error', text: data.detail || 'Failed to resolve prediction' })
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error - check API connection' })
    }
  }

  useEffect(() => {
    loadPundits()
  }, [])

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)
    
    try {
      const res = await fetch(`${API_URL}/api/admin/predictions/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      const data = await res.json()
      
      if (res.ok) {
        const trInfo = data.tr_index ? ` (TR Index: ${data.tr_index.total.toFixed(0)} - ${data.tr_index.tier})` : ''
        setMessage({ type: 'success', text: `Prediction added for ${data.pundit}: "${data.claim}"${trInfo}` })
        setFormData({
          pundit_username: '',
          claim: '',
          quote: '',
          source_url: '',
          category: 'general',
          timeframe_days: 90,
          tr_specificity: 3,
          tr_verifiability: 3,
          tr_boldness: 1,
          tr_stakes: 2
        })
        setSelectedPundit(null)
        setPunditSearch('')
        setTrPreview(null)
      } else {
        setMessage({ type: 'error', text: data.detail || 'Failed to add prediction' })
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error - check API connection' })
    }
    
    setLoading(false)
  }

  const fetchRSSArticles = async () => {
    setRssLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/admin/rss/fetch`, { method: 'POST' })
      const data = await res.json()
      setRssArticles(data.articles || [])
    } catch (err) {
      console.error('Failed to fetch RSS:', err)
    }
    setRssLoading(false)
  }
  
  // Bot/Scheduler functions
  const loadBotStatus = async () => {
    setBotLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/admin/scheduler/status`)
      if (res.ok) {
        const data = await res.json()
        setBotStatus(data)
      }
    } catch (err) {
      console.error('Failed to load bot status:', err)
    }
    setBotLoading(false)
  }
  
  const startBot = async () => {
    setBotLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/admin/scheduler/start?rss_interval_hours=6&enable_historical=true`, { method: 'POST' })
      if (res.ok) {
        setMessage({ type: 'success', text: 'Bot started successfully!' })
        loadBotStatus()
      } else {
        setMessage({ type: 'error', text: 'Failed to start bot' })
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Error starting bot' })
    }
    setBotLoading(false)
  }
  
  const stopBot = async () => {
    setBotLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/admin/scheduler/stop`, { method: 'POST' })
      if (res.ok) {
        setMessage({ type: 'success', text: 'Bot stopped' })
        loadBotStatus()
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Error stopping bot' })
    }
    setBotLoading(false)
  }
  
  const runHistoricalCollection = async (startYear: number = 2020) => {
    setHistoricalLoading(true)
    setHistoricalResults(null)
    try {
      const res = await fetch(`${API_URL}/api/admin/historical/collect?start_year=${startYear}&max_per_pundit=15`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setHistoricalResults(data)
        setMessage({ type: 'success', text: `Collected ${data.articles_collected} articles, extracted ${data.predictions_extracted} predictions!` })
      } else {
        setMessage({ type: 'error', text: 'Historical collection failed' })
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Error running historical collection' })
    }
    setHistoricalLoading(false)
  }
  
  const runAutoAgent = async () => {
    setBotLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/admin/auto-agent/run`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setMessage({ type: 'success', text: `Auto-agent complete! Found ${data.stats?.new_predictions || 0} new predictions` })
        loadBotStatus()
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Error running auto-agent' })
    }
    setBotLoading(false)
  }

  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-3xl font-black text-slate-900 mb-2">Admin Panel</h1>
      <p className="text-slate-500 mb-8">Add predictions and manage data sources</p>
      
      {/* Tabs */}
      <div className="flex flex-wrap gap-2 mb-8">
        <button
          onClick={() => setActiveTab('manual')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-colors ${
            activeTab === 'manual' 
              ? 'bg-blue-600 text-white' 
              : 'bg-white border text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Plus className="h-4 w-4" />
          Add Prediction
        </button>
        <button
          onClick={() => setActiveTab('pundit')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-colors ${
            activeTab === 'pundit' 
              ? 'bg-blue-600 text-white' 
              : 'bg-white border text-slate-600 hover:bg-slate-50'
          }`}
        >
          <UserPlus className="h-4 w-4" />
          Add Pundit
        </button>
        <button
          onClick={() => setActiveTab('rss')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-colors ${
            activeTab === 'rss' 
              ? 'bg-blue-600 text-white' 
              : 'bg-white border text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Rss className="h-4 w-4" />
          RSS Feeds
        </button>
        <button
          onClick={() => {
            setActiveTab('verify')
            loadPendingPredictions()
          }}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-colors ${
            activeTab === 'verify' 
              ? 'bg-emerald-600 text-white' 
              : 'bg-white border text-slate-600 hover:bg-slate-50'
          }`}
        >
          <ClipboardCheck className="h-4 w-4" />
          Verify Predictions
        </button>
        <button
          onClick={() => {
            setActiveTab('bot')
            loadBotStatus()
          }}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-colors ${
            activeTab === 'bot' 
              ? 'bg-purple-600 text-white' 
              : 'bg-white border text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Bot className="h-4 w-4" />
          Data Bot
        </button>
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

      {/* Manual Entry Tab */}
      {activeTab === 'manual' && (
        <form onSubmit={handleManualSubmit} className="bg-white border rounded-xl p-6 space-y-6">
          <div className="relative" ref={dropdownRef}>
            <label className="block text-sm font-bold text-slate-700 mb-2">Pundit</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={selectedPundit ? `${selectedPundit.name} (@${selectedPundit.username})` : punditSearch}
                onChange={(e) => {
                  setPunditSearch(e.target.value)
                  setSelectedPundit(null)
                  setFormData({...formData, pundit_username: ''})
                  setShowPunditDropdown(true)
                }}
                onFocus={() => setShowPunditDropdown(true)}
                placeholder="Search pundit by name..."
                className="w-full border rounded-lg pl-10 pr-4 py-2 text-slate-900"
                required={!selectedPundit}
              />
            </div>
            
            {/* Dropdown */}
            {showPunditDropdown && punditSearch && !selectedPundit && (
              <div className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-48 overflow-y-auto">
                {filteredPundits.length > 0 ? (
                  filteredPundits.map(p => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => {
                        setSelectedPundit(p)
                        setFormData({...formData, pundit_username: p.username})
                        setPunditSearch('')
                        setShowPunditDropdown(false)
                      }}
                      className="w-full px-4 py-2 text-left hover:bg-blue-50 flex items-center gap-2"
                    >
                      <span className="font-bold text-slate-900">{p.name}</span>
                      <span className="text-slate-500 text-sm">@{p.username}</span>
                    </button>
                  ))
                ) : (
                  <div className="px-4 py-2 text-slate-500 text-sm">
                    No pundits found. Add one in the "Add Pundit" tab.
                  </div>
                )}
              </div>
            )}
            
            {selectedPundit && (
              <button
                type="button"
                onClick={() => {
                  setSelectedPundit(null)
                  setPunditSearch('')
                  setFormData({...formData, pundit_username: ''})
                }}
                className="absolute right-3 top-9 text-xs text-slate-400 hover:text-rose-500"
              >
                Clear
              </button>
            )}
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-700 mb-2">Claim (extracted prediction)</label>
            <input
              type="text"
              value={formData.claim}
              onChange={(e) => setFormData({...formData, claim: e.target.value})}
              placeholder="e.g., Bitcoin will reach $150,000 by end of 2026"
              className="w-full border rounded-lg px-4 py-2 text-slate-900"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-700 mb-2">Original Quote</label>
            <textarea
              value={formData.quote}
              onChange={(e) => setFormData({...formData, quote: e.target.value})}
              placeholder="Paste the exact quote from the source..."
              className="w-full border rounded-lg px-4 py-2 text-slate-900 h-24"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-700 mb-2">Source URL</label>
            <input
              type="url"
              value={formData.source_url}
              onChange={(e) => setFormData({...formData, source_url: e.target.value})}
              placeholder="https://..."
              className="w-full border rounded-lg px-4 py-2 text-slate-900"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
                className="w-full border rounded-lg px-4 py-2 text-slate-900"
              >
                <optgroup label="Topics">
                  <option value="politics">Politics</option>
                  <option value="economy">Economy</option>
                  <option value="markets">Markets</option>
                  <option value="crypto">Crypto</option>
                  <option value="tech">Tech</option>
                  <option value="macro">Macro</option>
                  <option value="sports">Sports</option>
                  <option value="entertainment">Entertainment</option>
                  <option value="religion">Religion</option>
                  <option value="science">Science</option>
                  <option value="business">Business</option>
                  <option value="media">Media</option>
                  <option value="health">Health</option>
                  <option value="climate">Climate</option>
                  <option value="geopolitics">Geopolitics</option>
                  <option value="general">General</option>
                </optgroup>
                <optgroup label="Americas">
                  <option value="us">United States</option>
                  <option value="us-politics">US Politics</option>
                  <option value="us-sports">US Sports</option>
                  <option value="latam">Latin America</option>
                  <option value="brazil">Brazil</option>
                  <option value="mexico">Mexico</option>
                  <option value="canada">Canada</option>
                </optgroup>
                <optgroup label="Europe">
                  <option value="uk">United Kingdom</option>
                  <option value="uk-politics">UK Politics</option>
                  <option value="eu">European Union</option>
                  <option value="germany">Germany</option>
                  <option value="france">France</option>
                  <option value="italy">Italy</option>
                  <option value="spain">Spain</option>
                  <option value="scandinavia">Scandinavia</option>
                  <option value="balkans">Balkans</option>
                  <option value="eastern-europe">Eastern Europe</option>
                  <option value="russia">Russia</option>
                </optgroup>
                <optgroup label="Asia-Pacific">
                  <option value="china">China</option>
                  <option value="japan">Japan</option>
                  <option value="india">India</option>
                  <option value="south-korea">South Korea</option>
                  <option value="southeast-asia">Southeast Asia</option>
                  <option value="australia">Australia</option>
                  <option value="oceania">Oceania</option>
                </optgroup>
                <optgroup label="Middle East & Africa">
                  <option value="middle-east">Middle East</option>
                  <option value="israel">Israel</option>
                  <option value="turkey">Turkey</option>
                  <option value="iran">Iran</option>
                  <option value="gulf-states">Gulf States</option>
                  <option value="mena">MENA Region</option>
                  <option value="africa">Africa</option>
                  <option value="south-africa">South Africa</option>
                </optgroup>
                <optgroup label="Central Asia">
                  <option value="central-asia">Central Asia</option>
                  <option value="pakistan">Pakistan</option>
                  <option value="afghanistan">Afghanistan</option>
                </optgroup>
              </select>
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Timeframe (days until resolution)</label>
              <input
                type="number"
                value={formData.timeframe_days}
                onChange={(e) => setFormData({...formData, timeframe_days: parseInt(e.target.value)})}
                className="w-full border rounded-lg px-4 py-2 text-slate-900"
                min={1}
                max={1825}
              />
              <p className="text-xs text-slate-400 mt-1">Max 5 years (1825 days). Shorter predictions score higher.</p>
            </div>
          </div>
          
          {/* TR Prediction Index Scoring */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-5 w-5 text-blue-600" />
              <h3 className="font-bold text-slate-900">TR Prediction Index</h3>
              {trPreview && (
                <span className={`ml-auto text-sm font-bold px-3 py-1 rounded-full ${
                  trPreview.tier === 'gold' ? 'bg-yellow-100 text-yellow-700' :
                  trPreview.tier === 'silver' ? 'bg-slate-200 text-slate-700' :
                  trPreview.tier === 'bronze' ? 'bg-orange-100 text-orange-700' :
                  'bg-rose-100 text-rose-700'
                }`}>
                  {trPreview.passed ? `${trPreview.total.toFixed(0)}/100 ${trPreview.tier.toUpperCase()}` : 'REJECTED'}
                </span>
              )}
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Specificity */}
              <div>
                <label className="flex justify-between text-sm font-bold text-slate-700 mb-2">
                  <span>Specificity</span>
                  <span className="text-blue-600">{formData.tr_specificity}/5</span>
                </label>
                <input
                  type="range"
                  min={1}
                  max={5}
                  value={formData.tr_specificity}
                  onChange={(e) => setFormData({...formData, tr_specificity: parseInt(e.target.value)})}
                  className="w-full accent-blue-600"
                />
                <p className="text-xs text-slate-500 mt-1">
                  {formData.tr_specificity <= 2 ? '⚠️ Too vague - needs concrete numbers/dates' : 
                   formData.tr_specificity === 3 ? '✓ Has measurable outcome' : 
                   '✓✓ Very specific with clear targets'}
                </p>
              </div>
              
              {/* Verifiability */}
              <div>
                <label className="flex justify-between text-sm font-bold text-slate-700 mb-2">
                  <span>Verifiability</span>
                  <span className="text-blue-600">{formData.tr_verifiability}/5</span>
                </label>
                <input
                  type="range"
                  min={1}
                  max={5}
                  value={formData.tr_verifiability}
                  onChange={(e) => setFormData({...formData, tr_verifiability: parseInt(e.target.value)})}
                  className="w-full accent-blue-600"
                />
                <p className="text-xs text-slate-500 mt-1">
                  {formData.tr_verifiability <= 2 ? '⚠️ Hard to verify objectively' : 
                   formData.tr_verifiability === 3 ? '✓ Can be verified with public data' : 
                   '✓✓ Easily verified, clear criteria'}
                </p>
              </div>
              
              {/* Boldness */}
              <div>
                <label className="flex justify-between text-sm font-bold text-slate-700 mb-2">
                  <span>Boldness</span>
                  <span className="text-blue-600">{formData.tr_boldness}/5</span>
                </label>
                <input
                  type="range"
                  min={1}
                  max={5}
                  value={formData.tr_boldness}
                  onChange={(e) => setFormData({...formData, tr_boldness: parseInt(e.target.value)})}
                  className="w-full accent-blue-600"
                />
                <p className="text-xs text-slate-500 mt-1">
                  {formData.tr_boldness === 1 ? 'Consensus view' : 
                   formData.tr_boldness <= 3 ? 'Somewhat contrarian' : 
                   '🔥 Very contrarian, against consensus'}
                </p>
              </div>
              
              {/* Stakes */}
              <div>
                <label className="flex justify-between text-sm font-bold text-slate-700 mb-2">
                  <span>Stakes/Impact</span>
                  <span className="text-blue-600">{formData.tr_stakes}/5</span>
                </label>
                <input
                  type="range"
                  min={1}
                  max={5}
                  value={formData.tr_stakes}
                  onChange={(e) => setFormData({...formData, tr_stakes: parseInt(e.target.value)})}
                  className="w-full accent-blue-600"
                />
                <p className="text-xs text-slate-500 mt-1">
                  {formData.tr_stakes <= 2 ? 'Minor impact' : 
                   formData.tr_stakes <= 3 ? 'Moderate impact' : 
                   '💥 Major market/world impact'}
                </p>
              </div>
            </div>
            
            {/* Preview button */}
            <button
              type="button"
              onClick={async () => {
                try {
                  const res = await fetch(`${API_URL}/api/tr-index/calculate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      timeframe_days: formData.timeframe_days,
                      specificity: formData.tr_specificity,
                      verifiability: formData.tr_verifiability,
                      boldness: formData.tr_boldness,
                      stakes: formData.tr_stakes
                    })
                  })
                  const data = await res.json()
                  setTrPreview(data)
                } catch (err) {
                  console.error('Failed to calculate TR Index:', err)
                }
              }}
              className="mt-4 w-full bg-white border border-blue-300 text-blue-600 font-bold py-2 rounded-lg hover:bg-blue-50 transition-colors"
            >
              Preview Score
            </button>
            
            {trPreview && !trPreview.passed && (
              <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded-lg">
                <p className="text-sm text-rose-700 font-medium">
                  ❌ {trPreview.rejection_reason}
                </p>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white font-bold py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Adding...' : 'Add Prediction'}
          </button>
        </form>
      )}

      {/* Add Pundit Tab */}
      {activeTab === 'pundit' && (
        <form onSubmit={async (e) => {
          e.preventDefault()
          setLoading(true)
          setMessage(null)
          
          try {
            const res = await fetch(`${API_URL}/api/admin/pundits/add`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                ...newPundit,
                domains: newPundit.domains.split(',').map(d => d.trim())
              })
            })
            
            const data = await res.json()
            
            if (res.ok) {
              setMessage({ type: 'success', text: `Pundit added: ${data.name} (@${data.username})` })
              setNewPundit({ name: '', username: '', bio: '', affiliation: '', domains: 'markets' })
              setPunditNameSearch('')
              loadPundits() // Refresh the list
            } else {
              setMessage({ type: 'error', text: data.detail || 'Failed to add pundit' })
            }
          } catch (err) {
            setMessage({ type: 'error', text: 'Network error - check API connection' })
          }
          
          setLoading(false)
        }} className="bg-white border rounded-xl p-6 space-y-6">
          
          {/* Known pundits database hint */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-blue-600 flex-shrink-0" />
            <p className="text-sm text-blue-700">
              <strong>{KNOWN_PUNDITS.length} known pundits</strong> in database. Start typing to auto-fill details!
            </p>
          </div>
          
          <div className="relative" ref={knownPunditRef}>
            <label className="block text-sm font-bold text-slate-700 mb-2">Full Name *</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={newPundit.name || punditNameSearch}
                onChange={(e) => {
                  const val = e.target.value
                  setPunditNameSearch(val)
                  setNewPundit({...newPundit, name: val})
                  setShowKnownPundits(true)
                }}
                onFocus={() => setShowKnownPundits(true)}
                placeholder="Start typing... e.g., Elon, Cathie, Saylor"
                className="w-full border rounded-lg pl-10 pr-4 py-2 text-slate-900"
                required
              />
            </div>
            
            {/* Known pundit suggestions dropdown */}
            {showKnownPundits && punditNameSearch.length >= 2 && knownPunditSuggestions.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-64 overflow-y-auto">
                <div className="px-3 py-2 bg-slate-50 border-b">
                  <p className="text-xs text-slate-500 font-medium">Click to auto-fill all fields</p>
                </div>
                {knownPunditSuggestions.map(kp => (
                  <button
                    key={kp.username}
                    type="button"
                    onClick={() => {
                      setNewPundit({
                        name: kp.name,
                        username: kp.username,
                        bio: kp.bio,
                        affiliation: kp.affiliation,
                        domains: kp.domains.join(', ')
                      })
                      setPunditNameSearch('')
                      setShowKnownPundits(false)
                    }}
                    className="w-full px-4 py-3 text-left hover:bg-blue-50 border-b last:border-b-0"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-bold text-slate-900">{kp.name}</span>
                        <span className="text-slate-500 text-sm ml-2">@{kp.username}</span>
                      </div>
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                        {kp.domains[0]}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">{kp.affiliation}</p>
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-bold text-slate-700 mb-2">Twitter/X Username *</label>
            <input
              type="text"
              value={newPundit.username}
              onChange={(e) => setNewPundit({...newPundit, username: e.target.value})}
              placeholder="e.g., elonmusk (without @)"
              className="w-full border rounded-lg px-4 py-2 text-slate-900"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-700 mb-2">Affiliation</label>
            <input
              type="text"
              value={newPundit.affiliation}
              onChange={(e) => setNewPundit({...newPundit, affiliation: e.target.value})}
              placeholder="e.g., Berkshire Hathaway CEO"
              className="w-full border rounded-lg px-4 py-2 text-slate-900"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-700 mb-2">Bio</label>
            <textarea
              value={newPundit.bio}
              onChange={(e) => setNewPundit({...newPundit, bio: e.target.value})}
              placeholder="Brief description of who they are and what they're known for..."
              className="w-full border rounded-lg px-4 py-2 text-slate-900 h-20"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-700 mb-2">Domains (comma-separated)</label>
            <input
              type="text"
              value={newPundit.domains}
              onChange={(e) => setNewPundit({...newPundit, domains: e.target.value})}
              placeholder="e.g., markets, economy, crypto"
              className="w-full border rounded-lg px-4 py-2 text-slate-900"
            />
            <p className="text-xs text-slate-400 mt-1">Topics: politics, economy, markets, sports, tech, religion, etc. | Regions: us, uk, eu, israel, japan, china, india, russia, brazil, latam, mena, etc.</p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white font-bold py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Adding...' : 'Add Pundit'}
          </button>
          
          {/* Current pundits list */}
          <div className="pt-4 border-t">
            <p className="text-sm font-bold text-slate-700 mb-2">Currently Tracked ({pundits.length})</p>
            <div className="flex flex-wrap gap-2">
              {pundits.map(p => (
                <span key={p.id} className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full font-medium">
                  {p.name}
                </span>
              ))}
            </div>
          </div>
          
          {/* Not yet tracked pundits */}
          <div className="pt-4 border-t">
            <p className="text-sm font-bold text-slate-700 mb-2">Suggested Pundits to Track ({KNOWN_PUNDITS.length - pundits.length} available)</p>
            <p className="text-xs text-slate-500 mb-3">Click any name to auto-fill the form:</p>
            <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
              {KNOWN_PUNDITS
                .filter(kp => !trackedUsernames.includes(kp.username.toLowerCase()))
                .slice(0, 30)
                .map(kp => (
                  <button
                    key={kp.username}
                    type="button"
                    onClick={() => {
                      setNewPundit({
                        name: kp.name,
                        username: kp.username,
                        bio: kp.bio,
                        affiliation: kp.affiliation,
                        domains: kp.domains.join(', ')
                      })
                    }}
                    className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-full hover:bg-blue-100 hover:text-blue-700 transition-colors"
                  >
                    {kp.name}
                  </button>
                ))}
              {KNOWN_PUNDITS.filter(kp => !trackedUsernames.includes(kp.username.toLowerCase())).length > 30 && (
                <span className="text-xs text-slate-400 px-2 py-1">
                  +{KNOWN_PUNDITS.filter(kp => !trackedUsernames.includes(kp.username.toLowerCase())).length - 30} more...
                </span>
              )}
            </div>
          </div>
        </form>
      )}

      {/* RSS Feeds Tab */}
      {activeTab === 'rss' && (
        <div className="space-y-6">
          <button
            onClick={fetchRSSArticles}
            disabled={rssLoading}
            className="flex items-center gap-2 bg-blue-600 text-white font-bold px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${rssLoading ? 'animate-spin' : ''}`} />
            {rssLoading ? 'Fetching...' : 'Fetch Latest Articles'}
          </button>

          {rssArticles.length > 0 && (
            <div className="space-y-4">
              <p className="text-sm text-slate-500">{rssArticles.length} articles with prediction keywords</p>
              
              {rssArticles.map((article, i) => (
                <div key={i} className="bg-white border rounded-xl p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <p className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-1">{article.source}</p>
                      <h3 className="font-bold text-slate-900 mb-2">{article.title}</h3>
                      <p className="text-sm text-slate-500 line-clamp-2">{article.summary}</p>
                      {article.pundits_mentioned.length > 0 && (
                        <div className="mt-2 flex gap-1">
                          {article.pundits_mentioned.map(p => (
                            <span key={p} className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full font-bold">
                              @{p}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-bold text-blue-600 hover:underline whitespace-nowrap"
                    >
                      View →
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}

          {rssArticles.length === 0 && !rssLoading && (
            <div className="bg-white border rounded-xl p-12 text-center">
              <Rss className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">Click "Fetch Latest Articles" to pull from news feeds</p>
            </div>
          )}
        </div>
      )}

      {/* Verify Predictions Tab */}
      {activeTab === 'verify' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Pending Verification</h2>
              <p className="text-sm text-slate-500">Manually verify predictions that can't be auto-resolved via Polymarket</p>
            </div>
            <button
              onClick={loadPendingPredictions}
              disabled={verifyLoading}
              className="flex items-center gap-2 bg-emerald-600 text-white font-bold px-4 py-2 rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${verifyLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {verifyLoading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-emerald-600 border-t-transparent rounded-full" />
            </div>
          ) : pendingPredictions.length > 0 ? (
            <div className="space-y-4">
              {pendingPredictions.map(pred => (
                <div key={pred.id} className="bg-white border rounded-xl overflow-hidden">
                  {/* Header */}
                  <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-amber-700 uppercase tracking-wider">
                        {pred.category}
                      </span>
                      <span className="text-xs text-amber-600">•</span>
                      <span className="text-xs text-amber-600">
                        Resolves: {pred.timeframe ? new Date(pred.timeframe).toLocaleDateString() : 'TBD'}
                      </span>
                    </div>
                    {pred.tr_index_score && (
                      <span className="text-xs font-bold bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                        TR: {pred.tr_index_score.toFixed(0)}
                      </span>
                    )}
                  </div>
                  
                  {/* Content */}
                  <div className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-bold text-slate-900">{pred.pundit_name}</span>
                      <span className="text-sm text-slate-500">@{pred.pundit_username}</span>
                    </div>
                    
                    <p className="font-bold text-slate-900 mb-2">{pred.claim}</p>
                    
                    <div className="bg-slate-50 rounded-lg p-3 mb-3 border-l-4 border-slate-300 italic text-sm text-slate-600">
                      "{pred.quote}"
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <a
                        href={pred.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:underline"
                      >
                        View Source →
                      </a>
                      
                      {/* Resolution Buttons */}
                      <div className="flex gap-2">
                        <button
                          onClick={() => resolvePrediction(pred.id, 'correct')}
                          className="flex items-center gap-1 bg-emerald-600 text-white font-bold px-4 py-2 rounded-lg hover:bg-emerald-700 transition-colors"
                        >
                          <Check className="h-4 w-4" />
                          CORRECT
                        </button>
                        <button
                          onClick={() => resolvePrediction(pred.id, 'wrong')}
                          className="flex items-center gap-1 bg-rose-600 text-white font-bold px-4 py-2 rounded-lg hover:bg-rose-700 transition-colors"
                        >
                          <X className="h-4 w-4" />
                          WRONG
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-white border rounded-xl p-12 text-center">
              <ClipboardCheck className="h-12 w-12 text-emerald-300 mx-auto mb-4" />
              <p className="text-slate-500 font-bold">No predictions pending verification</p>
              <p className="text-sm text-slate-400 mt-1">All predictions are either resolved or awaiting their deadline</p>
            </div>
          )}
        </div>
      )}
      
      {/* Bot Control Tab */}
      {activeTab === 'bot' && (
        <div className="space-y-6">
          {/* Scheduler Status Card */}
          <div className="bg-white border rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                  <Bot className="h-5 w-5 text-purple-600" />
                  Data Collection Bot
                </h2>
                <p className="text-sm text-slate-500">Automatically collects predictions from news sources</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={loadBotStatus}
                  disabled={botLoading}
                  className="p-2 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors"
                >
                  <RefreshCw className={`h-4 w-4 ${botLoading ? 'animate-spin' : ''}`} />
                </button>
                {botStatus?.is_running ? (
                  <button
                    onClick={stopBot}
                    disabled={botLoading}
                    className="flex items-center gap-2 bg-rose-600 text-white font-bold px-4 py-2 rounded-lg hover:bg-rose-700 transition-colors disabled:opacity-50"
                  >
                    <Square className="h-4 w-4" />
                    Stop Bot
                  </button>
                ) : (
                  <button
                    onClick={startBot}
                    disabled={botLoading}
                    className="flex items-center gap-2 bg-emerald-600 text-white font-bold px-4 py-2 rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
                  >
                    <Play className="h-4 w-4" />
                    Start Bot
                  </button>
                )}
              </div>
            </div>
            
            {/* Status Display */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className={`p-4 rounded-lg ${botStatus?.is_running ? 'bg-emerald-50 border border-emerald-200' : 'bg-slate-50 border border-slate-200'}`}>
                <div className="flex items-center gap-2 mb-1">
                  <div className={`h-3 w-3 rounded-full ${botStatus?.is_running ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`} />
                  <span className="text-sm font-bold text-slate-700">Status</span>
                </div>
                <span className={`text-lg font-black ${botStatus?.is_running ? 'text-emerald-600' : 'text-slate-500'}`}>
                  {botStatus?.is_running ? 'Running' : 'Stopped'}
                </span>
              </div>
              
              <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
                <span className="text-sm font-bold text-slate-700 block mb-1">RSS Ingestion</span>
                <span className="text-lg font-black text-blue-600">
                  {botStatus?.stats?.rss_ingestion?.predictions || 0} predictions
                </span>
                <span className="text-xs text-slate-500 block">
                  {botStatus?.stats?.rss_ingestion?.runs || 0} runs
                </span>
              </div>
              
              <div className="p-4 rounded-lg bg-purple-50 border border-purple-200">
                <span className="text-sm font-bold text-slate-700 block mb-1">Historical Collection</span>
                <span className="text-lg font-black text-purple-600">
                  {botStatus?.stats?.historical_collection?.articles || 0} articles
                </span>
                <span className="text-xs text-slate-500 block">
                  {botStatus?.stats?.historical_collection?.predictions || 0} predictions
                </span>
              </div>
            </div>
            
            {/* Scheduled Jobs */}
            {botStatus?.jobs && botStatus.jobs.length > 0 && (
              <div className="border-t pt-4">
                <h3 className="text-sm font-bold text-slate-700 mb-2">Scheduled Jobs</h3>
                <div className="space-y-2">
                  {botStatus.jobs.map(job => (
                    <div key={job.id} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2">
                      <span className="text-sm font-medium text-slate-700">{job.name}</span>
                      <span className="text-xs text-slate-500">
                        Next: {job.next_run ? new Date(job.next_run).toLocaleString() : 'Not scheduled'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          {/* Manual Actions */}
          <div className="bg-white border rounded-xl p-6">
            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Zap className="h-5 w-5 text-amber-500" />
              Manual Actions
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Run Auto-Agent Now */}
              <div className="border rounded-lg p-4">
                <h4 className="font-bold text-slate-900 mb-1">Run RSS Scan Now</h4>
                <p className="text-sm text-slate-500 mb-3">Fetch latest articles from RSS feeds and extract predictions</p>
                <button
                  onClick={runAutoAgent}
                  disabled={botLoading}
                  className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white font-bold px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  <Rss className="h-4 w-4" />
                  {botLoading ? 'Running...' : 'Scan RSS Now'}
                </button>
              </div>
              
              {/* Run Historical Collection */}
              <div className="border rounded-lg p-4">
                <h4 className="font-bold text-slate-900 mb-1">Historical Collection</h4>
                <p className="text-sm text-slate-500 mb-3">Collect predictions from 2020-present (takes a few minutes)</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => runHistoricalCollection(2023)}
                    disabled={historicalLoading}
                    className="flex-1 flex items-center justify-center gap-2 bg-purple-600 text-white font-bold px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                  >
                    <History className="h-4 w-4" />
                    {historicalLoading ? 'Collecting...' : '2023+'}
                  </button>
                  <button
                    onClick={() => runHistoricalCollection(2020)}
                    disabled={historicalLoading}
                    className="flex-1 flex items-center justify-center gap-2 bg-purple-800 text-white font-bold px-4 py-2 rounded-lg hover:bg-purple-900 transition-colors disabled:opacity-50"
                  >
                    <History className="h-4 w-4" />
                    {historicalLoading ? 'Collecting...' : '2020+'}
                  </button>
                </div>
              </div>
            </div>
            
            {/* Historical Results */}
            {historicalResults && (
              <div className={`mt-4 p-4 rounded-lg ${historicalResults.status === 'completed' ? 'bg-emerald-50 border border-emerald-200' : 'bg-amber-50 border border-amber-200'}`}>
                <h4 className="font-bold text-slate-900 mb-2">Collection Results</h4>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <span className="text-2xl font-black text-slate-900">{historicalResults.articles_collected}</span>
                    <span className="text-xs text-slate-500 block">Articles</span>
                  </div>
                  <div>
                    <span className="text-2xl font-black text-emerald-600">{historicalResults.predictions_extracted}</span>
                    <span className="text-xs text-slate-500 block">Predictions</span>
                  </div>
                  <div>
                    <span className="text-2xl font-black text-rose-600">{historicalResults.errors?.length || 0}</span>
                    <span className="text-xs text-slate-500 block">Errors</span>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Info Box */}
          <div className="bg-purple-50 border border-purple-200 rounded-xl p-6">
            <h3 className="font-bold text-purple-900 mb-2">How the Bot Works</h3>
            <ul className="text-sm text-purple-800 space-y-1">
              <li>• <strong>RSS Scan</strong>: Runs every 6 hours, fetches latest news articles</li>
              <li>• <strong>AI Extraction</strong>: Uses Claude AI to identify predictions from known pundits</li>
              <li>• <strong>Historical Collection</strong>: Searches GDELT and Google News archives for past predictions</li>
              <li>• <strong>Auto-matching</strong>: Attempts to match predictions to Polymarket for verification</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
