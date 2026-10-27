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
    page_title="A & W AI Video Creation Tool", 
    page_icon="🎬", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark Elegant Theme CSS Injection
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #161b22 50%, #1a0e14 100%);
        color: #f0f6fc;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    h1 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    .stCaption {
        color: #8b949e !important;
        font-size: 0.95rem !important;
    }
    .stTextInput input, .stSelectbox > div > div, .stTextArea textarea {
        background-color: #161b22 !important;
        color: #f0f6fc !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #8b0000 0%, #5a0000 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(139, 0, 0, 0.3) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #a30000 0%, #700000 100%) !important;
        box-shadow: 0 6px 16px rgba(139, 0, 0, 0.5) !important;
        transform: translateY(-1px);
    }
    div[data-testid="stBlock"] {
        background-color: rgba(22, 27, 34, 0.6);
        border-radius: 12px;
        padding: 10px;
        border: 1px solid #21262d;
    }
    hr {
        border-color: #30363d !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎬 A & W AI Video Creation Tool")
st.caption("Professional AI Video Studio: Made by Eng. Ahmed El Naggar and his Sem Sem ❤️")

st.markdown("---")

# Initialize Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

# Input Mode Switcher Radio
input_mode = st.radio(
    "⚙️ Choose Input Mode:",
    ["AI Description / Topic (Let AI write script)", "Direct Custom Script (Paste your exact script)"],
    horizontal=True
)

st.markdown("---")

# Dashboard Controls
col_top1, col_top2 = st.columns([2, 1])

with col_top1:
    if input_mode == "AI Description / Topic (Let AI write script)":
        topic = st.text_input(
            "💡 What is your video about?", 
            value="",
            placeholder="Type any topic in Arabic, Franco, or English (e.g. 7omos el sham)..."
        )
        custom_script_input = ""
    else:
        topic = st.text_input(
            "🏷️ Video Title / Topic Name:", 
            value="",
            placeholder="Name your project (e.g. Kunafa Masterclass)..."
        )
        custom_script_input = st.text_area(
            "📝 Paste Your Exact Script Here (Timings [0:00] and markdown like ** will be automatically cleaned):",
            value="",
            height=140,
            placeholder="Type or paste your exact script here..."
        )

    style = st.selectbox(
        "🎭 Tone & Style:",
        ["Informative & Engaging", "Professional & Corporate", "Educational & Clear", "Casual & Friendly"]
    )

with col_top2:
    voice_options_map = {
        "👨 US Male (Guy - Deep & Emotional)": "en-US-GuyNeural",
        "👩 US Female (Jenny - Friendly & Warm)": "en-US-JennyNeural",
        "👨 UK Male (Ryan - Clear & Professional)": "en-GB-RyanNeural",
        "👩 UK Female (Sonia - Elegant & Expressive)": "en-GB-SoniaNeural"
    }
    
    voice_option_label = st.selectbox(
        "🎙️ Choose Human Voice Character:",
        list(voice_options_map.keys())
    )
    selected_voice_code = voice_options_map[voice_option_label]

    video_format = st.radio(
        "📱 Video Format / Type:",
        ["YouTube Short (30-59 sec)", "Long Video (1-15 min)"],
        horizontal=True
    )

col_mid1, col_mid2, col_mid3 = st.columns([1, 1, 1])

with col_mid1:
    if video_format == "Long Video (1-15 min)":
        duration = st.slider("⏱️ Target Duration (Minutes):", 0.5, 15.0, 2.0, 0.5)
    else:
        duration = 0.75
        st.info("📌 Shorts Mode: ~45 seconds optimized.")

with col_mid2:
    enable_subtitles = st.checkbox("💬 Burn-in Dynamic Subtitles", value=True)
    enable_bg_music = st.checkbox("🎵 Royalty-Free Background Music", value=True)

with col_mid3:
    st.subheader("🖼️ Custom Media")
    uploaded_file = st.file_uploader("Upload Image/Video (Opt):", type=["jpg", "jpeg", "png", "mp4"], label_visibility="collapsed")

st.markdown("---")

col_action1, col_action2 = st.columns([3, 1])
with col_action1:
    generate_btn = st.button("🚀 Generate AI Video Now", type="primary", use_container_width=True)
with col_action2:
    if st.button("🔄 Reset Project", use_container_width=True):
        st.session_state.generated_data = None
        st.rerun()

# Script Generator function
def generate_script_with_gemini(user_prompt, target_word_count, tone_style):
    if "GEMINI_API_KEY" not in st.secrets:
        raise ValueError("GEMINI_API_KEY is missing from Streamlit Secrets! Please add it.")
    
    api_key = st.secrets["GEMINI_API_KEY"]
    target_model_path = "models/gemini-3.8-flash"
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/{target_model_path}:generateContent?key={api_key}"
    
    prompt = f"""You are an advanced AI master instructor and expert technical/culinary guide with native multilingual and slang-translation capabilities.
The user's topic/input is: "{user_prompt}".
Tone & Style: {tone_style}.

CORE DIRECTIVES:
1. DECODE INTENT INTELLIGENTLY: Automatically interpret what the user wants, regardless of whether it's written in Franco or Arabic.
2. ZERO GENERIC FILLER: Strictly ban generic introductions, robot phrases, or clichés. Give rich, concrete steps, exact proportions, timings, and professional techniques.
3. NARRATION READY: Write entirely in clear, engaging English suitable for professional voiceover narration. DO NOT include bracketed timestamps like [Opening - 0:00] or markdown bold asterisks.
4. LENGTH: Must be substantial (at least {target_word_count} words).
"""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}
    
    script_text = None
    for attempt in range(4):
        try:
            response = requests.post(gen_url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                res_data = response.json()
                candidate_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if len(candidate_text.split()) > 35 and "Preparation of all required ingredients" not in candidate_text:
                    script_text = candidate_text
                    break
        except Exception:
            time.sleep(2)
            continue
            
    if not script_text or len(script_text.split()) < 35:
        script_text = (
            f"Welcome to this comprehensive masterclass guide dedicated entirely to {user_prompt}. "
            f"In this detailed walkthrough, we will break down every essential phase required to achieve absolute mastery. "
            f"Phase one: Initial setup and gathering precise components with accurate measurements. "
            f"Phase two: Step-by-step operational execution following precise techniques and timing parameters. "
            f"Phase three: Quality control, fine-tuning, and final presentation to guarantee exceptional results."
        ) * max(1, target_word_count // 100)

    words_list = user_prompt.split()
    keywords = words_list[:4] if len(words_list) >= 4 else ["guide", "tutorial"]
    tags = f"{user_prompt}, guide, tutorial, 2026"
    hooks = [
        f"Master {user_prompt} with this exact professional method!",
        f"The ultimate step-by-step guide to {user_prompt}.",
        f"Here is how to do {user_prompt} correctly every single time."
    ]

    return {
        "script": script_text,
        "hooks": hooks,
        "search_keywords": keywords,
        "tags": tags
    }

# Advanced Helper function to clean text for voiceover (Removes brackets [...] and markdown asterisks **)
def clean_script_for_voiceover(raw_text):
    # Removes anything inside square brackets []
    cleaned = re.sub(r'\[.*?\]', '', raw_text)
    # Removes markdown bold/italic asterisks ** or *
    cleaned = cleaned.replace('**', '').replace('*', '')
    # Clean multiple newline characters left over
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    return cleaned.strip()

# Smart Gender-Aware Animated Narrator Avatar
def generate_narrator_avatar_frame(width, height, frame_count, voice_code):
    is_female = "Female" in voice_code or "Jenny" in voice_code or "Sonia" in voice_code
    
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    
    draw.ellipse([width//2 - 250, -150, width//2 + 250, 300], fill=(30, 41, 59))
    
    center_x = width // 2
    center_y = height // 2 - 100
    
    if is_female:
        draw.polygon([
            (center_x - 75, center_y + 160),
            (center_x + 75, center_y + 160),
            (center_x + 95, center_y + 280),
            (center_x - 95, center_y + 280)
        ], fill=(225, 29, 72))
        
        draw.polygon([
            (center_x - 22, center_y + 160),
            (center_x + 22, center_y + 160),
            (center_x + 10, center_y + 240),
            (center_x - 10, center_y + 240)
        ], fill=(255, 255, 255))
        draw.ellipse([center_x - 8, center_y + 175, center_x + 8, center_y + 190], outline=(234, 179, 8), width=3)
        
        draw.ellipse([
            (center_x - 60, center_y - 30),
            (center_x + 60, center_y + 140)
        ], fill=(254, 215, 170))
        
        draw.arc([
            (center_x - 68, center_y - 45),
            (center_x + 68, center_y + 90)
        ], start=180, end=360, fill=(15, 23, 42), width=30)
        
        draw.ellipse([center_x - 28, center_y + 32, center_x - 12, center_y + 48], fill=(15, 23, 42))
        draw.ellipse([center_x + 12, center_y + 32, center_x + 28, center_y + 48], fill=(15, 23, 42))
        
    else:
        draw.polygon([
            (center_x - 80, center_y + 160),
            (center_x + 80, center_y + 160),
            (center_x + 105, center_y + 280),
            (center_x - 105, center_y + 280)
        ], fill=(37, 99, 235))
        
        draw.polygon([
            (center_x - 26, center_y + 160),
            (center_x + 26, center_y + 160),
            (center_x + 12, center_y + 250),
            (center_x - 12, center_y + 250)
        ], fill=(255, 255, 255))
        draw.polygon([
            (center_x - 7, center_y + 160),
            (center_x + 7, center_y + 160),
            (center_x + 3, center_y + 220),
            (center_x - 3, center_y + 220)
        ], fill=(220, 38, 38))
        
        draw.ellipse([
            (center_x - 65, center_y - 30),
            (center_x + 65, center_y + 140)
        ], fill=(254, 215, 170))
        
        draw.arc([
            (center_x - 68, center_y - 40),
            (center_x + 68, center_y + 60)
        ], start=180, end=360, fill=(30, 41, 59), width=22)
        
        draw.ellipse([center_x - 30, center_y + 30, center_x - 12, center_y + 48], fill=(15, 23, 42))
        draw.ellipse([center_x + 12, center_y + 30, center_x + 30, center_y + 48], fill=(15, 23, 42))

    mouth_open = (frame_count // 6) % 2 == 0
    if mouth_open:
        draw.ellipse([center_x - 16, center_y + 80, center_x + 16, center_y + 102], fill=(153, 27, 27))
    else:
        draw.rectangle([center_x - 15, center_y + 88, center_x + 15, center_y + 94], fill=(153, 27, 27))
        
    return img

def fetch_royalty_free_music(output_path):
    safe_audio_urls = [
        "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
        "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73467.mp3"
    ]
    for music_url in safe_audio_urls:
        try:
            res = requests.get(music_url, timeout=8)
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
    if input_mode == "AI Description / Topic (Let AI write script)" and not topic.strip():
        st.warning("⚠️ Please enter what you want the video to be about in the box above!")
    elif input_mode == "Direct Custom Script (Paste your exact script)" and not custom_script_input.strip():
        st.warning("⚠️ Please paste your custom script in the text area above!")
    else:
        status_container = st.empty()
        metric_container = st.empty()
        progress_bar = st.progress(0)
        
        def update_progress(percent, text):
            val = max(0, min(100, int(percent)))
            progress_bar.progress(val)
            metric_container.metric(label="📊 Production Progress", value=f"{val}%", delta=f"{val}/100%")
            status_container.info(text)

        try:
            is_short = (video_format == "YouTube Short (30-59 sec)")
            width, height = (720, 1280) if is_short else (1280, 720)
            
            # Determine Script Source
            if input_mode == "AI Description / Topic (Let AI write script)":
                target_words = int(duration * 135) if not is_short else int(duration * 60 * 2.2)
                update_progress(5, f"🤖 Step 1/4: Generating script using AI...")
                data = generate_script_with_gemini(topic, target_words, style)
                raw_script = data['script']
                project_topic = topic
                hooks = data['hooks']
                tags = data['tags']
            else:
                update_progress(5, f"📝 Step 1/4: Using your direct custom script...")
                raw_script = custom_script_input.strip()
                project_topic = topic if topic.strip() else "Custom Video"
                words_list = project_topic.split()
                tags = f"{project_topic}, tutorial, guide, 2026"
                hooks = [
                    f"Master {project_topic} with this precise method!",
                    f"The ultimate guide to {project_topic}.",
                    f"Here is everything you need to know about {project_topic}."
                ]

            # Clean raw script for voiceover & subtitles (filters out brackets and asterisks **)
            voice_script = clean_script_for_voiceover(raw_script)

            update_progress(15, f"🎙️ Step 2/4: Synthesizing full-duration voiceover ({selected_voice_code})...")
            audio_raw = "raw_human_voice.mp3"
            audio_final = "final_voice.mp3"
            
            asyncio.run(generate_human_voice(voice_script, selected_voice_code, audio_raw))
            subprocess.run(f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.02' {audio_final}", shell=True, check=True)

            probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            final_audio_dur = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
            
            update_progress(30, f"🎨 Step 3/4: Rendering full {final_audio_dur:.1f}s animated narrator video...")
            fps = 24
            total_frames = int(fps * final_audio_dur)
            video_no_audio = "temp_video.mp4"
            video_with_subtitles = "temp_subtitles.mp4"
            audio_combined = "combined_audio.mp3"
            final_mp4 = "final_generated_video.mp4"

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))

            for frame_num in range(total_frames):
                avatar_img = generate_narrator_avatar_frame(width, height, frame_num, selected_voice_code)
                frame_np = np.array(avatar_img)
                cv_bgr_frame = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
                out.write(cv_bgr_frame)
                
                if frame_num % 120 == 0:
                    render_progress = 30 + int((frame_num / total_frames) * 40)
                    update_progress(render_progress, f"🎥 Rendering video frames ({frame_num}/{total_frames})...")

            out.release()

            update_progress(75, "🎵 Mixing background music...")
            voice_to_use = audio_final
            if enable_bg_music:
                bg_music_file = "bg_music.mp3"
                if fetch_royalty_free_music(bg_music_file):
                    try:
                        subprocess.run(f"ffmpeg -y -i {audio_final} -stream_loop -1 -i {bg_music_file} -filter_complex \"[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first[a]\" -map \"[a]\" {audio_combined}", shell=True, check=True)
                        voice_to_use = audio_combined
                    except:
                        voice_to_use = audio_final

            update_progress(85, "🎥 Step 4/4: Burning prominent dynamic subtitles...")
            video_to_merge = video_no_audio
            if enable_subtitles:
                try:
                    chunks = split_script_into_chunks(voice_script, max_words=4)
                    srt_content = ""
                    time_per_chunk = final_audio_dur / float(len(chunks))
                    for idx, chunk in enumerate(chunks):
                        start_s = idx * time_per_chunk
                        end_s = (idx + 1) * time_per_chunk
                        def fmt_time(s):
                            hrs = int(s // 3600)
                            mins = int((s % 3600) // 60)
                            secs = int(s % 60)
                            millis = int((s - int(s)) * 1000)
                            return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"
                        srt_content += f"{idx + 1}\n{fmt_time(start_s)} --> {fmt_time(end_s)}\n{chunk.upper()}\n\n"
                        
                    with open("subtitles.srt", "w", encoding="utf-8") as f:
                        f.write(srt_content)
                        
                    font_size = 24 if is_short else 30
                    subtitle_filter = f"subtitles=subtitles.srt:force_style='FontSize={font_size},PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4,Alignment=2,MarginV=60'"
                    subprocess.run(f"ffmpeg -y -i {video_no_audio} -vf \"{subtitle_filter}\" -c:v libx264 -preset ultrafast {video_with_subtitles}", shell=True, check=True)
                    video_to_merge = video_with_subtitles
                except:
                    pass

            update_progress(95, "📦 Finalizing media package...")
            subprocess.run(f"ffmpeg -y -i {video_to_merge} -i {voice_to_use} -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest {final_mp4}", shell=True, check=True)

            update_progress(100, "🎉 Production Complete Successfully!")
            
            if not os.path.exists(final_mp4):
                subprocess.run(f"ffmpeg -y -f lavfi -i color=c=black:s={width}x{height}:r=24 -i {audio_final} -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest {final_mp4}", shell=True, check=True)

            with open(final_mp4, "rb") as f:
                video_bytes = f.read()

            st.session_state.generated_data = {
                "hooks": hooks,
                "script": raw_script,
                "tags": tags,
                "video_bytes": video_bytes,
                "is_short": is_short,
                "topic": project_topic,
                "duration": final_audio_dur
            }

        except Exception as e:
            st.error(f"❌ Detailed Generation Error: {str(e)}")

if st.session_state.generated_data:
    res = st.session_state.generated_data
    st.markdown("---")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader(f"Final Video Output ({res['duration']:.1f}s)")
        video_file_io = BytesIO(res["video_bytes"])
        st.video(video_file_io)
        
        file_label = "Shorts_MP4" if res["is_short"] else "Video_MP4"
        st.download_button(
            label=f"⬇️ Download {file_label}",
            data=res["video_bytes"],
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
