// src/components/predictions/PredictionCardWithVotes.tsx
'use client'
import Link from "next/link"
import { formatDate, cn } from "@/lib/utils"
import { ExternalLink, User, CheckCircle, XCircle, Clock, Shield, Copy, Timer, Hourglass, Flag } from "lucide-react"
import { VoteButtons } from "./VoteButtons"
import { PredictionWithPundit } from "@/lib/api"
import { useState } from "react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Generate UI Avatars URL - consistent with PunditCard
function getAvatarUrl(name: string): string {
  const encoded = encodeURIComponent(name)
  return `https://ui-avatars.com/api/?name=${encoded}&background=000&color=fff&bold=true&size=128`
}

interface Props {
  prediction: PredictionWithPundit
}

function getStatusDisplay(status: string, outcome?: string | null, timeframe?: string | null) {
  // Resolved predictions
  if (status === 'resolved' && outcome) {
    if (outcome === 'YES') {
      return { color: 'bg-green-500 text-white', label: 'CORRECT', icon: CheckCircle }
    } else {
      return { color: 'bg-red-500 text-white', label: 'WRONG', icon: XCircle }
    }
  }
  
  // Check if deadline has passed
  const isPastDue = timeframe ? new Date(timeframe) < new Date() : false
  
  if (isPastDue) {
    // Past deadline but not resolved - awaiting resolution
    return { color: 'bg-amber-500 text-white', label: 'AWAITING', icon: Hourglass }
  }
  
  // Future deadline - actively tracking
  return { color: 'bg-blue-600 text-white', label: 'TRACKING', icon: Timer }
}

// Calculate time remaining until deadline
function getTimeRemaining(timeframe?: string | null) {
  if (!timeframe) return null
  const deadline = new Date(timeframe)
  const now = new Date()
  const diff = deadline.getTime() - now.getTime()
  
  if (diff < 0) {
    const daysPast = Math.abs(Math.floor(diff / (1000 * 60 * 60 * 24)))
    return { text: `${daysPast}d overdue`, isPast: true }
  }
  
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const months = Math.floor(days / 30)
  const years = Math.floor(days / 365)
  
  if (years > 0) return { text: `${years}y ${months % 12}mo left`, isPast: false }
  if (months > 0) return { text: `${months}mo left`, isPast: false }
  if (days > 0) return { text: `${days}d left`, isPast: false }
  return { text: 'Due today', isPast: false }
}

export function PredictionCardWithVotes({ prediction: pred }: Props) {
  const statusDisplay = getStatusDisplay(pred.status, pred.outcome, pred.timeframe)
  const StatusIcon = statusDisplay.icon
  const isResolved = pred.status === 'resolved' && pred.outcome
  const isCorrect = pred.outcome === 'YES'
  const timeRemaining = getTimeRemaining(pred.timeframe)
  const [showHash, setShowHash] = useState(false)
  const [copied, setCopied] = useState(false)
  const [showReport, setShowReport] = useState(false)
  const [reportReason, setReportReason] = useState('')
  const [reportSent, setReportSent] = useState(false)

  const copyHash = () => {
    if (pred.chain_hash) {
      navigator.clipboard.writeText(pred.chain_hash)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }
  
  const submitReport = async () => {
    if (!reportReason.trim()) return
    try {
      await fetch(`${API_URL}/api/predictions/${pred.id}/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: reportReason })
      })
      setReportSent(true)
      setTimeout(() => {
        setShowReport(false)
        setReportSent(false)
        setReportReason('')
      }, 2000)
    } catch {
      // Silent fail
    }
  }

  return (
    <div className={cn(
      "bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 overflow-hidden hover:shadow-md transition-shadow",
      isResolved && isCorrect && "border-green-400 dark:border-green-700",
      isResolved && !isCorrect && "border-red-400 dark:border-red-700"
    )}>
      {/* Status Banner */}
      <div className={cn("px-4 py-2 flex items-center justify-between", statusDisplay.color)}>
        <div className="flex items-center gap-2">
          <StatusIcon className="h-4 w-4" />
          <span className="text-xs font-black uppercase tracking-wider">{statusDisplay.label}</span>
          {/* Time remaining/overdue indicator */}
          {!isResolved && timeRemaining && (
            <span className={cn(
              "text-[10px] font-bold px-1.5 py-0.5 rounded",
              timeRemaining.isPast ? "bg-red-600/30" : "bg-white/20"
            )}>
              {timeRemaining.text}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {pred.tr_index?.score && (
            <span 
              className={cn(
                "flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full cursor-help",
                pred.tr_index.tier === 'gold' ? 'bg-yellow-400/90 text-yellow-900' :
                pred.tr_index.tier === 'silver' ? 'bg-neutral-300/90 text-neutral-800' :
                'bg-orange-300/90 text-orange-900'
              )}
              title={`TR Score: ${pred.tr_index.score.toFixed(0)}/100 (${pred.tr_index.tier === 'gold' ? 'Gold - Exceptional' : pred.tr_index.tier === 'silver' ? 'Silver - Good' : 'Bronze - Acceptable'})\n\nMeasures prediction quality:\n• Specificity - Clear targets?\n• Verifiability - Can we check it?\n• Boldness - Non-obvious?\n• Relevance - Timely?\n• Stakes - Significant?`}
            >
              <span className="text-sm">
                {pred.tr_index.tier === 'gold' ? '🥇' : pred.tr_index.tier === 'silver' ? '🥈' : '🥉'}
              </span>
              <span className="text-[10px] opacity-70">TR</span>
              {pred.tr_index.score.toFixed(0)}
            </span>
          )}
          <span className="text-xs font-semibold uppercase tracking-wider opacity-80">{pred.category}</span>
        </div>
      </div>
      
      <div className="p-4">
        {/* Pundit Header */}
        <Link href={`/pundits/${pred.pundit.id}`} className="flex items-center gap-3 mb-3 group">
          <div className="h-10 w-10 rounded-full border-2 border-neutral-200 dark:border-neutral-700 overflow-hidden bg-black flex items-center justify-center flex-shrink-0">
            <img 
              src={getAvatarUrl(pred.pundit.name)} 
              alt={pred.pundit.name} 
              className="h-full w-full object-cover" 
            />
          </div>
          <div className="min-w-0">
            <p className="font-bold text-black dark:text-white text-sm truncate">{pred.pundit.name}</p>
            <p className="text-xs text-neutral-500">@{pred.pundit.username}</p>
          </div>
        </Link>

        {/* Claim */}
        <p className="font-bold text-black dark:text-white mb-3 line-clamp-2">{pred.claim}</p>
        
        {/* Quote */}
        <div className="bg-neutral-50 dark:bg-neutral-800 p-3 mb-3 border-l-4 border-neutral-300 dark:border-neutral-600 italic text-sm text-neutral-600 dark:text-neutral-400 line-clamp-2">
          "{pred.quote}"
        </div>

        {/* Footer with Voting */}
        <div className="flex items-center justify-between text-xs text-neutral-400">
          <div className="flex items-center gap-3">
            <span>{pred.captured_at ? formatDate(pred.captured_at) : 'Unknown date'}</span>
            <VoteButtons predictionId={pred.id} />
          </div>
          <div className="flex items-center gap-2">
            {/* Hash Chain Verification Badge */}
            <div className="relative">
              {pred.chain_hash && (
                <button 
                  onClick={() => setShowHash(!showHash)}
                  className="flex items-center gap-1 font-bold text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300"
                  title="Cryptographically verified on blockchain"
                >
                  <Shield className="h-3 w-3" />
                  <span className="hidden sm:inline">Verified</span>
                </button>
              )}
              {showHash && pred.chain_hash && (
                <div className="absolute bottom-full right-0 mb-2 p-2 bg-black dark:bg-white text-white dark:text-black text-[10px] font-mono whitespace-nowrap z-10 shadow-lg">
                  <div className="flex items-center gap-2">
                    <span>#{pred.chain_index || '?'}</span>
                    <span>{pred.chain_hash}</span>
                    <button onClick={copyHash} className="hover:text-green-400 dark:hover:text-green-600">
                      <Copy className="h-3 w-3" />
                    </button>
                    {copied && <span className="text-green-400 dark:text-green-600 ml-2">Copied!</span>}
                  </div>
                </div>
              )}
            </div>
            {pred.source_url && 
             pred.source_url !== 'https://example.com/test' && 
             !pred.source_url.includes('archive.trackrecord.life') && (
              <a href={pred.source_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white hover:underline font-bold">
                Source <ExternalLink className="h-3 w-3" />
              </a>
            )}
            {pred.source_url?.includes('archive.trackrecord.life') && (
              <span className="flex items-center gap-1 text-neutral-400 text-[10px]">
                Historical data
              </span>
            )}
            {/* Report Button */}
            <button
              onClick={() => setShowReport(!showReport)}
              className="flex items-center gap-1 text-neutral-400 hover:text-red-500 transition-colors"
              title="Report issue"
            >
              <Flag className="h-3 w-3" />
            </button>
          </div>
          
          {/* Report Form */}
          {showReport && (
            <div className="mt-3 p-3 bg-neutral-50 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700">
              {reportSent ? (
                <p className="text-sm text-green-600 dark:text-green-400 font-bold">Thanks for reporting!</p>
              ) : (
                <>
                  <p className="text-xs text-neutral-500 mb-2">Report an issue with this prediction:</p>
                  <select
                    value={reportReason}
                    onChange={(e) => setReportReason(e.target.value)}
                    className="w-full text-sm border border-neutral-200 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-2 py-1 mb-2"
                  >
                    <option value="">Select reason...</option>
                    <option value="broken_source">Source link broken</option>
                    <option value="wrong_pundit">Wrong pundit attribution</option>
                    <option value="duplicate">Duplicate prediction</option>
                    <option value="not_prediction">Not a real prediction</option>
                    <option value="wrong_outcome">Outcome is incorrect</option>
                    <option value="other">Other issue</option>
                  </select>
                  <div className="flex gap-2">
                    <button
                      onClick={submitReport}
                      disabled={!reportReason}
                      className="flex-1 text-xs bg-red-500 text-white px-2 py-1 font-bold disabled:opacity-50"
                    >
                      Submit Report
                    </button>
                    <button
                      onClick={() => setShowReport(false)}
                      className="text-xs text-neutral-500 hover:text-neutral-700 px-2 py-1"
                    >
                      Cancel
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
