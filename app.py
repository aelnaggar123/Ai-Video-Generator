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

# Smart Script Parser: Extracts Guidance/Cues and Spoken Lines
def parse_cinematic_script(raw_text):
    scenes = []
    # Split by common scene markers or double newlines
    raw_scenes = re.split(r'(?:Scene \d+|#|\n\s*\n)', raw_text)
    
    for s in raw_scenes:
        if not s.strip():
            continue
        # Extract instructions/guidance inside brackets if any
        guidance_match = re.findall(r'\[(.*?)\]', s)
        guidance = " ".join(guidance_match) if guidance_match else "Cinematic Scene"
        
        # Clean spoken text (remove bracketed notes)
        spoken = re.sub(r'\[.*?\]', '', s).replace('**', '').replace('*', '').strip()
        if spoken:
            scenes.append({
                "guidance": guidance,
                "spoken": spoken
            })
            
    if not scenes:
        scenes = [{"guidance": "General Scene", "spoken": clean_script_for_voiceover(raw_text)}]
    return scenes

def clean_script_for_voiceover(raw_text):
    cleaned = re.sub(r'\[.*?\]', '', raw_text)
    cleaned = cleaned.replace('**', '').replace('*', '')
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    return cleaned.strip()

# Generate a Warm/Cinematic Scene Image based on Guidance
def generate_cinematic_scene_image(width, height, guidance_text, theme="Warm"):
    # Warm Theme Color Palette (Oranges, Ambers, Deep Browns, Soft Golds)
    if "warm" in theme.lower() or "sunset" in guidance_text.lower() or "cozy" in guidance_text.lower():
        bg_color = (40, 20, 10)
        accent_color = (234, 88, 12) # Warm Amber/Orange
        secondary_color = (251, 191, 36) # Soft Gold
    else:
        bg_color = (15, 23, 42)
        accent_color = (225, 29, 72)
        secondary_color = (56, 189, 248)

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw artistic abstract cinematic elements
    draw.ellipse([-100, -100, width + 100, height // 2], fill=accent_color)
    draw.rectangle([50, height - 150, width - 50, height - 50], fill=(30, 20, 15))
    
    # Draw Guidance Text Overlay as a visual cue on the scene
    wrapped_text = f"SCENE: {guidance_text[:60]}..."
    draw.rectangle([40, height // 2 - 40, width - 40, height // 2 + 40], fill=(0, 0, 0, 160))
    draw.text((60, height // 2 - 20), wrapped_text, fill=secondary_color)
    
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
st.markdown("Professional Storytelling & Character Video Production: Ahmed El Naggar & Sem Sem ❤️")

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
        ["Warm & Cozy (Sunset/Gold)", "Dark & Blood Red (Minimalist)", "Cinematic Blue"]
    )
    enable_subs = st.checkbox("💬 Burn-in Subtitles", value=True)
    enable_music = st.checkbox("🎵 Background Music", value=True)
    use_uploaded_assets = st.checkbox("Use Uploaded Assets as Scenes", value=True)

col1, col2 = st.columns([2, 1])

with col1:
    script_input = st.text_area(
        "📝 Full Cinematic Script (with [Guidance] & Scenes)",
        height=220,
        placeholder="Example:\n[Scene 1: Warm morning coffee on a balcony]\nHello everyone, welcome to our story.\n\n[Scene 2: Walking down a historic street]\nToday we explore amazing places..."
    )

with col2:
    uploaded_files = st.file_uploader(
        "🖼️ Upload Custom Scene Images",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

if st.button("🚀 Render Cinematic Video", use_container_width=True):
    if not script_input.strip():
        st.error("⚠️ Please enter a script first!")
    else:
        status_box = st.status("🎬 Parsing Script & Initializing Studio Pipeline...", expanded=True)
        
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
            
            # Parse scenes and spoken text
            parsed_scenes = parse_cinematic_script(script_input)
            full_voice_script = " ".join([sc["spoken"] for sc in parsed_scenes])

            status_box.update(label="🎙️ Synthesizing Pro Voiceover for all Scenes...")
            audio_raw = "raw_human_voice.mp3"
            audio_final = "final_voice.mp3"
            asyncio.run(generate_human_voice(full_voice_script, voice_code, audio_raw))
            subprocess.run(f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.02' {audio_final}", shell=True, check=True)

            probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            final_audio_dur = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
            
            fps = 24
            total_frames = int(fps * final_audio_dur)
            video_no_audio = "temp_video.mp4"
            video_with_subtitles = "temp_subtitles.mp4"
            audio_combined = "combined_audio.mp3"
            final_mp4 = "final_generated_video.mp4"

            status_box.update(label="🎞️ Rendering Scene-by-Scene Visuals...")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))

            # Load uploaded images if any
            user_images = []
            if uploaded_files and use_uploaded_assets:
                for uf in uploaded_files:
                    img_bytes = uf.read()
                    img_pil = Image.open(BytesIO(img_bytes)).convert("RGB").resize((width, height))
                    user_images.append(img_pil)

            # Distribute frames across parsed scenes
            frames_per_scene = max(1, total_frames // len(parsed_scenes))

            for scene_idx, scene in enumerate(parsed_scenes):
                scene_frames = frames_per_scene if scene_idx < len(parsed_scenes) - 1 else (total_frames - (frames_per_scene * scene_idx))
                
                # Determine scene image source
                if user_images and scene_idx < len(user_images):
                    base_scene_img = user_images[scene_idx]
                else:
                    base_scene_img = generate_cinematic_scene_image(width, height, scene["guidance"], visual_theme)

                for f_in_scene in range(scene_frames):
                    frame_np = np.array(base_scene_img)
                    cv_bgr_frame = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
                    out.write(cv_bgr_frame)

            out.release()

            voice_to_use = audio_final
            if enable_music:
                status_box.update(label="🎵 Mixing Warm Background Music...")
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
                    chunks = split_script_into_chunks(full_voice_script, max_words=4)
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

            status_box.update(label="🚀 Finalizing Cinematic Masterpiece...")
            subprocess.run(f"ffmpeg -y -i {video_to_merge} -i {voice_to_use} -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest {final_mp4}", shell=True, check=True)

            status_box.update(label="✅ Render Complete!", state="complete")
            st.success("🎉 Your multi-scene cinematic video with Warm Theme & Guidance is ready!")
            st.video(final_mp4)

        except Exception as e:
            status_box.update(label="❌ Render Failed!", state="error")
            st.error(f"Error during rendering: {str(e)}")
