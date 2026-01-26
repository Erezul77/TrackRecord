// src/app/apply/page.tsx
'use client'
import { useState } from 'react'
import { Send, CheckCircle, AlertCircle, User, Twitter, Youtube, Globe, Mic, Briefcase, Trophy } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const CATEGORIES = [
  { id: 'markets', label: 'Markets / Stocks', icon: '📈' },
  { id: 'crypto', label: 'Crypto / Web3', icon: '₿' },
  { id: 'politics', label: 'Politics', icon: '🏛️' },
  { id: 'tech', label: 'Tech / AI', icon: '🤖' },
  { id: 'economy', label: 'Economy / Macro', icon: '💰' },
  { id: 'sports', label: 'Sports', icon: '⚽' },
  { id: 'entertainment', label: 'Entertainment', icon: '🎬' },
  { id: 'science', label: 'Science', icon: '🔬' },
  { id: 'geopolitics', label: 'Geopolitics', icon: '🌍' },
  { id: 'health', label: 'Health / Medicine', icon: '🏥' },
]

export default function ApplyPage() {
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    twitter_username: '',
    youtube_channel: '',
    website: '',
    podcast: '',
    affiliation: '',
    bio: '',
    expertise: [] as string[],
    sample_predictions: '',
    why_track: ''
  })

  const toggleExpertise = (id: string) => {
    if (formData.expertise.includes(id)) {
      setFormData({...formData, expertise: formData.expertise.filter(e => e !== id)})
    } else {
      setFormData({...formData, expertise: [...formData.expertise, id]})
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)
    
    try {
      const res = await fetch(`${API_URL}/api/pundit-applications`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      if (res.ok) {
        setSubmitted(true)
      } else {
        const data = await res.json()
        setMessage({ type: 'error', text: data.detail || 'Application failed. Please try again.' })
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' })
    }
    
    setLoading(false)
  }

  if (submitted) {
    return (
      <div className="container mx-auto px-4 py-12 max-w-2xl">
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-8 text-center">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-black text-green-700 dark:text-green-400 mb-2">Application Received!</h1>
          <p className="text-green-600 dark:text-green-400 mb-4">
            Thank you for applying to be tracked on TrackRecord. We'll review your application and get back to you within 48 hours.
          </p>
          <p className="text-sm text-green-500">
            Check your email ({formData.email}) for confirmation.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-12 max-w-2xl">
      <div className="mb-8">
        <h1 className="text-3xl font-black text-black dark:text-white mb-2 flex items-center gap-3">
          <Trophy className="h-8 w-8 text-amber-500" />
          Apply to Be Tracked
        </h1>
        <p className="text-neutral-500">
          Are you a pundit, analyst, or expert who makes public predictions? 
          Apply to have your track record on TrackRecord.
        </p>
      </div>

      {/* Benefits */}
      <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-6 mb-8">
        <h3 className="font-bold text-black dark:text-white mb-4">Why Get Tracked?</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 text-green-600">
              <Trophy className="h-4 w-4" />
            </div>
            <div>
              <p className="font-bold text-black dark:text-white text-sm">Build Credibility</p>
              <p className="text-xs text-neutral-500">Prove your track record publicly</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 text-blue-600">
              <User className="h-4 w-4" />
            </div>
            <div>
              <p className="font-bold text-black dark:text-white text-sm">Grow Your Audience</p>
              <p className="text-xs text-neutral-500">Get discovered by people seeking experts</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 text-purple-600">
              <Briefcase className="h-4 w-4" />
            </div>
            <div>
              <p className="font-bold text-black dark:text-white text-sm">Stand Out</p>
              <p className="text-xs text-neutral-500">Differentiate from talking heads</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="p-2 bg-amber-100 dark:bg-amber-900/30 text-amber-600">
              <CheckCircle className="h-4 w-4" />
            </div>
            <div>
              <p className="font-bold text-black dark:text-white text-sm">Transparency</p>
              <p className="text-xs text-neutral-500">Show you stand behind your calls</p>
            </div>
          </div>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`mb-6 p-4 flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400' : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
        }`}>
          {message.type === 'success' ? <CheckCircle className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
          {message.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-6 space-y-6">
        {/* Basic Info */}
        <div className="border-b border-neutral-200 dark:border-neutral-800 pb-4 mb-4">
          <h3 className="font-bold text-black dark:text-white mb-4 flex items-center gap-2">
            <User className="h-4 w-4" />
            Basic Information
          </h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Full Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="e.g., John Smith"
                className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-2 text-black dark:text-white"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Email *</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="your@email.com"
                className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-2 text-black dark:text-white"
                required
              />
            </div>
          </div>
          
          <div className="mt-4">
            <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Affiliation / Company</label>
            <input
              type="text"
              value={formData.affiliation}
              onChange={(e) => setFormData({...formData, affiliation: e.target.value})}
              placeholder="e.g., Bloomberg, Independent Analyst, University"
              className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-2 text-black dark:text-white"
            />
          </div>
          
          <div className="mt-4">
            <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">Short Bio *</label>
            <textarea
              value={formData.bio}
              onChange={(e) => setFormData({...formData, bio: e.target.value})}
              placeholder="Tell us about your background and expertise (2-3 sentences)"
              className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-2 text-black dark:text-white h-20"
              required
            />
          </div>
        </div>

        {/* Social Links */}
        <div className="border-b border-neutral-200 dark:border-neutral-800 pb-4 mb-4">
          <h3 className="font-bold text-black dark:text-white mb-4">Social & Media Presence</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2 flex items-center gap-2">
                <Twitter className="h-4 w-4" />
                Twitter/X Username
              </label>
              <input
                type="text"
                value={formData.twitter_username}
                onChange={(e) => setFormData({...formData, twitter_username: e.target.value})}
                placeholder="@username"
                className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-2 text-black dark:text-white"
              />
            </div>
            
            <div>
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2 flex items-center gap-2">
                <Youtube className="h-4 w-4" />
                YouTube Channel
              </label>
              <input
                type="url"
                value={formData.youtube_channel}
                onChange={(e) => setFormData({...formData, youtube_channel: e.target.value})}
                placeholder="https://youtube.com/@channel"
                className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-2 text-black dark:text-white"
              />
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2 flex items-center gap-2">
                  <Globe className="h-4 w-4" />
                  Website/Newsletter
                </label>
                <input
                  type="url"
                  value={formData.website}
                  onChange={(e) => setFormData({...formData, website: e.target.value})}
                  placeholder="https://..."
                  className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-2 text-black dark:text-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2 flex items-center gap-2">
                  <Mic className="h-4 w-4" />
                  Podcast
                </label>
                <input
                  type="text"
                  value={formData.podcast}
                  onChange={(e) => setFormData({...formData, podcast: e.target.value})}
                  placeholder="Podcast name or URL"
                  className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-2 text-black dark:text-white"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Expertise Areas */}
        <div className="border-b border-neutral-200 dark:border-neutral-800 pb-4 mb-4">
          <h3 className="font-bold text-black dark:text-white mb-4">Areas of Expertise *</h3>
          <p className="text-sm text-neutral-500 mb-4">Select all that apply</p>
          
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {CATEGORIES.map(cat => (
              <button
                key={cat.id}
                type="button"
                onClick={() => toggleExpertise(cat.id)}
                className={`p-2 text-left text-sm border transition-colors ${
                  formData.expertise.includes(cat.id)
                    ? 'bg-black dark:bg-white text-white dark:text-black border-black dark:border-white'
                    : 'bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 border-neutral-200 dark:border-neutral-700 hover:border-black dark:hover:border-white'
                }`}
              >
                <span className="mr-1">{cat.icon}</span> {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Sample Predictions */}
        <div className="border-b border-neutral-200 dark:border-neutral-800 pb-4 mb-4">
          <h3 className="font-bold text-black dark:text-white mb-2">Sample Predictions *</h3>
          <p className="text-sm text-neutral-500 mb-4">
            Share 2-3 specific predictions you've made publicly (with dates and sources if possible)
          </p>
          <textarea
            value={formData.sample_predictions}
            onChange={(e) => setFormData({...formData, sample_predictions: e.target.value})}
            placeholder="Example:
1. (March 2024) I predicted Bitcoin would reach $70k before the halving - tweet link
2. (Jan 2024) I said the Fed would hold rates through Q1 - newsletter post
3. ..."
            className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-2 text-black dark:text-white h-32"
            required
          />
        </div>

        {/* Motivation */}
        <div>
          <h3 className="font-bold text-black dark:text-white mb-2">Why do you want to be tracked?</h3>
          <textarea
            value={formData.why_track}
            onChange={(e) => setFormData({...formData, why_track: e.target.value})}
            placeholder="What motivates you to have your predictions publicly tracked and scored?"
            className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-2 text-black dark:text-white h-20"
          />
        </div>

        <button
          type="submit"
          disabled={loading || formData.expertise.length === 0}
          className="w-full bg-black dark:bg-white text-white dark:text-black font-bold py-3 hover:bg-neutral-800 dark:hover:bg-neutral-200 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <Send className="h-5 w-5" />
          {loading ? 'Submitting...' : 'Submit Application'}
        </button>
        
        <p className="text-xs text-neutral-400 text-center">
          Applications are reviewed within 48 hours. We may reach out for verification.
        </p>
      </form>
    </div>
  )
}
