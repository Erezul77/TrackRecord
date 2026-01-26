// src/app/resolve/page.tsx
'use client'
import { useState, useEffect } from 'react'
import { 
  Gavel, RefreshCw, CheckCircle, XCircle, Clock, 
  ExternalLink, User, AlertTriangle, History,
  ThumbsUp, ThumbsDown, Link as LinkIcon, Calendar
} from 'lucide-react'
import { cn } from '@/lib/utils'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Generate UI Avatars URL - consistent with other pages
function getAvatarUrl(name: string): string {
  const encoded = encodeURIComponent(name)
  return `https://ui-avatars.com/api/?name=${encoded}&background=000&color=fff&bold=true&size=128`
}

interface PendingPrediction {
  id: string
  pundit_id: string
  pundit_name: string
  pundit_username: string
  pundit_avatar: string | null
  claim: string
  quote: string
  category: string
  source_url: string
  timeframe: string
  captured_at: string
  days_overdue: number
  status: string
  tr_index_score: number | null
  community_votes: {
    upvotes: number
    downvotes: number
  }
}

interface Resolution {
  id: string
  pundit_name: string
  claim: string
  category: string
  outcome: string
  outcome_label: string
  timeframe: string
  resolved_at: string | null
}

export default function ResolutionCenterPage() {
  const [activeTab, setActiveTab] = useState<'pending' | 'history'>('pending')
  const [predictions, setPredictions] = useState<PendingPrediction[]>([])
  const [history, setHistory] = useState<Resolution[]>([])
  const [loading, setLoading] = useState(true)
  const [resolving, setResolving] = useState<string | null>(null)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  
  // Resolution form state
  const [resolutionForm, setResolutionForm] = useState<{
    predictionId: string | null
    evidenceUrl: string
    notes: string
  }>({
    predictionId: null,
    evidenceUrl: '',
    notes: ''
  })

  useEffect(() => {
    loadPendingPredictions()
  }, [])

  const loadPendingPredictions = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/resolution/ready`)
      const data = await res.json()
      setPredictions(data.predictions || [])
    } catch (err) {
      console.error('Failed to load predictions:', err)
    }
    setLoading(false)
  }

  const loadHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/api/resolution/history`)
      const data = await res.json()
      setHistory(data.resolutions || [])
    } catch (err) {
      console.error('Failed to load history:', err)
    }
  }

  const openResolutionForm = (predictionId: string) => {
    setResolutionForm({
      predictionId,
      evidenceUrl: '',
      notes: ''
    })
  }

  const resolvePrediction = async (outcome: 'correct' | 'wrong') => {
    if (!resolutionForm.predictionId) return
    
    if (!resolutionForm.evidenceUrl || !resolutionForm.evidenceUrl.startsWith('http')) {
      setMessage({ type: 'error', text: 'Evidence URL is required - must provide proof!' })
      return
    }
    
    setResolving(resolutionForm.predictionId)
    setMessage(null)
    
    try {
      const res = await fetch(`${API_URL}/api/admin/predictions/${resolutionForm.predictionId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          outcome,
          evidence_url: resolutionForm.evidenceUrl,
          notes: resolutionForm.notes
        })
      })
      
      if (res.ok) {
        setMessage({ type: 'success', text: `Prediction marked as ${outcome.toUpperCase()}. Resolution is FINAL.` })
        setPredictions(prev => prev.filter(p => p.id !== resolutionForm.predictionId))
        setResolutionForm({ predictionId: null, evidenceUrl: '', notes: '' })
      } else {
        const data = await res.json()
        setMessage({ type: 'error', text: data.detail || 'Failed to resolve prediction' })
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error - check API connection' })
    }
    
    setResolving(null)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <div className="container mx-auto px-4 py-12 max-w-5xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-black text-black dark:text-white mb-2 flex items-center gap-3">
          <Gavel className="h-8 w-8" />
          Resolution Center
        </h1>
        <p className="text-neutral-500">
          Review predictions past their deadline and mark them as CORRECT or WRONG.
          <span className="font-bold text-red-600 dark:text-red-400 ml-1">Resolutions are FINAL.</span>
        </p>
      </div>

      {/* Rules Banner */}
      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 p-4 mb-8">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5" />
          <div>
            <h3 className="font-bold text-amber-800 dark:text-amber-300 mb-1">Resolution Rules</h3>
            <ul className="text-sm text-amber-700 dark:text-amber-400 space-y-1">
              <li>• <strong>Binary only:</strong> CORRECT or WRONG - no partial credit</li>
              <li>• <strong>Evidence required:</strong> Must provide URL proof of outcome</li>
              <li>• <strong>Final decision:</strong> Once resolved, it cannot be changed</li>
              <li>• <strong>Be objective:</strong> Judge based on the exact claim, not intent</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={cn(
          "mb-6 p-4 flex items-center gap-2",
          message.type === 'success' ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400' : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
        )}>
          {message.type === 'success' ? <CheckCircle className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
          {message.text}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => {
            setActiveTab('pending')
            loadPendingPredictions()
          }}
          className={cn(
            "flex items-center gap-2 px-4 py-2 font-bold text-sm transition-colors",
            activeTab === 'pending'
              ? 'bg-black dark:bg-white text-white dark:text-black'
              : 'bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400 hover:border-black dark:hover:border-white'
          )}
        >
          <Clock className="h-4 w-4" />
          Pending Resolution ({predictions.length})
        </button>
        <button
          onClick={() => {
            setActiveTab('history')
            loadHistory()
          }}
          className={cn(
            "flex items-center gap-2 px-4 py-2 font-bold text-sm transition-colors",
            activeTab === 'history'
              ? 'bg-black dark:bg-white text-white dark:text-black'
              : 'bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400 hover:border-black dark:hover:border-white'
          )}
        >
          <History className="h-4 w-4" />
          Resolution History
        </button>
      </div>

      {/* Pending Tab */}
      {activeTab === 'pending' && (
        <div className="space-y-4">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-black dark:border-white border-t-transparent rounded-full" />
            </div>
          ) : predictions.length > 0 ? (
            predictions.map(pred => (
              <div key={pred.id} className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 overflow-hidden">
                {/* Header */}
                <div className={cn(
                  "px-4 py-2 flex items-center justify-between border-b",
                  pred.days_overdue > 30 ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800" :
                  pred.days_overdue > 7 ? "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800" :
                  "bg-neutral-50 dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700"
                )}>
                  <div className="flex items-center gap-3">
                    <span className={cn(
                      "text-xs font-black uppercase tracking-wider px-2 py-0.5",
                      pred.days_overdue > 30 ? "bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200" :
                      pred.days_overdue > 7 ? "bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200" :
                      "bg-neutral-200 dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200"
                    )}>
                      {pred.days_overdue} days overdue
                    </span>
                    <span className="text-xs font-bold text-neutral-600 dark:text-neutral-400 uppercase">{pred.category}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {pred.tr_index_score && (
                      <span className="text-xs font-bold bg-black dark:bg-white text-white dark:text-black px-2 py-0.5 rounded-full">
                        TR: {pred.tr_index_score.toFixed(0)}
                      </span>
                    )}
                    <span className="text-xs text-neutral-500 flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      Deadline: {formatDate(pred.timeframe)}
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-4">
                  {/* Pundit */}
                  <div className="flex items-center gap-3 mb-3">
                    <div className="h-10 w-10 rounded-full border-2 border-neutral-200 dark:border-neutral-700 overflow-hidden bg-black flex items-center justify-center">
                      <img 
                        src={getAvatarUrl(pred.pundit_name)} 
                        alt={pred.pundit_name} 
                        className="h-full w-full object-cover" 
                      />
                    </div>
                    <div>
                      <p className="font-bold text-black dark:text-white">{pred.pundit_name}</p>
                      <p className="text-sm text-neutral-500">@{pred.pundit_username}</p>
                    </div>
                  </div>

                  {/* Claim */}
                  <p className="font-bold text-lg text-black dark:text-white mb-3">{pred.claim}</p>

                  {/* Quote */}
                  <div className="bg-neutral-50 dark:bg-neutral-800 p-3 mb-4 border-l-4 border-neutral-300 dark:border-neutral-600 italic text-sm text-neutral-600 dark:text-neutral-400">
                    "{pred.quote}"
                  </div>

                  {/* Community Opinion */}
                  <div className="flex items-center gap-4 mb-4 p-3 bg-neutral-50 dark:bg-neutral-800">
                    <span className="text-sm font-bold text-neutral-600 dark:text-neutral-400">Community thinks:</span>
                    <div className="flex items-center gap-2">
                      <ThumbsUp className="h-4 w-4 text-green-600 dark:text-green-400" />
                      <span className="text-sm font-bold text-green-600 dark:text-green-400">{pred.community_votes.upvotes}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <ThumbsDown className="h-4 w-4 text-red-600 dark:text-red-400" />
                      <span className="text-sm font-bold text-red-600 dark:text-red-400">{pred.community_votes.downvotes}</span>
                    </div>
                  </div>

                  {/* Source Link */}
                  <div className="flex items-center justify-between mb-4">
                    <a
                      href={pred.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-black dark:text-white hover:underline flex items-center gap-1"
                    >
                      <ExternalLink className="h-3 w-3" />
                      View Original Source
                    </a>
                  </div>

                  {/* Resolution Form */}
                  {resolutionForm.predictionId === pred.id ? (
                    <div className="border-t border-neutral-200 dark:border-neutral-700 pt-4 space-y-4">
                      <div>
                        <label className="block text-sm font-bold text-black dark:text-white mb-2">
                          <LinkIcon className="h-4 w-4 inline mr-1" />
                          Evidence URL (REQUIRED)
                        </label>
                        <input
                          type="url"
                          value={resolutionForm.evidenceUrl}
                          onChange={(e) => setResolutionForm({...resolutionForm, evidenceUrl: e.target.value})}
                          placeholder="https://... (link proving the outcome)"
                          className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-2 text-black dark:text-white"
                          required
                        />
                        <p className="text-xs text-neutral-400 mt-1">Link to article, data, or source that proves the outcome</p>
                      </div>

                      <div>
                        <label className="block text-sm font-bold text-black dark:text-white mb-2">Notes (optional)</label>
                        <input
                          type="text"
                          value={resolutionForm.notes}
                          onChange={(e) => setResolutionForm({...resolutionForm, notes: e.target.value})}
                          placeholder="Brief explanation..."
                          className="w-full border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-4 py-2 text-black dark:text-white"
                        />
                      </div>

                      <div className="flex gap-3">
                        <button
                          onClick={() => resolvePrediction('correct')}
                          disabled={resolving === pred.id}
                          className="flex-1 flex items-center justify-center gap-2 bg-green-600 text-white font-bold py-3 hover:bg-green-700 transition-colors disabled:opacity-50"
                        >
                          <CheckCircle className="h-5 w-5" />
                          CORRECT
                        </button>
                        <button
                          onClick={() => resolvePrediction('wrong')}
                          disabled={resolving === pred.id}
                          className="flex-1 flex items-center justify-center gap-2 bg-red-600 text-white font-bold py-3 hover:bg-red-700 transition-colors disabled:opacity-50"
                        >
                          <XCircle className="h-5 w-5" />
                          WRONG
                        </button>
                      </div>

                      <button
                        onClick={() => setResolutionForm({ predictionId: null, evidenceUrl: '', notes: '' })}
                        className="w-full text-sm text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => openResolutionForm(pred.id)}
                      className="w-full bg-black dark:bg-white text-white dark:text-black font-bold py-3 hover:bg-neutral-800 dark:hover:bg-neutral-200 transition-colors flex items-center justify-center gap-2"
                    >
                      <Gavel className="h-4 w-4" />
                      Resolve This Prediction
                    </button>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-12 text-center">
              <CheckCircle className="h-12 w-12 text-green-300 dark:text-green-600 mx-auto mb-4" />
              <p className="text-neutral-500 font-bold text-lg">All caught up!</p>
              <p className="text-sm text-neutral-400 mt-1">No predictions are past their deadline</p>
            </div>
          )}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="space-y-3">
          {history.length > 0 ? (
            history.map(res => (
              <div key={res.id} className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-4 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-black dark:text-white truncate">{res.claim}</p>
                  <p className="text-sm text-neutral-500">{res.pundit_name} • {res.category}</p>
                </div>
                <div className="flex items-center gap-3 ml-4">
                  <span className="text-xs text-neutral-400">{res.timeframe ? formatDate(res.timeframe) : ''}</span>
                  <span className={cn(
                    "text-xs font-black px-3 py-1 rounded-full",
                    res.outcome === 'YES' ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400" : "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400"
                  )}>
                    {res.outcome_label}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-12 text-center">
              <History className="h-12 w-12 text-neutral-300 dark:text-neutral-600 mx-auto mb-4" />
              <p className="text-neutral-500 font-bold">No resolutions yet</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
