// src/components/AuthButton.tsx
'use client'
import { useState, useEffect } from 'react'
import { User, LogOut, LogIn } from 'lucide-react'
import Link from 'next/link'

export function AuthButton() {
  const [user, setUser] = useState<{ user_id: string; display_name: string } | null>(null)
  const [showDropdown, setShowDropdown] = useState(false)

  useEffect(() => {
    // Check localStorage for user
    const stored = localStorage.getItem('community_user')
    if (stored) {
      try {
        setUser(JSON.parse(stored))
      } catch {
        localStorage.removeItem('community_user')
      }
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('community_user')
    setUser(null)
    setShowDropdown(false)
    window.location.reload()
  }

  if (user) {
    return (
      <div className="relative">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="flex items-center gap-2 bg-black text-white px-3 py-1.5 text-sm font-medium hover:bg-neutral-800 transition-colors"
        >
          <User className="h-4 w-4" />
          <span className="hidden sm:inline">{user.display_name}</span>
        </button>
        
        {showDropdown && (
          <div className="absolute right-0 top-full mt-2 bg-white border border-neutral-200 shadow-lg py-1 min-w-[150px] z-50">
            <Link
              href="/compete"
              className="block px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100"
              onClick={() => setShowDropdown(false)}
            >
              My Predictions
            </Link>
            <button
              onClick={handleLogout}
              className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <Link
      href="/compete"
      className="flex items-center gap-2 bg-black text-white px-3 py-1.5 text-sm font-medium hover:bg-neutral-800 transition-colors"
    >
      <LogIn className="h-4 w-4" />
      <span className="hidden sm:inline">Sign In</span>
    </Link>
  )
}
