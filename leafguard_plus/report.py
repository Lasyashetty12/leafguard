"""A one-page diagnosis report (HTML) the farmer can save, print or show to an agriculture officer."""
import base64
import html
import time

import cv2

from .i18n import farmer_message


def _img(rgb, max_side=520):
    h, w = rgb.shape[:2]
    s = min(1.0, max_side / max(h, w))
    small = cv2.resize(rgb, (int(w * s), int(h * s))) if s < 1 else rgb
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(small, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 82])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


def build(rgb, result, verdict, lang, sev=None, stab=None, cf=None):
    esc = html.escape
    head, lines = farmer_message(verdict, result.get("cls"), lang, sev)
    head_en, lines_en = farmer_message(verdict, result.get("cls"), "en", sev)
    checks = "".join(f"<li><b class='{'ok' if c['passed'] else 'no'}'>{'Passed' if c['passed'] else 'Failed'}</b> "
                     f"{esc(c['name'])} <small>({esc(str(c['value']))})</small></li>"
                     for c in result.get("checks", []))
    pics = [("Photo", rgb)]
    if "heatmap" in result.get("images", {}):
        pics.append(("Where the disease was found", result["images"]["heatmap"]))
    if sev and sev.get("level"):
        pics.append((f"Affected area: {round(sev['percent'])}% ({sev['level']})", sev["overlay"]))
    figs = "".join(f"<figure><img src='{_img(im)}'><figcaption>{esc(c)}</figcaption></figure>" for c, im in pics)
    extra = ""
    if stab:
        extra += (f"<p><b>Self-doubt test:</b> {stab['n_agree']} of {stab['n']} re-checks gave the same answer "
                  f"({'stable' if stab['stable'] else 'UNSTABLE, answer downgraded to Not sure'}).</p>")
    if cf:
        extra += f"<p><b>Proof test:</b> {esc(cf['message'])}</p>"
    local = ""
    if lang != "en":
        local = f"<div class='local'><h2>{esc(head)}</h2>" + "".join(f"<p>{esc(x)}</p>" for x in lines) + "</div>"
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>LeafGuard Report</title>
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@600&family=Raleway:wght@400;600&family=Noto+Sans+Kannada&family=Noto+Sans+Devanagari&display=swap" rel="stylesheet">
<meta name="viewport" content="width=device-width,initial-scale=1"><style>
body{{font-family:Raleway,system-ui,'Noto Sans Kannada','Noto Sans Devanagari',sans-serif;max-width:860px;margin:24px auto;padding:0 16px;color:#14532D;background:#F0FDF4}}
h1,h2{{font-family:Lora,Georgia,serif}} .ok{{color:#15803D}} .no{{color:#B91C1C}}
.top{{display:flex;justify-content:space-between;align-items:baseline;border-bottom:2px solid #15803D;padding-bottom:6px;gap:12px;flex-wrap:wrap}}
.card{{background:#fff;border:1px solid #BBF7D0;border-radius:18px;padding:14px 18px;margin:16px 0}} .local{{background:#FEF9C3;border-radius:18px;padding:14px 18px}}
figure{{display:inline-block;margin:6px;width:260px;vertical-align:top}} img{{width:100%;border-radius:8px}}
figcaption{{font-size:13px;color:#555}} small{{color:#777}} ul{{padding-left:18px}}
</style></head><body>
<div class="top"><h1>LeafGuard diagnosis report</h1><span>{time.strftime('%d %b %Y, %H:%M')}</span></div>
<div class="card"><h2>{esc(head_en)}</h2>{''.join(f'<p>{esc(x)}</p>' for x in lines_en)}</div>
{local}
{figs}
<h3>Safety checks passed before answering</h3><ul>{checks}</ul>
{extra}
<p><small>LeafGuard is a decision aid, not a replacement for an agriculture expert. Kisan Call Centre: 1800-180-1551 (free).</small></p>
</body></html>"""
