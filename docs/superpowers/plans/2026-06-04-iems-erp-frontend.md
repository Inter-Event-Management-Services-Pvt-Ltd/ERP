# IEMS ERP Frontend — Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up the complete frontend shell — TypeScript, Tailwind, design tokens, app shell, all shared components, auth wiring, and route stubs — so the frontend is ready to wire up as soon as the backend API shell is available.

**Architecture:** Next.js App Router with TypeScript; Tailwind CSS v3 extended with IEMS design tokens; shadcn/ui as the accessible primitive layer; Supabase SSR for session management; @tanstack/react-query bootstrapped but no queries implemented; all 35 routes stubbed.

**Tech Stack:** Next.js 15 · TypeScript · Tailwind CSS v3 · shadcn/ui · @supabase/ssr · @tanstack/react-query · react-hook-form · zod · Vitest · React Testing Library · lucide-react

**Scope:** Shell only. No business workflows. No API calls. No backend logic. Route pages render `<SkeletonScreen />` or a placeholder. Stop here and confirm before Phase 2.

---

## File Structure

```
apps/web/
├── src/
│   ├── app/
│   │   ├── layout.tsx                          [create]
│   │   ├── page.tsx                            [create]
│   │   ├── login/page.tsx                      [create]
│   │   ├── auth/callback/route.ts              [create]
│   │   ├── dashboard/page.tsx                  [create — stub]
│   │   ├── attendance/page.tsx                 [create — stub]
│   │   ├── leave/page.tsx                      [create — stub]
│   │   ├── tasks/page.tsx                      [create — stub]
│   │   ├── calendar/page.tsx                   [create — stub]
│   │   ├── projects/page.tsx                   [create — stub]
│   │   ├── projects/[id]/page.tsx              [create — stub]
│   │   ├── projects/[id]/documents/page.tsx    [create — stub]
│   │   ├── documents/[id]/page.tsx             [create — stub]
│   │   ├── approvals/page.tsx                  [create — stub]
│   │   ├── approvals/[id]/page.tsx             [create — stub]
│   │   ├── notifications/page.tsx              [create — stub]
│   │   ├── archive/page.tsx                    [create — stub]
│   │   ├── archive/rooms/page.tsx              [create — stub]
│   │   ├── archive/rooms/[id]/page.tsx         [create — stub]
│   │   ├── archive/files/[id]/page.tsx         [create — stub]
│   │   ├── archive/files/[id]/checkout/page.tsx [create — stub]
│   │   ├── archive/files/[id]/return/page.tsx  [create — stub]
│   │   ├── archive/files/[id]/verify/page.tsx  [create — stub]
│   │   ├── admin/page.tsx                      [create — stub]
│   │   ├── admin/employees/page.tsx            [create — stub]
│   │   ├── admin/departments/page.tsx          [create — stub]
│   │   ├── admin/roles/page.tsx                [create — stub]
│   │   ├── admin/policies/page.tsx             [create — stub]
│   │   ├── admin/folder-templates/page.tsx     [create — stub]
│   │   ├── admin/archive-locations/page.tsx    [create — stub]
│   │   ├── admin/audit/page.tsx                [create — stub]
│   │   ├── director/page.tsx                   [create — stub]
│   │   ├── director/projects/page.tsx          [create — stub]
│   │   ├── director/attendance/page.tsx        [create — stub]
│   │   ├── director/tasks/page.tsx             [create — stub]
│   │   ├── director/calendar/page.tsx          [create — stub]
│   │   ├── director/approvals/page.tsx         [create — stub]
│   │   ├── director/archive/page.tsx           [create — stub]
│   │   └── director/audit/page.tsx             [create — stub]
│   ├── components/
│   │   ├── layout/
│   │   │   ├── app-shell.tsx
│   │   │   ├── sidebar.tsx
│   │   │   ├── top-bar.tsx
│   │   │   ├── page-header.tsx
│   │   │   ├── content-area.tsx
│   │   │   └── detail-drawer.tsx
│   │   ├── states/
│   │   │   ├── skeleton-screen.tsx
│   │   │   ├── empty-state.tsx
│   │   │   ├── error-state.tsx
│   │   │   ├── permission-denied.tsx
│   │   │   └── offline-banner.tsx
│   │   └── status/
│   │       ├── badge.tsx
│   │       ├── status-dot.tsx
│   │       ├── toast-provider.tsx
│   │       ├── confirm-dialog.tsx
│   │       └── loading-spinner.tsx
│   ├── lib/
│   │   ├── supabase/client.ts
│   │   ├── supabase/server.ts
│   │   └── utils.ts
│   ├── hooks/
│   │   ├── use-auth.ts
│   │   └── use-role.ts
│   ├── types/index.ts
│   ├── middleware.ts
│   └── styles/globals.css
├── tailwind.config.ts                          [create]
├── postcss.config.mjs                          [create]
├── tsconfig.json                               [create]
├── vitest.config.ts                            [create]
├── vitest.setup.ts                             [create]
├── components.json                             [create]
└── .env.local.example                          [create]
```

**Modified:**
- `apps/web/package.json`
- `apps/web/next.config.mjs`

---

## Task 1: Install dependencies

**Files:**
- Modify: `apps/web/package.json`

- [ ] **Step 1: Install runtime dependencies**

```bash
cd apps/web
npm install typescript @types/react @types/react-dom @types/node \
  tailwindcss@^3 autoprefixer postcss \
  clsx tailwind-merge class-variance-authority tailwindcss-animate \
  @supabase/supabase-js @supabase/ssr \
  @tanstack/react-query \
  react-hook-form @hookform/resolvers zod \
  lucide-react \
  date-fns \
  qrcode.react
```

- [ ] **Step 2: Install dev/test dependencies**

```bash
cd apps/web
npm install --save-dev \
  vitest @vitejs/plugin-react \
  @testing-library/react @testing-library/user-event @testing-library/jest-dom \
  jsdom
```

- [ ] **Step 3: Verify package.json has all deps**

```bash
cd apps/web && cat package.json
```

Expected: `dependencies` includes `tailwindcss`, `@supabase/supabase-js`, `@tanstack/react-query`. `devDependencies` includes `vitest`, `@testing-library/react`.

- [ ] **Step 4: Add test script to package.json**

In `apps/web/package.json`, add `"test": "vitest"` and `"test:run": "vitest run"` to the `scripts` block:

```json
{
  "name": "iems-erp-web",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "vitest",
    "test:run": "vitest run"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "typescript": "^5.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@types/node": "^20.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.3.0",
    "class-variance-authority": "^0.7.0",
    "tailwindcss-animate": "^1.0.7",
    "@supabase/supabase-js": "^2.45.0",
    "@supabase/ssr": "^0.5.0",
    "@tanstack/react-query": "^5.50.0",
    "react-hook-form": "^7.52.0",
    "@hookform/resolvers": "^3.9.0",
    "zod": "^3.23.0",
    "lucide-react": "^0.400.0",
    "date-fns": "^3.6.0",
    "qrcode.react": "^4.1.0"
  },
  "devDependencies": {
    "vitest": "^1.6.0",
    "@vitejs/plugin-react": "^4.3.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.0",
    "@testing-library/jest-dom": "^6.4.0",
    "jsdom": "^24.1.0"
  }
}
```

- [ ] **Step 5: Commit**

```bash
cd apps/web && git add package.json package-lock.json
git commit -m "chore: install frontend deps — TS, Tailwind, shadcn, Supabase, React Query, Vitest"
```

---

## Task 2: TypeScript + Tailwind + PostCSS config

**Files:**
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/tailwind.config.ts`
- Create: `apps/web/postcss.config.mjs`

- [ ] **Step 1: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 2: Create tailwind.config.ts**

```typescript
import type { Config } from 'tailwindcss'
import animate from 'tailwindcss-animate'

const config: Config = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          base: '#1c1611',
          raised: '#261d15',
          deep: '#15110c',
          border: '#352616',
        },
        'text-primary': '#f3e9cf',
        accent: {
          saffron: '#d4924a',
          madder: '#8b3a1f',
          warning: '#f3a86e',
          critical: '#fca5a5',
        },
      },
      fontFamily: {
        serif: ['var(--font-serif)', 'Georgia', 'serif'],
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      backgroundImage: {
        'gradient-strip':
          'linear-gradient(90deg, #8b3a1f 0%, #d4924a 55%, #f3e9cf 100%)',
      },
      transitionDuration: {
        '100': '100ms',
        '120': '120ms',
        '140': '140ms',
        '160': '160ms',
        '180': '180ms',
        '220': '220ms',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        shimmer: 'shimmer 2s linear infinite',
        'fade-in': 'fade-in 180ms ease-out',
        'slide-up': 'slide-up 160ms ease-out',
      },
    },
  },
  plugins: [animate],
}

export default config
```

- [ ] **Step 3: Create postcss.config.mjs**

```javascript
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}

export default config
```

- [ ] **Step 4: Commit**

```bash
cd apps/web
git add tsconfig.json tailwind.config.ts postcss.config.mjs
git commit -m "chore: add TypeScript, Tailwind v3, and PostCSS config with IEMS design tokens"
```

---

## Task 3: Vitest + React Testing Library setup

**Files:**
- Create: `apps/web/vitest.config.ts`
- Create: `apps/web/vitest.setup.ts`

- [ ] **Step 1: Create vitest.config.ts**

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    globals: true,
    css: false,
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
})
```

- [ ] **Step 2: Create vitest.setup.ts**

```typescript
import '@testing-library/jest-dom'
```

- [ ] **Step 3: Write a smoke test to verify the setup works**

Create `apps/web/src/__tests__/setup.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'

function Smoke() {
  return <p>test harness working</p>
}

test('test harness renders', () => {
  render(<Smoke />)
  expect(screen.getByText('test harness working')).toBeInTheDocument()
})
```

- [ ] **Step 4: Run the smoke test**

```bash
cd apps/web && npm run test:run src/__tests__/setup.test.tsx
```

Expected output: `1 passed`

- [ ] **Step 5: Commit**

```bash
cd apps/web
git add vitest.config.ts vitest.setup.ts src/__tests__/setup.test.tsx
git commit -m "chore: add Vitest + React Testing Library with smoke test"
```

---

## Task 4: shadcn/ui init

**Files:**
- Create: `apps/web/components.json`

- [ ] **Step 1: Initialise shadcn/ui**

```bash
cd apps/web && npx shadcn@latest init --defaults
```

When prompted:
- Style: `Default`
- Base color: `Neutral`
- CSS variables: `No` (we use direct Tailwind token classes)

- [ ] **Step 2: Verify components.json was created**

```bash
cd apps/web && cat components.json
```

Expected: a JSON file with `"rsc": true`, `"tsx": true`, and aliases pointing to `@/components`.

- [ ] **Step 3: Install the primitive shadcn components we'll use as building blocks**

```bash
cd apps/web && npx shadcn@latest add dialog popover tooltip toast select
```

- [ ] **Step 4: Commit**

```bash
cd apps/web
git add components.json src/components/ui/
git commit -m "chore: initialise shadcn/ui with Dialog, Popover, Tooltip, Toast, Select primitives"
```

---

## Task 5: Design tokens — globals.css + utility function

**Files:**
- Create: `apps/web/src/styles/globals.css`
- Create: `apps/web/src/lib/utils.ts`

- [ ] **Step 1: Create globals.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    color-scheme: dark;
  }

  * {
    @apply border-surface-border;
    box-sizing: border-box;
  }

  html,
  body {
    height: 100%;
  }

  body {
    @apply bg-surface-base text-text-primary font-sans antialiased;
  }

  /* Focus ring — saffron on ink */
  :focus-visible {
    @apply outline-none ring-2 ring-accent-saffron ring-offset-2 ring-offset-surface-base;
  }

  /* Scrollbar styling */
  ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  ::-webkit-scrollbar-track {
    background: #1c1611;
  }
  ::-webkit-scrollbar-thumb {
    background: #352616;
    border-radius: 3px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: #d4924a;
  }
}

@layer utilities {
  /* Gradient strip — 2px, full width, used once per shell */
  .gradient-strip {
    height: 2px;
    background: linear-gradient(90deg, #8b3a1f 0%, #d4924a 55%, #f3e9cf 100%);
  }

  /* Shimmer skeleton animation */
  .shimmer {
    background: linear-gradient(
      90deg,
      #261d15 25%,
      #352616 50%,
      #261d15 75%
    );
    background-size: 200% 100%;
    animation: shimmer 2s linear infinite;
  }
}

/* Honour reduced-motion — collapse all transitions and animations */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
  .shimmer {
    animation: none;
  }
}
```

- [ ] **Step 2: Create src/lib/utils.ts**

```typescript
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

- [ ] **Step 3: Write test for cn utility**

Create `apps/web/src/__tests__/lib/utils.test.ts`:

```typescript
import { cn } from '@/lib/utils'

test('cn merges class names', () => {
  expect(cn('px-4', 'py-2')).toBe('px-4 py-2')
})

test('cn resolves Tailwind conflicts — last value wins', () => {
  expect(cn('px-4', 'px-8')).toBe('px-8')
})

test('cn handles conditional classes', () => {
  expect(cn('base', false && 'skipped', 'included')).toBe('base included')
})
```

- [ ] **Step 4: Run the test**

```bash
cd apps/web && npm run test:run src/__tests__/lib/utils.test.ts
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
cd apps/web
git add src/styles/globals.css src/lib/utils.ts src/__tests__/lib/utils.test.ts
git commit -m "feat: add IEMS globals.css with design tokens and cn() utility"
```

---

## Task 6: Core type definitions

**Files:**
- Create: `apps/web/src/types/index.ts`

- [ ] **Step 1: Write test for role type completeness**

Create `apps/web/src/__tests__/types/roles.test.ts`:

```typescript
import type { UserRole } from '@/types'

// This test is a compile-time check. If any role is missing the type,
// TypeScript will fail the build.
test('all six roles are represented in the UserRole type', () => {
  const roles: UserRole[] = [
    'employee',
    'manager',
    'admin',
    'super_admin',
    'super_user',
    'director',
  ]
  expect(roles).toHaveLength(6)
})
```

- [ ] **Step 2: Run — expect FAIL (type not defined yet)**

```bash
cd apps/web && npm run test:run src/__tests__/types/roles.test.ts
```

Expected: compile error — `Cannot find module '@/types'`

- [ ] **Step 3: Create src/types/index.ts**

```typescript
export type UserRole =
  | 'employee'
  | 'manager'
  | 'admin'
  | 'super_admin'
  | 'super_user'
  | 'director'

export interface AuthUser {
  id: string
  email: string
  name: string
  avatar_url: string | null
  role: UserRole
  department_id: string | null
}

export interface NavItem {
  label: string
  href: string
  icon: React.ElementType
  badge?: number
  roles?: UserRole[]
}

export type BadgeVariant =
  | 'active'
  | 'pending'
  | 'overdue'
  | 'approved'
  | 'rejected'
  | 'archived'
  | 'info'
  | 'warning'
  | 'critical'

export type Severity = 'critical' | 'high' | 'normal' | 'info'
```

- [ ] **Step 4: Run test — expect PASS**

```bash
cd apps/web && npm run test:run src/__tests__/types/roles.test.ts
```

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
cd apps/web
git add src/types/index.ts src/__tests__/types/roles.test.ts
git commit -m "feat: add core TypeScript types — UserRole, AuthUser, NavItem, BadgeVariant"
```

---

## Task 7: Supabase client setup + .env example

**Files:**
- Create: `apps/web/src/lib/supabase/client.ts`
- Create: `apps/web/src/lib/supabase/server.ts`
- Create: `apps/web/.env.local.example`

- [ ] **Step 1: Create src/lib/supabase/client.ts**

```typescript
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

- [ ] **Step 2: Create src/lib/supabase/server.ts**

```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createClient() {
  const cookieStore = await cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // Called from a Server Component — mutations ignored
          }
        },
      },
    }
  )
}
```

- [ ] **Step 3: Create .env.local.example**

```bash
# Copy this file to .env.local and fill in your values.
# Never commit .env.local.

NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Backend FastAPI URL (used by server-side fetches)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 4: Commit**

```bash
cd apps/web
git add src/lib/supabase/ .env.local.example
git commit -m "feat: add Supabase SSR client helpers and .env.local.example"
```

---

## Task 8: Route middleware (session refresh + redirect)

**Files:**
- Create: `apps/web/src/middleware.ts`

- [ ] **Step 1: Create src/middleware.ts**

```typescript
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

const PUBLIC_ROUTES = ['/login', '/auth/callback']

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          )
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const {
    data: { user },
  } = await supabase.auth.getUser()

  const { pathname } = request.nextUrl
  const isPublic = PUBLIC_ROUTES.some((r) => pathname.startsWith(r))

  if (!user && !isPublic) {
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }

  if (user && pathname === '/login') {
    const url = request.nextUrl.clone()
    url.pathname = '/dashboard'
    return NextResponse.redirect(url)
  }

  return supabaseResponse
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
```

- [ ] **Step 2: Commit**

```bash
cd apps/web
git add src/middleware.ts
git commit -m "feat: add Next.js middleware — Supabase session refresh and unauthenticated redirect to /login"
```

---

## Task 9: Root layout + font loading

**Files:**
- Create: `apps/web/src/app/layout.tsx`
- Modify: `apps/web/next.config.mjs`

- [ ] **Step 1: Update next.config.mjs — add CSP headers**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ]
  },
}

export default nextConfig
```

- [ ] **Step 2: Create src/app/layout.tsx**

```typescript
import type { Metadata } from 'next'
import { Instrument_Serif, Geist, JetBrains_Mono } from 'next/font/google'
import '@/styles/globals.css'

const instrumentSerif = Instrument_Serif({
  weight: ['400'],
  style: ['italic'],
  subsets: ['latin'],
  variable: '--font-serif',
  display: 'swap',
})

const geist = Geist({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'IEMS ERP',
  description: 'Internal ERP for IEMS event management',
  robots: { index: false, follow: false },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="en"
      className={`${instrumentSerif.variable} ${geist.variable} ${jetbrainsMono.variable}`}
    >
      <body>{children}</body>
    </html>
  )
}
```

- [ ] **Step 3: Create src/app/page.tsx (root redirect)**

```typescript
import { redirect } from 'next/navigation'

export default function RootPage() {
  redirect('/dashboard')
}
```

- [ ] **Step 4: Commit**

```bash
cd apps/web
git add src/app/layout.tsx src/app/page.tsx next.config.mjs
git commit -m "feat: add root layout with IEMS fonts (Instrument Serif, Geist, JetBrains Mono) and security headers"
```

---

## Task 10: use-auth + use-role hooks

**Files:**
- Create: `apps/web/src/hooks/use-auth.ts`
- Create: `apps/web/src/hooks/use-role.ts`

- [ ] **Step 1: Write tests**

Create `apps/web/src/__tests__/hooks/use-role.test.ts`:

```typescript
import { canAccess } from '@/hooks/use-role'
import type { UserRole } from '@/types'

test('director can access director routes', () => {
  expect(canAccess('director', ['director'])).toBe(true)
})

test('employee cannot access admin routes', () => {
  expect(canAccess('employee', ['admin', 'super_admin', 'super_user'])).toBe(false)
})

test('admin can access admin routes', () => {
  expect(canAccess('admin', ['admin', 'super_admin', 'super_user'])).toBe(true)
})

test('empty allowed list grants access to all roles', () => {
  expect(canAccess('employee', [])).toBe(true)
})
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd apps/web && npm run test:run src/__tests__/hooks/use-role.test.ts
```

Expected: error — module not found

- [ ] **Step 3: Create src/hooks/use-role.ts**

```typescript
import type { UserRole } from '@/types'

export function canAccess(role: UserRole, allowedRoles: UserRole[]): boolean {
  if (allowedRoles.length === 0) return true
  return allowedRoles.includes(role)
}

export function useRole(role: UserRole | undefined) {
  return {
    isEmployee: role === 'employee',
    isManager: role === 'manager',
    isAdmin: role === 'admin' || role === 'super_admin' || role === 'super_user',
    isSuperUser: role === 'super_user',
    isDirector: role === 'director',
    canAccess: (allowedRoles: UserRole[]) =>
      role ? canAccess(role, allowedRoles) : false,
  }
}
```

- [ ] **Step 4: Create src/hooks/use-auth.ts**

```typescript
'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { AuthUser } from '@/types'

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const supabase = createClient()

    supabase.auth.getUser().then(({ data }) => {
      if (data.user) {
        setUser({
          id: data.user.id,
          email: data.user.email ?? '',
          name: data.user.user_metadata?.full_name ?? data.user.email ?? '',
          avatar_url: data.user.user_metadata?.avatar_url ?? null,
          role: data.user.user_metadata?.iems_role ?? 'employee',
          department_id: data.user.user_metadata?.department_id ?? null,
        })
      }
      setLoading(false)
    })

    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        setUser({
          id: session.user.id,
          email: session.user.email ?? '',
          name: session.user.user_metadata?.full_name ?? session.user.email ?? '',
          avatar_url: session.user.user_metadata?.avatar_url ?? null,
          role: session.user.user_metadata?.iems_role ?? 'employee',
          department_id: session.user.user_metadata?.department_id ?? null,
        })
      } else {
        setUser(null)
      }
    })

    return () => listener.subscription.unsubscribe()
  }, [])

  return { user, loading }
}
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
cd apps/web && npm run test:run src/__tests__/hooks/use-role.test.ts
```

Expected: `4 passed`

- [ ] **Step 6: Commit**

```bash
cd apps/web
git add src/hooks/use-auth.ts src/hooks/use-role.ts src/__tests__/hooks/use-role.test.ts
git commit -m "feat: add use-auth and use-role hooks with canAccess guard"
```

---

## Task 11: AppShell + TopBar components

**Files:**
- Create: `apps/web/src/components/layout/app-shell.tsx`
- Create: `apps/web/src/components/layout/top-bar.tsx`
- Create: `apps/web/src/__tests__/components/layout/app-shell.test.tsx`

- [ ] **Step 1: Write tests**

Create `apps/web/src/__tests__/components/layout/app-shell.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { AppShell } from '@/components/layout/app-shell'

// Minimal sidebar stub so the test doesn't need Supabase
jest.mock('@/components/layout/sidebar', () => ({
  Sidebar: () => <nav aria-label="main navigation" />,
}))

test('AppShell renders the gradient strip', () => {
  render(
    <AppShell>
      <main>content</main>
    </AppShell>
  )
  const strip = document.querySelector('.gradient-strip')
  expect(strip).toBeInTheDocument()
})

test('AppShell renders children inside the content area', () => {
  render(
    <AppShell>
      <p>page content</p>
    </AppShell>
  )
  expect(screen.getByText('page content')).toBeInTheDocument()
})
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd apps/web && npm run test:run src/__tests__/components/layout/app-shell.test.tsx
```

Expected: error — module not found

- [ ] **Step 3: Create src/components/layout/top-bar.tsx**

```typescript
import { Bell } from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'

interface TopBarProps {
  breadcrumb?: React.ReactNode
  className?: string
}

export function TopBar({ breadcrumb, className }: TopBarProps) {
  return (
    <header
      className={cn(
        'flex h-14 items-center justify-between px-4 bg-surface-deep border-b border-surface-border',
        className
      )}
    >
      {/* Logo — collapsed to "i", expanded shows "IEMS" via the sidebar */}
      <div className="flex items-center gap-3">
        <span className="font-mono text-accent-saffron font-semibold text-sm tracking-widest">
          IEMS
        </span>
        {breadcrumb && (
          <div className="flex items-center gap-1 text-sm text-text-primary/60">
            {breadcrumb}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <Link
          href="/notifications"
          aria-label="Notifications"
          className="relative p-2 rounded-md hover:bg-surface-raised transition-colors"
        >
          <Bell size={18} className="text-text-primary/70" />
        </Link>
      </div>
    </header>
  )
}
```

- [ ] **Step 4: Create src/components/layout/app-shell.tsx**

```typescript
import { cn } from '@/lib/utils'
import { TopBar } from './top-bar'
import { Sidebar } from './sidebar'

interface AppShellProps {
  children: React.ReactNode
  breadcrumb?: React.ReactNode
  className?: string
}

export function AppShell({ children, breadcrumb, className }: AppShellProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-surface-base">
      {/* Icon rail / hover-expand sidebar */}
      <Sidebar />

      {/* Main column */}
      <div className="flex flex-1 flex-col min-w-0">
        <TopBar breadcrumb={breadcrumb} />

        {/* 2px gradient strip — appears once per shell, immediately below TopBar */}
        <div className="gradient-strip flex-none" aria-hidden="true" />

        {/* Scrollable content area */}
        <main
          className={cn('flex-1 overflow-y-auto', className)}
          id="main-content"
        >
          {children}
        </main>
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
cd apps/web && npm run test:run src/__tests__/components/layout/app-shell.test.tsx
```

Expected: `2 passed`

- [ ] **Step 6: Commit**

```bash
cd apps/web
git add src/components/layout/app-shell.tsx src/components/layout/top-bar.tsx src/__tests__/components/layout/app-shell.test.tsx
git commit -m "feat: add AppShell (gradient strip) and TopBar components"
```

---

## Task 12: Sidebar component

**Files:**
- Create: `apps/web/src/components/layout/sidebar.tsx`
- Create: `apps/web/src/__tests__/components/layout/sidebar.test.tsx`

- [ ] **Step 1: Write tests**

Create `apps/web/src/__tests__/components/layout/sidebar.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { Sidebar } from '@/components/layout/sidebar'

// Mock Next.js router
vi.mock('next/navigation', () => ({
  usePathname: () => '/dashboard',
}))

// Mock auth — employee role
vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => ({
    user: { role: 'employee', name: 'Test User', avatar_url: null },
    loading: false,
  }),
}))

test('sidebar renders main navigation landmark', () => {
  render(<Sidebar />)
  expect(screen.getByRole('navigation', { name: /main navigation/i })).toBeInTheDocument()
})

test('sidebar hides Admin link for employee role', () => {
  render(<Sidebar />)
  expect(screen.queryByRole('link', { name: /admin/i })).not.toBeInTheDocument()
})

test('sidebar hides Director link for employee role', () => {
  render(<Sidebar />)
  expect(screen.queryByRole('link', { name: /director/i })).not.toBeInTheDocument()
})

test('sidebar icon-only buttons have aria-labels', () => {
  render(<Sidebar />)
  const iconLinks = screen.getAllByRole('link')
  iconLinks.forEach((link) => {
    const hasLabel =
      link.getAttribute('aria-label') ||
      link.textContent?.trim()
    expect(hasLabel).toBeTruthy()
  })
})
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd apps/web && npm run test:run src/__tests__/components/layout/sidebar.test.tsx
```

Expected: error — module not found

- [ ] **Step 3: Create src/components/layout/sidebar.tsx**

```typescript
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  FolderOpen,
  Archive,
  CalendarDays,
  CheckSquare,
  Clock,
  Bell,
  ShieldCheck,
  BarChart3,
  LogOut,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/hooks/use-auth'
import { canAccess } from '@/hooks/use-role'
import type { NavItem, UserRole } from '@/types'

const NAV_GROUPS: { label: string; items: NavItem[] }[] = [
  {
    label: 'Workspace',
    items: [
      { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      { label: 'Projects', href: '/projects', icon: FolderOpen },
      { label: 'Archive', href: '/archive', icon: Archive },
    ],
  },
  {
    label: 'People',
    items: [
      { label: 'Attendance', href: '/attendance', icon: Clock },
      { label: 'Tasks', href: '/tasks', icon: CheckSquare },
      { label: 'Calendar', href: '/calendar', icon: CalendarDays },
    ],
  },
  {
    label: 'Approvals',
    items: [
      { label: 'Approvals', href: '/approvals', icon: Bell },
    ],
  },
  {
    label: 'Admin',
    items: [
      {
        label: 'Admin',
        href: '/admin',
        icon: ShieldCheck,
        roles: ['admin', 'super_admin', 'super_user'] as UserRole[],
      },
    ],
  },
  {
    label: 'Director',
    items: [
      {
        label: 'Director',
        href: '/director',
        icon: BarChart3,
        roles: ['director'] as UserRole[],
      },
    ],
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const { user } = useAuth()
  const role = user?.role

  const isActive = (href: string) =>
    href === '/dashboard' ? pathname === href : pathname.startsWith(href)

  return (
    <nav
      aria-label="main navigation"
      className={cn(
        'group flex flex-col h-full bg-surface-deep border-r border-surface-border',
        'w-11 hover:w-[200px] transition-[width] duration-[180ms] ease-out overflow-hidden flex-none'
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center px-3 border-b border-surface-border overflow-hidden">
        <span className="font-mono text-accent-saffron font-semibold text-sm tracking-widest whitespace-nowrap">
          <span className="group-hover:hidden">i</span>
          <span className="hidden group-hover:inline">IEMS</span>
        </span>
      </div>

      {/* Nav groups */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden py-2">
        {NAV_GROUPS.map((group) => {
          const visibleItems = group.items.filter(
            (item) => !item.roles || (role && canAccess(role, item.roles))
          )
          if (visibleItems.length === 0) return null

          return (
            <div key={group.label} className="mb-1">
              {visibleItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-label={item.label}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 mx-1 rounded-md',
                    'transition-colors duration-100',
                    'whitespace-nowrap overflow-hidden',
                    isActive(item.href)
                      ? 'bg-accent-madder text-text-primary'
                      : 'text-text-primary/60 hover:bg-surface-raised hover:text-text-primary'
                  )}
                >
                  <item.icon
                    size={18}
                    aria-hidden="true"
                    className="flex-none"
                  />
                  <span className="text-sm font-sans opacity-0 group-hover:opacity-100 transition-opacity duration-[180ms]">
                    {item.label}
                  </span>
                </Link>
              ))}
            </div>
          )
        })}
      </div>

      {/* Footer — user + logout */}
      {user && (
        <div className="border-t border-surface-border p-2">
          <div className="flex items-center gap-3 px-1 overflow-hidden">
            <div className="w-7 h-7 rounded-full bg-accent-madder flex-none flex items-center justify-center text-xs font-mono text-text-primary uppercase">
              {user.name.charAt(0)}
            </div>
            <span className="text-xs text-text-primary/60 truncate opacity-0 group-hover:opacity-100 transition-opacity duration-[180ms]">
              {user.name}
            </span>
          </div>
          <button
            aria-label="Sign out"
            className="mt-1 flex items-center gap-3 w-full px-1 py-2 rounded-md text-text-primary/40 hover:text-text-primary/70 hover:bg-surface-raised transition-colors"
          >
            <LogOut size={16} aria-hidden="true" className="flex-none ml-0.5" />
            <span className="text-xs opacity-0 group-hover:opacity-100 transition-opacity duration-[180ms]">
              Sign out
            </span>
          </button>
        </div>
      )}
    </nav>
  )
}
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd apps/web && npm run test:run src/__tests__/components/layout/sidebar.test.tsx
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
cd apps/web
git add src/components/layout/sidebar.tsx src/__tests__/components/layout/sidebar.test.tsx
git commit -m "feat: add Sidebar — icon rail (44px), hover-expand (200px), role-filtered nav"
```

---

## Task 13: PageHeader + ContentArea + DetailDrawer

**Files:**
- Create: `apps/web/src/components/layout/page-header.tsx`
- Create: `apps/web/src/components/layout/content-area.tsx`
- Create: `apps/web/src/components/layout/detail-drawer.tsx`
- Create: `apps/web/src/__tests__/components/layout/page-header.test.tsx`

- [ ] **Step 1: Write tests**

Create `apps/web/src/__tests__/components/layout/page-header.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { PageHeader } from '@/components/layout/page-header'

test('renders the title in an h1', () => {
  render(<PageHeader title="Projects" />)
  expect(screen.getByRole('heading', { level: 1, name: 'Projects' })).toBeInTheDocument()
})

test('renders an optional subtitle', () => {
  render(<PageHeader title="Projects" subtitle="2026-Q2" />)
  expect(screen.getByText('2026-Q2')).toBeInTheDocument()
})

test('renders children as the action slot', () => {
  render(
    <PageHeader title="Projects">
      <button>New Project</button>
    </PageHeader>
  )
  expect(screen.getByRole('button', { name: 'New Project' })).toBeInTheDocument()
})
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd apps/web && npm run test:run src/__tests__/components/layout/page-header.test.tsx
```

- [ ] **Step 3: Create src/components/layout/page-header.tsx**

```typescript
import { cn } from '@/lib/utils'

interface PageHeaderProps {
  title: string
  subtitle?: string
  children?: React.ReactNode
  className?: string
}

export function PageHeader({ title, subtitle, children, className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        'flex items-start justify-between px-6 py-5 border-b border-surface-border',
        className
      )}
    >
      <div>
        <h1 className="font-serif italic text-2xl text-text-primary leading-tight">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-0.5 font-mono text-xs text-accent-saffron tracking-wide uppercase">
            {subtitle}
          </p>
        )}
      </div>
      {children && (
        <div className="flex items-center gap-2 mt-0.5">{children}</div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Create src/components/layout/content-area.tsx**

```typescript
import { cn } from '@/lib/utils'

export function ContentArea({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn('px-6 py-5 max-w-7xl mx-auto w-full', className)}>
      {children}
    </div>
  )
}
```

- [ ] **Step 5: Create src/components/layout/detail-drawer.tsx**

```typescript
'use client'

import { X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useEffect, useRef } from 'react'

interface DetailDrawerProps {
  open: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  className?: string
}

export function DetailDrawer({ open, onClose, title, children, className }: DetailDrawerProps) {
  const closeRef = useRef<HTMLButtonElement>(null)

  // Return focus to close button when drawer opens
  useEffect(() => {
    if (open) closeRef.current?.focus()
  }, [open])

  // Keyboard: Escape closes
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape' && open) onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  return (
    <aside
      aria-label={title}
      aria-hidden={!open}
      className={cn(
        'flex-none bg-surface-deep border-l border-surface-border overflow-y-auto',
        'transition-[width] duration-[220ms] ease-out',
        open ? 'w-[260px]' : 'w-0',
        className
      )}
    >
      {open && (
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-serif italic text-base text-text-primary">{title}</h2>
            <button
              ref={closeRef}
              onClick={onClose}
              aria-label="Close drawer"
              className="p-1 rounded hover:bg-surface-raised text-text-primary/60 hover:text-text-primary transition-colors"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
          {children}
        </div>
      )}
    </aside>
  )
}
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
cd apps/web && npm run test:run src/__tests__/components/layout/page-header.test.tsx
```

Expected: `3 passed`

- [ ] **Step 7: Commit**

```bash
cd apps/web
git add src/components/layout/page-header.tsx \
        src/components/layout/content-area.tsx \
        src/components/layout/detail-drawer.tsx \
        src/__tests__/components/layout/page-header.test.tsx
git commit -m "feat: add PageHeader (Instrument Serif title), ContentArea, DetailDrawer components"
```

---

## Task 14: State components

**Files:**
- Create: `apps/web/src/components/states/skeleton-screen.tsx`
- Create: `apps/web/src/components/states/empty-state.tsx`
- Create: `apps/web/src/components/states/error-state.tsx`
- Create: `apps/web/src/components/states/permission-denied.tsx`
- Create: `apps/web/src/components/states/offline-banner.tsx`
- Create: `apps/web/src/__tests__/components/states/states.test.tsx`

- [ ] **Step 1: Write tests**

Create `apps/web/src/__tests__/components/states/states.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { PermissionDenied } from '@/components/states/permission-denied'
import { OfflineBanner } from '@/components/states/offline-banner'

describe('EmptyState', () => {
  test('renders heading and body', () => {
    render(<EmptyState heading="No projects yet" body="Create one to get started." />)
    expect(screen.getByRole('heading', { name: 'No projects yet' })).toBeInTheDocument()
    expect(screen.getByText('Create one to get started.')).toBeInTheDocument()
  })
})

describe('ErrorState', () => {
  test('renders error message and retry button', () => {
    const retry = vi.fn()
    render(<ErrorState message="Failed to load." onRetry={retry} />)
    expect(screen.getByText('Failed to load.')).toBeInTheDocument()
    screen.getByRole('button', { name: /retry/i }).click()
    expect(retry).toHaveBeenCalledOnce()
  })
})

describe('PermissionDenied', () => {
  test('shows generic message — no resource details', () => {
    render(<PermissionDenied />)
    expect(screen.getByRole('heading')).toBeInTheDocument()
    // Must not contain any path or ID
    expect(screen.queryByText(/\/[a-z]/)).toBeNull()
  })
})

describe('OfflineBanner', () => {
  test('renders when visible is true', () => {
    render(<OfflineBanner visible />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  test('renders nothing when visible is false', () => {
    const { container } = render(<OfflineBanner visible={false} />)
    expect(container.firstChild).toBeNull()
  })
})
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd apps/web && npm run test:run src/__tests__/components/states/states.test.tsx
```

- [ ] **Step 3: Create src/components/states/skeleton-screen.tsx**

```typescript
import { cn } from '@/lib/utils'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'rounded bg-surface-raised shimmer',
        className
      )}
    />
  )
}

export function SkeletonScreen({ rows = 4 }: { rows?: number }) {
  return (
    <div aria-busy="true" aria-label="Loading" className="p-6 space-y-4">
      <Skeleton className="h-8 w-48" />
      <div className="space-y-2">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create src/components/states/empty-state.tsx**

```typescript
import { InboxIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  heading: string
  body: string
  icon?: React.ElementType
  action?: React.ReactNode
  className?: string
}

export function EmptyState({
  heading,
  body,
  icon: Icon = InboxIcon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-20 px-6 text-center',
        className
      )}
    >
      <Icon
        size={40}
        aria-hidden="true"
        className="mb-4 text-text-primary/20"
      />
      <h2 className="font-serif italic text-xl text-text-primary mb-2">
        {heading}
      </h2>
      <p className="text-sm text-text-primary/60 max-w-sm">{body}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
```

- [ ] **Step 5: Create src/components/states/error-state.tsx**

```typescript
import { AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ErrorStateProps {
  message: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({ message, onRetry, className }: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-20 px-6 text-center',
        className
      )}
    >
      <AlertTriangle
        size={40}
        aria-hidden="true"
        className="mb-4 text-accent-critical"
      />
      <h2 className="font-serif italic text-xl text-text-primary mb-2">
        Something went wrong
      </h2>
      <p className="text-sm text-text-primary/60 max-w-sm">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-6 px-4 py-2 text-sm font-sans rounded-md bg-accent-madder text-text-primary hover:bg-accent-madder/80 transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  )
}
```

- [ ] **Step 6: Create src/components/states/permission-denied.tsx**

```typescript
import { Lock } from 'lucide-react'

export function PermissionDenied() {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
      <Lock
        size={40}
        aria-hidden="true"
        className="mb-4 text-text-primary/20"
      />
      <h2 className="font-serif italic text-xl text-text-primary mb-2">
        Access restricted
      </h2>
      <p className="text-sm text-text-primary/60 max-w-sm">
        You don&apos;t have permission to view this page. Contact your administrator if you believe this is an error.
      </p>
    </div>
  )
}
```

- [ ] **Step 7: Create src/components/states/offline-banner.tsx**

```typescript
import { WifiOff } from 'lucide-react'

export function OfflineBanner({ visible }: { visible: boolean }) {
  if (!visible) return null

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center gap-2 px-4 py-2 bg-accent-warning/10 border-b border-accent-warning/30 text-accent-warning text-sm font-sans"
    >
      <WifiOff size={14} aria-hidden="true" />
      <span>You&apos;re offline. Showing cached data.</span>
    </div>
  )
}
```

- [ ] **Step 8: Run tests — expect PASS**

```bash
cd apps/web && npm run test:run src/__tests__/components/states/states.test.tsx
```

Expected: all tests pass

- [ ] **Step 9: Commit**

```bash
cd apps/web
git add src/components/states/ src/__tests__/components/states/
git commit -m "feat: add state components — SkeletonScreen, EmptyState, ErrorState, PermissionDenied, OfflineBanner"
```

---

## Task 15: Status components

**Files:**
- Create: `apps/web/src/components/status/badge.tsx`
- Create: `apps/web/src/components/status/status-dot.tsx`
- Create: `apps/web/src/components/status/loading-spinner.tsx`
- Create: `apps/web/src/components/status/confirm-dialog.tsx`
- Create: `apps/web/src/components/status/toast-provider.tsx`
- Create: `apps/web/src/__tests__/components/status/badge.test.tsx`

- [ ] **Step 1: Write tests**

Create `apps/web/src/__tests__/components/status/badge.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { Badge } from '@/components/status/badge'

test('renders the label', () => {
  render(<Badge variant="active">ACTIVE</Badge>)
  expect(screen.getByText('ACTIVE')).toBeInTheDocument()
})

test('renders status not by colour alone — text is present', () => {
  render(<Badge variant="overdue">OVERDUE</Badge>)
  // Text content must be readable without colour
  expect(screen.getByText('OVERDUE')).toBeInTheDocument()
})
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd apps/web && npm run test:run src/__tests__/components/status/badge.test.tsx
```

- [ ] **Step 3: Create src/components/status/badge.tsx**

```typescript
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'
import type { BadgeVariant } from '@/types'

const badgeVariants = cva(
  'inline-flex items-center font-mono text-[10px] tracking-widest uppercase px-2 py-0.5 rounded-sm',
  {
    variants: {
      variant: {
        active:   'bg-accent-saffron/15 text-accent-saffron',
        pending:  'bg-surface-raised text-text-primary/60',
        overdue:  'bg-accent-warning/15 text-accent-warning',
        approved: 'bg-accent-saffron/15 text-accent-saffron',
        rejected: 'bg-accent-madder/20 text-accent-critical',
        archived: 'bg-surface-raised text-text-primary/40',
        info:     'bg-surface-raised text-text-primary/60',
        warning:  'bg-accent-warning/15 text-accent-warning',
        critical: 'bg-accent-madder/30 text-accent-critical',
      },
    },
    defaultVariants: { variant: 'info' },
  }
)

interface BadgeProps extends VariantProps<typeof badgeVariants> {
  variant: BadgeVariant
  children: React.ReactNode
  className?: string
}

export function Badge({ variant, children, className }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)}>
      {children}
    </span>
  )
}
```

- [ ] **Step 4: Create src/components/status/status-dot.tsx**

```typescript
import { cn } from '@/lib/utils'

type DotColor = 'green' | 'yellow' | 'red' | 'grey'

const dotColors: Record<DotColor, string> = {
  green:  'bg-green-400',
  yellow: 'bg-accent-warning',
  red:    'bg-accent-critical',
  grey:   'bg-text-primary/30',
}

interface StatusDotProps {
  color: DotColor
  label: string
  className?: string
}

export function StatusDot({ color, label, className }: StatusDotProps) {
  return (
    <span className={cn('flex items-center gap-1.5', className)}>
      <span
        aria-hidden="true"
        className={cn('w-1.5 h-1.5 rounded-full', dotColors[color])}
      />
      <span className="text-xs font-sans text-text-primary/70">{label}</span>
    </span>
  )
}
```

- [ ] **Step 5: Create src/components/status/loading-spinner.tsx**

```typescript
import { cn } from '@/lib/utils'

export function LoadingSpinner({ className }: { className?: string }) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn('inline-block', className)}
    >
      <div className="h-4 w-4 animate-spin rounded-full border-2 border-text-primary/20 border-t-accent-saffron" />
      <span className="sr-only">Loading…</span>
    </div>
  )
}
```

- [ ] **Step 6: Create src/components/status/confirm-dialog.tsx**

```typescript
'use client'

import { useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'

interface ConfirmDialogProps {
  open: boolean
  title: string
  description: string
  confirmLabel?: string
  onConfirm: () => void
  onCancel: () => void
  destructive?: boolean
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  onConfirm,
  onCancel,
  destructive = false,
}: ConfirmDialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null)

  // Focus cancel button when dialog opens (safer default for destructive actions)
  useEffect(() => {
    if (open) cancelRef.current?.focus()
  }, [open])

  // Trap focus and handle Escape
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onCancel])

  if (!open) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
      aria-describedby="confirm-desc"
      className="fixed inset-0 z-50 flex items-center justify-center"
    >
      <div
        className="absolute inset-0 bg-black/60"
        onClick={onCancel}
        aria-hidden="true"
      />
      <div className="relative bg-surface-raised border border-surface-border rounded-lg p-6 max-w-sm w-full mx-4 animate-fade-in">
        <h2 id="confirm-title" className="font-serif italic text-lg text-text-primary mb-2">
          {title}
        </h2>
        <p id="confirm-desc" className="text-sm text-text-primary/70 mb-6">
          {description}
        </p>
        <div className="flex gap-3 justify-end">
          <button
            ref={cancelRef}
            onClick={onCancel}
            className="px-4 py-2 text-sm font-sans rounded-md border border-surface-border text-text-primary/70 hover:text-text-primary hover:bg-surface-base transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className={cn(
              'px-4 py-2 text-sm font-sans rounded-md text-text-primary transition-colors',
              destructive
                ? 'bg-accent-madder hover:bg-accent-madder/80'
                : 'bg-accent-saffron/20 hover:bg-accent-saffron/30'
            )}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 7: Create src/components/status/toast-provider.tsx**

```typescript
'use client'

import { createContext, useContext, useState, useCallback } from 'react'
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

type ToastType = 'success' | 'error' | 'info'

interface Toast {
  id: string
  type: ToastType
  message: string
}

interface ToastCtx {
  toast: (type: ToastType, message: string) => void
}

const ToastContext = createContext<ToastCtx>({ toast: () => {} })

export function useToast() {
  return useContext(ToastContext)
}

const icons: Record<ToastType, React.ElementType> = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
}

const colours: Record<ToastType, string> = {
  success: 'text-accent-saffron',
  error: 'text-accent-critical',
  info: 'text-text-primary/70',
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const toast = useCallback((type: ToastType, message: string) => {
    const id = crypto.randomUUID()
    setToasts((prev) => [...prev, { id, type, message }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div
        aria-live="polite"
        aria-atomic="false"
        className="fixed bottom-4 right-4 z-50 flex flex-col gap-2"
      >
        {toasts.map((t) => {
          const Icon = icons[t.type]
          return (
            <div
              key={t.id}
              role="status"
              className="flex items-start gap-2 bg-surface-raised border border-surface-border rounded-md px-4 py-3 shadow-lg animate-slide-up max-w-xs"
            >
              <Icon
                size={16}
                aria-hidden="true"
                className={cn('mt-0.5 flex-none', colours[t.type])}
              />
              <span className="text-sm text-text-primary flex-1">{t.message}</span>
              <button
                onClick={() => dismiss(t.id)}
                aria-label="Dismiss notification"
                className="p-0.5 text-text-primary/40 hover:text-text-primary transition-colors"
              >
                <X size={12} aria-hidden="true" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}
```

- [ ] **Step 8: Run badge tests — expect PASS**

```bash
cd apps/web && npm run test:run src/__tests__/components/status/badge.test.tsx
```

Expected: `2 passed`

- [ ] **Step 9: Commit**

```bash
cd apps/web
git add src/components/status/ src/__tests__/components/status/
git commit -m "feat: add status components — Badge, StatusDot, LoadingSpinner, ConfirmDialog, ToastProvider"
```

---

## Task 16: Login page

**Files:**
- Create: `apps/web/src/app/login/page.tsx`
- Create: `apps/web/src/app/auth/callback/route.ts`
- Create: `apps/web/src/__tests__/app/login.test.tsx`

- [ ] **Step 1: Write tests**

Create `apps/web/src/__tests__/app/login.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import LoginPage from '@/app/login/page'

test('renders the IEMS ERP heading', () => {
  render(<LoginPage />)
  expect(screen.getByRole('heading', { name: /IEMS/i })).toBeInTheDocument()
})

test('renders a Google Sign-In button', () => {
  render(<LoginPage />)
  expect(
    screen.getByRole('button', { name: /sign in with google/i })
  ).toBeInTheDocument()
})

test('Google Sign-In button is keyboard focusable', () => {
  render(<LoginPage />)
  const btn = screen.getByRole('button', { name: /sign in with google/i })
  btn.focus()
  expect(document.activeElement).toBe(btn)
})
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd apps/web && npm run test:run src/__tests__/app/login.test.tsx
```

- [ ] **Step 3: Create src/app/login/page.tsx**

```typescript
'use client'

import { createClient } from '@/lib/supabase/client'

export default function LoginPage() {
  async function handleGoogleSignIn() {
    const supabase = createClient()
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
  }

  return (
    <div className="min-h-screen bg-surface-base flex items-center justify-center">
      <div className="w-full max-w-sm px-8 py-10 bg-surface-raised border border-surface-border rounded-xl">
        {/* Logo + gradient strip */}
        <div className="mb-8 text-center">
          <div className="gradient-strip mb-6 rounded-full" />
          <h1 className="font-mono text-accent-saffron text-2xl font-semibold tracking-widest">
            IEMS
          </h1>
          <p className="mt-1 font-serif italic text-text-primary/60 text-sm">
            Event Management ERP
          </p>
        </div>

        <button
          onClick={handleGoogleSignIn}
          className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-md border border-surface-border bg-surface-base text-text-primary text-sm font-sans hover:bg-surface-raised transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron focus-visible:ring-offset-2 focus-visible:ring-offset-surface-raised"
        >
          {/* Google G logo — inline SVG to avoid external request */}
          <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
            <path
              d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"
              fill="#4285F4"
            />
            <path
              d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z"
              fill="#34A853"
            />
            <path
              d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"
              fill="#FBBC05"
            />
            <path
              d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"
              fill="#EA4335"
            />
          </svg>
          Sign in with Google
        </button>

        <p className="mt-6 text-center text-xs text-text-primary/30 font-sans">
          Access restricted to authorised IEMS personnel
        </p>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create src/app/auth/callback/route.ts**

```typescript
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next') ?? '/dashboard'

  if (code) {
    const supabase = await createClient()
    await supabase.auth.exchangeCodeForSession(code)
  }

  return NextResponse.redirect(`${origin}${next}`)
}
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
cd apps/web && npm run test:run src/__tests__/app/login.test.tsx
```

Expected: `3 passed`

- [ ] **Step 6: Commit**

```bash
cd apps/web
git add src/app/login/ src/app/auth/ src/__tests__/app/login.test.tsx
git commit -m "feat: add login page with Google Sign-In and auth callback route"
```

---

## Task 17: Update root layout with providers

**Files:**
- Modify: `apps/web/src/app/layout.tsx`

- [ ] **Step 1: Update layout.tsx to include QueryClient and ToastProvider**

```typescript
import type { Metadata } from 'next'
import { Instrument_Serif, Geist, JetBrains_Mono } from 'next/font/google'
import '@/styles/globals.css'
import { Providers } from './providers'

const instrumentSerif = Instrument_Serif({
  weight: ['400'],
  style: ['italic'],
  subsets: ['latin'],
  variable: '--font-serif',
  display: 'swap',
})

const geist = Geist({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'IEMS ERP',
  description: 'Internal ERP for IEMS event management',
  robots: { index: false, follow: false },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${instrumentSerif.variable} ${geist.variable} ${jetbrainsMono.variable}`}
    >
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

- [ ] **Step 2: Create src/app/providers.tsx**

```typescript
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import { ToastProvider } from '@/components/status/toast-provider'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        retry: 1,
      },
    },
  }))

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        {children}
      </ToastProvider>
    </QueryClientProvider>
  )
}
```

- [ ] **Step 3: Commit**

```bash
cd apps/web
git add src/app/layout.tsx src/app/providers.tsx
git commit -m "feat: wire React Query and ToastProvider into root layout"
```

---

## Task 18: Route stubs — all 35 routes

**Files:** All 33 remaining route `page.tsx` files (login and auth/callback already created).

- [ ] **Step 1: Create the dashboard stub**

Create `apps/web/src/app/dashboard/page.tsx`:

```typescript
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default function DashboardPage() {
  return (
    <AppShell>
      <PageHeader title="Dashboard" subtitle="Home" />
      <ContentArea>
        <SkeletonScreen rows={6} />
      </ContentArea>
    </AppShell>
  )
}
```

- [ ] **Step 2: Create all remaining Employee route stubs**

The pattern below is identical for every stub. Create one file per route using this template — replace `Title` and `subtitle` with the values in the table.

| File | Title | Subtitle |
|---|---|---|
| `src/app/attendance/page.tsx` | `Attendance` | `My records` |
| `src/app/leave/page.tsx` | `Leave` | `Requests` |
| `src/app/tasks/page.tsx` | `Tasks` | `My tasks` |
| `src/app/calendar/page.tsx` | `Calendar` | `Shared` |
| `src/app/projects/page.tsx` | `Projects` | `All projects` |
| `src/app/approvals/page.tsx` | `Approvals` | `Queue` |
| `src/app/notifications/page.tsx` | `Notifications` | `` |

Template:

```typescript
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default function __PAGE__() {
  return (
    <AppShell>
      <PageHeader title="__TITLE__" subtitle="__SUBTITLE__" />
      <ContentArea>
        <SkeletonScreen rows={6} />
      </ContentArea>
    </AppShell>
  )
}
```

- [ ] **Step 3: Create dynamic route stubs**

Create each file below — use the same template but with `params` for dynamic segments:

`apps/web/src/app/projects/[id]/page.tsx`:

```typescript
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default function ProjectDetailPage({ params }: { params: { id: string } }) {
  return (
    <AppShell>
      <PageHeader title="Project" subtitle={params.id} />
      <ContentArea>
        <SkeletonScreen rows={8} />
      </ContentArea>
    </AppShell>
  )
}
```

`apps/web/src/app/projects/[id]/documents/page.tsx`:

```typescript
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default function DocumentsPage({ params }: { params: { id: string } }) {
  return (
    <AppShell>
      <PageHeader title="Documents" subtitle={`Project ${params.id}`} />
      <ContentArea>
        <SkeletonScreen rows={8} />
      </ContentArea>
    </AppShell>
  )
}
```

Create the remaining dynamic stubs using the same pattern for:
- `src/app/documents/[id]/page.tsx`
- `src/app/approvals/[id]/page.tsx`
- `src/app/archive/rooms/[id]/page.tsx`
- `src/app/archive/files/[id]/page.tsx`
- `src/app/archive/files/[id]/checkout/page.tsx`
- `src/app/archive/files/[id]/return/page.tsx`
- `src/app/archive/files/[id]/verify/page.tsx`

- [ ] **Step 4: Create static Archive + Admin + Director stubs**

Use the same template for all remaining static routes:

| File | Title | Subtitle |
|---|---|---|
| `src/app/archive/page.tsx` | `Archive` | `Overview` |
| `src/app/archive/rooms/page.tsx` | `Rooms` | `Physical archive` |
| `src/app/admin/page.tsx` | `Admin` | `Overview` |
| `src/app/admin/employees/page.tsx` | `Employees` | `Management` |
| `src/app/admin/departments/page.tsx` | `Departments` | `` |
| `src/app/admin/roles/page.tsx` | `Roles` | `Assignments` |
| `src/app/admin/policies/page.tsx` | `Policies` | `ABAC viewer` |
| `src/app/admin/folder-templates/page.tsx` | `Folder Templates` | `` |
| `src/app/admin/archive-locations/page.tsx` | `Archive Locations` | `` |
| `src/app/admin/audit/page.tsx` | `Audit Log` | `Full history` |
| `src/app/director/page.tsx` | `Director Dashboard` | `Overview` |
| `src/app/director/projects/page.tsx` | `Projects` | `All projects` |
| `src/app/director/attendance/page.tsx` | `Attendance` | `Company-wide` |
| `src/app/director/tasks/page.tsx` | `Tasks` | `Workload` |
| `src/app/director/calendar/page.tsx` | `Calendar` | `Director` |
| `src/app/director/approvals/page.tsx` | `Approvals` | `All pending` |
| `src/app/director/archive/page.tsx` | `Archive` | `Storage view` |
| `src/app/director/audit/page.tsx` | `Audit` | `Event feed` |

- [ ] **Step 5: Run build to check all routes resolve**

```bash
cd apps/web && npm run build
```

Expected: `Compiled successfully`. All 35 routes appear in the build output with no TS errors.

- [ ] **Step 6: Commit**

```bash
cd apps/web
git add src/app/
git commit -m "feat: add route stubs for all 35 routes — shell renders, awaiting API wiring"
```

---

## Task 19: Full test run + dev server smoke check

- [ ] **Step 1: Run all tests**

```bash
cd apps/web && npm run test:run
```

Expected: all tests pass with 0 failures.

- [ ] **Step 2: Start dev server**

```bash
cd apps/web && npm run dev
```

- [ ] **Step 3: Verify in browser**

Open `http://localhost:3000`. Expected behaviour:
- Redirected to `/login`
- Login page renders with IEMS logo, gradient strip, and Google Sign-In button
- No console errors

- [ ] **Step 4: Verify shell on a stub route**

With a valid Supabase session (or by temporarily bypassing middleware), open `/dashboard`.
Expected: `AppShell` renders with sidebar icon rail, gradient strip under top bar, and `SkeletonScreen` in the content area.

- [ ] **Step 5: Commit**

```bash
cd apps/web && git add -A && git commit -m "chore: verify full test suite and dev server smoke pass"
```

---

## Pause here

**All 35 routes are stubbed. The design system, app shell, shared components, auth wiring, and testing infrastructure are in place.**

Do not proceed to Phase 2 (business features and API wiring) until:

1. The backend FastAPI shell is deployed and `GET /v1/me` returns a user with `iems_role` in `user_metadata`
2. API shapes in `docs/api-contract.md` are confirmed complete
3. The 6 unresolved API needs in spec section 13 are confirmed with Codex

**Report to the user which files were created or modified, then stop.**
