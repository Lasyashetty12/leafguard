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


def browser_speak_html(text, lang, label="🔊 Speak (browser voice)"):
    """A small HTML button that uses the browser's speech engine (no internet needed)."""
    locale = {"en": "en-IN", "kn": "kn-IN", "hi": "hi-IN"}.get(lang, "en-IN")
    return f"""
<button id="sp" style="padding:8px 14px;border-radius:8px;border:1px solid #9bb59b;background:#eef6ee;
cursor:pointer;font-size:15px">{html.escape(label)}</button>
<span id="msg" style="margin-left:8px;font:13px sans-serif;color:#666"></span>
<script>
document.getElementById('sp').onclick = function() {{
  const u = new SpeechSynthesisUtterance({json.dumps(text)});
  u.lang = {json.dumps(locale)};
  const v = speechSynthesis.getVoices().find(v => v.lang && v.lang.toLowerCase().startsWith({json.dumps(lang)}));
  if (v) u.voice = v; else document.getElementById('msg').textContent = 'No {locale} voice on this computer, using default.';
  speechSynthesis.cancel(); speechSynthesis.speak(u);
}};
</script>"""
