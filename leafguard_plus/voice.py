"""Speak the result aloud.

1st choice: gTTS (Google voices, good Kannada and Hindi; needs internet) -> mp3 bytes
Fallback  : the browser's own speech engine (works offline if the computer has that language's voice)
"""
import html
import io
import json


def tts_mp3(text, lang):
    """Return mp3 bytes, or None if gTTS isn't installed / no internet."""
    try:
        from gtts import gTTS

        buf = io.BytesIO()
        gTTS(text=text, lang=lang).write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return None


def browser_speak_html(text, lang, label="Speak (browser voice)"):
    """A small HTML button that uses the browser's speech engine (no internet needed)."""
    locale = {"en": "en-IN", "kn": "kn-IN", "hi": "hi-IN"}.get(lang, "en-IN")
    return f"""
<style>
#sp{{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 18px;border-radius:12px;
border:1.5px solid #15803D;background:#fff;color:#15803D;font:600 15px Raleway,system-ui,sans-serif;cursor:pointer;
transition:background .15s ease}} #sp:hover{{background:#DCFCE7}} #sp:focus-visible{{outline:3px solid #15803D;outline-offset:2px}}
@media (prefers-reduced-motion: reduce){{#sp{{transition:none}}}}
</style>
<button id="sp" type="button"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 4.7a.7.7 0 0 0-1.2-.5L6.41
7.59A1.4 1.4 0 0 1 5.42 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.42a1.4 1.4 0 0 1 1 .41l3.38 3.38a.7.7 0 0 0 1.2-.5z"/>
<path d="M16 9a5 5 0 0 1 0 6"/></svg>{html.escape(label)}</button>
<span id="msg" role="status" style="margin-left:8px;font:13px Raleway,sans-serif;color:#475569"></span>
<script>
document.getElementById('sp').onclick = function() {{
  const u = new SpeechSynthesisUtterance({json.dumps(text)});
  u.lang = {json.dumps(locale)};
  const v = speechSynthesis.getVoices().find(v => v.lang && v.lang.toLowerCase().startsWith({json.dumps(lang)}));
  if (v) u.voice = v; else document.getElementById('msg').textContent = 'No {locale} voice on this computer, using default.';
  speechSynthesis.cancel(); speechSynthesis.speak(u);
}};
</script>"""
