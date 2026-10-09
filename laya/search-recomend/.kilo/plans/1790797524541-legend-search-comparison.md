# Legend for Search Comparison

## Context

The two-column search comparison interface (`public/index.html`, `public/busca.css`, `public/app.js`) is already implemented. Tiles are visually distinguished via `border-left` colors:
- `source-both` → `var(--ok)` (green)
- `source-keyword` → `#4a6fa5` (blue)
- `source-laya` → `var(--accent)` (orange)

However, there is **no permanent legend** explaining these color codes. Users currently rely on `title` tooltips, which are not mobile-friendly.

## Objective

Add a concise, permanent legend below each column header so users can instantly understand what each border color means, without relying on hover tooltips.

## Requirements

1. **HTML**: Insert a legend element below `.coluna-header` in each `.coluna` (`#coluna-keyword` and `#coluna-laya`).
2. **CSS**: Style `.coluna-legend` to be compact, fit within existing column padding, and use existing CSS variables for colors.
3. **Mobile**: At `<=640px`, legends should stack naturally with columns (no extra media queries needed if using flex/grid within `.coluna`).
4. **No JS changes**: Rendering logic does not need modification; legend is static HTML.

## Acceptance Criteria

- Legend is visible on desktop and mobile.
- Legend text is concise (e.g., color swatch + short label).
- Colors match existing `.source-both`, `.source-keyword`, `.source-laya` definitions.
- No regression in existing two-column layout or tile rendering.
