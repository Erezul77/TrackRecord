// src/components/predictions/VoteButtons.tsx
'use client'
import { useState, useEffect } from 'react'
import { ThumbsUp, ThumbsDown } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface VoteButtonsProps {
  predictionId: string
}

export function VoteButtons({ predictionId }: VoteButtonsProps) {
  const [upvotes, setUpvotes] = useState(0)
  const [downvotes, setDownvotes] = useState(0)
  const [userVote, setUserVote] = useState<'up' | 'down' | null>(null)
  const [userId, setUserId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Check if user is logged in (from localStorage)
    const stored = localStorage.getItem('community_user')
    if (stored) {
      const user = JSON.parse(stored)
      setUserId(user.user_id)
    }
    
    // Load current votes
    loadVotes()
  }, [])

  const loadVotes = async () => {
    try {
      const userParam = userId ? `?user_id=${userId}` : ''
      const res = await fetch(`${API_URL}/api/predictions/${predictionId}/votes${userParam}`)
      if (res.ok) {
        const data = await res.json()
        setUpvotes(data.upvotes)
        setDownvotes(data.downvotes)
        setUserVote(data.user_vote)
      }
    } catch (err) {
      console.error('Failed to load votes:', err)
    }
  }

  const handleVote = async (voteType: 'up' | 'down') => {
    if (!userId) {
      alert('Please register at /compete to vote on predictions!')
      return
    }
    
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/predictions/${predictionId}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, vote_type: voteType })
      })
      
      if (res.ok) {
        const data = await res.json()
        
        // Update UI based on response
        if (data.status === 'removed') {
          // Vote was toggled off
          if (voteType === 'up') setUpvotes(v => v - 1)
          else setDownvotes(v => v - 1)
          setUserVote(null)
        } else if (data.status === 'updated') {
          // Vote was changed
          if (voteType === 'up') {
            setUpvotes(v => v + 1)
            setDownvotes(v => v - 1)
          } else {
            setUpvotes(v => v - 1)
            setDownvotes(v => v + 1)
          }
          setUserVote(voteType)
        } else {
          // New vote
          if (voteType === 'up') setUpvotes(v => v + 1)
          else setDownvotes(v => v + 1)
          setUserVote(voteType)
        }
      }
    } catch (err) {
      console.error('Failed to vote:', err)
    }
    setLoading(false)
  }

  const score = upvotes - downvotes

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={() => handleVote('up')}
        disabled={loading}
        className={`p-1.5  transition-all ${
          userVote === 'up'
            ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
            : 'hover:bg-green-50 dark:hover:bg-green-900/20 text-neutral-400 hover:text-green-600 dark:hover:text-green-400'
        } disabled:opacity-50`}
        title={userId ? 'Upvote' : 'Register to vote'}
      >
        <ThumbsUp className="h-4 w-4" />
      </button>
      
      <span className={`min-w-[2rem] text-center text-sm font-bold ${
        score > 0 ? 'text-green-500' :
        score < 0 ? 'text-red-500' :
        'text-neutral-400'
      }`}>
        {score > 0 ? `+${score}` : score}
      </span>
      
      <button
        onClick={() => handleVote('down')}
        disabled={loading}
        className={`p-1.5  transition-all ${
          userVote === 'down'
            ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
            : 'hover:bg-red-50 dark:hover:bg-red-900/20 text-neutral-400 hover:text-red-600 dark:hover:text-red-400'
        } disabled:opacity-50`}
        title={userId ? 'Downvote' : 'Register to vote'}
      >
        <ThumbsDown className="h-4 w-4" />
      </button>
    </div>
  )
}
