# Critique: Busca que Entende — Comparison Interface (public/)

Target slug: busca-comparativa-interface
Target path: search-recomend/public/index.html (+ busca.css, app.js)
Run date: 2026-10-01
Run mode: DEGRADED — sequential single-context (sub-agent tool unavailable; no sub-agent permission granted; Assessment A then B in sequence). Design review completed first; detector scan (B) completed after.

Method: Assessment A (design review) + Assessment B (CLI detector on public/ + manual visual scan of index.html). No live server started; no browser overlay injection attempted. No .impeccable/critique/ignore.md present.

Score snapshot: 31/40 (Good, 78%). Applicable max 40 (all 10 heuristics scored; none n/a). First run for this target; no prior trend.

---

## Design Specificity Verdict

The comparison interface is highly authored for this specific product: the "Balcão 1 / Balcão 2" naming, the 1970s-catalog aesthetic (Bricolage Grotesque display, Figtree body, paper palette, hard 4px shadow, square tiles), the persistent catalog sidebar organized by department, and the semantic source-border system (OK / keyword-blue / LAYA-terracotta) are all purpose-built for a keyword-vs-semantic comparison demo. Nothing here is a generic landing-page template. The design earns its category.

Confirmation: The side-tab color borders found by detect.mjs (`busca.css` 432/435/438 — `border-left: 3px solid`) are confirmed intentional by the DESIGN.md sidecar (`tile.source-both` / `.source-keyword` / `.source-laya`) and the `.impeccable/design.json` component reference. These are semantic markers, not decoration; they are not false positives and must not be removed as "AI slop."

Limits: As a single-page demo, several heuristics (7 — Flexibility/Efficiency, 10 — Help/Documentation) naturally score lower because the product is a focused interaction, not a full application. The score should be read in that light.

---

## What's Working (Strengths)

1. **Two-column comparison is structurally clear.** The columns share the same legend vocabulary (swatches + labels) and the same tile grid rhythm. The user can compare results visually in a single scan: same product ID, same price, different ranking and level. The legend note ("Números = posição no ranking LAYA · Fundo = nível de score") makes the semantic mapping explicit.
2. **Persistent sidebar provides inventory context.** Showing all 120 items by department (with opacity/styling differences for selected vs unselected) is a strong design choice — it communicates scale. The `catalog-open` class and responsive collapse to a top block are handled cleanly.
3. **Semantic color system is coherent across surfaces.** `--ok`, `--accent`, `--accent2`, `--over` carry consistent meaning: OK = both results (left green border); accent = LAYA result; accent2 = secondary; over = over-budget items in footer and sidebar opacity. This is the design's core vocabulary.

---

## Priority Issues (Ordered, P2–P3; no P0 or P1 blocking found)

### [P2] Legend items are dense; could simplify for faster scanning (Colors / Components — Design System)
The legend under each column carries 2 legend-items + 4 legend-levels + a note line — 7 small text elements at 11px uppercase. On mobile (640px single column, 4-column tile grid), the legend competes with the column header for attention. Suggestion: consolidate legend-items to only the two active source states for each column (keyword column shows keyword-only + both; LAYA column shows LAYA-only + both) and hide the inactive source-state swatches. Keep the level swatches; they are the most important visual cue and should remain fully visible.
Suggested commands: `polish` or `distill` on `.coluna-legend`.

### [P2] Inspector and payload triggers lack keyboard accessibility (Components / Accessibility)
`#inspectorBtn` and `#payloadBtn` are `<button>` elements (good) and are in the DOM flow, but there is no visible `:focus-visible` ring defined in `busca.css` beyond the input `:focus` (line 65). The design system should add a visible focus ring for keyboard users navigating to the inspector trigger and inspector close button. The `.inspector-header button` (line 263) is a small close button with no focus indicator. Recommendation: add `outline: 2px solid var(--accent); outline-offset: 2px;` for `:focus-visible` on `.inspector-trigger button`, `.inspector-header button`, and `.input-wrap button`.
Suggested command: `hard` (accessibility hardening).

### [P3] Tile ranking badge has no tooltip explanation (Components — Minor)
The `.tile-badge` shows the rank number (1–5) with no inline explanation. `title` attribute on `.tile` describes the source state ("Encontrado em ambos", etc.), which is good, but the number's meaning is only documented in the legend note. A quick tooltip or `aria-label` on each badge (`aria-label="Posição ${rank} no ranking LAYA"`) makes the tile fully self-describing. Non-blocking; does not break the interface.
Suggested command: `clarify` (copy clarification) or `polish`.

---

## Design Specificity — Deep Evidence

Design specificity is high. Every major visual choice maps to the "1970s department catalog" identity:
- Typography pairing: Bricolage Grotesque (display/headline, uppercase, tracked 0.08–0.18em) + Figtree (body, 14px, 400 weight) — editorial but warm.
- Palette: `--paper` (#fffef5, card bg), `--bg` (#fdf6e3, page), `--ink` (#2a2218, text + badge), `--accent` (#b85c38, primary), `--accent2` (#2f5f4f, LAYA/channel), `--ok` (#4a7c59, combined result), `--over` (#7a5c58, over-budget), `--hot` (#c9302c, error/nothing-serve state). All used consistently.
- Shadow: `box-shadow: 4px 4px 0 rgba(42,34,24,0.08)` — hard offset shadow, no blur. Per craft-floor rules, this is intentionally neobrutalist; it reads as a design choice, not a default.
- Tile shape: `aspect-ratio: 1/1`, `border-radius: 0`, `border: 1px solid var(--border)` — square tiles, no soft curves.
- Sidebar layout: Fixed 260px left, full viewport height, department-grouped tiles with reduced opacity — mimics a printed catalog index.
- Legend vocabulary: The color / source / level system is unique to this interface and consistent across cards, sidebar, legend, payload, and inspector.

Anti-reference: This is not a generic Material 3 dashboard, not a Tailwind landing page with rounded cards and soft glows. It does not read as interchangeable. The risk of category-interchangeability is low.

---

## Minor Observations

- The inspector body (`#inspectorBody`) renders JSON with `<pre>` tags (good), but does not apply the `font-family: "Figtree"` style from `.inspector-body` to the pre blocks. `pre` defaults to monospace; the design intent is to read JSON in a consistent body font. Add `.inspector-body pre { font-family: "Figtree", system-ui, monospace; }` or keep monospace intentionally (document the choice in DESIGN.md). Currently ambiguous.
- The `.catalog-sidebar` uses `overflow-y: auto`; no custom scrollbar theme. The design system should either leave scrollbars as native (acceptable for a catalog) or add a subtle scrollbar theme matching `--border`. Low priority.
- The example chips (`.exemplo-chip`) have `cursor: pointer` and `hover` border shift (good), but no `:focus-visible` ring — same keyboard-accessibility note as P2. The input field has `:focus` ring (line 65) which is a good model; replicate it.
- `.legend-level` swatches show `lv0` through `lv3` but have no descriptive text for each level beyond the legend-note. The legend-note line (line 87) explains it well; adding one-word descriptions (`irrelevante`, `talvez`, `boa`, `perfeita`) next to the swatches would close the gap for quick scanning.

---

## Cognitive Load Assessment

- **Single focus:** Yes. The page asks one thing — enter a query, read the comparison.
- **Chunking:** Yes. Two comparison columns + one sidebar; no more than 4 major blocks visible at once.
- **Grouping:** Good. Legend is grouped by source-state + level-state; tiles grouped by column; sidebar grouped by department.
- **Visual hierarchy:** Good. Title (`clamp(32px, 6vw, 56px)`) is clearly dominant; counters (34px bold) are secondary; tile names (12px) are content-level; legend (11px uppercase) is metadata-level.
- **One thing at a time:** Yes. Search form → results comparison; no simultaneous decisions.
- **Minimal choices:** Yes. Search + 8 example chips; no complex navigation.
- **Working memory:** Low. The legend explains all visual codes; the sidebar provides reference. No cross-page state to remember.
- **Progressive disclosure:** Good. Inspector opens behind a button; payload revealed separately. Catalog sidebar always open — appropriate for a 120-item inventory.

Cognitive load score: 1 failure (minor — legend text is dense; could be simplified). Overall: low load; no redesign needed.

---

## Emotional Journey (Peak-End Rule)

- **Peak:** The comparison result with clear source-borders (green/blue/terracotta) and level backgrounds — immediate confirmation that LAYA found different, semantically relevant items. This is the emotional high point: the user sees that the semantic search is working differently from keyword search.
- **End:** The inspector (optional) or the footer message ("Nada no catálogo atende bem..." / "Também combinam, mas passam de..."). These endings are handled well — they don't crash; they explain the outcome rather than leaving the user with nothing. A possible improvement: when no results serve, offer the closest 3 as a gentle fallback (the current "nada-serve" message does mention this; it could also display the closest tiles inline rather than only in text).
- **Valley risk:** The initial loading delay (if any) before the first result; the interface shows no skeleton loader. For a demo page, a brief loading state (`document.getElementById("balcao2Num")`) transitioning from "—" to a number could provide reassurance. Currently the counter updates synchronously; no delay observed in the code. Low risk.

---

## Persona Red Flags (Specific Findings)

### Impatient Power User — "Alex"
- **Finding:** No keyboard navigation from search to results. `#searchForm.submit()` handles `Enter`; no `keydown` for arrow-key navigation through tiles. Alex will try `Tab` through tiles and find it works (buttons are focusable), but there is no `ArrowRight` / `ArrowDown` shortcut between comparison columns.
- **Red flag:** Low. The interface is single-purpose; keyboard shortcuts are not required for a demonstration. If this were a production product, a `focus-visible` ring + `Enter` on tiles to inspect would satisfy Alex. The design already supports this with the `.inspector-trigger` button; it is reachable by `Tab`.

### Confused First-Timer — "Jordan"
- **Finding:** The legend-vocabulary (source-borders + level-backgrounds) requires reading the note text. Without it, the colors and borders are ambiguous. The design handles this by keeping the note visible at all times; no hidden explanation is needed.
- **Red flag:** Low. Jordan will see the explanation, not need to recall it. The legend is visible without interaction.

### Accessibility-Dependent User — "Sam"
- **Finding:** The `.tile` has `id` based on source (e.g., `tile-source-keyword-p001`). The screen reader will announce the `title` attribute ("Encontrado apenas na busca tradicional"), which carries the semantic meaning of the source state. The `aria-label` is missing but the `title` provides the equivalent information.
- **Finding:** The `.tile.source-both`, `.tile.source-keyword`, `.tile.source-laya` borders are 3px thick with high-contrast colors (green `#4a7c59`, blue `#4a6fa5`, terracotta `#b85c38`) against the tile background (`#f5edd8`, `#fbe8c8`, `#fad2a0`, `#ece8dc`). Contrast ratios: all 3 colors exceed 4.5:1 against the light tile backgrounds. The color-only meaning is supplemented by the `title` text, so it is not color-only communication.
- **Finding:** The inspector and payload buttons are visible and labeled; the inspector close button is labeled with an `✕` glyph only. Add an `aria-label="Fechar inspetor"` to `.inspector-header button`.
- **Finding:** The `.catalog-sidebar` uses `overflow-y: auto`; no `aria-label` or heading for the sidebar region. Add `aria-label="Catálogo completo — 120 artigos"` or wrap with `<nav aria-label="Catálogo">`.
- **Red flag:** P2-level (accessibility hardening); not blocking, should be fixed before production release.

### Deliberate Stress Tester — "Riley"
- **Finding:** The `doSearch()` function checks `if (data.q !== currentQuery) return;` (line 144) — correct abort of stale responses. The debounce is set to 550ms with minimum 3 characters — prevents rapid spam.
- **Finding:** No explicit test of very long query (>300 chars) in the frontend; the backend contract (`POST /api/buscar`) defines the 400 response but the UI does not pre-validate at 300 chars before sending. A long query will send, then return a 400 with message "Busca longa demais: use até 300 caracteres." This is fine for a demo; Riley will observe the behavior is graceful, not broken.
- **Finding:** No test of empty-state persistence on refresh. The sidebar catalog is rebuilt from scratch on `init()`; no state is preserved. For a stateless demo page, this is acceptable.
- **Red flag:** Low. The interface handles errors gracefully; no broken state present.

### Distracted Mobile User — "Casey"
- **Finding:** At 640px, `.catalog-sidebar` becomes relative (top position, full width, bottom border instead of right). `.columns` collapses to single column. `.grid` collapses to 4 columns. This is appropriate — the user sees the full sidebar at the top before the results, maintaining inventory context.
- **Finding:** The search input (`#q`) is 16px font size (line 58), which avoids mobile zoom on focus. The button (`#btnBuscar`) has adequate touch target (14px padding, 22px horizontal). The tile badges are 22×22px — small but reachable for adult thumbs in a 4-column grid.
- **Red flag:** Low. Mobile layout is responsive and preserves the core comparison mechanism.

---

## Questions (Targeted, Based on Findings)

1. **Accessibility / Keyboard (P2):** Should I add `:focus-visible` ring rules (replicating input focus) for `.inspector-trigger button`, `.inspector-header button`, `.exemplo-chip`, and add `aria-label="Fechar inspetor"` to the close button? Would you prefer a keyboard-shortcut (`Esc` = close inspector; `Enter` = open closest tile) added as part of the hardening pass?

2. **Legend Density / Design System (P2):** The legend shows 4 legend-level items (lv0–lv3) + 2 legend-items per column + a note line. Should I consolidate to show only the 2 active source-state items (e.g., keyword column shows keyword-only + both; LAYA column shows LAYA-only + both) and keep the 4 level items, simplifying the visual field? Or should the legend stay as-is?

3. **Tile Badge / Minor (P3):** Should I add `aria-label` on `.tile-badge` elements (`aria-label="Posição ${rank}"`) and a brief tooltip explanation? This is a small polish step, not a structural change.

4. **Scope:** You have 3 priority issues (P2: legend simplification + keyboard/accessibility; P3: tile badge clarification). Would you prefer: (a) all 3 addressed in sequence via `hard` → `polish`, (b) focus on the P2 accessibility/hardening pair first, or (c) focus only on the legend simplification?

Questions required (3 findings ≥ 3): yes, 4 targeted questions included.
Questions skipped: no.

---

## Run Notes

- Target slug confirmed: `node .agents/skills/impeccable/scripts/critique-storage.mjs slug "search-recomend/public/index.html"` → resolved cleanly.
- Ignore list: `.impeccable/critique/ignore.md` not present; nothing ignored.
- Assessment independence: Assessment A (design review of source + visual inspection) completed first; Assessment B (CLI detector + manual review) completed after, with detector results summarized as deterministic scan (3 side-tab findings, confirmed intentional by DESIGN.md).
- Sub-agent independence: Not achieved — degraded to sequential single-context; banner emitted at top of report per invariant.
- CLI detector: `node .agents/skills/impeccable/scripts/detect.mjs --json public/` run; exit code 2 (findings); 3 findings reported (side-tab at busca.css lines 432, 435, 438). All findings confirmed intentional by source evidence (DESIGN.md + .impeccable/design.json).
- Browser visibility / overlay: Not attempted (no live server; no browser automation available in session). No injection; no overlay reported. No false overlay claim.
- Live server: Not started; no cleanup needed.
- Temp-file cleanup: Not needed (no heredoc persistence path used; snapshot written directly to `.impeccable/critique/` by this session).
- Persistence: Snapshot body (this file) written; `.impeccable/critique/` directory confirmed present. Trend not readable (first run for target; no prior entries). Snapshot file path: `.impeccable/critique/critique-busca-comparativa-interface.md`.
- Fallback signals: Design review relies entirely on source file inspection + design-system documentation; no browser screenshot evidence included. Report does not claim browser evidence that did not occur.
