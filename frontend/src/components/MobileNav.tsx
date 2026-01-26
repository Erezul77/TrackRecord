// src/components/MobileNav.tsx
'use client'
import { useState } from 'react'
import Link from 'next/link'
import { Menu, X } from 'lucide-react'

export function MobileNav() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="md:hidden">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white transition-colors"
      >
        {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </button>
      
      {isOpen && (
        <div className="absolute top-16 left-0 right-0 bg-white dark:bg-black border-b border-neutral-200 dark:border-neutral-800 shadow-lg z-50">
          <nav className="container mx-auto px-4 py-4 flex flex-col gap-2">
            <Link 
              href="/" 
              onClick={() => setIsOpen(false)}
              className="text-sm font-semibold text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white py-3 border-b border-neutral-100 dark:border-neutral-800"
            >
              Leaderboard
            </Link>
            <Link 
              href="/predictions" 
              onClick={() => setIsOpen(false)}
              className="text-sm font-semibold text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white py-3 border-b border-neutral-100 dark:border-neutral-800"
            >
              Predictions
            </Link>
            <Link 
              href="/compete" 
              onClick={() => setIsOpen(false)}
              className="text-sm font-semibold text-amber-600 hover:text-amber-700 py-3 border-b border-neutral-100 dark:border-neutral-800"
            >
              Compete
            </Link>
            <Link 
              href="/submit" 
              onClick={() => setIsOpen(false)}
              className="text-sm font-semibold text-blue-600 hover:text-blue-700 py-3 border-b border-neutral-100 dark:border-neutral-800"
            >
              + Submit Prediction
            </Link>
            <Link 
              href="/apply" 
              onClick={() => setIsOpen(false)}
              className="text-sm font-semibold text-green-600 hover:text-green-700 py-3 border-b border-neutral-100 dark:border-neutral-800"
            >
              Apply to be Tracked
            </Link>
            <Link 
              href="/resolve" 
              onClick={() => setIsOpen(false)}
              className="text-sm font-semibold text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white py-3 border-b border-neutral-100 dark:border-neutral-800"
            >
              Resolution Center
            </Link>
            <Link 
              href="/admin" 
              onClick={() => setIsOpen(false)}
              className="text-sm font-semibold text-neutral-400 hover:text-black dark:hover:text-white py-3"
            >
              Admin
            </Link>
          </nav>
        </div>
      )}
    </div>
  )
}
