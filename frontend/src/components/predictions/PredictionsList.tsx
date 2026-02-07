// src/components/predictions/PredictionsList.tsx
'use client'
import { useState, useEffect } from 'react'
import { Clock, ArrowUpDown, Flame, Star, Calendar, SortAsc, Filter, Search, X, ChevronDown, ChevronUp } from 'lucide-react'
import { PredictionCardWithVotes } from './PredictionCardWithVotes'
import { PredictionWithPundit } from '@/lib/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const SORT_OPTIONS = [
  { value: 'default', label: 'Open First', icon: Clock, description: 'Open predictions first, then resolved' },
  { value: 'newest', label: 'Newest', icon: SortAsc, description: 'Most recent first' },
  { value: 'oldest', label: 'Oldest', icon: SortAsc, description: 'Oldest first' },
  { value: 'resolving_soon', label: 'Resolving Soon', icon: Calendar, description: 'About to resolve first' },
  { value: 'boldest', label: 'Boldest', icon: Flame, description: 'Most contrarian first' },
  { value: 'highest_score', label: 'Highest Rated', icon: Star, description: 'Best TR Index first' },
]

// Topics
const TOPIC_CATEGORIES = ['All', 'Politics', 'Economy', 'Markets', 'Crypto', 'Tech', 'Sports', 'Entertainment', 'Religion', 'Science', 'Health', 'Climate', 'Geopolitics']

// Regions
const REGION_CATEGORIES = ['US', 'UK', 'EU', 'China', 'Japan', 'India', 'Israel', 'Russia', 'Brazil', 'LATAM', 'Middle-East', 'Africa']

// Time Horizons
const HORIZON_OPTIONS = [
  { value: 'All', label: 'All Horizons', description: 'All time horizons' },
  { value: 'ST', label: 'Short-term', description: 'Less than 6 months' },
  { value: 'MT', label: 'Medium-term', description: '6-24 months' },
  { value: 'LT', label: 'Long-term', description: '2-5 years' },
  { value: 'V', label: 'Visionary', description: '5+ years' },
]

export function PredictionsList() {
  const [predictions, setPredictions] = useState<PredictionWithPundit[]>([])
  const [loading, setLoading] = useState(true)
  const [sort, setSort] = useState('default')
  const [category, setCategory] = useState('All')
  const [horizon, setHorizon] = useState('All')
  const [showRegions, setShowRegions] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [filtersOpen, setFiltersOpen] = useState(false)

  useEffect(() => {
    loadPredictions()
  }, [sort, category, horizon])

  const loadPredictions = async () => {
    setLoading(true)
    try {
      const categoryParam = category !== 'All' ? `&category=${category.toLowerCase()}` : ''
      const horizonParam = horizon !== 'All' ? `&horizon=${horizon}` : ''
      const res = await fetch(`${API_URL}/api/predictions/recent?limit=300&sort=${sort}${categoryParam}${horizonParam}`, {
        cache: 'no-store'
      })
      if (res.ok) {
        const data = await res.json()
        setPredictions(data)
      }
    } catch (err) {
      console.error('Failed to load predictions:', err)
    }
    setLoading(false)
  }

  const currentSort = SORT_OPTIONS.find(o => o.value === sort) || SORT_OPTIONS[0]
  const currentHorizon = HORIZON_OPTIONS.find(o => o.value === horizon) || HORIZON_OPTIONS[0]

  // Filter predictions by search query (client-side)
  const filteredPredictions = searchQuery.trim() 
    ? predictions.filter(p => 
        p.claim.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.pundit.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.pundit.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.quote && p.quote.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : predictions

  // Check if any filters are active
  const hasActiveFilters = category !== 'All' || horizon !== 'All' || sort !== 'default'

  return (
    <div>
      {/* Compact Filter Bar */}
      <div className="mb-6 flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-neutral-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search predictions or pundits..."
            className="w-full pl-10 pr-10 py-2.5 border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 text-black dark:text-white placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
        
        {/* Filter Toggle Button */}
        <button
          onClick={() => setFiltersOpen(!filtersOpen)}
          className={`flex items-center justify-center gap-2 px-4 py-2.5 font-bold text-sm transition-colors ${
            hasActiveFilters 
              ? 'bg-black dark:bg-white text-white dark:text-black' 
              : 'bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-800'
          }`}
        >
          <Filter className="h-4 w-4" />
          <span>Filters</span>
          {hasActiveFilters && (
            <span className="bg-white dark:bg-black text-black dark:text-white text-xs px-1.5 py-0.5 rounded-full">
              {(category !== 'All' ? 1 : 0) + (horizon !== 'All' ? 1 : 0) + (sort !== 'default' ? 1 : 0)}
            </span>
          )}
          {filtersOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>

      {/* Active Filters Display (always visible when filters are active) */}
      {hasActiveFilters && !filtersOpen && (
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <span className="text-xs text-neutral-500">Active:</span>
          {category !== 'All' && (
            <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-1 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded">
              {category}
              <button onClick={() => setCategory('All')} className="hover:text-red-500">
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
          {horizon !== 'All' && (
            <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-1 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded">
              {currentHorizon.label}
              <button onClick={() => setHorizon('All')} className="hover:text-red-500">
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
          {sort !== 'default' && (
            <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-1 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded">
              {currentSort.label}
              <button onClick={() => setSort('default')} className="hover:text-red-500">
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
          <button 
            onClick={() => { setCategory('All'); setHorizon('All'); setSort('default'); }}
            className="text-xs text-neutral-500 hover:text-red-500 underline"
          >
            Clear all
          </button>
        </div>
      )}

      {/* Collapsible Filter Panel */}
      {filtersOpen && (
        <div className="mb-6 p-4 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg space-y-4">
          {/* Category Filters */}
          <div>
            <div className="flex items-center gap-3 mb-3">
              <span className="text-sm font-bold text-neutral-600 dark:text-neutral-400">
                Category:
              </span>
              <button
                onClick={() => setShowRegions(!showRegions)}
                className={`text-xs font-medium px-2 py-1 rounded transition-colors ${
                  showRegions ? 'bg-black dark:bg-white text-white dark:text-black' : 'bg-white dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700'
                }`}
              >
                {showRegions ? '← Topics' : 'Regions →'}
              </button>
            </div>
            
            <div className="flex gap-2 flex-wrap">
              {(showRegions ? ['All', ...REGION_CATEGORIES] : TOPIC_CATEGORIES).map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategory(cat)}
                  className={`text-sm font-bold px-3 py-1.5 transition-colors ${
                    cat === category
                      ? 'bg-black dark:bg-white text-white dark:text-black shadow-sm'
                      : 'bg-white dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 border border-neutral-200 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-700'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Horizon Filter */}
          <div>
            <span className="text-sm font-bold text-neutral-600 dark:text-neutral-400 block mb-3">
              Time Horizon:
            </span>
            <div className="flex gap-2 flex-wrap">
              {HORIZON_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setHorizon(opt.value)}
                  title={opt.description}
                  className={`text-sm font-bold px-3 py-1.5 transition-colors ${
                    opt.value === horizon
                      ? opt.value === 'ST' ? 'bg-blue-500 text-white shadow-sm'
                      : opt.value === 'MT' ? 'bg-purple-500 text-white shadow-sm'
                      : opt.value === 'LT' ? 'bg-orange-500 text-white shadow-sm'
                      : opt.value === 'V' ? 'bg-amber-400 text-black shadow-sm'
                      : 'bg-black dark:bg-white text-white dark:text-black shadow-sm'
                      : 'bg-white dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 border border-neutral-200 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-700'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Sort Controls */}
          <div>
            <span className="text-sm font-bold text-neutral-600 dark:text-neutral-400 block mb-3">
              Sort by:
            </span>
            <div className="flex flex-wrap gap-2">
              {SORT_OPTIONS.map(option => {
                const Icon = option.icon
                return (
                  <button
                    key={option.value}
                    onClick={() => setSort(option.value)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium transition-all ${
                      sort === option.value
                        ? 'bg-black dark:bg-white text-white dark:text-black'
                        : 'bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-700'
                    }`}
                    title={option.description}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {option.label}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Search Results Count */}
      {searchQuery && (
        <p className="text-sm text-neutral-500 mb-4">
          Found {filteredPredictions.length} result{filteredPredictions.length !== 1 ? 's' : ''} for "{searchQuery}"
        </p>
      )}

      {/* Predictions Grid */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin h-10 w-10 border-4 border-black dark:border-white border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPredictions.length > 0 ? (
            filteredPredictions.map((pred) => (
              <PredictionCardWithVotes key={pred.id} prediction={pred} />
            ))
          ) : (
            <div className="col-span-full bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-12 sm:p-20 text-center">
              <Clock className="h-12 w-12 text-neutral-300 dark:text-neutral-600 mx-auto mb-4" />
              <p className="text-neutral-400 font-bold text-xl">No predictions found.</p>
              <p className="text-neutral-400 mt-2">{searchQuery ? 'Try a different search term.' : 'Check back later as our AI processes more content.'}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
