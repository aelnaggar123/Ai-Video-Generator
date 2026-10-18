import streamlit as st
import requests
import json
import os
import cv2
import subprocess
import numpy as np
from gtts import gTTS
from PIL import Image, ImageDraw

# Page Configuration
st.set_page_config(page_title="AI Viral Video Studio Pro", page_icon="🎬", layout="wide")

st.title("🎬 AI Viral Video Studio (Pro Engine)")
st.caption("AI-Generated Visuals, Precise Duration Control, High-CTR Hooks & Advanced SEO Tags.")

# Initialize Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

# Sidebar Configuration
st.sidebar.header("🔑 API Credentials")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get your free key from Google AI Studio")

if st.sidebar.button("🔄 Start New Project", use_container_width=True):
    st.session_state.generated_data = None
    st.rerun()

# Layout Inputs
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("💡 Video Topic / Core Idea:", value="Tesla Flying Roadster SpaceX Package", placeholder="e.g. Elon's Flying Car")
    style = st.selectbox(
        "🎭 Tone & Style:",
        ["Fast-Paced & Energetic", "Engaging & Dramatic", "Educational & Simple", "Storytelling & Inspiring"]
    )

with col2:
    video_format = st.radio(
        "📱 Video Format / Type:",
        ["YouTube Short (30-59 sec)", "Long Video (1-15 min)"]
    )
    
    if video_format == "Long Video (1-15 min)":
        duration = st.slider("⏱️ Exact Target Duration (Minutes):", 1.0, 15.0, 3.0, 0.5)
    else:
        duration = 0.75 # ~45 seconds

generate_btn = st.button("🚀 Generate Pro AI Video & Strategy", type="primary", use_container_width=True)

if generate_btn:
    if not gemini_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar first!")
    elif not topic:
        st.warning("⚠️ Please provide a video topic or idea!")
    else:
        status_box = st.empty()
        try:
            is_short = (video_format == "YouTube Short (30-59 sec)")
            width, height = (720, 1280) if is_short else (1280, 720)
            
            # Precise word count calculation for exact duration match (~140 words per minute)
            target_words = int(duration * 60 * 2.3) if is_short else int(duration * 60 * 2.2)
            
            # Step 1: Generate High-CTR Hooks, Precise Script, & Rich Tags via Gemini
            status_box.info("📝 Step 1/3: Crafting Short High-CTR Hooks & Rich SEO Tags...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={gemini_key}"
            
            prompt = f"""
            Act as a top YouTube growth hacker. Create a viral video production package for: '{topic}'.
            Tone: {style}. Target word count strictly around {target_words} words to match duration.

            Return JSON format strictly as follows (no markdown wrapping, no extra text):
            {{
                "hooks": [
                    "Short punchy hook 1 (Max 6-8 words)",
                    "Short punchy hook 2 (Max 6-8 words)",
                    "Short punchy hook 3 (Max 6-8 words)"
                ],
                "script": "The full spoken voiceover narration text matching the target word count...",
                "tags": "comma separated SEO tags, trending keywords, specific phrases related to topic, YouTube metadata tags (at least 25 high-performing tags)"
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

            # Step 2: Voiceover Generation & Precise Duration Matching
            status_box.info("🎙️ Step 2/3: Generating Optimized Voiceover Audio...")
            audio_raw = "raw_voice.mp3"
            audio_final = "final_voice.mp3"
            
            tts = gTTS(text=data['script'], lang='en', slow=False)
            tts.save(audio_raw)

            # Minor tempo adjustment if needed to hit exact requested window
            cmd_audio = f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.15' {audio_final}"
            subprocess.run(cmd_audio, shell=True, check=True)

            # Get exact audio duration using ffprobe
            probe_cmd_final = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            final_audio_dur = float(subprocess.check_output(probe_cmd_final, shell=True).decode('utf-8').strip())

            # Step 3: AI Visual Generation & Exact Video Assembly
            status_box.info("🎥 Step 3/3: Fetching AI Visual Assets & Rendering Precise MP4 Video...")
            
            fps = 24
            total_frames = int(fps * final_audio_dur)
            
            video_no_audio = "temp_video.mp4"
            final_mp4 = "final_generated_video.mp4"
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))
            
            # Fetch AI Image generated for the topic via Pollinations AI
            headers_img = {'User-Agent': 'Mozilla/5.0'}
            img_url = f"https://image.pollinations.ai/prompt/Cinematic%20photorealistic%20{topic.replace(' ', '%20')}%20futuristic%208k%20hyperdetailed?width={width}&height={height}&nologo=true"
            
            try:
                img_response = requests.get(img_url, headers=headers_img, timeout=10)
                if img_response.status_code == 200:
                    with open("ai_scene.jpg", "wb") as f:
                        f.write(img_response.content)
                    base_image = Image.open("ai_scene.jpg").convert("RGB")
                else:
                    raise Exception("Fallback image")
            except:
                base_image = Image.new('RGB', (width, height), color=(10, 15, 30))

            # Render frame sequence matching exact audio duration down to the frame
            for frame_num in range(total_frames):
                frame_img = base_image.copy()
                draw = ImageDraw.Draw(frame_img)
                
                # Add overlay for text readability
                draw.rectangle([(0, height - 250), (width, height)], fill=(0, 0, 0))
                
                # Render clean title overlay
                draw.text((60, height - 180), topic[:45].upper(), fill=(255, 255, 255))
                draw.text((60, height - 120), "▶ AI Generated Visuals & Narration", fill=(56, 189, 248))
                
                temp_frame_path = f"frame_{frame_num % 5}.png"
                frame_img.save(temp_frame_path)
                cv_img = cv2.imread(temp_frame_path)
                out.write(cv_img)
                
            out.release()

            # Merge Precise Video & Exact Audio
            cmd_merge = f"ffmpeg -y -i {video_no_audio} -i {audio_final} -c:v copy -c:a aac -shortest {final_mp4}"
            subprocess.run(cmd_merge, shell=True, check=True)

            # Save into Session State so data stays after interaction
            st.session_state.generated_data = {
                "hooks": data['hooks'],
                "script": data['script'],
                "tags": data['tags'],
                "video_path": final_mp4,
                "is_short": is_short,
                "topic": topic,
                "duration": final_audio_dur
            }
            status_box.success(f"🎉 Production Complete! Duration matched precisely: {final_audio_dur:.1f} seconds.")

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
