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
st.caption("Automated Scripting, Logical Smart Visual Search, Multi-Gender Voices & Guaranteed Video Rendering.")

# Initialize Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

# Retrieve Gemini Key securely from Streamlit Secrets or Manual Input
secret_gemini_key = st.secrets.get("GEMINI_API_KEY", "AQ.Ab8RN6KQIGkmobkIijJY3qpaRtiYEEa5aVDYRW0EUC-aqTI8kw") if hasattr(st, "secrets") else "AQ.Ab8RN6KQIGkmobkIijJY3qpaRtiYEEa5aVDYRW0EUC-aqTI8kw"

# Sidebar Configuration
st.sidebar.header("⚙️ API Keys & Settings")
gemini_key = st.sidebar.text_input("Gemini API Key", value=secret_gemini_key, type="password", help="GCP / Gemini API Key")
pexels_key = st.sidebar.text_input("Pexels API Key (Optional)", value="", type="password", help="Get free key from pexels.com/api")

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
        duration = 0.75

generate_btn = st.button("🚀 Generate Complete Video", type="primary", use_container_width=True)

if generate_btn:
    active_key = gemini_key if gemini_key else secret_gemini_key
    if not active_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar or save it in Streamlit Secrets!")
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
            
            status_text.text("📝 Step 1/3: Analyzing idea, writing script & extracting logical keywords... [Est: 5s]")
            progress_bar.progress(15)
            
            # Compatible header configuration for both AI Studio & GCP keys
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={active_key}"
            headers = {'Content-Type': 'application/json'}
            
            prompt = f"""
            The user provided this video topic/idea (Franco, Arabic, or English): '{topic}'.
            Act as an elite YouTube content creator and producer. 
            1. Write an engaging voiceover script in English based on the core meaning of the topic. Tone: {style}. Word count around {target_words} words.
            2. Extract 3 broad, logical English search keywords/phrases (simple 1-2 words like 'luxury car', 'technology', 'futuristic city', 'space rocket') to search for stock images/visuals matching the core meaning.
            3. Generate 3 short viral hooks and comma-separated SEO tags.

            Return JSON format strictly as follows (no markdown wrapping, no extra text):
            {{
                "hooks": ["Hook 1", "Hook 2", "Hook 3"],
                "script": "Full voiceover narration script...",
                "tags": "tag1, tag2, tag3",
                "search_keywords": ["keyword1", "keyword2", "keyword3"]
            }}
            """
            
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            
            if response.status_code != 200:
                # Fallback to bearer header if standard query param fails
                headers_auth = {'Content-Type': 'application/json', 'Authorization': f'Bearer {active_key}'}
                url_alt = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
                response = requests.post(url_alt, headers=headers_auth, data=json.dumps(payload))
                
            if response.status_code != 200:
                st.error(f"API Error ({response.status_code}): {response.text}")
                st.stop()
                
            result = response.json()
            raw_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3].strip()
                
            data = json.loads(raw_text)
            progress_bar.progress(35)

            # Step 2: Voiceover Generation
            status_text.text(f"🎙️ Step 2/3: Synthesizing voiceover with {voice_option}... [Est: 10s]")
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

            # Step 3: Visuals Assembly
            status_text.text("🎥 Step 3/3: Assembling visual scenes and rendering final video... [Est: 15s]")
            
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

            if not custom_video_used and pexels_key:
                keywords = data.get("search_keywords", ["technology"])
                headers_pexels = {"Authorization": pexels_key}
                
                for kw in keywords[:3]:
                    try:
                        p_url = f"https://api.pexels.com/v1/search?query={kw.replace(' ', '%20')}&per_page=1"
                        res_p = requests.get(p_url, headers=headers_pexels, timeout=4)
                        if res_p.status_code == 200:
                            p_data = res_p.json()
                            if p_data.get("photos"):
                                img_src = p_data["photos"][0]["src"]["large"]
                                img_bytes = requests.get(img_src, timeout=4).content
                                with open("pexels_temp.jpg", "wb") as f:
                                    f.write(img_bytes)
                                scene_images.append(Image.open("pexels_temp.jpg").convert("RGB"))
                    except:
                        pass

            if not custom_video_used and len(scene_images) == 0:
                cinematic_colors = [
                    (15, 23, 42),
                    (49, 46, 129),
                    (88, 28, 135)
                ]
                for col in cinematic_colors:
                    canvas = Image.new('RGB', (width, height), color=col)
                    scene_images.append(canvas)

            if not custom_video_used:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))
                frames_per_scene = max(1, total_frames // len(scene_images))

                for frame_num in range(total_frames):
                    scene_idx = min(frame_num // frames_per_scene, len(scene_images) - 1)
                    base_scene = scene_images[scene_idx].copy()
                    
                    zoom_factor = 1.0 + 0.05 * np.sin(frame_num / 20.0)
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

                cmd_merge = f"ffmpeg -y -i {video_no_audio} -i {audio_final} -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest {final_mp4}"
                subprocess.run(cmd_merge, shell=True, check=True)

            progress_bar.progress(100)
            elapsed_time = time.time() - start_time
            status_text.success(f"🎉 Production Complete in {elapsed_time:.1f}s!")

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
