'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

const IS_DEV = process.env.NODE_ENV === 'development'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleGoogleSignIn() {
    const supabase = createClient()
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    })
  }

  async function handleDevSignIn(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    const supabase = createClient()
    const { error: err } = await supabase.auth.signInWithPassword({ email, password })
    setLoading(false)
    if (err) {
      setError(err.message)
    } else {
      router.push('/dashboard')
    }
  }

  return (
    <div className="min-h-screen bg-surface-base flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="bg-surface-raised border border-surface-border rounded-xl overflow-hidden">
          <div className="gradient-strip" aria-hidden="true" />

          <div className="px-8 py-10">
            {/* Logo */}
            <div className="text-center mb-8">
              <p className="font-mono text-accent-saffron text-2xl font-semibold tracking-[0.3em]">
                IEMS
              </p>
              <p className="mt-1.5 font-serif italic text-text-primary/50 text-sm">
                Event Management ERP
              </p>
            </div>

            {/* Google Sign-In */}
            <button
              onClick={handleGoogleSignIn}
              className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-md border border-surface-border bg-surface-base text-text-primary text-sm font-sans hover:bg-surface-deep transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron focus-visible:ring-offset-2 focus-visible:ring-offset-surface-raised"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" focusable="false">
                <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4" />
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853" />
                <path d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05" />
                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335" />
              </svg>
              Sign in with Google
            </button>

            {/* Dev-only email/password form */}
            {IS_DEV && (
              <>
                <div className="my-5 flex items-center gap-3">
                  <div className="flex-1 h-px bg-surface-border" />
                  <span className="font-mono text-[10px] text-accent-warning tracking-widest uppercase">
                    Dev only
                  </span>
                  <div className="flex-1 h-px bg-surface-border" />
                </div>

                <form onSubmit={handleDevSignIn} className="space-y-3">
                  <div>
                    <label htmlFor="dev-email" className="sr-only">Email</label>
                    <input
                      id="dev-email"
                      type="email"
                      placeholder="Email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      className="w-full px-3 py-2.5 rounded-md bg-surface-base border border-surface-border text-text-primary text-sm font-sans placeholder:text-text-primary/30 focus-visible:ring-2 focus-visible:ring-accent-saffron outline-none"
                    />
                  </div>
                  <div>
                    <label htmlFor="dev-password" className="sr-only">Password</label>
                    <input
                      id="dev-password"
                      type="password"
                      placeholder="Password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="w-full px-3 py-2.5 rounded-md bg-surface-base border border-surface-border text-text-primary text-sm font-sans placeholder:text-text-primary/30 focus-visible:ring-2 focus-visible:ring-accent-saffron outline-none"
                    />
                  </div>

                  {error && (
                    <p role="alert" className="text-xs text-accent-critical font-sans">
                      {error}
                    </p>
                  )}

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full px-4 py-2.5 rounded-md bg-accent-madder text-text-primary text-sm font-sans hover:bg-accent-madder/80 transition-colors disabled:opacity-50"
                  >
                    {loading ? 'Signing in…' : 'Sign in'}
                  </button>
                </form>
              </>
            )}

            <p className="mt-6 text-center text-xs text-text-primary/25 font-sans leading-relaxed">
              Access restricted to authorised IEMS personnel
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
