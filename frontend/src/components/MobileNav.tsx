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
        className="p-2 text-slate-600 hover:text-blue-600"
      >
        {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </button>
      
      {isOpen && (
        <div className="absolute top-16 left-0 right-0 bg-white border-b shadow-lg z-50">
          <nav className="container mx-auto px-4 py-4 flex flex-col gap-4">
            <Link 
              href="/" 
              onClick={() => setIsOpen(false)}
              className="text-sm font-bold text-slate-600 hover:text-blue-600 py-2"
            >
              Leaderboard
            </Link>
            <Link 
              href="/predictions" 
              onClick={() => setIsOpen(false)}
              className="text-sm font-bold text-slate-600 hover:text-blue-600 py-2"
            >
              Predictions
            </Link>
            <Link 
              href="/compete" 
              onClick={() => setIsOpen(false)}
              className="text-sm font-bold text-yellow-600 hover:text-yellow-700 py-2"
            >
              🏆 Compete
            </Link>
            <Link 
              href="/submit" 
              onClick={() => setIsOpen(false)}
              className="text-sm font-bold text-emerald-600 hover:text-emerald-700 py-2"
            >
              + Submit Prediction
            </Link>
            <Link 
              href="/admin" 
              onClick={() => setIsOpen(false)}
              className="text-sm font-bold text-slate-600 hover:text-blue-600 py-2"
            >
              Admin
            </Link>
          </nav>
        </div>
      )}
    </div>
  )
}
