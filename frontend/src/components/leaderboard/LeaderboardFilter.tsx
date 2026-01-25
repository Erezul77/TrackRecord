// src/components/leaderboard/LeaderboardFilter.tsx
'use client'
import { useState } from 'react'
import { Pundit } from '@/lib/api'
import { PunditCard } from './PunditCard'
import { cn } from '@/lib/utils'

interface LeaderboardFilterProps {
  pundits: Pundit[]
}

// Topics
const TOPICS = ['All', 'Politics', 'Economy', 'Crypto', 'Markets', 'Tech', 'Macro', 'Sports', 'Entertainment', 'Religion', 'Science', 'Health', 'Climate', 'Geopolitics', 'Business', 'Media']

// Geographic Regions
const REGIONS = ['Global', 'Americas', 'Europe', 'Asia-Pacific', 'Middle-East', 'Africa', 'US', 'UK', 'EU', 'China', 'Japan', 'India', 'Russia', 'Brazil', 'Israel', 'Balkans', 'LATAM', 'MENA', 'Southeast-Asia', 'Central-Asia', 'Oceania', 'Scandinavia']

const CATEGORIES = [...TOPICS, ...REGIONS.filter(r => r !== 'Global')]

export function LeaderboardFilter({ pundits }: LeaderboardFilterProps) {
  const [activeCategory, setActiveCategory] = useState('All')
  
  const filteredPundits = activeCategory === 'All' 
    ? pundits 
    : pundits.filter(p => p.domains?.some(d => d.toLowerCase() === activeCategory.toLowerCase()))

  // Get unique categories from pundits
  const availableCategories = ['All', ...new Set(pundits.flatMap(p => p.domains || []).map(d => d.charAt(0).toUpperCase() + d.slice(1)))]
  
  return (
    <>
      <div className="flex gap-2 flex-wrap">
        {availableCategories.map((cat: string) => (
          <button 
            key={cat} 
            onClick={() => setActiveCategory(cat)}
            className={cn(
              "text-sm font-medium px-4 py-2 transition-colors",
              cat === activeCategory 
                ? "bg-black dark:bg-white text-white dark:text-black" 
                : "bg-white dark:bg-neutral-900 text-neutral-600 dark:text-neutral-400 border border-neutral-200 dark:border-neutral-800 hover:border-black dark:hover:border-white hover:text-black dark:hover:text-white"
            )}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="space-y-3 mt-8">
        {filteredPundits.length > 0 ? (
          filteredPundits.map((pundit: Pundit, index: number) => (
            <PunditCard key={pundit.id} pundit={pundit} rank={index + 1} />
          ))
        ) : (
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-12 text-center">
            <p className="text-neutral-500 font-medium">No pundits found in this category.</p>
          </div>
        )}
      </div>
    </>
  )
}
