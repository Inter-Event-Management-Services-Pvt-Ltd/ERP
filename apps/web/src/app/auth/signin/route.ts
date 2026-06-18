import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { NextResponse, type NextRequest } from 'next/server'

export async function GET(request: NextRequest) {
  const cookieStore = await cookies()

  // Derive the public-facing origin from Caddy's forwarded headers so the
  // OAuth redirect_uri resolves to the real domain, not the container address.
  const proto =
    request.headers.get('x-forwarded-proto') ??
    new URL(request.url).protocol.replace(':', '')
  const host =
    request.headers.get('x-forwarded-host') ??
    request.headers.get('host') ??
    new URL(request.url).host
  const origin = `${proto}://${host}`

  // SUPABASE_URL is a runtime env var for server-side use inside Docker
  // (e.g. http://host.docker.internal:54321 locally, or the managed HTTPS URL
  // in production). Falls back to the build-time public var when not set.
  const supabaseUrl =
    process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL!

  const supabase = createServerClient(
    supabaseUrl,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(
          cookiesToSet: Array<{ name: string; value: string; options?: Record<string, unknown> }>
        ) {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(
              name,
              value,
              options as Parameters<typeof cookieStore.set>[2]
            )
          )
        },
      },
    }
  )

  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${origin}/auth/callback`,
      skipBrowserRedirect: true,
    },
  })

  if (error || !data.url) {
    return NextResponse.redirect(`${origin}/login`)
  }

  return NextResponse.redirect(data.url)
}
