# Frontend Security, Accessibility, and Motion Practices

## Security Baseline

The frontend is an untrusted client.

```text
Frontend route guard ≠ authorization
Hidden button ≠ permission check
Client validation ≠ server validation
```

### Required Practices

- Never expose the Supabase service-role key.
- Keep sensitive writes behind FastAPI.
- Use safe, backend-created signed URLs.
- Use React escaping by default.
- Avoid `dangerouslySetInnerHTML`.
- Do not render unsanitized uploaded HTML.
- Avoid unrestricted remote scripts.
- Apply Content Security Policy.
- Add security response headers.
- Do not leak internal object keys in user-facing UI when avoidable.
- Do not log auth tokens or restricted metadata.
- Keep error messages useful but non-sensitive.
- Review any third-party component before adding it.
- Keep dependencies minimal.

### Recommended Security Headers

Review and configure:

```text
Content-Security-Policy
Strict-Transport-Security
X-Content-Type-Options
Referrer-Policy
Permissions-Policy
frame-ancestors through CSP
```

If authenticated write requests rely on cookies, review CSRF protections with Codex.

## Motion Principles

Motion should improve orientation and feedback, not decorate every interaction.

### Use Motion For

- drawer and dialog transitions
- navigation continuity
- task completion feedback
- skeleton loading transitions
- expanding folder-tree nodes
- small state changes
- success confirmations

### Avoid

- long blocking transitions
- excessive parallax
- auto-playing decorative movement
- animated background noise
- bouncing buttons
- motion on every dashboard card
- animation-only status communication
- large layout shifts

### Timing Guidance

Use restrained durations:

```text
micro-feedback: approximately 100–180 ms
standard transitions: approximately 160–260 ms
drawers and dialogs: approximately 180–320 ms
```

Use judgment rather than treating these values as rigid rules.

### Reduced Motion

Respect:

```css
@media (prefers-reduced-motion: reduce) {
  /* reduce or remove non-essential motion */
}
```

Provide a static or reduced alternative for non-essential animation.

### Performance

Prefer:

```text
opacity
transform
```

Avoid unnecessary animation of layout-heavy properties.

## Accessibility

- preserve keyboard interaction
- preserve focus after dialogs
- focus first meaningful control in dialogs
- return focus when dialogs close
- use semantic labels
- avoid hover-only actions
- ensure touch targets are usable
- provide accessible status text
- verify contrast
- test with reduced motion enabled
