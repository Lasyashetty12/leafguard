# LeafGuard design system

Generated with the reference skill **ui-ux-pro-max-skill** (`--design-system`, query: *agriculture crop health AI
diagnosis tool farmers trust*), then adapted for Streamlit and for Kannada / Hindi users.

| Token | Value | Use |
|---|---|---|
| Style | **Organic Biophilic** | nature, rounded, calm, trustworthy |
| Primary | `#15803D` earth green | buttons, toggles, links, brand |
| Accent | `#A16207` harvest gold | small labels (eyebrows) |
| Background | `#F0FDF4` mint | page |
| Text | `#14532D` deep green | body text (contrast > 9:1) |
| Border | `#BBF7D0` | cards, inputs |
| Fonts | **Lora** headings, **Raleway** body, Noto Sans Kannada / Devanagari fallbacks | |
| Radius | 16–20px cards, 12px buttons | |
| Motion | subtle 350ms fade, off for `prefers-reduced-motion` | |

## Status language: never colour-only

Every answer = **icon + word + colour** (WCAG "use of colour"):

| Answer | Icon | Colours |
|---|---|---|
| No disease found | leaf | green |
| Disease detected | warning triangle | orange |
| Not sure | question mark | yellow |
| Retake photo | camera | blue |
| Not a leaf | no-entry sign | pink |

## Checklist applied (from the skill's pre-delivery checklist)

- [x] No emojis as icons: Lucide SVG icons inline (work offline), Material icons in Streamlit widgets
- [x] Pointer cursor and 150–300ms hover transitions on clickable elements
- [x] Text contrast ≥ 4.5:1 (status colours ≥ 7:1)
- [x] Visible keyboard focus ring
- [x] `prefers-reduced-motion` respected
- [x] Touch targets ≥ 44px with ≥ 8px gaps (phones in the field)
- [x] Progress indicator: the 5-stage step bar shows where LeafGuard stopped and why
- [x] Every refusal gives a recovery step (retake tips, call Kisan Call Centre)
- [x] Responsive: checked at 1440px desktop and 390px phone

## Files

- `.streamlit/config.toml`: theme (colours, fonts, radius)
- `leafguard_plus/ui.py`: tokens, CSS, icons, and components (verdict card, raw-model card, step bar, checks list, stat tiles, chips, sidebar navigation)
- `backup/`: the previous look (`app_v1.py`, `pages_v1/`, `leafguard_plus_v1/`). To go back, copy `backup/app_v1.py` over `app.py` and delete `.streamlit/config.toml`.
