# Claude Frontend Checklist

## Ownership

- [ ] Only frontend-owned files were modified.
- [ ] Any backend requirement was recorded for Codex.
- [ ] API contract was followed.

## Design Workflow

- [ ] Screen purpose documented.
- [ ] User role documented.
- [ ] Either Claude Design or Google Stitch used where useful.
- [ ] Generated output reviewed before implementation.
- [ ] Shared components reused.
- [ ] Responsive states implemented.
- [ ] Empty state implemented.
- [ ] Loading state implemented.
- [ ] Error state implemented.
- [ ] Permission-denied state implemented.

## Security

- [ ] No secrets exposed.
- [ ] No service-role key referenced.
- [ ] No direct sensitive write bypass.
- [ ] No unsafe HTML rendering.
- [ ] No restricted metadata leak.
- [ ] Security headers reviewed.
- [ ] Third-party packages reviewed.
- [ ] Download links come from backend signed-URL flow.

## Accessibility

- [ ] Semantic structure.
- [ ] Keyboard navigation.
- [ ] Visible focus.
- [ ] Accessible labels.
- [ ] Accessible form errors.
- [ ] No color-only critical state.
- [ ] No hover-only critical action.
- [ ] Touch targets checked.
- [ ] Reduced-motion path checked.

## Motion

- [ ] Motion is purposeful.
- [ ] Motion does not block workflow.
- [ ] Reduced-motion mode supported.
- [ ] No excessive parallax.
- [ ] No animation on every card.
- [ ] Opacity and transform preferred.
- [ ] No major layout shift introduced.

## Validation

- [ ] Lint passes.
- [ ] Type check passes.
- [ ] Tests pass.
- [ ] Production build passes.
- [ ] Responsive QA completed.
- [ ] Screenshot or visual notes added.
