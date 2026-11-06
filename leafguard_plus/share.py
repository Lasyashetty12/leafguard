"""Share a diagnosis on WhatsApp (opens WhatsApp / WhatsApp Web with the message pre-filled)."""
import urllib.parse

from .i18n import KCC


def whatsapp_link(text):
    return "https://wa.me/?text=" + urllib.parse.quote(text)


def diagnosis_message(disease, verdict_text, severity=None, act_by=None, today=(), place=None):
    lines = ["LeafGuard crop check", f"Result: {verdict_text}"]
    if disease:
        lines.append(f"Disease: {disease}")
    if severity:
        lines.append(f"Affected area: {severity}")
    if act_by:
        lines.append(f"Act by: {act_by}")
    if place:
        lines.append(f"Location: {place}")
    if today:
        lines.append("Steps for today:")
        lines += [f"- {t}" for t in today]
    lines.append(f"Please advise on treatment and dose. (Kisan Call Centre: {KCC})")
    return "\n".join(lines)
