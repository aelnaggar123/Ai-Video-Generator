import streamlit as st
import requests
import json
import os
import cv2
import subprocess
from gtts import gTTS
from PIL import Image, ImageDraw

# Page Configuration
st.set_page_config(page_title="AI Video Studio - One Click MP4", page_icon="🎬", layout="wide")

st.title("🎬 1-Click AI Video Generator")
st.caption("Generate Script, AI Voiceover & Assembled MP4 Video Directly on Your Website!")

# Sidebar Configuration
st.sidebar.header("🔑 API Credentials")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get your free key from Google AI Studio")

# Input Layout
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("💡 Video Topic / Idea:", value="1 Second to 60mph: Inside Tesla’s Insane SpaceX Death Trap")
    style = st.selectbox(
        "🎭 Tone & Style:",
        ["Engaging & Dramatic", "Educational & Simple", "Storytelling & Inspiring", "Fast-Paced & Energetic"]
    )

with col2:
    duration = st.slider("⏱️ Target Duration (Minutes):", 1, 3, 1)

generate_btn = st.button("🚀 Generate Full MP4 Video", type="primary", use_container_width=True)

if generate_btn:
    if not gemini_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar first!")
    elif not topic:
        st.warning("⚠️ Please provide a video topic or idea!")
    else:
        status_box = st.empty()
        
        try:
            # Step 1: Generate Short Script
            status_box.info("📝 Step 1/3: Generating high-retention script with Gemini AI...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={gemini_key}"
            prompt = f"Write a short, punchy YouTube voiceover script (around 30-45 seconds) for: '{topic}'. Tone: {style}. Output ONLY plain spoken narrative text, no brackets or tags."
            
            headers = {'Content-Type': 'application/json'}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            result = response.json()
            
            if response.status_code != 200:
                st.error(f"API Error: {result.get('error', {}).get('message', 'Unknown error')}")
                st.stop()
                
            script_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
            st.success("✅ Script Written!")

            # Step 2: Generate Audio
            status_box.info("🎙️ Step 2/3: Converting script into AI Voiceover (MP3)...")
            audio_path = "voice.mp3"
            tts = gTTS(text=script_text, lang='en', slow=False)
            tts.save(audio_path)

            # Step 3: Render Visual Frames & Merge into MP4
            status_box.info("🎥 Step 3/3: Rendering frames & assembling final MP4 video file...")
            
            # Create a cover frame image using Pillow
            width, height = 1280, 720
            img = Image.new('RGB', (width, height), color=(15, 23, 42)) # Dark stylish background
            draw = ImageDraw.Draw(img)
            
            # Draw Title & Text
            draw.text((80, 260), "AI VIDEO STUDIO", fill=(56, 189, 248))
            draw.text((80, 320), topic[:45] + ("..." if len(topic) > 45 else ""), fill=(255, 255, 255))
            draw.text((80, 420), "🎙️ Narrated by AI Engine", fill=(148, 163, 184))
            
            frame_path = "frame.png"
            img.save(frame_path)

            # Generate Silent Video Clip with OpenCV
            video_no_audio = "temp_video.mp4"
            final_mp4 = "final_generated_video.mp4"
            
            # Read frame and convert for OpenCV
            cv_img = cv2.imread(frame_path)
            fps = 24
            duration_sec = 35 # Default render duration
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))
            
            for _ in range(fps * duration_sec):
                out.write(cv_img)
            out.release()

            # Merge Video & Audio using ffmpeg
            cmd = f"ffmpeg -y -i {video_no_audio} -i {audio_path} -c:v copy -c:a aac -shortest {final_mp4}"
            subprocess.run(cmd, shell=True, check=True)

            status_box.success("🎉 Your Video is Fully Ready!")
            st.markdown("---")
            
            # Display Final Video Directly on Page
            st.video(final_mp4)
            
            # Download Button for the complete MP4
            with open(final_mp4, "rb") as f:
                st.download_button(
                    label="⬇️ Download Complete Video (MP4)",
                    data=f,
                    file_name=f"AI_Video_{topic[:15].replace(' ', '_')}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"An error occurred during video assembly: {e}")
