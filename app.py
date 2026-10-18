import streamlit as st
import requests
import json
import os
from gtts import gTTS
from moviepy import TextClip, AudioFileClip, CompositeVideoClip, ColorClip

# Page Configuration
st.set_page_config(page_title="AI Video Studio - Full Auto", page_icon="🎬", layout="wide")

st.title("🎬 Fully Automated AI Video Generator")
st.caption("Generate Script, Voiceover, Visuals & Assembled MP4 Video in One Click!")

# Sidebar Configuration
st.sidebar.header("🔑 API Credentials")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get your free key from Google AI Studio")

# Input Layout
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("💡 Video Topic / Idea:", placeholder="e.g., The Untold Story of Apple in 3 Minutes")
    style = st.selectbox(
        "🎭 Tone & Style:",
        ["Engaging & Dramatic", "Educational & Simple", "Storytelling & Inspiring", "Professional & Formal"]
    )

with col2:
    duration = st.slider("⏱️ Target Duration (Minutes):", 1, 5, 1)

generate_btn = st.button("🚀 Generate Full MP4 Video", type="primary", use_container_width=True)

if generate_btn:
    if not gemini_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar first!")
    elif not topic:
        st.warning("⚠️ Please provide a video topic or idea!")
    else:
        status_box = st.empty()
        
        # Step 1: Generate Script
        status_box.info("📝 Step 1/4: Writing script with Gemini AI...")
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={gemini_key}"
            prompt = f"Write a short, high-energy YouTube voiceover script for: '{topic}'. Keep it under {duration*60} seconds. Output ONLY the plain text voiceover words to be spoken, no timestamps, no brackets, no extra formatting."
            
            headers = {'Content-Type': 'application/json'}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            result = response.json()
            
            if response.status_code != 200:
                st.error(f"API Error: {result.get('error', {}).get('message', 'Unknown error')}")
                st.stop()
                
            script_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
            st.success("✅ Script Generated!")
            with st.expander("Show Raw Script"):
                st.write(script_text)

            # Step 2: Generate Voiceover Audio
            status_box.info("🎙️ Step 2/4: Generating AI Voiceover audio...")
            audio_file = "voiceover.mp3"
            tts = gTTS(text=script_text, lang='en', slow=False)
            tts.save(audio_file)
            st.audio(audio_file)

            # Step 3: Video Assembly
            status_box.info("🎥 Step 3/4: Assembling video slides and audio track...")
            audio_clip = AudioFileClip(audio_file)
            video_duration = audio_clip.duration

            # Create a stylish dark background
            bg_clip = ColorClip(size=(1280, 720), color=(15, 23, 42), duration=video_duration)
            
            # Add Title Text Overlay
            txt_clip = TextClip(
                text=topic.upper(), 
                font_size=45, 
                color='white', 
                size=(1100, 600),
                method='caption'
            ).with_duration(video_duration).with_position('center')

            # Combine Video + Audio
            final_clip = CompositeVideoClip([bg_clip, txt_clip]).with_audio(audio_clip)
            
            output_video_path = "final_generated_video.mp4"
            status_box.info("⚡ Step 4/4: Rendering final MP4 file (this may take a minute)...")
            final_clip.write_videofile(output_video_path, fps=24, codec="libx264", audio_codec="aac")

            status_box.success("🎉 Your Video is Ready!")
            
            # Display Final Video
            st.video(output_video_path)
            
            # Download Button
            with open(output_video_path, "rb") as file:
                st.download_button(
                    label="⬇️ Download Ready Video (MP4)",
                    data=file,
                    file_name=f"{topic.replace(' ', '_')}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"An error occurred during video creation: {e}")
