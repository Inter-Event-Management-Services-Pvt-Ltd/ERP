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

  // Container-internal URL used for server-side Supabase API calls. Must match
  // server.ts so the PKCE code-verifier cookie key is the same at sign-in and
  // callback — @supabase/ssr derives the cookie name from the URL host.
  const serverUrl = process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL!
  // Browser-accessible URL. Injected at runtime via compose.yaml (not baked at
  // build time) so process.env reads the correct value inside the container.
  // In production these are identical; in local Docker they differ so the rewrite
  // below replaces the container-internal host before the redirect is sent.
  const browserUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? serverUrl

  const supabase = createServerClient(
    serverUrl,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookieOptions: { name: 'sb-iems' },
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

  // signInWithOAuth builds data.url from serverUrl. If that is a container-internal
  // address the browser cannot reach, swap the origin so the redirect works.
  const oauthUrl =
    serverUrl !== browserUrl && data.url.startsWith(serverUrl)
      ? browserUrl + data.url.slice(serverUrl.length)
      : data.url

  return NextResponse.redirect(oauthUrl)
}
