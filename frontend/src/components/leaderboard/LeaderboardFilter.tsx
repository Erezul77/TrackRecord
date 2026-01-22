// src/components/leaderboard/LeaderboardFilter.tsx
'use client'
import { useState } from 'react'
import { Pundit } from '@/lib/api'
import { PunditCard } from './PunditCard'
import { cn } from '@/lib/utils'

interface LeaderboardFilterProps {
  pundits: Pundit[]
}

const CATEGORIES = ['All', 'Politics', 'Economy', 'Crypto', 'Markets', 'Tech', 'Macro']

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
              "text-sm font-bold px-4 py-2 rounded-lg transition-colors",
              cat === activeCategory 
                ? "bg-blue-600 text-white shadow-sm" 
                : "bg-white text-slate-600 border hover:bg-slate-50"
            )}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="space-y-4 mt-8">
        {filteredPundits.length > 0 ? (
          filteredPundits.map((pundit: Pundit, index: number) => (
            <PunditCard key={pundit.id} pundit={pundit} rank={index + 1} />
          ))
        ) : (
          <div className="bg-white border rounded-xl p-12 text-center">
            <p className="text-slate-500 font-medium">No pundits found in this category.</p>
          </div>
        )}
      </div>
    </>
  )
}
