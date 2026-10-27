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
from PIL import Image, ImageDraw
from io import BytesIO

# Page Configuration
st.set_page_config(
    page_title="A & W Cinematic AI Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Blood Red & Dark Minimalist Styling
st.markdown("""
    <style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stButton>button {
        background-color: #e11d48;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #be123c;
        box-shadow: 0 4px 12px rgba(225, 29, 72, 0.4);
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    h1, h2, h3 {
        color: #f1f5f9;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# Regex Cleaner for Voiceover
def clean_script_for_voiceover(raw_text):
    cleaned = re.sub(r'\[.*?\]', '', raw_text)
    cleaned = cleaned.replace('**', '').replace('*', '')
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    return cleaned.strip()

# Smart Narrator Avatar Frame Generator
def generate_narrator_avatar_frame(width, height, frame_count, voice_code):
    is_female = "Female" in voice_code or "Jenny" in voice_code or "Sonia" in voice_code
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
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

    draw.ellipse([center_x - 32, center_y + 30, center_x - 12, center_y + 50], fill=(15, 23, 42))
    draw.ellipse([center_x + 12, center_y + 30, center_x + 32, center_y + 50], fill=(15, 23, 42))
    
    mouth_open = (frame_count // 6) % 2 == 0
    if mouth_open:
        draw.ellipse([center_x - 18, center_y + 82, center_x + 18, center_y + 106], fill=(153, 27, 27))
    else:
        draw.rectangle([center_x - 16, center_y + 90, center_x + 16, center_y + 97], fill=(153, 27, 27))
    return img

def fetch_royalty_free_music(output_path):
    safe_audio_urls = ["https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"]
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

# Main App Layout
st.title("🎬 A & W Cinematic AI Studio")
st.markdown("Professional Storytelling & Character Video Production: Masterminded by Eng. Ahmed El Naggar ❤️")

with st.sidebar:
    st.header("⚙️ Studio Settings")
    voice_choice = st.selectbox(
        "🎙️ Narrator Voice",
        ["US Male (Guy)", "US Female (Jenny)", "UK Male (Ryan)", "UK Female (Sonia)"]
    )
    format_choice = st.radio(
        "📱 Aspect Ratio",
        ["YouTube Short / Reel (9:16 Vertical)", "Cinematic Long Video (16:9 Horizontal)"]
    )
    enable_subs = st.checkbox("💬 Burn-in Subtitles", value=True)
    enable_music = st.checkbox("🎵 Background Music", value=True)
    use_avatar = st.checkbox("Use Smart Narrator Avatar", value=True)

col1, col2 = st.columns([2, 1])

with col1:
    script_input = st.text_area(
        "📝 Full Cinematic Script (with Scenes & Cues)",
        height=220,
        placeholder="Paste your full script here..."
    )

with col2:
    uploaded_files = st.file_uploader(
        "🖼️ Upload Scene Images / Character Assets",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

if st.button("🚀 Render Cinematic Video", use_container_width=True):
    if not script_input.strip():
        st.error("⚠️ Please enter a script first!")
    else:
        status_box = st.status("🎬 Initializing Cinematic Studio Pipeline...", expanded=True)
        
        try:
            voice_map = {
                "US Male (Guy)": "en-US-GuyNeural",
                "US Female (Jenny)": "en-US-JennyNeural",
                "UK Male (Ryan)": "en-GB-RyanNeural",
                "UK Female (Sonia)": "en-GB-SoniaNeural"
            }
            voice_code = voice_map.get(voice_choice, "en-US-GuyNeural")
            
            is_vertical = ("Vertical" in format_choice)
            width, height = (720, 1280) if is_vertical else (1280, 720)
            
            voice_script = clean_script_for_voiceover(script_input)

            status_box.update(label="🎙️ Synthesizing Pro Voiceover...")
            audio_raw = "raw_human_voice.mp3"
            audio_final = "final_voice.mp3"
            asyncio.run(generate_human_voice(voice_script, voice_code, audio_raw))
            subprocess.run(f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.02' {audio_final}", shell=True, check=True)

            probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            final_audio_dur = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
            
            fps = 24
            total_frames = int(fps * final_audio_dur)
            video_no_audio = "temp_video.mp4"
            video_with_subtitles = "temp_subtitles.mp4"
            audio_combined = "combined_audio.mp3"
            final_mp4 = "final_generated_video.mp4"

            status_box.update(label="🎞️ Rendering Video Frames & Avatar/Scenes...")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))

            scene_images = []
            if uploaded_files:
                for uf in uploaded_files:
                    img_bytes = uf.read()
                    img_pil = Image.open(BytesIO(img_bytes)).convert("RGB").resize((width, height))
                    scene_images.append(img_pil)

            frames_per_scene = max(1, total_frames // len(scene_images)) if scene_images else total_frames

            for frame_num in range(total_frames):
                if scene_images and not use_avatar:
                    scene_idx = min(frame_num // frames_per_scene, len(scene_images) - 1)
                    curr_img = scene_images[scene_idx]
                else:
                    curr_img = generate_narrator_avatar_frame(width, height, frame_num, voice_code)

                frame_np = np.array(curr_img)
                cv_bgr_frame = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
                out.write(cv_bgr_frame)

            out.release()

            voice_to_use = audio_final
            if enable_music:
                status_box.update(label="🎵 Mixing Cinematic Background Music...")
                bg_file = "bg_music.mp3"
                if fetch_royalty_free_music(bg_file):
                    try:
                        subprocess.run(f"ffmpeg -y -i {audio_final} -stream_loop -1 -i {bg_file} -filter_complex \"[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first[a]\" -map \"[a]\" {audio_combined}", shell=True, check=True)
                        voice_to_use = audio_combined
                    except:
                        pass

            video_to_merge = video_no_audio
            if enable_subs:
                status_box.update(label="💬 Burning Dynamic Subtitles...")
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

            status_box.update(label="🚀 Finalizing & Multiplexing Video Output...")
            subprocess.run(f"ffmpeg -y -i {video_to_merge} -i {voice_to_use} -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest {final_mp4}", shell=True, check=True)

            status_box.update(label="✅ Render Complete!", state="complete")
            st.success("🎉 Your cinematic masterpiece is ready!")
            st.video(final_mp4)

        except Exception as e:
            status_box.update(label="❌ Render Failed!", state="error")
            st.error(f"Error during rendering: {str(e)}")
