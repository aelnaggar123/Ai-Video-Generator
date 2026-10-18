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
st.caption("Custom Assets, Male/Female AI Voices, Clean Zoom Visuals, & Precise Duration Matching.")

# Initialize Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

# Default API Key set by user request
DEFAULT_API_KEY = "AQ.Ab8RN6Ia5F0k6PkHKVkdVBAsiBm9mBHfX9zXFZN27QMIRRt5ig"

# Sidebar Configuration
st.sidebar.header("⚙️ Settings & Key")
gemini_key = st.sidebar.text_input("Gemini API Key", value=DEFAULT_API_KEY, type="password", help="Editable default key")

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

# Map UI option to gTTS tld parameters
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

# Layout Inputs
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
            
            # Step 1: Script & Strategy Generation
            status_text.text("📝 Step 1/3: Analyzing Topic & Generating Script & SEO Strategy... [Est: 5s]")
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
                "scene_prompts": [
                    "Expressive cartoon character talking passionately about the topic, vibrant colors",
                    "Animated comic style illustration showing a surprising twist or reaction",
                    "Cartoon character pointing at a futuristic object, vibrant vector art background"
                ]
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

            # Step 2: Voiceover Audio Generation
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

            # Step 3: Visual Assembly (Custom Asset or Generated Cartoon + Clean Zoom)
            status_text.text("🎥 Step 3/3: Processing Clean Motion Visuals & Video Rendering... [Est: 15s]")
            
            fps = 24
            total_frames = int(fps * final_audio_dur)
            video_no_audio = "temp_video.mp4"
            final_mp4 = "final_generated_video.mp4"
            
            scene_images = []

            # Handle custom uploaded image/video if provided by user
            if uploaded_file is not None:
                if uploaded_file.type.startswith("image"):
                    custom_img = Image.open(uploaded_file).convert("RGB")
                    scene_images.append(custom_img)
                elif uploaded_file.type.startswith("video"):
                    with open("custom_input_vid.mp4", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    # Video overlay branch via ffmpeg directly
                    cmd_vid_audio = f"ffmpeg -y -stream_loop -1 -i custom_input_vid.mp4 -i {audio_final} -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest {final_mp4}"
                    subprocess.run(cmd_vid_audio, shell=True, check=True)
                    scene_images = None # Signals custom video bypass

            # If no custom image/video, fetch AI cartoon scene images
            if scene_images is not None and len(scene_images) == 0:
                scene_prompts = data.get("scene_prompts", [topic])
                for idx, s_prompt in enumerate(scene_prompts[:3]):
                    cleaned_prompt = s_prompt.replace(" ", "%20").replace(":", "").replace("?", "")
                    img_url = f"https://image.pollinations.ai/prompt/Expressive%20cartoon%20character%20comic%20{cleaned_prompt}%20vibrant%20colors?width={width}&height={height}&nologo=true"
                    try:
                        r = requests.get(img_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
                        if r.status_code == 200 and len(r.content) > 1000:
                            with open(f"cartoon_{idx}.jpg", "wb") as f:
                                f.write(r.content)
                            scene_images.append(Image.open(f"cartoon_{idx}.jpg").convert("RGB"))
                    except:
                        pass

            # Fallback canvas if empty
            if scene_images is not None and len(scene_images) == 0:
                fallback_canvas = Image.new('RGB', (width, height), color=(30, 27, 75))
                scene_images.append(fallback_canvas)

            # Render Zoom Frame Sequence if working with images
            if scene_images is not None:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))
                frames_per_scene = max(1, total_frames // len(scene_images))

                for frame_num in range(total_frames):
                    scene_idx = min(frame_num // frames_per_scene, len(scene_images) - 1)
                    base_scene = scene_images[scene_idx].copy()
                    
                    # Clean Smooth Dynamic Zoom Effect (No text bars at the bottom)
                    zoom_factor = 1.0 + 0.06 * np.sin(frame_num / 18.0)
                    zw, zh = int(width / zoom_factor), int(height / zoom_factor)
                    zx, zy = (width - zw) // 2, (height - zh) // 2
                    cropped = base_scene.crop((zx, zy, zx + zw, zy + zh))
                    active_frame = cropped.resize((width, height), Image.Resampling.LANCZOS)
                    
                    temp_frame_path = "temp_render_frame.png"
                    active_frame.save(temp_frame_path)
                    cv_img = cv2.imread(temp_frame_path)
                    out.write(cv_img)
                    
                    # Update progress bar smoothly during rendering
                    current_p = 60 + int((frame_num / total_frames) * 35)
                    progress_bar.progress(min(current_p, 95))

                out.release()

                # Merge Video & Audio
                cmd_merge = f"ffmpeg -y -i {video_no_audio} -i {audio_final} -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest {final_mp4}"
                subprocess.run(cmd_merge, shell=True, check=True)

            progress_bar.progress(100)
            elapsed_time = time.time() - start_time
            status_text.success(f"🎉 Production Complete in {elapsed_time:.1f}s! Lock below.")

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
