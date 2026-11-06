"""LeafGuard design system - "Organic Biophilic" (generated with ui-ux-pro-max-skill).

Rules followed (from the skill's UX guidelines and pre-delivery checklist):
  * status is never colour-only: every status = icon + word + colour
  * SVG icons (Lucide, inline so they work offline), no emojis as icons
  * text contrast >= 4.5:1, visible keyboard focus, 44px+ touch targets, 8px+ gaps
  * every refusal comes with a recovery step; multi-step work shows progress
  * subtle motion only, switched off for prefers-reduced-motion
"""
import html

import streamlit as st

# ---------------------------------------------------------------- tokens
C = {
    "primary": "#15803D", "on_primary": "#FFFFFF", "secondary": "#22C55E", "accent": "#A16207",
    "bg": "#F0FDF4", "fg": "#14532D", "card": "#FFFFFF", "muted": "#E8F0F1", "muted_fg": "#475569",
    "border": "#BBF7D0", "destructive": "#DC2626",
}

# status -> (word, icon, background, foreground, border). Contrast fg/bg >= 7:1 for all.
STATUS = {
    "HEALTHY": ("No disease found", "leaf", "#DCFCE7", "#14532D", "#86EFAC"),
    "DISEASED": ("Disease detected", "alert", "#FFF7ED", "#9A3412", "#FDBA74"),
    "UNCERTAIN": ("Not sure", "help", "#FEF9C3", "#854D0E", "#FDE047"),
    "RETAKE": ("Retake photo", "camera", "#E0F2FE", "#075985", "#7DD3FC"),
    "NOT_A_LEAF": ("Not a leaf", "ban", "#FCE7F3", "#9D174D", "#F9A8D4"),
}
TONES = {  # generic chips / tiles
    "good": ("#DCFCE7", "#14532D"), "warn": ("#FEF9C3", "#854D0E"), "bad": ("#FEE2E2", "#991B1B"),
    "info": ("#E0F2FE", "#075985"), "neutral": ("#F1F5F9", "#334155"), "brand": ("#15803D", "#FFFFFF"),
}

# ---------------------------------------------------------------- icons (Lucide, ISC licence)
_P = {
    "leaf": '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>'
            '<path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/>'
             '<path d="M12 9v4"/><path d="M12 17h.01"/>',
    "help": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    "camera": '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>'
              '<circle cx="12" cy="13" r="3"/>',
    "ban": '<circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "check_circle": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "x_circle": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 '
              '4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "cpu": '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/>'
           '<path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/>'
           '<path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>',
    "scan": '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/>'
            '<path d="M7 21H5a2 2 0 0 1-2-2v-2"/><circle cx="12" cy="12" r="3"/>',
    "gavel": '<path d="m14.5 12.5-8 8a2.12 2.12 0 1 1-3-3l8-8"/><path d="m16 16 6-6"/><path d="m8 8 6-6"/>'
             '<path d="m9 7 8 8"/><path d="m21 11-8-8"/>',
    "repeat": '<path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/>'
              '<path d="M21 13v1a4 4 0 0 1-4 4H3"/>',
    "flask": '<path d="M10 2v7.53a2 2 0 0 1-.21.9L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.07-10.12'
             'A2 2 0 0 1 14 9.53V2"/><path d="M8.5 2h7"/><path d="M7 16h10"/>',
    "gauge": '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    "volume": '<path d="M11 4.7a.7.7 0 0 0-1.2-.5L6.41 7.59A1.4 1.4 0 0 1 5.42 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.42'
              'a1.4 1.4 0 0 1 1 .41l3.38 3.38a.7.7 0 0 0 1.2-.5z"/><path d="M16 9a5 5 0 0 1 0 6"/>'
              '<path d="M19.36 18.36a9 9 0 0 0 0-12.72"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "video": '<path d="m16 13 5.22 3.48a.5.5 0 0 0 .78-.42V7.87a.5.5 0 0 0-.75-.43L16 10.5"/>'
             '<rect x="2" y="6" width="14" height="12" rx="2"/>',
    "phone": '<path d="M13.83 16.57a1 1 0 0 0 1.21-.3l.36-.47A2 2 0 0 1 17 15h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2A18 18 0 '
             '0 1 2 4a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v3a2 2 0 0 1-.8 1.6l-.47.35a1 1 0 0 0-.29 1.23 14 14 0 0 0 6.39 6.39"/>',
    "eye": '<path d="M2.06 12.35a1 1 0 0 1 0-.7 10.75 10.75 0 0 1 19.88 0 1 1 0 0 1 0 .7 10.75 10.75 0 0 1-19.88 0"/>'
           '<circle cx="12" cy="12" r="3"/>',
    "user": '<circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 0 0-16 0"/>',
    "dot": '<circle cx="12" cy="12" r="4" fill="currentColor"/>',
    "minus": '<path d="M5 12h14"/>',
    "chevron_up": '<path d="m18 15-6-6-6 6"/>',
    "sparkle": '<path d="M9.94 14.06 2 22"/><path d="m15 2 1.5 3.5L20 7l-3.5 1.5L15 12l-1.5-3.5L10 7l3.5-1.5z"/>',
}


def icon(name, size=20, color="currentColor", stroke=2.0, label=None):
    """Inline SVG icon. Decorative unless a label is given (then it is announced to screen readers)."""
    aria = f'role="img" aria-label="{html.escape(label)}"' if label else 'aria-hidden="true"'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" '
            f'class="lg-ico" {aria}>{_P[name]}</svg>')


# ---------------------------------------------------------------- global CSS
CSS = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Kannada:wght@400;600&family=Noto+Sans+Devanagari:wght@400;600&display=swap');
.lg-verdict, .lg-card, .lg-head, .lg-steps, .lg-chip, .lg-stat {{
  font-family: Raleway, 'Noto Sans Kannada', 'Noto Sans Devanagari', 'Nirmala UI', sans-serif; }}
:root {{ --lg-primary:{C['primary']}; --lg-fg:{C['fg']}; --lg-muted:{C['muted_fg']}; --lg-border:{C['border']};
         --lg-card:{C['card']}; --lg-accent:{C['accent']}; }}
html, body, [class*="st-"] {{ font-variant-numeric: lining-nums tabular-nums; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1240px; }}
h1, h2, h3 {{ letter-spacing: -0.01em; }}
.lg-ico {{ flex: none; vertical-align: middle; }}
.lg-muted {{ color: var(--lg-muted); }}

/* header */
.lg-head {{ display:flex; gap:16px; align-items:center; margin: 0 0 18px 0; }}
.lg-head .badge {{ width:52px; height:52px; border-radius:16px; background:var(--lg-primary); color:#fff;
                   display:flex; align-items:center; justify-content:center; box-shadow:0 8px 20px -10px rgba(21,128,61,.6); }}
.lg-head h1 {{ font-family: Lora, 'Noto Sans Kannada', 'Noto Sans Devanagari', serif; font-size: 2rem; margin:0; padding:0;
               color:var(--lg-fg); line-height:1.15; }}
.lg-head p {{ margin:2px 0 0 0; color:var(--lg-muted); font-size:1rem; }}
.lg-eyebrow {{ text-transform:uppercase; letter-spacing:.08em; font-size:.72rem; font-weight:700; color:var(--lg-accent); }}

/* cards */
.lg-card {{ background:var(--lg-card); border:1px solid var(--lg-border); border-radius:20px; padding:18px 20px;
            box-shadow: 0 1px 2px rgba(20,83,45,.05), 0 10px 28px -18px rgba(20,83,45,.30); margin-bottom: 12px; }}
.lg-card h3 {{ margin:0 0 8px 0 !important; padding:0 !important; font-size:1.05rem; display:flex; gap:8px; align-items:center; flex-wrap:wrap; }}
.lg-verdict {{ border-radius:20px; padding:18px 20px; border:1.5px solid; margin-bottom:12px; }}
.lg-verdict .row {{ display:flex; gap:14px; align-items:flex-start; }}
.lg-verdict .ib {{ width:48px; height:48px; border-radius:14px; display:flex; align-items:center; justify-content:center;
                   background:rgba(255,255,255,.75); flex:none; }}
.lg-verdict .title {{ font-family: Lora, 'Noto Sans Kannada', 'Noto Sans Devanagari', serif; font-size:1.45rem;
                      font-weight:600; line-height:1.25; margin:2px 0 4px 0; }}
.lg-verdict ul {{ margin:10px 0 0 0; padding-left: 0; list-style:none; }}
.lg-verdict li {{ display:flex; gap:8px; align-items:flex-start; margin:6px 0; line-height:1.45; }}
.lg-verdict li .lg-ico {{ margin-top:2px; }}
.lg-raw {{ background:#F8FAFC; border:1.5px dashed #94A3B8; color:#334155; }}

/* chips */
.lg-chip {{ display:inline-flex; align-items:center; gap:6px; padding:4px 10px; border-radius:999px; font-weight:700;
            font-size:.78rem; letter-spacing:.02em; white-space:nowrap; }}

/* checks list */
.lg-checks {{ list-style:none; margin:0; padding:0; }}
.lg-checks li {{ display:flex; align-items:center; gap:10px; padding:9px 0; border-bottom:1px solid #ECFDF5; }}
.lg-checks li:last-child {{ border-bottom:0; }}
.lg-checks .nm {{ font-weight:600; flex:1; min-width:0; font-size:.95rem; line-height:1.3; }}
.lg-checks .val {{ display:block; color:var(--lg-muted); font-weight:400; font-size:.8rem; margin-top:1px; }}

/* pipeline steps (progress indicator) */
.lg-steps {{ display:flex; gap:8px; flex-wrap:wrap; margin: 4px 0 16px 0; }}
.lg-step {{ flex:1 1 140px; display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:14px;
            border:1px solid var(--lg-border); background:#fff; min-height:48px; }}
.lg-step .n {{ width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center;
               font-weight:700; font-size:.8rem; flex:none; }}
.lg-step .t {{ font-weight:600; font-size:.88rem; line-height:1.2; }}
.lg-step .s {{ font-size:.75rem; color:var(--lg-muted); }}
.lg-step.done .n {{ background:#DCFCE7; color:#14532D; }}
.lg-step.stop {{ border-color:#FCA5A5; background:#FEF2F2; }} .lg-step.stop .n {{ background:#FEE2E2; color:#991B1B; }}
.lg-step.warn {{ border-color:#FDE047; background:#FEFCE8; }} .lg-step.warn .n {{ background:#FEF9C3; color:#854D0E; }}
.lg-step.todo {{ opacity:.55; }} .lg-step.todo .n {{ background:#F1F5F9; color:#475569; }}

/* stat tiles */
.lg-stat {{ border-radius:18px; padding:14px 16px; border:1px solid var(--lg-border); background:#fff; height:100%; }}
.lg-stat .v {{ font-family: Lora, serif; font-size:2.1rem; font-weight:700; line-height:1.1; }}
.lg-stat .l {{ color:var(--lg-muted); font-size:.85rem; margin-top:4px; }}

/* images, buttons, focus, motion */
[data-testid="stImage"] img {{ border-radius:14px; }}
[data-testid="stImageCaption"], [data-testid="caption"] {{ color: var(--lg-muted) !important; }}
.stButton button, .stDownloadButton button {{ min-height:44px; font-weight:600; transition: transform .15s ease, box-shadow .2s ease; }}
.stButton button:hover, .stDownloadButton button:hover {{ transform: translateY(-1px); box-shadow:0 6px 16px -8px rgba(21,128,61,.5); }}
button, [role="tab"], [role="radio"], a, label {{ cursor:pointer; }}
*:focus-visible {{ outline: 3px solid #15803D !important; outline-offset: 2px; }}
[data-baseweb="tab-list"] {{ gap: 6px; }}
[data-baseweb="tab"] {{ min-height:44px; }}
.lg-fade {{ animation: lgfade .35s ease-out both; }}
@keyframes lgfade {{ from {{ opacity:0; transform: translateY(8px); }} to {{ opacity:1; transform:none; }} }}
@media (prefers-reduced-motion: reduce) {{ *, *::before, *::after {{ animation:none !important; transition:none !important; }} }}
@media (max-width: 640px) {{ .lg-head h1 {{ font-size:1.6rem; }} .lg-verdict .title {{ font-size:1.25rem; }} }}

/* sidebar brand */
.lg-brand {{ display:flex; gap:10px; align-items:center; margin: 4px 0 6px 0; }}
.lg-brand .b {{ width:38px; height:38px; border-radius:12px; background:var(--lg-primary); color:#fff;
                display:flex; align-items:center; justify-content:center; }}
.lg-brand .n {{ font-family: Lora, serif; font-weight:700; font-size:1.25rem; color:var(--lg-fg); }}
.lg-brand .t {{ font-size:.75rem; color:var(--lg-muted); }}
</style>"""

# ---------------------------------------------------------------- motion layer
# Pure CSS: scroll-driven animations (no JavaScript), hover states, entrance animations.
# Everything is switched off for people who set "reduce motion" in their OS.
MOTION_CSS = """<style>
/* ---- long widget labels wrap instead of being cut off with "..." ---- */
[data-testid="stCheckbox"] label, [data-testid="stCheckbox"] label *, [data-testid="stRadio"] label * {
  white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }
[data-testid="stCheckbox"] label { align-items:flex-start; padding: 6px 0; }
/* ---- page atmosphere ---- */
[data-testid="stApp"] {
  background-image:
    radial-gradient(1200px 500px at 8% -10%, rgba(34,197,94,.13), transparent 60%),
    radial-gradient(900px 420px at 100% 0%, rgba(161,98,7,.07), transparent 55%);
  background-attachment: fixed;
}
::selection { background:#BBF7D0; color:#14532D; }
[data-testid="stMain"] { scroll-behavior:smooth; scroll-timeline: --lgpage block; scrollbar-color:#86EFAC transparent; }
[data-testid="stMain"]::-webkit-scrollbar { width:10px; }
[data-testid="stMain"]::-webkit-scrollbar-thumb { background:#86EFAC; border-radius:10px; border:2px solid #F0FDF4; }

/* ---- reading progress bar + back-to-top (driven by the page scroll) ---- */
.lg-scrollbar { position:fixed; top:0; left:0; right:0; height:4px; z-index:1000000; transform-origin:0 50%;
  background:linear-gradient(90deg,#15803D,#22C55E,#A16207); transform:scaleX(0); pointer-events:none; }
.lg-totop { position:fixed; right:22px; bottom:22px; z-index:999999; width:48px; height:48px; border-radius:16px;
  display:flex; align-items:center; justify-content:center; background:#15803D; color:#fff !important;
  box-shadow:0 10px 24px -10px rgba(21,128,61,.7); text-decoration:none !important; opacity:0; pointer-events:none;
  transition: transform .2s ease, background .2s ease; }
.lg-totop:hover { transform: translateY(-3px); background:#166534; }
@supports (animation-timeline: scroll()) {
  .lg-scrollbar { animation: lgprog linear both; animation-timeline: --lgpage; }
  .lg-totop { animation: lgshow linear both; animation-timeline: --lgpage; animation-range: 0px 400px; }
}
@keyframes lgprog { to { transform:scaleX(1); } }
@keyframes lgshow { 0%,60% { opacity:0; pointer-events:none; transform:translateY(12px); }
                    100% { opacity:1; pointer-events:auto; transform:none; } }

/* ---- scroll reveal: cards, tiles and photos slide in as they enter the screen ---- */
@supports (animation-timeline: view()) {
  .lg-card, .lg-stat, .lg-feature, [data-testid="stImage"], [data-testid="stVegaLiteChart"], [data-testid="stDataFrame"] {
    animation: lgreveal linear both; animation-timeline: view(); animation-range: entry 0% entry 70%; }
}
@keyframes lgreveal { from { opacity:0; transform: translateY(28px) scale(.98); } to { opacity:1; transform:none; } }

/* ---- hover: lift, glow, zoom ---- */
.lg-card, .lg-stat, .lg-feature, .lg-step { transition: transform .25s cubic-bezier(.2,.8,.2,1), box-shadow .25s ease, border-color .25s ease; }
.lg-card:hover, .lg-stat:hover, .lg-feature:hover { transform: translateY(-4px);
  box-shadow: 0 2px 4px rgba(20,83,45,.06), 0 18px 36px -18px rgba(20,83,45,.45); border-color:#4ADE80; }
.lg-step:hover { transform: translateY(-2px); box-shadow:0 10px 22px -16px rgba(20,83,45,.5); }
.lg-verdict { transition: transform .25s ease, box-shadow .25s ease; }
.lg-verdict:hover { transform: translateY(-2px); box-shadow: 0 16px 32px -20px rgba(0,0,0,.35); }
.lg-chip { transition: transform .15s ease, box-shadow .15s ease; }
.lg-chip:hover { transform: translateY(-1px); box-shadow: 0 4px 10px -6px rgba(0,0,0,.35); }
[data-testid="stImage"] { border-radius:14px; overflow:hidden; }
[data-testid="stImage"] img { transition: transform .45s cubic-bezier(.2,.8,.2,1), filter .3s ease; }
[data-testid="stImage"]:hover img { transform: scale(1.04); filter: saturate(1.08); }
.lg-checks li { transition: background .15s ease, padding .15s ease; border-radius:10px; }
.lg-checks li:hover { background:#F0FDF4; padding-left:8px; padding-right:8px; }

/* buttons: light sweep on the primary action */
[data-testid="stBaseButton-primary"] { position:relative; overflow:hidden; }
[data-testid="stBaseButton-primary"]::after { content:""; position:absolute; inset:0; transform:translateX(-120%);
  background:linear-gradient(110deg, transparent 30%, rgba(255,255,255,.35) 50%, transparent 70%); transition: transform .7s ease; }
[data-testid="stBaseButton-primary"]:hover::after { transform:translateX(120%); }
[data-testid="stBaseButton-secondary"]:hover { border-color:#15803D !important; color:#15803D !important; background:#F0FDF4 !important; }

/* sidebar links, tabs, uploader, expanders */
[data-testid="stSidebar"] a { transition: transform .18s ease, background .18s ease; border-radius:10px; }
[data-testid="stSidebar"] a:hover { transform: translateX(4px); background:#DCFCE7 !important; }
[data-baseweb="tab"] { border-radius:10px 10px 0 0; transition: background .18s ease; padding: 0 10px !important; }
[data-baseweb="tab"]:hover { background:#DCFCE7; }
[data-testid="stFileUploaderDropzone"] { border:2px dashed #86EFAC !important; background:#FFFFFF !important;
  transition: border-color .2s ease, background .2s ease, transform .2s ease; }
[data-testid="stFileUploaderDropzone"]:hover { border-color:#15803D !important; background:#F0FDF4 !important; transform: scale(1.005); }
[data-testid="stExpander"] details { transition: box-shadow .2s ease, border-color .2s ease; }
[data-testid="stExpander"] details:hover { border-color:#4ADE80; box-shadow:0 8px 20px -16px rgba(20,83,45,.5); }

/* ---- header: floating badge and drifting leaves ---- */
.lg-head { position:relative; }
.lg-head .badge { animation: lgfloat 5s ease-in-out infinite; background: linear-gradient(135deg,#15803D,#22C55E 60%,#15803D);
  background-size:200% 200%; }
@keyframes lgfloat { 0%,100% { transform: translateY(0); background-position:0% 50%; }
                     50% { transform: translateY(-4px); background-position:100% 50%; } }
.lg-leaves { position:absolute; inset:-10px 0 auto auto; width:260px; height:90px; pointer-events:none; opacity:.55; }
.lg-leaves svg { position:absolute; animation: lgdrift 9s ease-in-out infinite; }
.lg-leaves svg:nth-child(1) { right:30px; top:4px; }
.lg-leaves svg:nth-child(2) { right:120px; top:36px; animation-duration:11s; animation-delay:-3s; }
.lg-leaves svg:nth-child(3) { right:200px; top:8px; animation-duration:13s; animation-delay:-6s; }
@keyframes lgdrift { 0%,100% { transform: translate(0,0) rotate(0deg); } 50% { transform: translate(-10px,8px) rotate(18deg); } }
@media (max-width: 760px) { .lg-leaves { display:none; } }

/* ---- staged entrance: safety stages light up one after another ---- */
.lg-steps .lg-step { animation: lgstep .5s cubic-bezier(.2,.8,.2,1) both; animation-delay: calc(var(--i, 0) * 140ms); }
@keyframes lgstep { from { opacity:0; transform: translateY(10px) scale(.96); } to { opacity:1; transform:none; } }
.lg-step.stop .n { animation: lgstep .5s both, lgring 1.6s ease-out 1 calc(var(--i,0) * 140ms + 400ms); }
@keyframes lgring { 0% { box-shadow: 0 0 0 0 rgba(220,38,38,.45); } 100% { box-shadow: 0 0 0 14px rgba(220,38,38,0); } }

/* check marks draw themselves */
.lg-draw path, .lg-draw circle { stroke-dasharray: 70; stroke-dashoffset: 70;
  animation: lgdrawin .7s ease-out forwards; animation-delay: calc(var(--d, 0) * 90ms + 200ms); }
@keyframes lgdrawin { to { stroke-dashoffset: 0; } }
.lg-checks li { animation: lgfade .4s ease-out both; animation-delay: calc(var(--d, 0) * 70ms); }

/* ---- verdict icon personality ---- */
.lg-verdict { animation: lgpop .5s cubic-bezier(.2,1.2,.3,1) both; }
@keyframes lgpop { from { opacity:0; transform: translateY(10px) scale(.97); } to { opacity:1; transform:none; } }
.lg-v-healthy .ib { animation: lgbreathe 3.2s ease-in-out infinite; }
@keyframes lgbreathe { 0%,100% { box-shadow:0 0 0 0 rgba(21,128,61,.0); } 50% { box-shadow:0 0 0 8px rgba(21,128,61,.12); } }
.lg-v-diseased .ib { animation: lgpulse 1.8s ease-out 3; }
@keyframes lgpulse { 0% { box-shadow:0 0 0 0 rgba(234,88,12,.45); } 100% { box-shadow:0 0 0 16px rgba(234,88,12,0); } }
.lg-v-uncertain .ib svg { animation: lgwobble 1.2s ease-in-out 2; transform-origin:50% 60%; }
@keyframes lgwobble { 0%,100% { transform: rotate(0); } 25% { transform: rotate(-12deg); } 75% { transform: rotate(12deg); } }
.lg-v-not_a_leaf .ib { animation: lgshake .5s ease-in-out 2; }
@keyframes lgshake { 0%,100% { transform: translateX(0); } 25% { transform: translateX(-4px); } 75% { transform: translateX(4px); } }
.lg-v-retake .ib svg { animation: lgflash 1.4s ease-in-out 2; }
@keyframes lgflash { 0%,100% { opacity:1; } 50% { opacity:.35; } }

/* ---- numbers count up ---- */
@property --lgn { syntax: '<integer>'; initial-value: 0; inherits: false; }
.lg-count { --lgn: var(--to); counter-reset: lgn var(--lgn); animation: lgcount 1.3s cubic-bezier(.2,.8,.2,1); }
.lg-count::after { content: counter(lgn); }
@keyframes lgcount { from { --lgn: 0; } }

/* ---- feature strip on the start screen ---- */
.lg-features { display:grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); gap:12px; margin: 6px 0 16px 0; }
.lg-feature { background:#fff; border:1px solid #BBF7D0; border-radius:18px; padding:16px; position:relative; overflow:hidden; }
.lg-feature .fi { width:40px; height:40px; border-radius:12px; display:flex; align-items:center; justify-content:center;
  background:#DCFCE7; color:#15803D; margin-bottom:10px; transition: transform .3s cubic-bezier(.2,1.4,.3,1); }
.lg-feature:hover .fi { transform: rotate(-8deg) scale(1.1); }
.lg-feature b { display:block; font-family: Lora, serif; font-size:1.05rem; margin-bottom:4px; color:#14532D; }
.lg-feature span { color:#475569; font-size:.9rem; line-height:1.45; }
.lg-feature::before { content:""; position:absolute; inset:auto -40px -40px auto; width:110px; height:110px; border-radius:50%;
  background: radial-gradient(circle, rgba(34,197,94,.16), transparent 70%); transition: transform .4s ease; }
.lg-feature:hover::before { transform: scale(1.6); }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation:none !important; transition:none !important; scroll-behavior:auto !important; }
  .lg-totop { opacity:1; pointer-events:auto; }
  .lg-draw path, .lg-draw circle { stroke-dashoffset: 0; }
}
</style>"""

_LEAF_SVG = ('<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="#15803D" stroke-width="1.6" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + _P["leaf"] + '</svg>')


def _no_blank_lines(css):
    # Streamlit's Markdown ends an HTML block at a blank line, which would drop the rest of the <style>
    return "\n".join(line for line in css.splitlines() if line.strip())


def apply():
    # one single <style> block: Streamlit keeps only the first <style> in a Markdown element
    css = CSS.replace("</style>", "") + MOTION_CSS.replace("<style>", "")
    st.markdown(_no_blank_lines(css) + "<div id='lg-top'></div><div class='lg-scrollbar' aria-hidden='true'></div>"
                f"<a class='lg-totop' href='#lg-top' aria-label='Back to top'>{icon('chevron_up', 22, '#fff', 2.6)}</a>",
                unsafe_allow_html=True)


def sidebar():
    """Brand + navigation (with icons) at the top of the sidebar, on every page."""
    with st.sidebar:
        st.markdown(f"<div class='lg-brand'><div class='b'>{icon('shield', 22, '#fff')}</div>"
                    f"<div><div class='n'>LeafGuard</div><div class='t'>Knows when it doesn't know</div></div></div>",
                    unsafe_allow_html=True)
        for path, label, ic in [("app.py", "Diagnose", ":material/eco:"),
                                ("pages/1_Deep_Check.py", "Deep Check", ":material/biotech:"),
                                ("pages/2_Fool_Me_Arena.py", "Fool Me Arena", ":material/target:"),
                                ("pages/3_Live_Camera.py", "Live Camera", ":material/videocam:"),
                                ("pages/4_Treatment_Plan.py", "Treatment Plan", ":material/healing:"),
                                ("pages/5_Field_Scan.py", "Field Scan", ":material/grid_view:"),
                                ("pages/6_Field_Diary.py", "Field Diary", ":material/menu_book:")]:
            try:
                st.page_link(path, label=label, icon=ic)
            except Exception:  # e.g. when a page is run on its own
                pass
        st.divider()


# ---------------------------------------------------------------- components
def header(title, subtitle, ic="leaf", eyebrow=None):
    eb = f"<div class='lg-eyebrow'>{html.escape(eyebrow)}</div>" if eyebrow else ""
    leaves = "<div class='lg-leaves' aria-hidden='true'>" + "".join(_LEAF_SVG.format(s=sz) for sz in (34, 24, 18)) + "</div>"
    st.markdown(f"<div class='lg-head'>{leaves}<div class='badge'>{icon(ic, 26, '#fff')}</div>"
                f"<div>{eb}<h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div></div>",
                unsafe_allow_html=True)


def chip(text, tone="neutral", ic=None):
    bg, fg = TONES[tone]
    i = icon(ic, 14, fg, 2.4) if ic else ""
    return f"<span class='lg-chip' style='background:{bg};color:{fg}'>{i}{html.escape(text)}</span>"


def status_chip(verdict):
    word, ic, bg, fg, _ = STATUS[verdict]
    return f"<span class='lg-chip' style='background:{bg};color:{fg};border:1px solid {fg}33'>{icon(ic, 14, fg, 2.4)}{word}</span>"


def verdict_card(verdict, headline, lines=(), label="LeafGuard says", footnotes=(), raw_html_lines=False):
    """Main result card: icon + status word + colour + headline + next steps."""
    word, ic, bg, fg, border = STATUS[verdict]
    esc = (lambda x: x) if raw_html_lines else html.escape
    items = "".join(f"<li>{icon('check' if verdict in ('HEALTHY', 'DISEASED') else 'dot', 16, fg, 2.4)}"
                    f"<span>{esc(x)}</span></li>" for x in lines)
    notes = "".join(f"<div class='lg-muted' style='font-size:.85rem;margin-top:6px'>{html.escape(n)}</div>"
                    for n in footnotes)
    st.markdown(
        f"<div class='lg-verdict lg-fade' role='status' aria-live='polite' "
        f"style='background:{bg};color:{fg};border-color:{border}'>"
        f"<div class='row lg-v-{verdict.lower()}'><div class='ib'>{icon(ic, 26, fg, 2.2)}</div><div style='flex:1'>"
        f"<div style='display:flex;gap:8px;align-items:center;flex-wrap:wrap'>"
        f"<span class='lg-eyebrow' style='color:{fg}'>{html.escape(label)}</span>{status_chip(verdict)}</div>"
        f"<div class='title'>{html.escape(headline)}</div></div></div>"
        f"<ul>{items}</ul>{notes}</div>", unsafe_allow_html=True)


def raw_card(answer, detail, note="Answers every photo, even a mug or a blurry shot."):
    st.markdown(
        f"<div class='lg-verdict lg-raw'><div class='row'><div class='ib' style='background:#E2E8F0'>"
        f"{icon('cpu', 26, '#334155', 2.2)}</div><div style='flex:1'>"
        f"<span class='lg-eyebrow' style='color:#475569'>Raw model, no safety layer</span>"
        f"<div class='title' style='color:#1E293B'>{html.escape(answer)}</div>"
        f"<div style='color:#334155'>{html.escape(detail)}</div>"
        f"<div class='lg-muted' style='font-size:.85rem;margin-top:6px'>{html.escape(note)}</div></div></div></div>",
        unsafe_allow_html=True)


def checks_list(checks, title="Safety checks"):
    rows = ""
    for k, c in enumerate(checks):
        ok = c["passed"]
        ic = icon("check_circle" if ok else "x_circle", 20, "#15803D" if ok else "#B91C1C", 2.2,
                  label="passed" if ok else "failed").replace("class='lg-ico'", "class='lg-ico lg-draw'").replace(
                  'class="lg-ico"', 'class="lg-ico lg-draw"')
        rows += (f"<li style='--d:{k}'>{ic}<span class='nm'>{html.escape(c['name'])}"
                 f"<span class='val'>{html.escape(str(c['value']))}</span></span></li>")
    st.markdown(f"<div class='lg-card'><h3>{html.escape(title)}</h3><ul class='lg-checks'>{rows}</ul></div>",
                unsafe_allow_html=True)


STAGES = [("Photo quality", "camera"), ("Is it a leaf?", "leaf"), ("Find the leaf", "scan"),
          ("Disease check", "cpu"), ("Decision", "gavel")]


def pipeline_steps(result):
    """Progress indicator: which safety stage passed, where LeafGuard stopped, and why."""
    checks = result.get("checks", [])
    q = [c for c in checks if c["gate"] == "quality"]
    leaf = [c for c in checks if c["name"] == "Is it a leaf?"]
    seg = [c for c in checks if c["name"].startswith("Leaf found")]
    model = [c for c in checks if c["gate"] == "model"]
    v = result.get("verdict")
    states = []
    for group in (q, leaf, seg):
        if not group:
            states.append(("todo", "skipped"))
        elif all(c["passed"] for c in group):
            states.append(("done", "passed"))
        else:
            states.append(("stop", next(c["name"] for c in group if not c["passed"])))
    if not model:
        states.append(("todo", "skipped"))
    elif all(c["passed"] for c in model):
        states.append(("done", "passed"))
    else:
        states.append(("warn", next(c["name"] for c in model if not c["passed"])))
    word = STATUS[v][0] if v in STATUS else "-"
    states.append(("done" if v in ("HEALTHY", "DISEASED") else "warn", word))
    # once a stage stops, later stages never ran
    stopped = False
    html_steps = ""
    for i, ((name, ic), (st_, sub)) in enumerate(zip(STAGES, states)):
        if stopped and i < 4:
            st_, sub = "todo", "not reached"
        if st_ == "stop":
            stopped = True
        mark = {"done": icon("check", 16, "#14532D", 3), "stop": icon("x", 16, "#991B1B", 3),
                "warn": icon("alert", 15, "#854D0E", 2.6), "todo": str(i + 1)}[st_]
        if st_ == "done":
            mark = mark.replace('class="lg-ico"', f'class="lg-ico lg-draw" style="--d:{i * 1.6}"')
        html_steps += (f"<div class='lg-step {st_}' style='--i:{i}'><div class='n'>{mark}</div>"
                       f"<div><div class='t'>{name}</div><div class='s'>{html.escape(sub)}</div></div></div>")
    st.markdown(f"<div class='lg-steps' aria-label='LeafGuard safety stages'>{html_steps}</div>", unsafe_allow_html=True)


def _counting(value):
    """'52%' or '7' -> an animated count-up (screen readers get the real value)."""
    import re
    m = re.fullmatch(r"(\d{1,4})(%?)", str(value).strip())
    if not m:
        return html.escape(str(value))
    return (f"<span role='img' aria-label='{m.group(1)}{m.group(2)}'><span class='lg-count' style='--to:{m.group(1)}'>"
            f"</span>{m.group(2)}</span>")


def stat(value, label, tone="neutral", ic=None):
    bg, fg = TONES[tone]
    i = f"<div style='margin-bottom:6px'>{icon(ic, 20, fg)}</div>" if ic else ""
    return (f"<div class='lg-stat' style='background:{bg};border-color:{fg}22'>{i}"
            f"<div class='v' style='color:{fg}'>{_counting(value)}</div>"
            f"<div class='l'>{html.escape(label)}</div></div>")


def card(title, body_html, ic=None):
    i = icon(ic, 18, C["primary"]) + " " if ic else ""
    st.markdown(f"<div class='lg-card'><h3>{i}{html.escape(title)}</h3>{body_html}</div>", unsafe_allow_html=True)


def features(items):
    """Feature strip: [(icon, title, text), ...] - hover to animate."""
    cards = "".join(f"<div class='lg-feature'><div class='fi'>{icon(ic, 22, '#15803D')}</div>"
                    f"<b>{html.escape(t)}</b><span>{html.escape(x)}</span></div>" for ic, t, x in items)
    st.markdown(f"<div class='lg-features'>{cards}</div>", unsafe_allow_html=True)


def link(page, label, ic=None, **kw):
    """st.page_link that never crashes (e.g. when a page is opened on its own)."""
    try:
        st.page_link(page, label=label, icon=ic or kw.get("icon"))
    except Exception:
        pass
