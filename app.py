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
from io import BytesIO

# Page Configuration
st.set_page_config(page_title="A & W AI Video Creation Tool", page_icon="🎬", layout="wide")

st.title("🎬 A & W AI Video Creation Tool")
st.caption("Automated Scripting, Smart Real Web HD Visuals, Voices & Clean Assembly.")

# Initialize Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

# Retrieve API Key from Streamlit Secrets
secret_gemini_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""

# Sidebar Configuration
st.sidebar.header("⚙️ Settings & Voices")
gemini_key = st.sidebar.text_input("Gemini API Key (Optional / AIza...)", value=secret_gemini_key, type="password")

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
    uploaded_file = st.file_uploader("Upload your own Image or Video (Optional):", type=["jpg", "jpeg", "png", "mp4"])

with col2:
    video_format = st.radio(
        "📱 Video Format / Type:",
        ["YouTube Short (30-59 sec)", "Long Video (1-15 min)"]
    )
    
    if video_format == "Long Video (1-15 min)":
        duration = st.slider("⏱️ Target Duration (Minutes):", 1.0, 15.0, 3.0, 0.5)
    else:
        duration = 0.75

generate_btn = st.button("🚀 Generate Video with Real Web Photos", type="primary", use_container_width=True)

# Helper function to fetch guaranteed REAL HD photos directly from live web image providers
def fetch_guaranteed_web_photo(keyword, width, height, index=0):
    clean_kw = keyword.strip().replace(" ", ",").lower()
    
    # Provider 1: LoremFlickr (Reliable live topic tag photo engine)
    try:
        url = f"https://loremflickr.com/{width}/{height}/{clean_kw}?lock={index + 10}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200 and len(res.content) > 10000:
            return Image.open(BytesIO(res.content)).convert("RGB")
    except:
        pass

    # Provider 2: Picsum photos with topic seeds
    try:
        url_alt = f"https://picsum.photos/seed/{clean_kw}{index}/{width}/{height}"
        res_alt = requests.get(url_alt, timeout=6)
        if res_alt.status_code == 200 and len(res_alt.content) > 10000:
            return Image.open(BytesIO(res_alt.content)).convert("RGB")
    except:
        pass

    return None

if generate_btn:
    active_gemini_key = gemini_key if gemini_key else secret_gemini_key
    
    if not topic:
        st.warning("⚠️ Please provide a video topic or idea!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        start_time = time.time()
        
        try:
            is_short = (video_format == "YouTube Short (30-59 sec)")
            width, height = (720, 1280) if is_short else (1280, 720)
            target_words = int(duration * 60 * 2.3) if is_short else int(duration * 60 * 2.2)
            
            status_text.text("📝 Step 1/3: Writing script & extracting visual keywords... [Est: 5s]")
            progress_bar.progress(15)
            
            script_data = None
            
            # Use Gemini if valid key provided
            if active_gemini_key and active_gemini_key.startswith("AIza"):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={active_gemini_key}"
                    prompt = f"""
                    The user provided this video topic/idea: '{topic}'.
                    Act as an elite YouTube content creator and producer. 
                    1. Write an engaging voiceover script in English based on the core meaning. Tone: {style}. Word count around {target_words} words.
                    2. Extract 5 specific, real-world English visual search keywords related to the topic (e.g. 'car', 'technology', 'city', 'future', 'space').
                    3. Generate 3 short viral hooks and comma-separated SEO tags.
                    Return JSON format strictly as follows (no markdown wrapping, no extra text):
                    {{
                        "hooks": ["Hook 1", "Hook 2", "Hook 3"],
                        "script": "Full voiceover narration script...",
                        "tags": "tag1, tag2, tag3",
                        "search_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
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
            
            # Smart Fallback Script Generator
            if not script_data:
                clean_topic_words = topic.split()[:2]
                main_kw = clean_topic_words[0] if clean_topic_words else "technology"
                script_data = {
                    "hooks": [
                        f"You won't believe what is happening with {topic}!",
                        f"The truth behind {topic} revealed!",
                        "Everything you knew about this is completely wrong!"
                    ],
                    "script": f"Welcome back everyone. Today we are diving deep into a fascinating topic that has taken the internet by storm: {topic}. As we examine the details closely, experts are split on what this means for the future. Stay tuned as we break down all the key aspects, the hidden implications, and what you need to know right now.",
                    "tags": f"{topic}, viral video, tech news, trending, analysis",
                    "search_keywords": [main_kw, "car", "technology", "city", "future"]
                }
            
            data = script_data
            progress_bar.progress(35)

            # Step 2: Voiceover Generation
            status_text.text(f"🎙️ Step 2/3: Synthesizing voiceover... [Est: 10s]")
            audio_raw = "raw_voice.mp3"
            audio_final = "final_voice.mp3"
            
            selected_tld = tld_map.get(voice_option, "com")
            tts = gTTS(text=data['script'], lang='en', tld=selected_tld, slow=False)
            tts.save(audio_raw)

            cmd_audio = f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.20' {audio_final}"
            subprocess.run(cmd_audio, shell=True, check=True)

            probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            final_audio_dur = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
            progress_bar.progress(55)

            # Step 3: Fetch Real HD Photos (No Colors, No Zoom)
            status_text.text("🌐 Step 3/3: Downloading real topic HD photos from web... [Est: 10s]")
            
            fps = 24
            total_frames = int(fps * final_audio_dur)
            video_no_audio = "temp_video.mp4"
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
                keywords = data.get("search_keywords", ["car", "technology", "city", "future"])
                for idx, kw in enumerate(keywords):
                    img = fetch_guaranteed_web_photo(kw, width, height, index=idx)
                    if img:
                        scene_images.append(img)
                        
            # If still no images, force generate from topic terms
            if not custom_video_used and len(scene_images) == 0:
                for idx in range(4):
                    img = fetch_guaranteed_web_photo("technology", width, height, index=idx)
                    if img:
                        scene_images.append(img)

            # Render Clean HD Photo Transitions (Strictly Real Photos)
            if not custom_video_used and len(scene_images) > 0:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))
                frames_per_scene = max(1, total_frames // len(scene_images))

                for frame_num in range(total_frames):
                    scene_idx = min(frame_num // frames_per_scene, len(scene_images) - 1)
                    active_scene = scene_images[scene_idx].copy()
                    
                    resized_scene = active_scene.resize((width, height), Image.Resampling.LANCZOS)
                    
                    temp_frame_path = "temp_render_frame.png"
                    resized_scene.save(temp_frame_path)
                    cv_img = cv2.imread(temp_frame_path)
                    out.write(cv_img)
                    
                    current_p = 60 + int((frame_num / total_frames) * 35)
                    progress_bar.progress(min(current_p, 95))

                out.release()

                cmd_merge = f"ffmpeg -y -i {video_no_audio} -i {audio_final} -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest {final_mp4}"
                subprocess.run(cmd_merge, shell=True, check=True)

            progress_bar.progress(100)
            elapsed_time = time.time() - start_time
            status_text.success(f"🎉 Real Photos Video Production Complete in {elapsed_time:.1f}s!")

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
