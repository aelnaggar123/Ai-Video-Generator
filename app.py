import streamlit as st
import requests
import json
import os
import cv2
import subprocess
import numpy as np
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont

# Page Configuration
st.set_page_config(page_title="AI Viral Video Studio", page_icon="🎬", layout="wide")

st.title("🎬 AI Viral Video Studio (All-in-One)")
st.caption("Generate Script, Fast Voiceover, SEO Hooks, & Assembled Video that STAYS on your page!")

# Initialize Session State to prevent page refresh data wiping
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

# Sidebar Configuration
st.sidebar.header("🔑 API Credentials")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get your free key from Google AI Studio")

if st.sidebar.button("🔄 Start New Project", use_container_width=True):
    st.session_state.generated_data = None
    st.rerun()

# Layout Inputs
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("💡 Video Topic / Core Idea:", value="Tesla Flying Roadster SpaceX Package", placeholder="e.g. Elon's Flying Car")
    style = st.selectbox(
        "🎭 Tone & Style:",
        ["Fast-Paced & Energetic", "Engaging & Dramatic", "Educational & Simple", "Storytelling & Inspiring"]
    )

with col2:
    video_format = st.radio(
        "📱 Video Format / Type:",
        ["YouTube Short (30-59 sec)", "Long Video (1-15 min)"]
    )
    
    if video_format == "Long Video (1-15 min)":
        duration = st.slider("⏱️ Target Duration (Minutes):", 1, 15, 2)
    else:
        duration = 1

generate_btn = st.button("🚀 Generate Viral Video & Strategy", type="primary", use_container_width=True)

if generate_btn:
    if not gemini_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar first!")
    elif not topic:
        st.warning("⚠️ Please provide a video topic or idea!")
    else:
        status_box = st.empty()
        try:
            is_short = (video_format == "YouTube Short (30-59 sec)")
            width, height = (720, 1280) if is_short else (1280, 720)
            
            # Step 1: Generate Gemini Content (Hooks, Script, SEO Tags)
            status_box.info("📝 Step 1/3: Crafting High-Retention Script & SEO Strategy with Gemini...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={gemini_key}"
            
            length_desc = "30-45 seconds (approx 90 words)" if is_short else f"{duration} minutes (approx {duration * 130} words)"
            
            prompt = f"""
            You are a viral YouTube creator. Create a video production kit for topic: '{topic}'.
            Tone: {style}. Length: {length_desc}.

            Return JSON format strictly as follows (no markdown wrapping, no extra text):
            {{
                "hooks": ["Hook Option 1", "Hook Option 2", "Hook Option 3"],
                "script": "The full spoken voiceover text here...",
                "tags": "#Tesla #ElonMusk #Tech #Shorts"
            }}
            """
            
            headers = {'Content-Type': 'application/json'}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            result = response.json()
            
            if response.status_code != 200:
                st.error(f"API Error: {result.get('error', {}).get('message', 'Unknown error')}")
                st.stop()
                
            raw_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
            # Clean JSON string if enclosed in backticks
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3].strip()
                
            data = json.loads(raw_text)

            # Step 2: Voiceover (Fast pacing)
            status_box.info("🎙️ Step 2/3: Generating Fast & Energetic Voiceover...")
            audio_raw = "raw_voice.mp3"
            audio_fast = "fast_voice.mp3"
            
            tts = gTTS(text=data['script'], lang='en', slow=False)
            tts.save(audio_raw)

            # Speed up audio by 1.25x using ffmpeg filter for higher energy pacing
            cmd_audio = f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.25' {audio_fast}"
            subprocess.run(cmd_audio, shell=True, check=True)

            # Step 3: Render Animated Frame Sequence
            status_box.info("🎥 Step 3/3: Assembling Dynamic Frames & Rendering Video...")
            
            # Create colorful animated background frames (Zoom effect & flashing highlights)
            fps = 24
            render_duration = 35 if is_short else min(duration * 60, 180)
            total_frames = fps * render_duration
            
            video_no_audio = "temp_video.mp4"
            final_mp4 = "final_generated_video.mp4"
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))
            
            # Dynamic Frame Generator
            for frame_num in range(total_frames):
                # Subtle color pulse in background for motion feeling
                bg_val = int(20 + 15 * np.sin(frame_num / 10.0))
                img = Image.new('RGB', (width, height), color=(bg_val, 24, 48))
                draw = ImageDraw.Draw(img)
                
                # Dynamic visual text layout
                accent_color = (255, 69, 0) if (frame_num // 12) % 2 == 0 else (56, 189, 248)
                
                if is_short:
                    draw.text((60, 400), "🔥 VIRAL SHORTS", fill=accent_color)
                    draw.text((60, 480), topic[:30].upper(), fill=(255, 255, 255))
                    draw.text((60, 580), "⚡ AUDIO SPEEDED 1.25X", fill=(200, 200, 200))
                else:
                    draw.text((80, 220), "🎬 AI VIDEO STUDIO", fill=accent_color)
                    draw.text((80, 280), topic[:40].upper(), fill=(255, 255, 255))
                    draw.text((80, 360), "🎙️ Fast-Paced Dynamic Narration", fill=(200, 200, 200))
                
                # Save frame temporarily
                temp_frame_path = "temp_f.png"
                img.save(temp_frame_path)
                cv_img = cv2.imread(temp_frame_path)
                out.write(cv_img)
                
            out.release()

            # Merge Fast Audio & Dynamic Video
            cmd_merge = f"ffmpeg -y -i {video_no_audio} -i {audio_fast} -c:v copy -c:a aac -shortest {final_mp4}"
            subprocess.run(cmd_merge, shell=True, check=True)

            # Store in Session State so it NEVER vanishes on interaction/download
            st.session_state.generated_data = {
                "hooks": data['hooks'],
                "script": data['script'],
                "tags": data['tags'],
                "video_path": final_mp4,
                "is_short": is_short,
                "topic": topic
            }
            status_box.success("🎉 Production Complete! All assets locked below.")

        except Exception as e:
            st.error(f"An error occurred: {e}")

# Display Results if stored in Session State (Saves state during downloads & refreshes!)
if st.session_state.generated_data:
    res = st.session_state.generated_data
    st.markdown("---")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("📺 Generated Video Output")
        st.video(res["video_path"])
        
        file_label = "Shorts_MP4" if res["is_short"] else "Video_MP4"
        with open(res["video_path"], "rb") as f:
            st.download_button(
                label=f"⬇️ Download {file_label}",
                data=f,
                file_name=f"AI_{file_label}_{res['topic'][:10].replace(' ', '_')}.mp4",
                mime="video/mp4",
                use_container_width=True
            )
            
    with col_right:
        st.subheader("🎯 Suggested Viral Hooks / Titles")
        for idx, hook in enumerate(res["hooks"], 1):
            st.info(f"**Option {idx}:** {hook}")
            
        st.subheader("📌 Recommended SEO Tags")
        st.code(res["tags"], language="text")

    st.markdown("---")
    st.subheader("🎙️ Generated Voiceover Script")
    st.text_area("Copy Script Text:", res["script"], height=180)
