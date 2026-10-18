import streamlit as st
import requests
import json
import os
import cv2
import subprocess
import numpy as np
from gtts import gTTS
from PIL import Image, ImageDraw

# Page Configuration
st.set_page_config(page_title="AI Viral Video Studio Pro", page_icon="🎬", layout="wide")

st.title("🎬 AI Viral Video Studio (Pro Engine)")
st.caption("Multiple Voice Accents, Multi-Scene AI Visuals, Precise Duration Control & High-CTR SEO.")

# Initialize Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

# Sidebar Configuration
st.sidebar.header("🔑 API & Voice Settings")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get your free key from Google AI Studio")

# Voice Accent Selection
voice_option = st.sidebar.selectbox(
    "🎙️ Voice Accent & Style:",
    [
        "🇺🇸 US Voice (Standard Energetic)",
        "🇬🇧 UK Voice (Dramatic / Deep)",
        "🇦🇺 Australian Voice (Casual / Deep)",
        "🇨🇦 Canadian Voice (Smooth)",
        "🇮🇳 Indian Accent (Fast Tech)"
    ]
)

# Map UI option to gTTS tld parameter
tld_map = {
    "🇺🇸 US Voice (Standard Energetic)": "com",
    "🇬🇧 UK Voice (Dramatic / Deep)": "co.uk",
    "🇦🇺 Australian Voice (Casual / Deep)": "com.au",
    "🇨🇦 Canadian Voice (Smooth)": "ca",
    "🇮🇳 Indian Accent (Fast Tech)": "co.in"
}

if st.sidebar.button("🔄 Start New Project", use_container_width=True):
    st.session_state.generated_data = None
    st.rerun()

# Layout Inputs
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("💡 Video Topic / Core Idea:", value="Tesla’s Flying Car: Pure Genius or Billionaire Marketing Fraud?", placeholder="e.g. Elon's Flying Car")
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
        duration = st.slider("⏱️ Exact Target Duration (Minutes):", 1.0, 15.0, 3.0, 0.5)
    else:
        duration = 0.75 # ~45 seconds

generate_btn = st.button("🚀 Generate Pro AI Video & Strategy", type="primary", use_container_width=True)

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
            
            target_words = int(duration * 60 * 2.3) if is_short else int(duration * 60 * 2.2)
            
            # Step 1: Generate Content via Gemini
            status_box.info("📝 Step 1/3: Crafting High-CTR Hooks, Script & SEO Tags...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={gemini_key}"
            
            prompt = f"""
            Act as a top YouTube growth hacker. Create a viral video production package for: '{topic}'.
            Tone: {style}. Target word count strictly around {target_words} words.

            Return JSON format strictly as follows (no markdown wrapping, no extra text):
            {{
                "hooks": [
                    "Short punchy hook 1 (Max 6-8 words)",
                    "Short punchy hook 2 (Max 6-8 words)",
                    "Short punchy hook 3 (Max 6-8 words)"
                ],
                "script": "The full spoken voiceover narration text matching the target word count...",
                "tags": "comma separated SEO tags, trending keywords, specific phrases related to topic"
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
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3].strip()
                
            data = json.loads(raw_text)

            # Step 2: Voiceover Generation with Selected Accent
            status_box.info(f"🎙️ Step 2/3: Generating Voiceover with {voice_option}...")
            audio_raw = "raw_voice.mp3"
            audio_final = "final_voice.mp3"
            
            selected_tld = tld_map.get(voice_option, "com")
            tts = gTTS(text=data['script'], lang='en', tld=selected_tld, slow=False)
            tts.save(audio_raw)

            # Speedup audio slightly for better energy
            cmd_audio = f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.20' {audio_final}"
            subprocess.run(cmd_audio, shell=True, check=True)

            # Get exact audio duration
            probe_cmd_final = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            final_audio_dur = float(subprocess.check_output(probe_cmd_final, shell=True).decode('utf-8').strip())

            # Step 3: Multi-Scene AI Visual Generation & Video Assembly
            status_box.info("🎥 Step 3/3: Fetching Multiple AI Visual Scenes & Rendering Video...")
            
            # Fetch 3 distinct AI generated images to switch scenes during video
            scenes = []
            keywords = [topic, f"{topic} futuristic concept", f"{topic} close up detailed action"]
            
            for idx, kw in enumerate(keywords):
                cleaned_kw = kw.replace(" ", "%20").replace(":", "").replace("?", "")
                img_url = f"https://image.pollinations.ai/prompt/Cinematic%20photorealistic%20{cleaned_kw}%208k?width={width}&height={height}&nologo=true"
                
                scene_file = f"scene_{idx}.jpg"
                try:
                    headers_req = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                    r = requests.get(img_url, headers=headers_req, timeout=8)
                    if r.status_code == 200 and len(r.content) > 1000:
                        with open(scene_file, "wb") as f:
                            f.write(r.content)
                        img_obj = Image.open(scene_file).convert("RGB")
                        scenes.append(img_obj)
                except Exception:
                    pass

            # Fallback high-quality vibrant backdrop if API had issues
            if not scenes:
                fallback_img = Image.new('RGB', (width, height), color=(20, 30, 50))
                d_fall = ImageDraw.Draw(fallback_img)
                d_fall.rectangle([(0, 0), (width, height)], fill=(15, 23, 42))
                scenes.append(fallback_img)

            fps = 24
            total_frames = int(fps * final_audio_dur)
            frames_per_scene = max(1, total_frames // len(scenes))
            
            video_no_audio = "temp_video.mp4"
            final_mp4 = "final_generated_video.mp4"
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))
            
            # Render video sequence switching scenes seamlessly
            for frame_num in range(total_frames):
                scene_idx = min(frame_num // frames_per_scene, len(scenes) - 1)
                active_scene = scenes[scene_idx].copy()
                
                draw = ImageDraw.Draw(active_scene)
                
                # Dark overlay banner at bottom for clear captions/title
                draw.rectangle([(0, height - 220), (width, height)], fill=(0, 0, 0))
                
                # Display title & status
                draw.text((50, height - 160), topic[:42].upper(), fill=(255, 255, 255))
                draw.text((50, height - 100), f"▶ AI Scene {scene_idx + 1} | Narration Active", fill=(56, 189, 248))
                
                temp_frame_path = "temp_render_frame.png"
                active_scene.save(temp_frame_path)
                cv_img = cv2.imread(temp_frame_path)
                out.write(cv_img)
                
            out.release()

            # Merge Video & Audio
            cmd_merge = f"ffmpeg -y -i {video_no_audio} -i {audio_final} -c:v copy -c:a aac -shortest {final_mp4}"
            subprocess.run(cmd_merge, shell=True, check=True)

            # Store in Session State
            st.session_state.generated_data = {
                "hooks": data['hooks'],
                "script": data['script'],
                "tags": data['tags'],
                "video_path": final_mp4,
                "is_short": is_short,
                "topic": topic,
                "duration": final_audio_dur
            }
            status_box.success(f"🎉 Production Complete! Video rendered with multiple AI scenes ({final_audio_dur:.1f}s).")

        except Exception as e:
            st.error(f"An error occurred: {e}")

# Display Results from Session State
if st.session_state.generated_data:
    res = st.session_state.generated_data
    st.markdown("---")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader(f"📺 Final Video Output ({res['duration']:.1f}s)")
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
        st.subheader("🎯 High-CTR Short Viral Hooks")
        for idx, hook in enumerate(res["hooks"], 1):
            st.info(f"**Hook {idx}:** {hook}")
            
        st.subheader("📌 Highly Related SEO Tags & Keywords")
        st.code(res["tags"], language="text")

    st.markdown("---")
    st.subheader("🎙️ Generated Voiceover Script")
    st.text_area("Copy Script Text:", res["script"], height=180)
