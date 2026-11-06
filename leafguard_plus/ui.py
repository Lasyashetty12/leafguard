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
.lg-checks .nm {{ font-weight:600; flex:1; font-size:.95rem; }}
.lg-checks .val {{ color:var(--lg-muted); font-size:.85rem; text-align:right; }}

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


def apply():
    st.markdown(CSS, unsafe_allow_html=True)


def sidebar():
    """Brand + navigation (with icons) at the top of the sidebar, on every page."""
    with st.sidebar:
        st.markdown(f"<div class='lg-brand'><div class='b'>{icon('shield', 22, '#fff')}</div>"
                    f"<div><div class='n'>LeafGuard</div><div class='t'>Knows when it doesn't know</div></div></div>",
                    unsafe_allow_html=True)
        for path, label, ic in [("app.py", "Diagnose", ":material/eco:"),
                                ("pages/1_Deep_Check.py", "Deep Check", ":material/biotech:"),
                                ("pages/2_Fool_Me_Arena.py", "Fool Me Arena", ":material/target:"),
                                ("pages/3_Live_Camera.py", "Live Camera", ":material/videocam:")]:
            try:
                st.page_link(path, label=label, icon=ic)
            except Exception:  # e.g. when a page is run on its own
                pass
        st.divider()


# ---------------------------------------------------------------- components
def header(title, subtitle, ic="leaf", eyebrow=None):
    eb = f"<div class='lg-eyebrow'>{html.escape(eyebrow)}</div>" if eyebrow else ""
    st.markdown(f"<div class='lg-head'><div class='badge'>{icon(ic, 26, '#fff')}</div>"
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
        f"<div class='row'><div class='ib'>{icon(ic, 26, fg, 2.2)}</div><div style='flex:1'>"
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
    for c in checks:
        ok = c["passed"]
        ic = icon("check_circle" if ok else "x_circle", 20, "#15803D" if ok else "#B91C1C", 2.2,
                  label="passed" if ok else "failed")
        rows += (f"<li>{ic}<span class='nm'>{html.escape(c['name'])}</span>"
                 f"<span class='val'>{html.escape(str(c['value']))}</span></li>")
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
        html_steps += (f"<div class='lg-step {st_}'><div class='n'>{mark}</div>"
                       f"<div><div class='t'>{name}</div><div class='s'>{html.escape(sub)}</div></div></div>")
    st.markdown(f"<div class='lg-steps' aria-label='LeafGuard safety stages'>{html_steps}</div>", unsafe_allow_html=True)


def stat(value, label, tone="neutral", ic=None):
    bg, fg = TONES[tone]
    i = f"<div style='margin-bottom:6px'>{icon(ic, 20, fg)}</div>" if ic else ""
    return (f"<div class='lg-stat' style='background:{bg};border-color:{fg}22'>{i}"
            f"<div class='v' style='color:{fg}'>{html.escape(str(value))}</div>"
            f"<div class='l'>{html.escape(label)}</div></div>")


def card(title, body_html, ic=None):
    i = icon(ic, 18, C["primary"]) + " " if ic else ""
    st.markdown(f"<div class='lg-card'><h3>{i}{html.escape(title)}</h3>{body_html}</div>", unsafe_allow_html=True)
