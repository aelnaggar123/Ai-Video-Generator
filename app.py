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
from PIL import Image
from io import BytesIO

# Page Configuration
st.set_page_config(page_title="A & W AI Video Creation Tool", page_icon="🎬", layout="wide")

st.title("🎬 A & W AI Video Creation Tool")
st.caption("Ultra-Realistic Human Neural Voices, Topic Visuals, Non-Copyrighted Music, Subtitles & Smooth Motion.")

# Initialize Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

# Sidebar Configuration
st.sidebar.header("⚙️ Settings & Voices")
gemini_key = st.sidebar.text_input("Gemini API Key (Optional / AIza...)", value="", type="password")

# High-Quality Human Neural Voice Mapping (Microsoft Edge Neural Engine)
voice_options_map = {
    "👨 US Male (Guy - Deep & Emotional Narration)": "en-US-GuyNeural",
    "👩 US Female (Jenny - Friendly & Warm)": "en-US-JennyNeural",
    "👨 UK Male (Ryan - Clear & Professional)": "en-GB-RyanNeural",
    "👩 UK Female (Sonia - Elegant & Expressive)": "en-GB-SoniaNeural",
    "👦 Young Boy / Kid (Eric - Playful & Dynamic)": "en-US-EricNeural",
    "👧 Kids / Young Girl (Ana - Bright & Natural)": "en-US-AnaNeural"
}

voice_option_label = st.sidebar.selectbox(
    "🎙️ Choose Human Voice Character:",
    list(voice_options_map.keys())
)

selected_voice_code = voice_options_map[voice_option_label]

if st.sidebar.button("🔄 Start New Project", use_container_width=True):
    st.session_state.generated_data = None
    st.rerun()

# Main Layout
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input(
        "💡 Video Topic / Idea (Franco, Arabic, or English):", 
        value="Announcing we are having a baby! My wife surprised me with a positive pregnancy test when I came home from work."
    )
    style = st.selectbox(
        "🎭 Tone & Style:",
        ["Emotional & Heartwarming", "Excited & Joyful", "Surprised & Happy", "Storytelling & Inspiring"]
    )
    
    st.markdown("---")
    st.subheader("🖼️ Custom Visual Media (Optional)")
    uploaded_file = st.file_uploader("Upload your own Image or Video (Optional):", type=["jpg", "jpeg", "png", "mp4"])

with col2:
    video_format = st.radio(
        "📱 Video Format / Type:",
        ["YouTube Short (30-59 sec)", "Long Video (1-15 min)"]
    )
    
    if video_format == "Long Video (1-15 min)":
        duration = st.slider("⏱️ Target Duration (Minutes):", 1.0, 15.0, 1.0, 0.5)
    else:
        duration = 0.75

enable_subtitles = st.checkbox("💬 Burn-in Dynamic Subtitles on Video", value=True)
enable_bg_music = st.checkbox("🎵 Add Non-Copyrighted Background Music", value=True)

generate_btn = st.button("🚀 Generate Video with Music & Real Voice", type="primary", use_container_width=True)

# Helper function to fetch guaranteed REAL HD photos
def fetch_guaranteed_web_photo(keyword, width, height, index=0):
    clean_kw = keyword.strip().replace(" ", ",").lower()
    try:
        url = f"https://loremflickr.com/{width}/{height}/{clean_kw}?lock={index + 10}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200 and len(res.content) > 10000:
            return Image.open(BytesIO(res.content)).convert("RGB")
    except:
        pass

    try:
        url_alt = f"https://picsum.photos/seed/{clean_kw}{index}/{width}/{height}"
        res_alt = requests.get(url_alt, timeout=6)
        if res_alt.status_code == 200 and len(res_alt.content) > 10000:
            return Image.open(BytesIO(res_alt.content)).convert("RGB")
    except:
        pass

    return None

# Helper to fetch non-copyrighted background music suitable for YouTube
def fetch_royalty_free_music(output_path):
    # Public domain / CC0 safe ambient & emotional background audio streams
    safe_audio_urls = [
        "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
        "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73467.mp3",
        "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3"
    ]
    for music_url in safe_audio_urls:
        try:
            res = requests.get(music_url, timeout=10)
            if res.status_code == 200 and len(res.content) > 50000:
                with open(output_path, "wb") as f:
                    f.write(res.content)
                return True
        except:
            continue
    return False

# Helper to split text into short readable subtitle chunks
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

# Async Generator for Edge Realistic Human Voice
async def generate_human_voice(text, voice_code, output_file):
    communicate = edge_tts.Communicate(text, voice_code)
    await communicate.save(output_file)

if generate_btn:
    if not topic:
        st.warning("⚠️ Please provide a video topic or idea!")
    else:
        status_container = st.empty()
        metric_container = st.empty()
        progress_bar = st.progress(0)
        start_time = time.time()
        
        def update_progress(percent, text):
            progress_bar.progress(percent)
            metric_container.metric(label="📊 Production Progress", value=f"{percent}%", delta=f"{percent} out of 100%")
            status_container.info(text)

        try:
            is_short = (video_format == "YouTube Short (30-59 sec)")
            width, height = (720, 1280) if is_short else (1280, 720)
            target_words = int(duration * 135) if not is_short else int(duration * 60 * 2.2)
            
            update_progress(10, "📝 Step 1/5: Analyzing your exact story & writing custom script...")
            
            script_data = None
            
            if gemini_key and gemini_key.startswith("AIza"):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                    prompt = f"""
                    You are an expert personal storyteller. The user provided this exact personal story/idea: '{topic}'.
                    
                    CRITICAL INSTRUCTIONS:
                    - Do NOT use generic business or tech templates.
                    - Write a heartfelt, custom, emotional, and engaging voiceover script in English telling this exact story naturally. Tone: {style}. Target Word Count around {target_words} words.
                    - Extract 6 specific English visual keywords related directly to the story for image search (e.g., 'happy couple', 'pregnancy test', 'baby shoes', 'celebration', 'family joy').
                    - Generate 3 emotional/viral hooks and SEO tags.
                    
                    Return JSON strictly:
                    {{
                        "hooks": ["Hook 1", "Hook 2", "Hook 3"],
                        "script": "Full custom personal script...",
                        "tags": "tag1, tag2",
                        "search_keywords": ["keyword1", "keyword2", "keyword3", "keyword4"]
                    }}
                    """
                    payload = {"contents": [{"parts": [{"text": prompt}]}]}
                    response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                    if response.status_code == 200:
                        result = response.json()
                        raw_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                        if raw_text.startswith("```json"):
                            raw_text = raw_text[7:-3].strip()
                        elif raw_text.startswith("```"):
                            raw_text = raw_text[3:-3].strip()
                        script_data = json.loads(raw_text)
                except:
                    pass
            
            # Smart Custom Fallback tailored specifically to personal announcements / pregnancy
            if not script_data:
                low_topic = topic.lower()
                if "hamil" in low_topic or "preganancy" in low_topic or "pregnancy" in low_topic or "baby" in low_topic or "حامل" in topic:
                    custom_script = "I still cannot believe the moment I walked through that door after a long day at work. My wife looked at me with the biggest smile and handed me the greatest surprise of my life: a positive pregnancy test. Everything stopped in that instant. We are going to have a baby! I am sharing this special moment with all of you because my heart is just too full of joy. Drop your best wishes and congratulations for us below!"
                    search_keys = ["positive pregnancy test", "happy couple", "baby shoes", "celebration", "family joy", "smiling"]
                else:
                    custom_script = f"Today is one of the most unforgettable moments of my life, and I wanted to share it with all of you. {topic}. When this happened, it changed everything and brought so much happiness. Thank you for always celebrating these precious moments with us!"
                    search_keys = ["happy family", "celebration", "joyful moments", "smiling people", "surprised"]

                while len(custom_script.split()) < target_words:
                    custom_script += " This is a moment we will cherish forever, and looking ahead, our lives will never be the same in the most wonderful way possible."

                script_data = {
                    "hooks": [
                        "The best surprise I ever received when coming home from work!",
                        "My wife's life-changing surprise revealed!",
                        "We have the most amazing news to share!"
                    ],
                    "script": custom_script,
                    "tags": "pregnancy announcement, baby news, family joy, blessed, milestone",
                    "search_keywords": search_keys
                }
            
            data = script_data
            update_progress(25, f"🎙️ Step 2/5: Synthesizing Realistic Human Voice ({selected_voice_code})...")

            # Step 2: Realistic Human Voiceover Generation
            audio_raw = "raw_human_voice.mp3"
            audio_final = "final_voice.mp3"
            
            asyncio.run(generate_human_voice(data['script'], selected_voice_code, audio_raw))

            cmd_audio = f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.02' {audio_final}"
            subprocess.run(cmd_audio, shell=True, check=True)

            probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            final_audio_dur = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
            
            update_progress(45, "🌐 Step 3/5: Downloading real HD photos matching your story...")

            # Step 3: Fetch Real HD Photos
            fps = 24
            total_frames = int(fps * final_audio_dur)
            video_no_audio = "temp_video.mp4"
            video_with_subtitles = "temp_subtitles.mp4"
            audio_combined = "combined_audio.mp3"
            final_mp4 = "final_generated_video.mp4"
            
            custom_video_used = False
            scene_images = []

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

            if not custom_video_used:
                keywords = data.get("search_keywords", ["happy couple", "celebration"])
                for idx, kw in enumerate(keywords):
                    img = fetch_guaranteed_web_photo(kw, width, height, index=idx)
                    if img:
                        scene_images.append(img)
                        
            if not custom_video_used and len(scene_images) == 0:
                for idx in range(6):
                    img = fetch_guaranteed_web_photo("happy couple", width, height, index=idx)
                    if img:
                        scene_images.append(img)

            update_progress(65, "🎵 Step 4/5: Mixing royalty-free background music...")
            
            # Step 4: Mix Voiceover with Non-Copyrighted Music
            voice_to_use = audio_final
            if enable_bg_music:
                bg_music_file = "bg_music.mp3"
                if fetch_royalty_free_music(bg_music_file):
                    # Mix voiceover with background music (music volume set to 15% to keep speech clear)
                    cmd_mix = f"ffmpeg -y -i {audio_final} -stream_loop -1 -i {bg_music_file} -filter_complex \"[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first[a]\" -map \"[a]\" {audio_combined}"
                    try:
                        subprocess.run(cmd_mix, shell=True, check=True)
                        voice_to_use = audio_combined
                    except:
                        voice_to_use = audio_final

            # Step 5: Render Motion Video & Burn Subtitles
            update_progress(80, "🎥 Step 5/5: Rendering motion video & burning subtitles...")
            
            if not custom_video_used and len(scene_images) > 0:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))
                
                frames_per_scene = max(
