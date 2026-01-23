// src/app/admin/page.tsx
'use client'
import { useState, useEffect, useRef } from 'react'
import { Plus, Rss, RefreshCw, CheckCircle, AlertCircle, UserPlus, Search, Sparkles } from 'lucide-react'
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

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<'manual' | 'rss' | 'pundit'>('manual')
  const [pundits, setPundits] = useState<Pundit[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  
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
                <option value="crypto">Crypto</option>
                <option value="markets">Markets</option>
                <option value="economy">Economy</option>
                <option value="politics">Politics</option>
                <option value="tech">Tech</option>
                <option value="macro">Macro</option>
                <option value="general">General</option>
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
                max={365}
              />
              <p className="text-xs text-slate-400 mt-1">Max 12 months (365 days)</p>
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
            <p className="text-xs text-slate-400 mt-1">Options: markets, economy, crypto, politics, tech, macro</p>
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
    </div>
  )
}
