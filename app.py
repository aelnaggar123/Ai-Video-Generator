import streamlit as st
import requests
import json
import os
import cv2
import subprocess
import time
import numpy as np
from gtts import gTTS
from PIL import Image

# Page Configuration
st.set_page_config(page_title="A & W AI Video Creation Tool", page_icon="🎬", layout="wide")

st.title("🎬 A & W AI Video Creation Tool")
st.caption("Real HD Stock Visuals (Pexels), Custom Media Uploads, Multi-Gender Voices & Precise Duration Control.")

# Initialize Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

# Default Gemini Key
DEFAULT_GEMINI_KEY = "AQ.Ab8RN6Ia5F0k6PkHKVkdVBAsiBm9mBHfX9zXFZN27QMIRRt5ig"

# Sidebar Configuration
st.sidebar.header("⚙️ API Keys & Settings")
gemini_key = st.sidebar.text_input("Gemini API Key", value=DEFAULT_GEMINI_KEY, type="password", help="Gemini API Key for scripting & tags")
pexels_key = st.sidebar.text_input("Pexels API Key (Optional for Stock Videos)", value="", type="password", help="Get free key from pexels.com/api for real HD video clips")

voice_option = st.sidebar.selectbox(
    "🎙️ Voice Accent & Gender:",
    [
        "🇺🇸 US Female (Standard Energetic)",
        "🇺🇸 US Male (Deep & Authoritative)",
        "🇬🇧 UK Female (Dramatic & Elegant)",
        "🇬🇧 UK Male (Deep Narration)",
        "🇦🇺 Australian Male (Casual)",
        "🇨🇦 Canadian Female (Smooth)"
    ]
)

tld_map = {
    "🇺🇸 US Female (Standard Energetic)": "com",
    "🇺🇸 US Male (Deep & Authoritative)": "us",
    "🇬🇧 UK Female (Dramatic & Elegant)": "co.uk",
    "🇬🇧 UK Male (Deep Narration)": "co.uk",
    "🇦🇺 Australian Male (Casual)": "com.au",
    "🇨🇦 Canadian Female (Smooth)": "ca"
}

if st.sidebar.button("🔄 Start New Project", use_container_width=True):
    st.session_state.generated_data = None
    st.rerun()

# Main Layout
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("💡 Video Topic / Idea (Franco, Arabic, or English):", value="Tesla’s Flying Car: Pure Genius or Billionaire Marketing Fraud?")
    style = st.selectbox(
        "🎭 Tone & Style:",
        ["Fast-Paced & Energetic", "Engaging & Dramatic", "Educational & Simple", "Storytelling & Inspiring"]
    )
    
    st.markdown("---")
    st.subheader("🖼️ Custom Visual Media (Optional)")
    uploaded_file = st.file_uploader("Upload your own Image (JPG/PNG) or Video (MP4) to animate over audio:", type=["jpg", "jpeg", "png", "mp4"])

with col2:
    video_format = st.radio(
        "📱 Video Format / Type:",
        ["YouTube Short (30-59 sec)", "Long Video (1-15 min)"]
    )
    
    if video_format == "Long Video (1-15 min)":
        duration = st.slider("⏱️ Target Duration (Minutes):", 1.0, 15.0, 3.0, 0.5)
    else:
        duration = 0.75 # ~45 seconds

generate_btn = st.button("🚀 Generate Video & Strategy", type="primary", use_container_width=True)

if generate_btn:
    if not gemini_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar!")
    elif not topic:
        st.warning("⚠️ Please provide a video topic or idea!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        start_time = time.time()
        
        try:
            is_short = (video_format == "YouTube Short (30-59 sec)")
            width, height = (720, 1280) if is_short else (1280, 720)
            target_words = int(duration * 60 * 2.3) if is_short else int(duration * 60 * 2.2)
            
            # Step 1: Script, Tags, and Visual Search Queries via Gemini
            status_text.text("📝 Step 1/3: Crafting High-CTR Script, SEO Tags & Stock Search Queries... [Est: 5s]")
            progress_bar.progress(15)
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={gemini_key}"
            prompt = f"""
            The user provided this video topic/idea (Franco, Arabic, or English): '{topic}'.
            Act as a top YouTube growth hacker. Create a viral video production package in English.
            Tone: {style}. Target word count strictly around {target_words} words.

            Return JSON format strictly as follows (no markdown wrapping, no extra text):
            {{
                "hooks": [
                    "Short punchy hook 1 (Max 6-8 words)",
                    "Short punchy hook 2 (Max 6-8 words)",
                    "Short punchy hook 3 (Max 6-8 words)"
                ],
                "script": "The full spoken voiceover narration text in English matching the target word count...",
                "tags": "comma separated SEO tags, trending keywords, specific phrases related to topic",
                "search_keywords": ["simple search query 1", "simple search query 2", "simple search query 3"]
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
            progress_bar.progress(35)

            # Step 2: Voiceover Audio Generation & Duration Probe
            status_text.text(f"🎙️ Step 2/3: Generating Voiceover with {voice_option}... [Est: 10s]")
            audio_raw = "raw_voice.mp3"
            audio_final = "final_voice.mp3"
            
            selected_tld = tld_map.get(voice_option, "com")
            tts = gTTS(text=data['script'], lang='en', tld=selected_tld, slow=False)
            tts.save(audio_raw)

            cmd_audio = f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.20' {audio_final}"
            subprocess.run(cmd_audio, shell=True, check=True)

            probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            final_audio_dur = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
            progress_bar.progress(60)

            # Step 3: Fetch Stock Visuals (or Custom Upload / Fallback Canvas)
            status_text.text("🎥 Step 3/3: Gathering Stock Visuals & Rendering Final Video... [Est: 15s]")
            
            fps = 24
            total_frames = int(fps * final_audio_dur)
            video_no_audio = "temp_video.mp4"
            final_mp4 = "final_generated_video.mp4"
            
            custom_video_used = False
            scene_images = []

            # Option A: User Custom File Upload
            if uploaded_file is not None:
                if uploaded_file.type.startswith("image"):
                    custom_img = Image.open(uploaded_file).convert("RGB")
                    scene_images.append(custom_img)
                elif uploaded_file.type.startswith("video"):
                    with open("custom_input_vid.mp4", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    cmd_vid_audio = f"ffmpeg -y -stream_loop -1 -i custom_input_vid.mp4 -i {audio_final} -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest {final_mp4}"
                    subprocess.run(cmd_vid_audio, shell=True, check=True)
                    custom_video_used = True

            # Option B: Pexels API Stock Video/Image Fetch
            if not custom_video_used and pexels_key and len(scene_images) == 0:
                keywords = data.get("search_keywords", [topic])
                headers_pexels = {"Authorization": pexels_key}
                
                for kw in keywords[:3]:
                    try:
                        p_url = f"https://api.pexels.com/v1/search?query={kw}&per_page=1"
                        res_p = requests.get(p_url, headers=headers_pexels, timeout=5)
                        if res_p.status_code == 200:
                            p_data = res_p.json()
                            if p_data.get("photos"):
                                img_src = p_data["photos"][0]["src"]["large"]
                                img_bytes = requests.get(img_src, timeout=5).content
                                with open("pexels_temp.jpg", "wb") as f:
                                    f.write(img_bytes)
                                scene_images.append(Image.open("pexels_temp.jpg").convert("RGB"))
                    except:
                        pass

            # Option C: Fallback High-Contrast Visual Canvases (Guaranteed No Black Screens)
            if not custom_video_used and len(scene_images) == 0:
                colors = [(15, 23, 42), (30, 27, 75), (88, 28, 135)]
                for col in colors:
                    canvas = Image.new('RGB', (width, height), color=col)
                    scene_images.append(canvas)

            # Render Frame Sequence & Smooth Motion Zooming
            if not custom_video_used:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))
                frames_per_scene = max(1, total_frames // len(scene_images))

                for frame_num in range(total_frames):
                    scene_idx = min(frame_num // frames_per_scene, len(scene_images) - 1)
                    base_scene = scene_images[scene_idx].copy()
                    
                    # Clean Dynamic Zooming
                    zoom_factor = 1.0 + 0.06 * np.sin(frame_num / 18.0)
                    zw, zh = int(width / zoom_factor), int(height / zoom_factor)
                    zx, zy = (width - zw) // 2, (height - zh) // 2
                    cropped = base_scene.crop((zx, zy, zx + zw, zy + zh))
                    active_frame = cropped.resize((width, height), Image.Resampling.LANCZOS)
                    
                    temp_frame_path = "temp_render_frame.png"
                    active_frame.save(temp_frame_path)
                    cv_img = cv2.imread(temp_frame_path)
                    out.write(cv_img)
                    
                    current_p = 60 + int((frame_num / total_frames) * 35)
                    progress_bar.progress(min(current_p, 95))

                out.release()

                # Merge Video and Final Audio
                cmd_merge = f"ffmpeg -y -i {video_no_audio} -i {audio_final} -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest {final_mp4}"
                subprocess.run(cmd_merge, shell=True, check=True)

            progress_bar.progress(100)
            elapsed_time = time.time() - start_time
            status_text.success(f"🎉 Production Complete in {elapsed_time:.1f}s!")

            # Save in Session State
            st.session_state.generated_data = {
                "hooks": data['hooks'],
                "script": data['script'],
                "tags": data['tags'],
                "video_path": final_mp4,
                "is_short": is_short,
                "topic": topic,
                "duration": final_audio_dur
            }

        except Exception as e:
            st.error(f"An error occurred: {e}")

# Display Results
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
