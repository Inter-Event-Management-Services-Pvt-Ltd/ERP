# Claude Frontend Checklist

## Ownership

- [x] Only frontend-owned files were modified.
- [x] Any backend requirement was recorded for Codex (OPEN-025, OPEN-026, OPEN-027, OPEN-028, OPEN-029 — all resolved).
- [x] API contract was followed (no invented endpoints; undocumented details noted as OPEN items).

## Design Workflow

- [x] Screen purpose documented.
- [x] User role documented (canManage, canUpload, canExport, physical_file.checkout, archive.manage).
- [ ] Either Claude Design or Google Stitch used where useful.
- [x] Generated output reviewed before implementation.
- [x] Shared components reused (AppShell, PageHeader, ContentArea, SkeletonScreen, ConfirmDialog).
- [x] Responsive states implemented.
- [x] Empty state implemented (no folder selected, no exports, no rooms, no locations, no contents at selected location).
- [x] Loading state implemented (SkeletonScreen, Loader2 spinners, isPending).
- [x] Error state implemented (role="alert" inline errors, apiErrorMessage mapping).
- [x] Permission-denied state implemented (buttons hidden by permission, actions unavailable on wrong state).

## Security

- [x] No secrets exposed.
- [x] No service-role key referenced.
- [x] No direct sensitive write bypass (all uploads go through FastAPI, not Supabase Storage directly).
- [x] No unsafe HTML rendering (no dangerouslySetInnerHTML).
- [x] No restricted metadata leak (permission-denied hides resource details).
- [ ] Security headers reviewed.
- [x] Third-party packages reviewed (no new packages added; existing lucide-react, react-hook-form, zod, date-fns).
- [x] Download links come from backend signed-URL flow (on-demand only via onClick, never pre-fetched).

## Accessibility

- [x] Semantic structure (nav for folder tree, aria-label on breadcrumbs, role="alert" on errors).
- [x] Keyboard navigation (all actions via buttons with type="button", form submit on Enter).
- [x] Visible focus (focus:ring-2 focus:ring-accent-saffron on all interactive elements).
- [x] Accessible labels (aria-label on icon-only ActionBtn buttons).
- [x] Accessible form errors (role="alert" inline, associated with form context).
- [x] No color-only critical state (text labels accompany all status badges).
- [x] No hover-only critical action (all actions have keyboard-reachable equivalents).
- [x] Touch targets checked (py-1.5 px-2 minimum on folder rows, p-0.5 on action icons).
- [ ] Reduced-motion path checked.

## Motion

- [x] Motion is purposeful (folder chevron rotate, opacity on action buttons).
- [x] Motion does not block workflow (transitions are 100-180 ms, no blocking animations).
- [ ] Reduced-motion mode supported (CSS transitions only; prefers-reduced-motion not yet explicitly tested).
- [x] No excessive parallax.
- [x] No animation on every card.
- [x] Opacity and transform preferred (opacity-0/opacity-100 for action reveal, rotate-90 for chevron).
- [x] No major layout shift introduced.

## Validation

- [x] Lint passes.
- [x] Type check passes (npx tsc --noEmit clean after Phase 2 wiring).
- [ ] Tests pass.
- [ ] Production build passes.
- [ ] Responsive QA completed.
- [ ] Screenshot or visual notes added.
