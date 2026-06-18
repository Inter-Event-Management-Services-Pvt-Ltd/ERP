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

  // Use the same URL priority as server.ts / middleware.ts so the PKCE
  // code-verifier cookie key is consistent between sign-in and callback.
  // The cookie key is derived from the Supabase URL passed to createServerClient;
  // if sign-in and callback use different URLs the verifier lookup fails.
  const supabaseUrl = process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL!
  // Browser-accessible URL (baked into the image at build time via NEXT_PUBLIC_).
  // In production supabaseUrl === publicUrl (rewrite is a no-op).
  // In local Docker, SUPABASE_URL is the container-internal address; the rewrite
  // below replaces it in data.url so the browser can follow the OAuth redirect.
  const publicUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? supabaseUrl

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

  // Replace the internal Supabase address with the browser-accessible one.
  // signInWithOAuth constructs data.url using supabaseUrl; if that is a
  // Docker-internal address the browser can't reach, swap the base URL prefix.
  const oauthUrl =
    supabaseUrl !== publicUrl && data.url.startsWith(supabaseUrl)
      ? publicUrl + data.url.slice(supabaseUrl.length)
      : data.url

  return NextResponse.redirect(oauthUrl)
}
