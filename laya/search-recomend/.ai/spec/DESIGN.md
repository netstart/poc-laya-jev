---
name: Busca que Entende
description: Local semantic search demo — 1970s catalog aesthetic, neobrutalist depth, side-by-side keyword vs LAYA comparison.
colors:
  paper: "#fdf6e3"
  cream: "#fffef5"
  ink: "#2a2218"
  muted: "#6b5e4f"
  accent: "#b85c38"
  accent2: "#2f5f4f"
  border: "#d6c9b1"
  hot: "#c9302c"
  ok: "#4a7c59"
  over: "#7a5c58"
typography:
  display:
    fontFamily: "Bricolage Grotesque, sans-serif"
    fontWeight: 700
    letterSpacing: "0.08em"
  body:
    fontFamily: "Figtree, system-ui, sans-serif"
    fontWeight: 400
rounded:
  none: "0px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  tile:
    backgroundColor: "#e8e3d6"
    border: "1px solid {colors.border}"
    padding: "8px"
  tile-lv3:
    backgroundColor: "#fad2a0"
    borderColor: "{colors.accent}"
  tile-badge:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.cream}"
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.cream}"
    padding: "14px 22px"
  card:
    backgroundColor: "{colors.cream}"
    border: "1px solid {colors.border}"
    shadow: "4px 4px 0 {colors.shadow}"
---

# Design System: Busca que Entende

## Overview

**Creative North Star: "1970s Department Catalog"**

A tactile, paper-driven interface that feels like flipping through a vintage department store catalog — warm cream surfaces, bold uppercase labels, and hard-offset shadows that give each card a physical presence on the page. The design treats the 120-product catalog as a literal shelf: square tiles, department groups, and a persistent sidebar grid keep the inventory visible at all times.

The visual language is neobrutalist: no rounded corners on cards, no soft glows, no glass. Depth comes from `4px 4px 0` offset shadows and 1px solid borders. Typography pairs Bricolage Grotesque (display, uppercase, tracked) with Figtree (body) for a contemporary take on editorial catalog design.

**Key Characteristics:**
- Warm paper palette with terracotta accent and forest green secondary
- Hard-offset shadows, never soft blur
- Square catalog tiles with level-based color grading (lv0–lv3)
- Side-by-side comparison columns with semantic source borders
- Persistent left catalog sidebar, mobile: stacked

## Colors

Warm, low-saturation paper tones with two strategic accents — terracotta for the primary action and forest green for the LAYA/semantic channel.

### Primary
- **Terracotta** (`#b85c38`): Primary button, focus rings, lv3 tile border, source-laya indicator
- **Forest** (`#2f5f4f`): Accents for the LAYA channel, secondary emphasis

### Neutral
- **Cream** (`#fdf6e3`): Page background (`--bg`)
- **Paper** (`#fffef5`): Card and surface backgrounds (`--paper`)
- **Ink** (`#2a2218`): Body text, tile badges
- **Muted** (`#6b5e4f`): Labels, subtitles, secondary text
- **Tan** (`#d6c9b1`): Borders, dividers

### Semantic
- **Hot** (`#c9302c`): Alerts, "nothing serves" state
- **OK** (`#4a7c59`): Items found in both searches (source-both border)
- **Over** (`#7a5c58`): Over-budget items in sidebar

### Named Rules
**The Source-Color Rule.** Border-left color on tiles is semantic, not decorative: green = found in both searches, blue = keyword-only, terracotta = LAYA-only. Removing these borders destroys the comparison mechanic.

**The Level-Heat Rule.** Tile background shifts from cool gray (lv0) through warm cream (lv1) to amber (lv2) and terracotta-accented (lv3) — higher score = warmer surface. Never invert: lv0 must be the coolest, lv3 the warmest.

## Typography

**Display Font:** Bricolage Grotesque (weight 700, uppercase, letter-spacing 0.08–0.18em)
**Body Font:** Figtree (weight 400, system-ui fallback)

**Character:** Editorial and authoritative — the labels feel like a catalog index, not a app UI. Headlines are tracked and uppercase; body text is compact and warm.

### Hierarchy
- **Display** (700, clamp(32px, 6vw, 56px), ~1): Hero title, capa headline
- **Title** (700, 13px uppercase, 0.08em): Column headers, card titles, inspector sections
- **Body** (400, 12–16px, 1.3–1.5): Tile names, descriptions, inspector content
- **Label** (400, 10–12px, 0.15em uppercase): Subtitles, legend text, category groups

### Named Rules
**The Catalog Label Rule.** Every uppercase tracked label is a catalog artifact — selo, exemplos-label, categoria-title, contador-titulo. Keep them short (1–2 words) and always uppercase with letter-spacing.

## Layout

Fixed left sidebar (260px) with the catalog organized by department. Main content flows beside it with a 260px offset. The comparison view uses a 2-column grid (1fr 1fr) with 24px gap. Tiles use `auto-fill, minmax(110px, 1fr)` responsive grid. Mobile collapses sidebar to top, single column.

**Spacing rhythm:** 8px base unit. Cards pad 14–18px. Sections separate by 18–24px. The sidebar gutters at 16px.

## Elevation & Depth

**Neobrutalist hard shadow.** Every card uses `box-shadow: 4px 4px 0 rgba(42,34,24,0.08)` — a deliberate zero-blur offset that reads as physical lift. No soft glows, no layered shadows. Depth is binary: a surface either has the shadow or it doesn't.

### Shadow Vocabulary
- **Card** (`4px 4px 0 rgba(42,34,24,0.08)`): All cards, contadores, colunas, inspector
- **None**: Tiles, sidebar items, chips — flat by default

### Named Rules
**The Hard Shadow Rule.** The 4px offset shadow is the system's depth language. Soft blur shadows would read as generic/material and break the catalog identity. Zero-offset colored halos are decoration — banned.

## Shapes

**Zero border-radius everywhere.** Cards, buttons, tiles, inputs — all `border-radius: 0`. This is the neobrutalist signature. The only rounding is implicit in the square tile aspect-ratio (1:1).

**Borders:** 1px solid `#d6c9b1` on cards and tiles; 2px solid on sidebar, header bands, and mobile catalog.

## Components

### Result Tile
- **Shape:** 1:1 aspect-ratio, `border-radius: 0`, 1px solid border
- **Background:** lv0 `#e8e3d6`, lv1 `#f5edd8`, lv2 `#fbe8c8`, lv3 `#fad2a0` + accent border
- **Content:** id (11px muted), name (12px, -webkit-line-clamp 3), price (13px bold)
- **Badge:** Top-right corner, 22×22px, ink background, cream text, 1–5 ranking number
- **Source border:** Left 3px — OK green / keyword blue / terracotta (semantic, not decorative)

### Stat Card (Contador)
- **Shape:** Paper background, 1px solid border, hard shadow
- **Content:** Uppercase label (13px muted), large number (34px bold), sublabel (13px)

### Column (Comparativa)
- **Shape:** Paper background, 1px solid border, hard shadow, 16px padding
- **Header:** Uppercase title + subtitle, bottom border separator
- **Legend:** Inline flex, wrap, 11px uppercase — source swatches + level swatches

### Catalog Sidebar
- **Shape:** Fixed 260px left, 100vh, right border 2px
- **Category groups:** Uppercase 10px labels, dashed bottom border
- **Mobile:** Relative position, auto height, border-bottom instead of right

### Buttons
- **Primary:** Accent background, cream text, uppercase, 14px padding, no radius
- **Hover:** Darken accent by ~10%
- **Trigger:** Paper background, border, uppercase, cursor pointer

### Inspector / Payload
- **Shape:** Paper background, 1px border, no radius
- **Header:** Flex space-between, uppercase
- **Pre blocks:** `#f4efe3` background, 1px border, 10–12px monospace

### Example Chips
- **Shape:** Paper background, 1px border, 8px padding, gap 6px
- **Hover:** Border shifts to accent

## Do's and Don'ts

### Do:
- **Do** preserve the 2-column comparison layout — it is the product's core mechanic
- **Do** keep the sidebar catalog visible at all times; it contextualizes every search
- **Do** use the source-border colors (OK/blue/terracotta) consistently on tiles in both columns
- **Do** maintain the hard 4px shadow vocabulary across all cards
- **Do** use Bricolage Grotesque for all uppercase labels and the hero title

### Don't:
- **Don't** introduce rounded corners on cards or buttons — zero radius is the identity
- **Don't** replace the hard offset shadow with soft blur or layered shadows
- **Don't** add gradient text, glass effects, or backdrop-filter decoration
- **Don't** use emoji as icon substitutes — the system uses text labels and semantic colors
- **Don't** hide the catalog sidebar on desktop — it's always open (`catalog-open` class)
- **Don't** invent "AI glow" effects or soft blue tints on LAYA results — the system is paper-and-ink
