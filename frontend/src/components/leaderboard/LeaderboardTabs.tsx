// src/components/leaderboard/LeaderboardTabs.tsx
'use client'
import { useState, useEffect } from 'react'
import { Pundit } from '@/lib/api'
import { LeaderboardFilter } from './LeaderboardFilter'
import { Trophy, Users, Medal, TrendingUp } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface CommunityUser {
  rank: number
  id: string
  username: string
  display_name: string
  avatar_url?: string
  total_predictions: number
  correct: number
  wrong: number
  win_rate: number
}

interface LeaderboardTabsProps {
  pundits: Pundit[]
}

export function LeaderboardTabs({ pundits }: LeaderboardTabsProps) {
  const [activeTab, setActiveTab] = useState<'pundits' | 'amateurs'>('pundits')
  const [amateurs, setAmateurs] = useState<CommunityUser[]>([])
  const [loadingAmateurs, setLoadingAmateurs] = useState(false)

  useEffect(() => {
    if (activeTab === 'amateurs' && amateurs.length === 0) {
      loadAmateurs()
    }
  }, [activeTab])

  const loadAmateurs = async () => {
    setLoadingAmateurs(true)
    try {
      const res = await fetch(`${API_URL}/api/community/leaderboard?limit=50`)
      if (res.ok) {
        const data = await res.json()
        setAmateurs(data)
      }
    } catch (err) {
      console.error('Failed to load amateur leaderboard:', err)
    }
    setLoadingAmateurs(false)
  }

  return (
    <div>
      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('pundits')}
          className={`flex items-center gap-2 px-6 py-3 font-medium text-sm transition-all ${
            activeTab === 'pundits'
              ? 'bg-black dark:bg-white text-white dark:text-black'
              : 'bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-400 hover:border-black dark:hover:border-white'
          }`}
        >
          <Users className="h-4 w-4" />
          Pundits
        </button>
        <button
          onClick={() => setActiveTab('amateurs')}
          className={`flex items-center gap-2 px-6 py-3 font-medium text-sm transition-all ${
            activeTab === 'amateurs'
              ? 'bg-amber-500 text-white'
              : 'bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-400 hover:border-amber-500'
          }`}
        >
          <Trophy className="h-4 w-4" />
          Amateurs
        </button>
      </div>

      {/* Pundit Leaderboard */}
      {activeTab === 'pundits' && (
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
            <div>
              <h3 className="text-lg font-bold text-black dark:text-white">Professional Pundits</h3>
              <p className="text-sm text-neutral-500">Ranked by Accuracy</p>
            </div>
            <div className="text-xs text-neutral-500 bg-neutral-100 dark:bg-neutral-800 px-3 py-2">
              Min. 3 resolved predictions required
            </div>
          </div>
          {pundits.length > 0 ? (
            <LeaderboardFilter pundits={pundits} />
          ) : (
            <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-12 text-center">
              <p className="text-neutral-500 font-medium">No pundit data found.</p>
            </div>
          )}
        </div>
      )}

      {/* Amateur Leaderboard */}
      {activeTab === 'amateurs' && (
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
            <div>
              <h3 className="text-lg font-bold text-black dark:text-white">Community Predictors</h3>
              <p className="text-sm text-neutral-500">Compete and prove you're better than the pros!</p>
            </div>
            <a
              href="/compete"
              className="text-sm font-medium text-amber-600 hover:text-amber-700"
            >
              Join the competition →
            </a>
          </div>

          {loadingAmateurs ? (
            <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-12 text-center">
              <div className="animate-spin h-8 w-8 border-4 border-black dark:border-white border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-neutral-500">Loading leaderboard...</p>
            </div>
          ) : amateurs.length > 0 ? (
            <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 overflow-hidden">
              <table className="w-full">
                <thead className="bg-neutral-50 dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">Rank</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">User</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-neutral-500 uppercase tracking-wider">Win Rate</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-neutral-500 uppercase tracking-wider">Record</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-neutral-500 uppercase tracking-wider">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
                  {amateurs.map((user, i) => (
                    <tr key={user.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors">
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          {user.rank === 1 && <Medal className="h-5 w-5 text-yellow-500" />}
                          {user.rank === 2 && <Medal className="h-5 w-5 text-neutral-400" />}
                          {user.rank === 3 && <Medal className="h-5 w-5 text-orange-400" />}
                          <span className={`font-bold ${user.rank <= 3 ? 'text-lg text-black dark:text-white' : 'text-neutral-600 dark:text-neutral-400'}`}>
                            #{user.rank}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-full bg-black dark:bg-white flex items-center justify-center text-white dark:text-black font-bold">
                            {(user.display_name || user.username).charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-bold text-black dark:text-white">{user.display_name || user.username}</p>
                            <p className="text-sm text-neutral-500">@{user.username}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span className={`text-xl font-black ${
                          user.win_rate >= 0.6 ? 'text-green-600 dark:text-green-400' :
                          user.win_rate >= 0.4 ? 'text-black dark:text-white' :
                          'text-red-600 dark:text-red-400'
                        }`}>
                          {(user.win_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span className="font-bold text-green-600 dark:text-green-400">{user.correct}</span>
                        <span className="text-neutral-400 mx-1">-</span>
                        <span className="font-bold text-red-600 dark:text-red-400">{user.wrong}</span>
                      </td>
                      <td className="px-4 py-4 text-center text-neutral-600 dark:text-neutral-400 font-medium">
                        {user.total_predictions}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-12 text-center">
              <Trophy className="h-12 w-12 text-amber-400 mx-auto mb-4" />
              <p className="text-neutral-500 font-medium mb-4">No amateur predictions yet!</p>
              <a
                href="/compete"
                className="inline-flex items-center gap-2 bg-amber-500 text-white font-medium px-6 py-3 hover:bg-amber-600 transition-colors"
              >
                <TrendingUp className="h-4 w-4" />
                Be the first to compete
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
