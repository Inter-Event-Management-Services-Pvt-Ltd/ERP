---
name: iems-accessibility-motion-review
description: Use when reviewing or implementing IEMS ERP frontend accessibility, transitions, animation, responsive behavior, keyboard navigation, focus handling, or reduced-motion behavior. Codex frontend-only skill.
---

# Accessibility and Motion Review

Read:

- `docs/14_FRONTEND_DESIGN_SYSTEM.md`
- `docs/15_FRONTEND_SECURITY_MOTION.md`
- `docs/checklists/FRONTEND_CLAUDE.md`

Validate with Playwright MCP:

- keyboard navigation
- visible focus indicators
- logical heading order
- meaningful labels
- accessible form errors
- no hover-only critical actions
- responsive layout
- touch targets
- loading states
- empty states
- permission-denied states
- error states
- reduced-motion behavior
- no excessive animation
- no animation-only communication

Motion rules:

- prefer opacity and transform
- keep transitions restrained
- avoid unnecessary parallax
- avoid animating every card
- support `prefers-reduced-motion`
