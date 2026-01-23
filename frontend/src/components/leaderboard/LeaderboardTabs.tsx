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
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all ${
            activeTab === 'pundits'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-200'
              : 'bg-white border text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Users className="h-4 w-4" />
          Pundits
        </button>
        <button
          onClick={() => setActiveTab('amateurs')}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all ${
            activeTab === 'amateurs'
              ? 'bg-yellow-500 text-white shadow-lg shadow-yellow-200'
              : 'bg-white border text-slate-600 hover:bg-slate-50'
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
              <h2 className="text-xl font-bold text-slate-900">Professional Pundits</h2>
              <p className="text-sm text-slate-500">Ranked by Accuracy (Win Rate)</p>
            </div>
            <div className="text-xs text-slate-400 bg-slate-100 px-3 py-2 rounded-lg">
              Min. 3 resolved predictions required
            </div>
          </div>
          {pundits.length > 0 ? (
            <LeaderboardFilter pundits={pundits} />
          ) : (
            <div className="bg-white border rounded-xl p-12 text-center">
              <p className="text-slate-500 font-medium">No pundit data found.</p>
            </div>
          )}
        </div>
      )}

      {/* Amateur Leaderboard */}
      {activeTab === 'amateurs' && (
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Community Predictors</h2>
              <p className="text-sm text-slate-500">Compete and prove you're better than the pros!</p>
            </div>
            <a
              href="/compete"
              className="text-sm font-bold text-yellow-600 hover:text-yellow-700"
            >
              Join the competition →
            </a>
          </div>

          {loadingAmateurs ? (
            <div className="bg-white border rounded-xl p-12 text-center">
              <div className="animate-spin h-8 w-8 border-4 border-yellow-500 border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-slate-500">Loading leaderboard...</p>
            </div>
          ) : amateurs.length > 0 ? (
            <div className="bg-white border rounded-xl overflow-hidden">
              <table className="w-full">
                <thead className="bg-slate-50 border-b">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Rank</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">User</th>
                    <th className="px-4 py-3 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Win Rate</th>
                    <th className="px-4 py-3 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Record</th>
                    <th className="px-4 py-3 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {amateurs.map((user, i) => (
                    <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          {user.rank === 1 && <Medal className="h-5 w-5 text-yellow-500" />}
                          {user.rank === 2 && <Medal className="h-5 w-5 text-slate-400" />}
                          {user.rank === 3 && <Medal className="h-5 w-5 text-orange-400" />}
                          <span className={`font-bold ${user.rank <= 3 ? 'text-lg' : 'text-slate-600'}`}>
                            #{user.rank}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center text-white font-bold">
                            {(user.display_name || user.username).charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-bold text-slate-900">{user.display_name || user.username}</p>
                            <p className="text-sm text-slate-500">@{user.username}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span className={`text-xl font-black ${
                          user.win_rate >= 0.6 ? 'text-emerald-600' :
                          user.win_rate >= 0.4 ? 'text-slate-900' :
                          'text-rose-600'
                        }`}>
                          {(user.win_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span className="font-bold text-emerald-600">{user.correct}</span>
                        <span className="text-slate-400 mx-1">-</span>
                        <span className="font-bold text-rose-600">{user.wrong}</span>
                      </td>
                      <td className="px-4 py-4 text-center text-slate-600 font-medium">
                        {user.total_predictions}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-white border rounded-xl p-12 text-center">
              <Trophy className="h-12 w-12 text-yellow-300 mx-auto mb-4" />
              <p className="text-slate-500 font-medium mb-4">No amateur predictions yet!</p>
              <a
                href="/compete"
                className="inline-flex items-center gap-2 bg-yellow-500 text-white font-bold px-6 py-3 rounded-lg hover:bg-yellow-600 transition-colors"
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
