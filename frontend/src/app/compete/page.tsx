// src/app/compete/page.tsx
'use client'
import { useState, useEffect } from 'react'
import { Trophy, User, Target, TrendingUp, LogIn, UserPlus, Send, CheckCircle, XCircle, Clock, Star } from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface UserData {
  user_id: string
  username: string
  display_name: string
  stats: {
    total_predictions: number
    correct: number
    wrong: number
    win_rate: number
  }
}

interface Prediction {
  id: string
  claim: string
  category: string
  status: string
  outcome: string | null
  timeframe: string
  created_at: string
}

interface LeaderboardUser {
  rank: number
  id: string
  username: string
  display_name: string
  total_predictions: number
  correct: number
  wrong: number
  win_rate: number
}

export default function CompetePage() {
  const [user, setUser] = useState<UserData | null>(null)
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderboardUser[]>([])
  const [activeTab, setActiveTab] = useState<'dashboard' | 'leaderboard' | 'auth'>('auth')
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  
  // Auth form
  const [authForm, setAuthForm] = useState({
    username: '',
    email: '',
    password: '',
    display_name: ''
  })
  
  // Prediction form
  const [predictionForm, setPredictionForm] = useState({
    claim: '',
    category: 'markets',
    timeframe_days: 30
  })

  // Load from localStorage on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('community_user')
    if (savedUser) {
      const userData = JSON.parse(savedUser)
      setUser(userData)
      setActiveTab('dashboard')
      loadUserPredictions(userData.user_id)
    }
    loadLeaderboard()
  }, [])

  const loadUserPredictions = async (userId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/community/user/${userId}/predictions`)
      if (res.ok) {
        const data = await res.json()
        setPredictions(data)
      }
    } catch (err) {
      console.error('Failed to load predictions:', err)
    }
  }

  const loadLeaderboard = async () => {
    try {
      const res = await fetch(`${API_URL}/api/community/leaderboard`)
      if (res.ok) {
        const data = await res.json()
        setLeaderboard(data)
      }
    } catch (err) {
      console.error('Failed to load leaderboard:', err)
    }
  }

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)

    try {
      const endpoint = authMode === 'login' 
        ? `${API_URL}/api/community/login`
        : `${API_URL}/api/community/register`
      
      const body = authMode === 'login'
        ? { email: authForm.email, password: authForm.password }
        : authForm

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await res.json()

      if (res.ok) {
        if (authMode === 'register') {
          setMessage({ type: 'success', text: 'Registration successful! Please log in.' })
          setAuthMode('login')
        } else {
          localStorage.setItem('community_user', JSON.stringify(data))
          setUser(data)
          setActiveTab('dashboard')
          loadUserPredictions(data.user_id)
          setMessage({ type: 'success', text: `Welcome back, ${data.display_name}!` })
        }
      } else {
        setMessage({ type: 'error', text: data.detail || 'Authentication failed' })
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' })
    }

    setLoading(false)
  }

  const handleCreatePrediction = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return
    
    setLoading(true)
    setMessage(null)

    try {
      const res = await fetch(`${API_URL}/api/community/user/${user.user_id}/predictions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(predictionForm)
      })

      const data = await res.json()

      if (res.ok) {
        setMessage({ type: 'success', text: 'Prediction created!' })
        setPredictionForm({ claim: '', category: 'markets', timeframe_days: 30 })
        loadUserPredictions(user.user_id)
        // Update local user stats
        setUser(prev => prev ? {
          ...prev,
          stats: { ...prev.stats, total_predictions: prev.stats.total_predictions + 1 }
        } : null)
      } else {
        setMessage({ type: 'error', text: data.detail || 'Failed to create prediction' })
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' })
    }

    setLoading(false)
  }

  const handleLogout = () => {
    localStorage.removeItem('community_user')
    setUser(null)
    setPredictions([])
    setActiveTab('auth')
    setMessage({ type: 'success', text: 'Logged out successfully' })
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <div className="container mx-auto px-4 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="flex items-center justify-center gap-3 mb-4">
          <Trophy className="h-10 w-10 text-yellow-500" />
          <h1 className="text-4xl font-black text-slate-900 tracking-tighter">Prediction Competition</h1>
        </div>
        <p className="text-slate-500 text-lg max-w-xl mx-auto">
          Think you can beat the pundits? Make predictions, track your accuracy, and climb the leaderboard!
        </p>
      </div>

      {/* Tabs */}
      <div className="flex justify-center gap-2 mb-8">
        {user && (
          <button
            onClick={() => setActiveTab('dashboard')}
            className={cn(
              "flex items-center gap-2 px-6 py-3 rounded-lg font-bold transition-colors",
              activeTab === 'dashboard' 
                ? "bg-blue-600 text-white" 
                : "bg-white border text-slate-600 hover:bg-slate-50"
            )}
          >
            <User className="h-4 w-4" />
            My Dashboard
          </button>
        )}
        <button
          onClick={() => setActiveTab('leaderboard')}
          className={cn(
            "flex items-center gap-2 px-6 py-3 rounded-lg font-bold transition-colors",
            activeTab === 'leaderboard' 
              ? "bg-blue-600 text-white" 
              : "bg-white border text-slate-600 hover:bg-slate-50"
          )}
        >
          <Trophy className="h-4 w-4" />
          Leaderboard
        </button>
        {!user && (
          <button
            onClick={() => setActiveTab('auth')}
            className={cn(
              "flex items-center gap-2 px-6 py-3 rounded-lg font-bold transition-colors",
              activeTab === 'auth' 
                ? "bg-blue-600 text-white" 
                : "bg-white border text-slate-600 hover:bg-slate-50"
            )}
          >
            <LogIn className="h-4 w-4" />
            Join
          </button>
        )}
        {user && (
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-6 py-3 rounded-lg font-bold bg-white border text-slate-600 hover:bg-slate-50"
          >
            Logout
          </button>
        )}
      </div>

      {/* Message */}
      {message && (
        <div className={cn(
          "max-w-xl mx-auto mb-6 p-4 rounded-lg flex items-center gap-2",
          message.type === 'success' ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
        )}>
          {message.type === 'success' ? <CheckCircle className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
          {message.text}
        </div>
      )}

      {/* Auth Tab */}
      {activeTab === 'auth' && !user && (
        <div className="max-w-md mx-auto">
          <div className="bg-white border rounded-xl p-6">
            <div className="flex gap-2 mb-6">
              <button
                onClick={() => setAuthMode('login')}
                className={cn(
                  "flex-1 py-2 rounded-lg font-bold text-sm",
                  authMode === 'login' ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"
                )}
              >
                <LogIn className="h-4 w-4 inline mr-2" />
                Login
              </button>
              <button
                onClick={() => setAuthMode('register')}
                className={cn(
                  "flex-1 py-2 rounded-lg font-bold text-sm",
                  authMode === 'register' ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"
                )}
              >
                <UserPlus className="h-4 w-4 inline mr-2" />
                Register
              </button>
            </div>

            <form onSubmit={handleAuth} className="space-y-4">
              {authMode === 'register' && (
                <>
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Username</label>
                    <input
                      type="text"
                      value={authForm.username}
                      onChange={(e) => setAuthForm({...authForm, username: e.target.value})}
                      className="w-full border rounded-lg px-4 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Display Name</label>
                    <input
                      type="text"
                      value={authForm.display_name}
                      onChange={(e) => setAuthForm({...authForm, display_name: e.target.value})}
                      className="w-full border rounded-lg px-4 py-2"
                      placeholder="How you'll appear on leaderboard"
                    />
                  </div>
                </>
              )}
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Email</label>
                <input
                  type="email"
                  value={authForm.email}
                  onChange={(e) => setAuthForm({...authForm, email: e.target.value})}
                  className="w-full border rounded-lg px-4 py-2"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Password</label>
                <input
                  type="password"
                  value={authForm.password}
                  onChange={(e) => setAuthForm({...authForm, password: e.target.value})}
                  className="w-full border rounded-lg px-4 py-2"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white font-bold py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Please wait...' : (authMode === 'login' ? 'Login' : 'Create Account')}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && user && (
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* Stats Cards */}
            <div className="bg-white border rounded-xl p-6 text-center">
              <Target className="h-8 w-8 text-blue-600 mx-auto mb-2" />
              <div className="text-3xl font-black text-slate-900">{user.stats.total_predictions}</div>
              <div className="text-sm text-slate-500">Total Predictions</div>
            </div>
            <div className="bg-white border rounded-xl p-6 text-center">
              <TrendingUp className="h-8 w-8 text-emerald-600 mx-auto mb-2" />
              <div className="text-3xl font-black text-emerald-600">
                {(user.stats.win_rate * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-slate-500">Win Rate</div>
            </div>
            <div className="bg-white border rounded-xl p-6 text-center">
              <Trophy className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
              <div className="text-3xl font-black text-slate-900">
                {user.stats.correct}W - {user.stats.wrong}L
              </div>
              <div className="text-sm text-slate-500">Record</div>
            </div>
          </div>

          {/* Create Prediction */}
          <div className="bg-white border rounded-xl p-6 mb-8">
            <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Send className="h-5 w-5 text-blue-600" />
              Make a Prediction
            </h3>
            <form onSubmit={handleCreatePrediction} className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Your Prediction *</label>
                <textarea
                  value={predictionForm.claim}
                  onChange={(e) => setPredictionForm({...predictionForm, claim: e.target.value})}
                  placeholder="e.g., Bitcoin will reach $150,000 by the end of this timeframe"
                  className="w-full border rounded-lg px-4 py-2 h-20"
                  required
                />
                <p className="text-xs text-slate-400 mt-1">Be specific! Include targets and make it measurable.</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-1">Category</label>
                  <select
                    value={predictionForm.category}
                    onChange={(e) => setPredictionForm({...predictionForm, category: e.target.value})}
                    className="w-full border rounded-lg px-4 py-2"
                  >
                    <optgroup label="Topics">
                      <option value="markets">Markets</option>
                      <option value="crypto">Crypto</option>
                      <option value="economy">Economy</option>
                      <option value="politics">Politics</option>
                      <option value="tech">Tech</option>
                      <option value="sports">Sports</option>
                      <option value="entertainment">Entertainment</option>
                      <option value="religion">Religion</option>
                      <option value="science">Science</option>
                      <option value="health">Health</option>
                      <option value="climate">Climate</option>
                      <option value="geopolitics">Geopolitics</option>
                      <option value="other">Other</option>
                    </optgroup>
                    <optgroup label="Regions">
                      <option value="us">United States</option>
                      <option value="uk">United Kingdom</option>
                      <option value="eu">European Union</option>
                      <option value="china">China</option>
                      <option value="japan">Japan</option>
                      <option value="india">India</option>
                      <option value="israel">Israel</option>
                      <option value="russia">Russia</option>
                      <option value="brazil">Brazil</option>
                      <option value="latam">Latin America</option>
                      <option value="middle-east">Middle East</option>
                      <option value="africa">Africa</option>
                    </optgroup>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-1">Resolves In</label>
                  <select
                    value={predictionForm.timeframe_days}
                    onChange={(e) => setPredictionForm({...predictionForm, timeframe_days: parseInt(e.target.value)})}
                    className="w-full border rounded-lg px-4 py-2"
                  >
                    <option value={7}>1 Week</option>
                    <option value={14}>2 Weeks</option>
                    <option value={30}>1 Month</option>
                    <option value={90}>3 Months</option>
                    <option value={180}>6 Months</option>
                    <option value={365}>1 Year</option>
                  </select>
                </div>
              </div>
              <button
                type="submit"
                disabled={loading || !predictionForm.claim}
                className="w-full bg-blue-600 text-white font-bold py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Submit Prediction
              </button>
            </form>
          </div>

          {/* My Predictions */}
          <div>
            <h3 className="font-bold text-slate-900 mb-4">My Predictions</h3>
            {predictions.length > 0 ? (
              <div className="space-y-3">
                {predictions.map(pred => (
                  <div key={pred.id} className={cn(
                    "bg-white border rounded-xl p-4",
                    pred.outcome === 'YES' && "border-emerald-300 bg-emerald-50",
                    pred.outcome === 'NO' && "border-rose-300 bg-rose-50"
                  )}>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <p className="font-bold text-slate-900">{pred.claim}</p>
                        <p className="text-xs text-slate-500 mt-1">
                          {pred.category} • Resolves {formatDate(pred.timeframe)}
                        </p>
                      </div>
                      <div className={cn(
                        "px-3 py-1 rounded-full text-xs font-bold",
                        pred.outcome === 'YES' && "bg-emerald-500 text-white",
                        pred.outcome === 'NO' && "bg-rose-500 text-white",
                        !pred.outcome && "bg-blue-100 text-blue-700"
                      )}>
                        {pred.outcome === 'YES' ? 'CORRECT' : pred.outcome === 'NO' ? 'WRONG' : 'OPEN'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white border rounded-xl p-12 text-center text-slate-400">
                <Clock className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                <p className="font-bold">No predictions yet</p>
                <p className="text-sm">Make your first prediction above!</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Leaderboard Tab */}
      {activeTab === 'leaderboard' && (
        <div className="max-w-2xl mx-auto">
          <div className="bg-white border rounded-xl overflow-hidden">
            <div className="bg-slate-900 text-white p-4">
              <h3 className="font-bold flex items-center gap-2">
                <Trophy className="h-5 w-5 text-yellow-400" />
                Community Leaderboard
              </h3>
              <p className="text-xs text-slate-400 mt-1">Minimum 3 resolved predictions to rank</p>
            </div>
            
            {leaderboard.length > 0 ? (
              <div className="divide-y">
                {leaderboard.map((u, i) => (
                  <div key={u.id} className="flex items-center gap-4 p-4 hover:bg-slate-50">
                    <div className={cn(
                      "text-2xl font-black w-10 text-center",
                      i === 0 && "text-yellow-500",
                      i === 1 && "text-slate-400",
                      i === 2 && "text-amber-600",
                      i > 2 && "text-slate-300"
                    )}>
                      {u.rank}
                    </div>
                    <div className="flex-1">
                      <p className="font-bold text-slate-900">{u.display_name || u.username}</p>
                      <p className="text-xs text-slate-500">
                        {u.correct}W - {u.wrong}L • {u.total_predictions} predictions
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-black text-emerald-600">
                        {(u.win_rate * 100).toFixed(1)}%
                      </div>
                      <div className="flex gap-0.5 justify-end">
                        {[1,2,3,4,5].map(s => (
                          <Star key={s} className={cn(
                            "h-3 w-3",
                            s <= Math.ceil(u.win_rate * 5) ? "text-yellow-400 fill-yellow-400" : "text-slate-200"
                          )} />
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-12 text-center text-slate-400">
                <Trophy className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                <p className="font-bold">No ranked users yet</p>
                <p className="text-sm">Be the first to make 3 predictions!</p>
              </div>
            )}
          </div>
          
          {!user && (
            <div className="mt-6 text-center">
              <button
                onClick={() => setActiveTab('auth')}
                className="bg-blue-600 text-white font-bold px-8 py-3 rounded-lg hover:bg-blue-700"
              >
                Join the Competition
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
