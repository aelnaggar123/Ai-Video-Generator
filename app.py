import streamlit as st
import requests
import json
import os
import cv2
import subprocess
from gtts import gTTS
from PIL import Image, ImageDraw

# Page Configuration
st.set_page_config(page_title="AI Video Studio - Full Auto", page_icon="🎬", layout="wide")

st.title("🎬 1-Click AI Video Studio")
st.caption("Generate Custom Long-Form Videos (1-15 Mins) or Viral Vertical Shorts (30-59 Secs) instantly!")

# Sidebar Configuration
st.sidebar.header("🔑 API Credentials")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get your free key from Google AI Studio")

# Layout Inputs
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("💡 Video Topic / Idea:", value="1 Second to 60mph: Inside Tesla’s Insane SpaceX Death Trap")
    style = st.selectbox(
        "🎭 Tone & Style:",
        ["Engaging & Dramatic", "Educational & Simple", "Storytelling & Inspiring", "Fast-Paced & Energetic"]
    )

with col2:
    video_format = st.radio(
        "📱 Video Format / Type:",
        ["YouTube Short (30-59 sec)", "Long Video (1-15 min)"]
    )
    
    if video_format == "Long Video (1-15 min)":
        duration = st.slider("⏱️ Target Duration (Minutes):", 1, 15, 3)
    else:
        duration = 1 # Representing short format duration (<1 min)

generate_btn = st.button("🚀 Generate Full Video", type="primary", use_container_width=True)

if generate_btn:
    if not gemini_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar first!")
    elif not topic:
        st.warning("⚠️ Please provide a video topic or idea!")
    else:
        status_box = st.empty()
        
        try:
            # Determine dimensions and length constraints based on selected mode
            is_short = (video_format == "YouTube Short (30-59 sec)")
            width, height = (720, 1280) if is_short else (1280, 720) # 9:16 vertical for Shorts, 16:9 for Long
            
            if is_short:
                prompt_length = "between 30 and 50 seconds when spoken aloud (around 70 to 110 words)"
            else:
                prompt_length = f"suitable for a {duration}-minute YouTube video (around {duration * 130} words)"

            # Step 1: Generate Script
            status_box.info("📝 Step 1/3: Writing high-retention script with Gemini AI...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={gemini_key}"
            prompt = f"Write a high-energy YouTube voiceover script for: '{topic}'. Tone: {style}. Length requirement: {prompt_length}. Output ONLY plain spoken narration words, with no brackets, timestamps, or tags."
            
            headers = {'Content-Type': 'application/json'}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            result = response.json()
            
            if response.status_code != 200:
                st.error(f"API Error: {result.get('error', {}).get('message', 'Unknown error')}")
                st.stop()
                
            script_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
            st.success("✅ Script Written!")
            with st.expander("Show Generated Script Text"):
                st.write(script_text)

            # Step 2: Generate Audio
            status_box.info("🎙️ Step 2/3: Converting script into AI Voiceover (MP3)...")
            audio_path = "voice.mp3"
            tts = gTTS(text=script_text, lang='en', slow=False)
            tts.save(audio_path)

            # Step 3: Render Visual Frames & Merge into MP4
            status_box.info("🎥 Step 3/3: Rendering frames & assembling MP4 video file...")
            
            # Create Frame (Vertical or Horizontal depending on format)
            img = Image.new('RGB', (width, height), color=(15, 23, 42)) # Dark stylish backdrop
            draw = ImageDraw.Draw(img)
            
            # Formatting Text Placement
            if is_short:
                draw.text((60, 450), "YOUTUBE SHORT", fill=(56, 189, 248))
                draw.text((60, 520), topic[:30] + ("..." if len(topic) > 30 else ""), fill=(255, 255, 255))
                draw.text((60, 620), "🎙️ AI Narration", fill=(148, 163, 184))
            else:
                draw.text((80, 260), "AI VIDEO STUDIO", fill=(56, 189, 248))
                draw.text((80, 320), topic[:45] + ("..." if len(topic) > 45 else ""), fill=(255, 255, 255))
                draw.text((80, 420), "🎙️ AI Narration", fill=(148, 163, 184))
            
            frame_path = "frame.png"
            img.save(frame_path)

            # Generate Silent Video Clip with OpenCV
            video_no_audio = "temp_video.mp4"
            final_mp4 = "final_generated_video.mp4"
            
            cv_img = cv2.imread(frame_path)
            fps = 24
            render_duration = 45 if is_short else min(duration * 60, 300) # Render frame sequence
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))
            
            for _ in range(fps * render_duration):
                out.write(cv_img)
            out.release()

            # Merge Video & Audio using ffmpeg
            cmd = f"ffmpeg -y -i {video_no_audio} -i {audio_path} -c:v copy -c:a aac -shortest {final_mp4}"
            subprocess.run(cmd, shell=True, check=True)

            status_box.success("🎉 Your Video is Fully Ready!")
            st.markdown("---")
            
            # Display Final Video
            st.video(final_mp4)
            
            # Download Button
            file_label = "Shorts_MP4" if is_short else "Video_MP4"
            with open(final_mp4, "rb") as f:
                st.download_button(
                    label=f"⬇️ Download {file_label}",
                    data=f,
                    file_name=f"AI_{file_label}_{topic[:10].replace(' ', '_')}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"An error occurred during video assembly: {e}")
