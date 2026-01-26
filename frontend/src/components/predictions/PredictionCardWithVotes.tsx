// src/components/predictions/PredictionCardWithVotes.tsx
'use client'
import Link from "next/link"
import { formatDate, cn } from "@/lib/utils"
import { ExternalLink, User, CheckCircle, XCircle, Clock, Sparkles, Shield, Copy } from "lucide-react"
import { VoteButtons } from "./VoteButtons"
import { PredictionWithPundit } from "@/lib/api"
import { useState } from "react"

// Generate UI Avatars URL - consistent with PunditCard
function getAvatarUrl(name: string): string {
  const encoded = encodeURIComponent(name)
  return `https://ui-avatars.com/api/?name=${encoded}&background=000&color=fff&bold=true&size=128`
}

interface Props {
  prediction: PredictionWithPundit
}

function getStatusDisplay(status: string, outcome?: string | null) {
  if (status === 'resolved' && outcome) {
    if (outcome === 'YES') {
      return { color: 'bg-green-500 text-white', label: 'CORRECT', icon: CheckCircle }
    } else {
      return { color: 'bg-red-500 text-white', label: 'WRONG', icon: XCircle }
    }
  }
  return { color: 'bg-black dark:bg-white text-white dark:text-black', label: 'OPEN', icon: Clock }
}

export function PredictionCardWithVotes({ prediction: pred }: Props) {
  const statusDisplay = getStatusDisplay(pred.status, pred.outcome)
  const StatusIcon = statusDisplay.icon
  const isResolved = pred.status === 'resolved' && pred.outcome
  const isCorrect = pred.outcome === 'YES'
  const [showHash, setShowHash] = useState(false)
  const [copied, setCopied] = useState(false)

  const copyHash = () => {
    if (pred.chain_hash) {
      navigator.clipboard.writeText(pred.chain_hash)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
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
        </div>
        <div className="flex items-center gap-2">
          {pred.tr_index?.score && (
            <span className={cn(
              "flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full",
              pred.tr_index.tier === 'gold' ? 'bg-yellow-400/90 text-yellow-900' :
              pred.tr_index.tier === 'silver' ? 'bg-neutral-300/90 text-neutral-800' :
              'bg-orange-300/90 text-orange-900'
            )}>
              <Sparkles className="h-3 w-3" />
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
            {pred.chain_hash && (
              <div className="relative">
                <button 
                  onClick={() => setShowHash(!showHash)}
                  className="flex items-center gap-1 text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 font-bold"
                  title="Cryptographically verified"
                >
                  <Shield className="h-3 w-3" />
                  <span className="hidden sm:inline">Verified</span>
                </button>
                {showHash && (
                  <div className="absolute bottom-full right-0 mb-2 p-2 bg-black dark:bg-white text-white dark:text-black text-[10px] font-mono whitespace-nowrap z-10 shadow-lg">
                    <div className="flex items-center gap-2">
                      <span>#{pred.chain_index || '?'}</span>
                      <span>{pred.chain_hash}</span>
                      <button onClick={copyHash} className="hover:text-green-400 dark:hover:text-green-600">
                        <Copy className="h-3 w-3" />
                      </button>
                    </div>
                    {copied && <span className="text-green-400 dark:text-green-600 ml-2">Copied!</span>}
                  </div>
                )}
              </div>
            )}
            {pred.source_url && pred.source_url !== 'https://example.com/test' && (
              <a href={pred.source_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white hover:underline font-bold">
                Source <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
