'use client'
import { useState, useEffect, useRef } from 'react'
import { Globe } from 'lucide-react'
import { Language, LANGUAGES, getStoredLanguage, setStoredLanguage } from '@/lib/i18n'

interface LanguageSelectorProps {
  onChange?: (lang: Language) => void
}

export function LanguageSelector({ onChange }: LanguageSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [currentLang, setCurrentLang] = useState<Language>('en')
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setCurrentLang(getStoredLanguage())
  }, [])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (lang: Language) => {
    setCurrentLang(lang)
    setStoredLanguage(lang)
    setIsOpen(false)
    onChange?.(lang)
    // Reload page to apply translations (simple approach)
    // For a more sophisticated SPA approach, use React Context
    window.location.reload()
  }

  const currentLanguage = LANGUAGES.find(l => l.code === currentLang)

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
        title="Select Language"
      >
        <Globe className="w-4 h-4" />
        <span className="hidden sm:inline">{currentLanguage?.flag} {currentLanguage?.code.toUpperCase()}</span>
        <span className="sm:hidden">{currentLanguage?.flag}</span>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-50 max-h-96 overflow-y-auto">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleSelect(lang.code)}
              className={`w-full px-4 py-2 text-left text-sm hover:bg-slate-100 flex items-center gap-3 ${
                currentLang === lang.code ? 'bg-blue-50 text-blue-600' : 'text-slate-700'
              }`}
            >
              <span className="text-lg">{lang.flag}</span>
              <span>{lang.name}</span>
              {currentLang === lang.code && (
                <span className="ml-auto text-blue-600">✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
