// src/components/ThemeToggle.tsx
'use client'

import { useState, useEffect } from 'react'
import { Sun, Moon } from 'lucide-react'

export function ThemeToggle() {
  const [isDark, setIsDark] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Check localStorage - default to DARK mode
    const saved = localStorage.getItem('theme')
    
    if (saved === 'light') {
      // User explicitly chose light mode
      setIsDark(false)
      document.documentElement.classList.remove('dark')
    } else {
      // Default to dark mode
      setIsDark(true)
      document.documentElement.classList.add('dark')
      if (!saved) {
        localStorage.setItem('theme', 'dark')
      }
    }
  }, [])

  const toggleTheme = () => {
    const newIsDark = !isDark
    setIsDark(newIsDark)
    
    if (newIsDark) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }

  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <button className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800  transition-colors">
        <div className="h-5 w-5" />
      </button>
    )
  }

  return (
    <button
      onClick={toggleTheme}
      className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800  transition-colors"
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Light mode' : 'Dark mode'}
    >
      {isDark ? (
        <Sun className="h-5 w-5 text-yellow-400" />
      ) : (
        <Moon className="h-5 w-5 text-neutral-600" />
      )}
    </button>
  )
}
