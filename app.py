import streamlit as st
import requests
import os
import cv2
import subprocess
import asyncio
import edge_tts
import numpy as np
import re
from PIL import Image, ImageDraw
from io import BytesIO

# Page Configuration
st.set_page_config(
    page_title="A & W Cinematic Script Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark & Blood Red Theme Styling
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

# Smart Cinematic Script Parser (Extracts Scene Guidance & Spoken Text)
def parse_cinematic_script(raw_text):
    scenes = []
    # Split blocks by double newlines or Scene tags
    raw_blocks = re.split(r'\n\s*\n', raw_text)
    
    for block in raw_blocks:
        if not block.strip():
            continue
        
        # Extract guidance inside brackets if any
        guidance_match = re.findall(r'\[(.*?)\]', block)
        guidance = " ".join(guidance_match) if guidance_match else "Cinematic Scene"
        
        # Clean spoken text (remove bracketed notes)
        spoken = re.sub(r'\[.*?\]', '', block).replace('**', '').replace('*', '').strip()
        
        if spoken or guidance:
            scenes.append({
                "guidance": guidance,
                "spoken": spoken if spoken else guidance
            })
            
    if not scenes:
        scenes = [{"guidance": "Opening Scene", "spoken": raw_text}]
    return scenes

def clean_script_for_voiceover(scenes):
    full_text = " ".join([sc["spoken"] for sc in scenes if sc["spoken"]])
    return full_text

# Generate Cinematic Scene Image based on Theme & Guidance
def generate_cinematic_frame(width, height, guidance_text, theme="Warm & Cozy"):
    if "warm" in theme.lower():
        bg_color = (35, 20, 10)
        primary_accent = (234, 88, 12) # Warm Amber
        text_color = (253, 230, 138)
    elif "blood" in theme.lower() or "dark" in theme.lower():
        bg_color = (15, 23, 42)
        primary_accent = (225, 29, 72) # Blood Red
        text_color = (248, 250, 252)
    else:
        bg_color = (15, 23, 42)
        primary_accent = (37, 99, 235) # Cinematic Blue
        text_color = (224, 242, 254)

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw abstract cinematic shapes
    draw.ellipse([-150, -150, width + 150, height // 2], fill=primary_accent)
    draw.rectangle([40, height - 160, width - 40, height - 60], fill=(20, 24, 33))
    
    # Draw Scene Guidance Text on Visual
    display_text = f"SCENE: {guidance_text[:70]}"
    draw.rectangle([50, height // 2 - 45, width - 50, height // 2 + 45], fill=(0, 0, 0, 180))
    draw.text((70, height // 2 - 20), display_text, fill=text_color)
    
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

def split_text_into_chunks(text, max_words=4):
    words = text.split()
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

async def generate_voiceover(text, voice_code, output_file):
    communicate = edge_tts.Communicate(text, voice_code)
    await communicate.save(output_file)

# Main App Layout
st.title("🎬 A & W Cinematic Script Studio")
st.markdown("Professional Cinematic Script-to-Video Engine: Ahmed El Naggar & Sem Sem ❤️")

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
    visual_theme = st.selectbox(
        "🎨 Visual Theme",
        ["Warm & Cozy (Gold/Amber)", "Dark & Blood Red (Minimalist)", "Cinematic Blue"]
    )
    enable_subs = st.checkbox("💬 Burn-in Subtitles", value=True)
    enable_music = st.checkbox("🎵 Background Music", value=True)

col1, col2 = st.columns([2, 1])

with col1:
    script_input = st.text_area(
        "📝 Enter Cinematic Script (with [Scene Guidance])",
        height=260,
        placeholder="Example:\n[Scene 1: Warm morning sunlight hitting a quiet desk]\nWelcome to our journey of creation and success.\n\n[Scene 2: Transition to a modern architectural blueprint]\nEvery great project starts with a clear and structured plan."
    )

with col2:
    uploaded_files = st.file_uploader(
        "🖼️ Upload Custom Scene Images (Optional)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

if st.button("🚀 Render Cinematic Video from Script", use_container_width=True):
    if not script_input.strip():
        st.error("⚠️ Please enter a cinematic script first!")
    else:
        status_box = st.status("🎬 Parsing Script & Initializing Pipeline...", expanded=True)
        
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
            
            # Parse Script into Scenes
            parsed_scenes = parse_cinematic_script(script_input)
            voice_script = clean_script_for_voiceover(parsed_scenes)

            status_box.update(label="🎙️ Synthesizing Voiceover...")
            audio_raw = "raw_voice.mp3"
            audio_final = "final_voice.mp3"
            asyncio.run(generate_voiceover(voice_script, voice_code, audio_raw))
            subprocess.run(f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.02' {audio_final}", shell=True, check=True)

            probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            total_duration = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
            
            fps = 24
            total_frames = int(fps * total_duration)
            video_no_audio = "temp_video.mp4"
            video_with_subs = "temp_subtitles.mp4"
            audio_combined = "combined_audio.mp3"
            final_mp4 = "final_generated_video.mp4"

            status_box.update(label="🎞️ Rendering Scene-by-Scene Visuals...")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))

            # Load uploaded asset images if provided
            user_images = []
            if uploaded_files:
                for uf in uploaded_files:
                    img_bytes = uf.read()
                    img_pil = Image.open(BytesIO(img_bytes)).convert("RGB").resize((width, height))
                    user_images.append(img_pil)

            # Distribute frames proportionally across parsed scenes
            frames_per_scene = max(1, total_frames // len(parsed_scenes))

            for idx, scene in enumerate(parsed_scenes):
                scene_frame_count = frames_per_scene if idx < len(parsed_scenes) - 1 else (total_frames - (frames_per_scene * idx))
                
                # Pick image source: User uploaded or generated cinematic frame
                if user_images and idx < len(user_images):
                    base_img = user_images[idx]
                else:
                    base_img = generate_cinematic_frame(width, height, scene["guidance"], visual_theme)

                for _ in range(scene_frame_count):
                    frame_np = np.array(base_img)
                    cv_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
                    out.write(cv_bgr)

            out.release()

            audio_to_merge = audio_final
            if enable_music:
                status_box.update(label="🎵 Mixing Background Music...")
                bg_file = "bg_music.mp3"
                if fetch_royalty_free_music(bg_file):
                    try:
                        subprocess.run(f"ffmpeg -y -i {audio_final} -stream_loop -1 -i {bg_file} -filter_complex \"[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first[a]\" -map \"[a]\" {audio_combined}", shell=True, check=True)
                        audio_to_merge = audio_combined
                    except:
                        pass

            video_to_merge = video_no_audio
            if enable_subs:
                status_box.update(label="💬 Burning Dynamic Subtitles...")
                try:
                    chunks = split_text_into_chunks(voice_script, max_words=4)
                    srt_content = ""
                    time_per_chunk = total_duration / float(len(chunks))
                    for idx, chunk in enumerate(chunks):
                        start_s = idx * time_per_chunk
                        end_s = (idx + 1) * time_per_chunk
                        def fmt(s):
                            return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d},{int((s-int(s))*1000):03d}"
                        srt_content += f"{idx + 1}\n{fmt(start_s)} --> {fmt(end_s)}\n{chunk.upper()}\n\n"
                        
                    with open("subtitles.srt", "w", encoding="utf-8") as f:
                        f.write(srt_content)
                    
                    sub_filter = f"subtitles=subtitles.srt:force_style='FontSize=30,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4,Alignment=2,MarginV=60'"
                    subprocess.run(f"ffmpeg -y -i {video_no_audio} -vf \"{sub_filter}\" -c:v libx264 -preset ultrafast {video_with_subs}", shell=True, check=True)
                    video_to_merge = video_with_subs
                except:
                    pass

            status_box.update(label="🚀 Finalizing Cinematic Output...")
            subprocess.run(f"ffmpeg -y -i {video_to_merge} -i {audio_to_merge} -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest {final_mp4}", shell=True, check=True)

            status_box.update(label="✅ Render Complete!", state="complete")
            st.success("🎉 Your cinematic script-to-video masterpiece is ready!")
            st.video(final_mp4)

        except Exception as e:
            status_box.update(label="❌ Render Failed!", state="error")
            st.error(f"Error during rendering: {str(e)}")
