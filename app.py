import streamlit as st
import requests
import json
import os
import cv2
import subprocess
import time
import asyncio
import edge_tts
import numpy as np
import re
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Page Configuration
st.set_page_config(
    page_title="A & W Cinematic AI Studio", 
    page_icon="🎬", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark Elegant Cinematic Theme CSS
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #090d16 0%, #111827 50%, #1c0c14 100%);
        color: #f3f4f6;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    h1 {
        color: #ffffff !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    .stCaption {
        color: #9ca3af !important;
        font-size: 1rem !important;
    }
    .stTextInput input, .stSelectbox > div > div, .stTextArea textarea {
        background-color: #1f2937 !important;
        color: #f3f4f6 !important;
        border: 1px solid #374151 !important;
        border-radius: 8px !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 14px rgba(220, 38, 38, 0.4) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
        box-shadow: 0 6px 20px rgba(220, 38, 38, 0.6) !important;
        transform: translateY(-2px);
    }
    div[data-testid="stBlock"] {
        background-color: rgba(31, 41, 55, 0.5);
        border-radius: 12px;
        padding: 12px;
        border: 1px solid #374151;
    }
    hr {
        border-color: #374151 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎬 A & W Cinematic AI Studio Engine")
st.caption("Professional Storytelling & Character Video Production: Masterminded by Eng. Ahmed El Naggar ❤️")

st.markdown("---")

# Initialize Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

# Dashboard Layout Controls
col_top1, col_top2 = st.columns([2, 1])

with col_top1:
    project_title = st.text_input(
        "🏷️ Cinematic Story / Project Title:", 
        value="",
        placeholder="e.g. Kunafa Masterclass or Newly Married Journey..."
    )
    
    custom_script_input = st.text_area(
        "📝 Paste Your Full Cinematic Script (with Scenes & Cues):",
        value="",
        height=220,
        placeholder="Paste your rich narrative script here. Any bracketed tags like [Scene 1 - Morning] or [0:00-0:15] will be automatically filtered out from voiceover."
    )

with col_top2:
    voice_options_map = {
        "👨 US Male (Guy - Deep & Emotional)": "en-US-GuyNeural",
        "👩 US Female (Jenny - Friendly & Warm)": "en-US-JennyNeural",
        "👨 UK Male (Ryan - Clear & Professional)": "en-GB-RyanNeural",
        "👩 UK Female (Sonia - Elegant & Expressive)": "en-GB-SoniaNeural"
    }
    
    voice_option_label = st.selectbox(
        "🎙️ Choose Narrator Voice Identity:",
        list(voice_options_map.keys())
    )
    selected_voice_code = voice_options_map[voice_option_label]

    video_format = st.radio(
        "📱 Cinematic Aspect Ratio / Format:",
        ["YouTube Short / Reel (9:16 Vertical)", "Cinematic Long Video (16:9 Horizontal)"],
        horizontal=True
    )

col_mid1, col_mid2, col_mid3 = st.columns([1, 1, 1])

with col_mid1:
    enable_subtitles = st.checkbox("💬 Burn-in Cinematic Subtitles", value=True)

with col_mid2:
    enable_bg_music = st.checkbox("🎵 Soft Cinematic Background Music", value=True)

with col_mid3:
    use_avatar_fallback = st.checkbox("Use Smart Animated Narrator Avatar", value=True)

st.markdown("---")
st.subheader("🖼️ Custom Scene Assets & Character References (Optional)")
uploaded_scene_files = st.file_uploader(
    "Upload scene background images or character references in order (Jpg/Png):", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

st.markdown("---")

col_action1, col_action2 = st.columns([3, 1])
with col_action1:
    generate_btn = st.button("🚀 Render Cinematic Story Video Now", type="primary", use_container_width=True)
with col_action2:
    if st.button("🔄 Reset Studio Project", use_container_width=True):
        st.session_state.generated_data = None
        st.rerun()

# Regex Cleaner for Voiceover (Strips brackets, markdown asterisks, and timing metadata)
def clean_script_for_voiceover(raw_text):
    cleaned = re.sub(r'\[.*?\]', '', raw_text)
    cleaned = cleaned.replace('**', '').replace('*', '')
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    return cleaned.strip()

# Smart Gender-Aware Animated Narrator Avatar Frame Generator
def generate_narrator_avatar_frame(width, height, frame_count, voice_code):
    is_female = "Female" in voice_code or "Jenny" in voice_code or "Sonia" in voice_code
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    
    # Cinematic studio lighting
    draw.ellipse([width//2 - 300, -150, width//2 + 300, 350], fill=(30, 41, 59))
    
    center_x = width // 2
    center_y = height // 2 - 80
    
    if is_female:
        draw.polygon([(center_x - 85, center_y + 160), (center_x + 85, center_y + 160), (center_x + 105, center_y + 300), (center_x - 105, center_y + 300)], fill=(225, 29, 72))
        draw.ellipse([(center_x - 65, center_y - 30), (center_x + 65, center_y + 140)], fill=(254, 215, 170))
        draw.arc([(center_x - 72, center_y - 45), (center_x + 72, center_y + 90)], start=180, end=360, fill=(15, 23, 42), width=32)
    else:
        draw.polygon([(center_x - 90, center_y + 160), (center_x + 90, center_y + 160), (center_x + 115, center_y + 300), (center_x - 115, center_y + 300)], fill=(37, 99, 235))
        draw.ellipse([(center_x - 70, center_y - 30), (center_x + 70, center_y + 140)], fill=(254, 215, 170))
        draw.arc([(center_x - 72, center_y - 40), (center_x + 72, center_y + 60)], start=180, end=360, fill=(30, 41, 59), width=24)

    # Eyes
    draw.ellipse([center_x - 32, center_y + 30, center_x - 12, center_y + 50], fill=(15, 23, 42))
    draw.ellipse([center_x + 12, center_y + 30, center_x + 32, center_y + 50], fill=(15, 23, 42))
    
    # Talking mouth animation synced with frame loop
    mouth_open = (frame_count // 6) % 2 == 0
    if mouth_open:
        draw.ellipse([center_x - 18, center_y + 82, center_x + 18, center_y + 106], fill=(153, 27, 27))
    else:
        draw.rectangle([center_x - 16, center_y + 90, center_x + 16, center_y + 97], fill=(153, 27, 27))
    return img

def fetch_royalty_free_music(output_path):
    safe_audio_urls = [
        "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
        "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73467.mp3"
    ]
    for url in safe_audio_urls:
        try:
            res = requests.get(url, timeout=8)
            if res.status_code == 200 and len(res.content) > 50000:
                with open(output_path, "wb") as f:
                    f.write(res.content)
                return True
        except:
            continue
    return False

def split_script_into_chunks(script_text, max_words=4):
    words = script_text.split()
    chunks = []
    current_chunk = []
    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_words or word.endswith(('.', '!', '?', ',')):
            chunks.append(" ".join(current_chunk))
            current_chunk = []
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

async def generate_human_voice(text, voice_code, output_file):
    communicate = edge_tts.Communicate(text, voice_code)
    await communicate.save(output_file)

if generate_btn:
    if not custom_script_input.strip():
        st.warning("⚠️ Please paste your cinematic script in the text area above!")
    else:
        status_container = st.empty()
        metric_container = st.empty()
        progress_bar = st.progress(0)
        
        def update_progress(percent, text):
            val = max(0, min(100, int(percent)))
            progress_bar.progress(val)
            metric_container.metric(label="📊 Production Progress", value=f"{val}%")
            status_container.info(text)

        try:
            is_vertical = ("Vertical" in video_format)
            width, height = (720, 1280) if is_vertical else (1280, 720)
            
            raw_script = custom_script_input.strip()
            project_title_str = project_title.strip() if project_title.strip() else "Cinematic Story"
            voice_script = clean_script_for_voiceover(raw_script)

            update_progress(15, f"🎙️ Step 1/3: Synthesizing professional voiceover ({selected_voice_code})...")
            audio_raw = "raw_human_voice.mp3"
            audio_final = "final_voice.mp3"
            
            asyncio.run(generate_human_voice(voice_script, selected_voice_code, audio_raw))
            subprocess.run(f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.02' {audio_final}", shell=True, check=True)

            probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            final_audio_dur = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
            
            update_progress(40, f"🎨 Step 2/3: Rendering cinematic video frames ({final_audio_dur:.1f}s)...")
            fps = 24
            total_frames = int(fps * final_audio_dur)
            video_no_audio = "temp_video.mp4"
            video_with_subtitles = "temp_subtitles.mp4"
            audio_combined = "combined_audio.mp3"
            final_mp4 = "final_generated_video.mp4"

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))

            # Process scene images if uploaded
            scene_images = []
            if uploaded_scene_files:
                for uf in uploaded_scene_files:
                    img_pil = Image.open(uf).convert("RGB").resize((width, height))
                    scene_images.append(img_pil)

            frames_per_scene = max(1, total_frames // len(scene_images)) if scene_images else total_frames

            for frame_num in range(total_frames):
                if scene_images and not use_avatar_fallback:
                    scene_idx = min(frame_num // frames_per_scene, len(scene_images) - 1)
                    curr_img = scene_images[scene_idx]
                else:
                    curr_img = generate_narrator_avatar_frame(width, height, frame_num, selected_voice_code)

                frame_np = np.array(curr_img)
                cv_bgr_frame = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
                out.write(cv_bgr_frame)

            out.release()

            update_progress(70, "🎵 Mixing background cinematic audio...")
            voice_to_use = audio_final
            if enable_bg_music:
                bg_file = "bg_music.mp3"
                if fetch_royalty_free_music(bg_file):
                    try:
                        subprocess.run(f"ffmpeg -y -i {audio_final} -stream_loop -1 -i {bg_file} -filter_complex \"[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first[a]\" -map \"[a]\" {audio_combined}", shell=True, check=True)
                        voice_to_use = audio_combined
                    except:
                        pass

            update_progress(85, "🎥 Step 3/3: Burning cinematic dynamic subtitles...")
            video_to_merge = video_no_audio
            if enable_subtitles:
                try:
                    chunks = split_script_into_chunks(voice_script, max_words=4)
                    srt_content = ""
                    time_per_chunk = final_audio_dur / float(len(chunks))
                    for idx, chunk in enumerate(chunks):
                        start_s = idx * time_per_chunk
                        end_s = (idx + 1) * time_per_chunk
                        def fmt(s):
                            return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d},{int((s-int(s))*1000):03d}"
                        srt_content += f"{idx + 1}\n{fmt(start_s)} --> {fmt(end_s)}\n{chunk.upper()}\n\n"
                        
                    with open("subtitles.srt", "w", encoding="utf-8") as f:
                        f.write(srt_content)
                    
                    sub_filter = f"subtitles=subtitles.srt:force_style='FontSize=30,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4,Alignment=2,MarginV=60'"
                    subprocess.run(f"ffmpeg -y -i {video_no_audio} -vf \"{sub_filter}\" -c:v libx264 -preset ultrafast {video_with_subtitles}", shell=True, check=True)
                    video_to_merge = video_with_subtitles
                except:
                    pass

            update_progress(95, "📦 Packaging final cinematic video file...")
            subprocess.run(f"ffmpeg -y -i {video_to_merge} -i {voice_to_use} -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest {final_mp4}", shell=True, check=True)

            update_progress(100, "🎉 Cinematic Production Complete!")
            with open(final_mp4, "rb") as f:
                video_bytes = f.read()

            st.session_state.generated_data = {
                "script": raw_script,
                "video_bytes": video_bytes,
                "is_short": is_vertical,
                "topic": project_title_str,
                "duration": final_audio_dur
            }

        except Exception as e:
            st.error(f"❌ Detailed Production Error: {str(e)}")

if st.session_state.generated_data:
    res = st.session_state.generated_data
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader(f"📺 Final Video Output ({res['duration']:.1f}s)")
        st.video(BytesIO(res["video_bytes"]))
        st.download_button(
            "⬇️ Download Cinematic MP4", 
            res["video_bytes"], 
            file_name=f"Cinematic_{res['topic'][:15].replace(' ', '_')}.mp4", 
            mime="video/mp4", 
            use_container_width=True
        )
    with col2:
        st.subheader("📝 Project Master Script Reference")
        st.text_area("Script:", res["script"], height=200)
