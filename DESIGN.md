# Design System: Privexis

## 1. Visual Theme & Atmosphere

Privexis is a focused privacy evidence workbench: midnight surfaces, measured violet signals, and the calm precision of an operations room. Marketing pages use editorial asymmetry and generous space; authenticated screens become denser only where evidence tables need it. Keep every value legible and every visual effect subordinate to the evidence.

## 2. Color Palette & Roles

- **Midnight Canvas** (`#090B12`) — public page background.
- **Deep Slate** (`#10131D`) — application shell and raised panels.
- **Graphite Surface** (`#171B27`) — inputs, table headers, secondary panels.
- **Cloud Text** (`#F2F4FA`) — primary text.
- **Steel Text** (`#A1A8B8`) — supporting labels and descriptions.
- **Quiet Border** (`#292E3B`) — separators and control boundaries.
- **Signal Violet** (`#9B83E8`) — the sole interface accent for primary actions, focus, and selected states; never add neon glows.
- **Success** (`#63B79B`), **Warning** (`#D7AD62`), **Failure** (`#D87980`) — restrained semantic statuses, never decorative accents.
- Keep the supplied logo artwork's cyan and silver as intrinsic brand colors; do not apply them as a second UI accent.

## 3. Typography Rules

- **Display and body:** Geist Sans, with a system sans-serif fallback; compact, weight-led headings and relaxed body leading.
- **Mono:** Geist Mono for identifiers, counts, hashes, timestamps, and code.
- Keep paragraphs below roughly 65 characters per line. Use `clamp()` for display sizing; preserve a minimum 1rem body size.
- Avoid generic serif fonts and avoid using oversized headings as a substitute for hierarchy.

## 4. Component Stylings

- **Buttons:** solid Signal Violet for the single primary action; quiet outline or text treatment for secondary actions. Clear hover and focus states; press feedback uses a 1px transform, with no glow.
- **Cards:** square-ish 10–14px corners and subtle borders. Use elevation only to separate a meaningful layer; use dividers for dense tables.
- **Inputs:** visible label above each control, helper text below where needed, and inline errors. Use a distinct violet focus ring.
- **Tables:** sticky or repeated column labels when useful, aligned numeric values, readable row spacing, and overflow-safe cells.
- **Loading:** layout-matched skeletons. **Empty states:** concise explanation and a real next action. **Errors:** inline, specific, and recoverable.
- **Status:** combine restrained color with text or icon so meaning never depends on color alone.

## 5. Layout Principles

- Use a 12-column desktop grid within a 1,280px content width. Marketing pages use left-aligned split heroes and intentionally offset visual blocks; avoid centered-template composition.
- The app shell uses a compact persistent desktop navigation rail and a clear single-column mobile navigation pattern. Let wide data tables scroll within their own labeled region without making the whole page overflow.
- Use 4px spacing increments, with 24px panel padding and 48–88px public section gaps.
- At widths below 768px, collapse multi-column content to one column and keep all tap targets at least 44px.

## 6. Motion & Interaction

- Keep motion restrained: 140–220ms ease-out transitions for opacity and transform only. Respect `prefers-reduced-motion`.
- Use one-time stagger only for meaningful dashboard content; no perpetual shimmer or animated background. Keep keyboard focus visible and interaction behavior predictable.

## 7. Anti-Patterns (Banned)

- No copied reference logos, vendor marks, or screenshot UI presented as Privexis product screens.
- No purple neon, outer glow, gradient headline fills, generic hacker imagery, glassmorphism, or decorative circuit-board wallpaper.
- No Inter, emojis, pure black, fake testimonials, fabricated ratings, round-number performance claims, or unsupported compliance badges.
- No three equal feature cards, overlapping content, custom cursors, bouncing scroll prompts, or AI marketing clichés.
- No unlabeled demo metrics or scans presented as production results.
