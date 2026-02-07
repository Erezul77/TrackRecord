// src/app/verify-email/page.tsx
'use client'
import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function VerifyEmailContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get('token')
  
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setMessage('No verification token provided.')
      return
    }

    const verifyEmail = async () => {
      try {
        const res = await fetch(`${API_URL}/api/community/verify-email?token=${encodeURIComponent(token)}`, {
          method: 'POST'
        })
        const data = await res.json()
        
        if (res.ok) {
          setStatus('success')
          setMessage(data.message || 'Email verified successfully!')
          // Redirect to compete page after 2 seconds
          setTimeout(() => {
            router.push('/compete')
          }, 2000)
        } else {
          setStatus('error')
          setMessage(data.detail || 'Verification failed. Please try again.')
        }
      } catch (err) {
        setStatus('error')
        setMessage('Network error. Please try again later.')
      }
    }

    verifyEmail()
  }, [token, router])

  return (
    <div className="container mx-auto px-4 py-20">
      <div className="max-w-md mx-auto text-center">
        {status === 'loading' && (
          <>
            <Loader2 className="h-16 w-16 text-neutral-400 mx-auto mb-6 animate-spin" />
            <h1 className="text-2xl font-black text-black dark:text-white mb-2">Verifying your email...</h1>
            <p className="text-neutral-500">Please wait while we verify your email address.</p>
          </>
        )}

        {status === 'success' && (
          <>
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-6" />
            <h1 className="text-2xl font-black text-black dark:text-white mb-2">Email Verified!</h1>
            <p className="text-neutral-500 mb-6">{message}</p>
            <p className="text-sm text-neutral-400">Redirecting you to login...</p>
            <Link 
              href="/compete"
              className="inline-block mt-4 bg-black dark:bg-white text-white dark:text-black font-bold px-6 py-3 hover:bg-neutral-800 dark:hover:bg-neutral-200 transition-colors"
            >
              Go to Login
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <XCircle className="h-16 w-16 text-red-500 mx-auto mb-6" />
            <h1 className="text-2xl font-black text-black dark:text-white mb-2">Verification Failed</h1>
            <p className="text-neutral-500 mb-6">{message}</p>
            <div className="space-y-3">
              <Link 
                href="/compete"
                className="inline-block bg-black dark:bg-white text-white dark:text-black font-bold px-6 py-3 hover:bg-neutral-800 dark:hover:bg-neutral-200 transition-colors"
              >
                Try Again
              </Link>
              <p className="text-sm text-neutral-400">
                If the link expired, you can request a new verification email from the login page.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="container mx-auto px-4 py-20">
        <div className="max-w-md mx-auto text-center">
          <Loader2 className="h-16 w-16 text-neutral-400 mx-auto mb-6 animate-spin" />
          <h1 className="text-2xl font-black text-black dark:text-white mb-2">Loading...</h1>
        </div>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  )
}
