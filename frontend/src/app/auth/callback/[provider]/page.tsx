// src/app/auth/callback/[provider]/page.tsx
'use client'
import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useRouter } from 'next/navigation'
import { Loader2, CheckCircle, XCircle } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function OAuthCallbackPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const router = useRouter()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    const handleCallback = async () => {
      const provider = params.provider as string
      const code = searchParams.get('code')
      const state = searchParams.get('state')
      const error = searchParams.get('error')

      if (error) {
        setStatus('error')
        setMessage(`Authentication cancelled or failed: ${error}`)
        return
      }

      if (!code) {
        setStatus('error')
        setMessage('No authorization code received')
        return
      }

      // Verify state matches
      const savedState = localStorage.getItem('oauth_state')
      if (state && savedState && state !== savedState) {
        setStatus('error')
        setMessage('Security validation failed. Please try again.')
        return
      }

      try {
        // Exchange code for user data
        const res = await fetch(`${API_URL}/api/auth/${provider}/callback?code=${encodeURIComponent(code)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })

        const data = await res.json()

        if (res.ok && data.user_id) {
          // Store user in localStorage
          localStorage.setItem('community_user', JSON.stringify(data))
          localStorage.removeItem('oauth_state')
          
          // Notify other components
          window.dispatchEvent(new Event('auth-change'))
          
          setStatus('success')
          setMessage(`Welcome, ${data.display_name}!`)
          
          // Redirect to compete page after short delay
          setTimeout(() => {
            router.push('/compete')
          }, 1500)
        } else {
          setStatus('error')
          setMessage(data.detail || 'Authentication failed')
        }
      } catch (err) {
        setStatus('error')
        setMessage('Network error. Please try again.')
      }
    }

    handleCallback()
  }, [params.provider, searchParams, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-950">
      <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 p-8 max-w-md w-full mx-4 text-center">
        {status === 'loading' && (
          <>
            <Loader2 className="h-12 w-12 text-neutral-400 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-bold text-black dark:text-white mb-2">Signing you in...</h2>
            <p className="text-neutral-500">Please wait while we complete authentication</p>
          </>
        )}
        
        {status === 'success' && (
          <>
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-black dark:text-white mb-2">Success!</h2>
            <p className="text-neutral-500">{message}</p>
            <p className="text-sm text-neutral-400 mt-4">Redirecting...</p>
          </>
        )}
        
        {status === 'error' && (
          <>
            <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-black dark:text-white mb-2">Authentication Failed</h2>
            <p className="text-neutral-500 mb-6">{message}</p>
            <button
              onClick={() => router.push('/compete')}
              className="bg-black dark:bg-white text-white dark:text-black px-6 py-2 font-bold hover:bg-neutral-800 dark:hover:bg-neutral-200 transition-colors"
            >
              Try Again
            </button>
          </>
        )}
      </div>
    </div>
  )
}
