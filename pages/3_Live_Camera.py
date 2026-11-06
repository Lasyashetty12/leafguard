"""Live Camera: ESP32-CAM / webcam stream with a traffic-light guide and automatic diagnosis on a steady, good shot."""
import os
import sys
import time

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from leafguard_plus import ui  # noqa: E402
from leafguard_plus.i18n import LANGS, farmer_message  # noqa: E402
from leafguard_plus.live import (SteadyShot, blank_frame, draw_overlay, frame_light, open_source,  # noqa: E402
                                 read_rgb, result_banner)
from leafguard_plus.shared import card, get_guard, setup_page  # noqa: E402

setup_page("Live Camera", ":material/videocam:")
guard = get_guard()

ui.header("Live Camera", "Point the ESP32-CAM or webcam at a leaf. LeafGuard guides the shot and diagnoses "
          "automatically once the picture is good and steady.", "video", eyebrow="Real-time guidance")
st.markdown(" ".join([ui.chip("Red: fix the photo", "bad", "x_circle"),
                      ui.chip("Yellow: point at / move closer to a leaf", "warn", "alert"),
                      ui.chip("Green: good shot, hold still", "good", "check_circle")]), unsafe_allow_html=True)
st.write("")

a, b, c, d = st.columns([2.2, 1, 1, 1])
src = a.text_input("Camera", value="http://192.168.137.154:81/stream",
                   help="ESP32-CAM: http://<camera IP>:81/stream · Laptop webcam: 0 · Or a video file path")
needed = b.slider("Steady frames", 3, 15, 6, help="Green frames in a row before diagnosing")
lang = LANGS[c.selectbox("Language", list(LANGS))]
run = d.toggle("Start camera", value=False)

video_col, result_col = st.columns([1.5, 1])
frame_slot = video_col.empty()
status_slot = video_col.empty()
result_slot = result_col.container()

if not run:
    frame_slot.image(blank_frame("Press 'Start camera' to begin"), width="stretch")
    with result_slot:
        ui.card("Connecting the ESP32-CAM", "<ol style='margin:0;padding-left:18px;line-height:1.8'>"
                "<li>Laptop and camera on the same Wi-Fi / hotspot</li>"
                "<li>Type <code>http://&lt;camera IP&gt;:81/stream</code> above (or <code>0</code> for the webcam)</li>"
                "<li>Switch on <b>Start camera</b></li></ol>", "video")
    if st.session_state.get("live_history"):
        with result_slot:
            st.markdown("### Last diagnoses")
            for h in st.session_state["live_history"][-5:][::-1]:
                st.image(h["thumb"], caption=f"{h['time']} · {h['text']}", width=220)
    st.stop()

cap = open_source(src)
if not cap.isOpened():
    st.error(f"Can't open the camera '{src}'. Check the ESP32-CAM IP, that the laptop is on the same Wi-Fi, "
             f"or use 0 for the laptop webcam.")
    st.stop()

is_file = os.path.exists(src)
steady = SteadyShot(needed=needed)
history = st.session_state.setdefault("live_history", [])
banner = None          # (colour, text, until_time) shown after a diagnosis
failures, frames = 0, 0
last_ui = 0.0

while True:
    rgb = read_rgb(cap)
    if rgb is None:
        if is_file:
            status_slot.info("Video finished.")
            break
        failures += 1
        if failures > 50:
            status_slot.error("Lost the camera stream.")
            break
        time.sleep(0.05)
        continue
    failures = 0
    frames += 1

    colour, msg = frame_light(rgb, guard.th)
    fire = steady.update(colour)
    if colour == "green" and steady.progress is None and banner is None:
        msg = "Done. Move to the next leaf"
    shown = draw_overlay(rgb, colour, msg, steady.progress)

    if fire:
        status_slot.info("Good shot, diagnosing ...")
        r = guard.analyze(rgb)
        bc, btxt = result_banner(r)
        banner = (bc, btxt, time.time() + 4)
        headline, lines = farmer_message(r["verdict"], r.get("cls"), lang)
        thumb = r["images"].get("heatmap", rgb)
        history.append({"time": time.strftime("%H:%M:%S"), "text": headline, "thumb": thumb})
        with result_slot:
            card(r["verdict"], headline, lines)
            st.image(thumb, caption=time.strftime("%H:%M:%S"), width="stretch")
        status_slot.empty()

    if banner and time.time() < banner[2]:
        shown = draw_overlay(shown, banner[0], banner[1])
    elif banner:
        banner = None

    now = time.time()
    if now - last_ui > 0.08 or fire:  # ~12 screen updates per second
        frame_slot.image(shown, width="stretch")
        last_ui = now
    if is_file:
        time.sleep(0.03)

cap.release()
