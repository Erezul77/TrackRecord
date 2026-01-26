// src/components/AuthButton.tsx
'use client'
import { useState, useEffect } from 'react'
import { User, LogOut, LogIn } from 'lucide-react'
import Link from 'next/link'

export function AuthButton() {
  const [user, setUser] = useState<{ user_id: string; display_name: string } | null>(null)
  const [showDropdown, setShowDropdown] = useState(false)

  // Function to load user from localStorage
  const loadUser = () => {
    const stored = localStorage.getItem('community_user')
    if (stored) {
      try {
        setUser(JSON.parse(stored))
      } catch {
        localStorage.removeItem('community_user')
        setUser(null)
      }
    } else {
      setUser(null)
    }
  }

  useEffect(() => {
    // Initial load
    loadUser()

    // Listen for storage changes (from other tabs)
    const handleStorage = (e: StorageEvent) => {
      if (e.key === 'community_user') {
        loadUser()
      }
    }

    // Listen for custom auth event (from same tab)
    const handleAuthChange = () => {
      loadUser()
    }

    window.addEventListener('storage', handleStorage)
    window.addEventListener('auth-change', handleAuthChange)

    return () => {
      window.removeEventListener('storage', handleStorage)
      window.removeEventListener('auth-change', handleAuthChange)
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('community_user')
    // Notify other components about auth change
    window.dispatchEvent(new Event('auth-change'))
    setUser(null)
    setShowDropdown(false)
  }

  if (user) {
    return (
      <div className="relative">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="flex items-center gap-2 bg-black dark:bg-white text-white dark:text-black px-3 py-1.5 text-sm font-medium hover:bg-neutral-800 dark:hover:bg-neutral-200 transition-colors"
        >
          <User className="h-4 w-4" />
          <span className="hidden sm:inline">{user.display_name}</span>
        </button>
        
        {showDropdown && (
          <div className="absolute right-0 top-full mt-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 shadow-lg py-1 min-w-[150px] z-50">
            <Link
              href="/compete"
              className="block px-4 py-2 text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              onClick={() => setShowDropdown(false)}
            >
              My Predictions
            </Link>
            <button
              onClick={handleLogout}
              className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
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
      className="flex items-center gap-2 bg-black dark:bg-white text-white dark:text-black px-3 py-1.5 text-sm font-medium hover:bg-neutral-800 dark:hover:bg-neutral-200 transition-colors"
    >
      <LogIn className="h-4 w-4" />
      <span className="hidden sm:inline">Sign In</span>
    </Link>
  )
}
