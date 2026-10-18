import streamlit as st
import requests
import json
import os
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont

# Page Configuration
st.set_page_config(page_title="Fully Automated AI Video Studio", page_icon="🎬", layout="wide")

st.title("🎬 Automated In-House AI Video Generator")
st.caption("Generate Script, AI Voiceover, and Visual Video File directly on your website in 1-Click!")

# Sidebar Configuration
st.sidebar.header("🔑 API Credentials")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get your free key from Google AI Studio")

# Input Layout
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("💡 Video Topic / Idea:", placeholder="e.g., The Untold Story of Tesla Roadster")
    style = st.selectbox(
        "🎭 Tone & Style:",
        ["Engaging & Dramatic", "Educational & Simple", "Storytelling & Inspiring", "Fast-Paced & Energetic"]
    )

with col2:
    duration = st.slider("⏱️ Target Duration (Minutes):", 1, 5, 1)

generate_btn = st.button("🚀 Build Complete Video In-House", type="primary", use_container_width=True)

if generate_btn:
    if not gemini_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar first!")
    elif not topic:
        st.warning("⚠️ Please provide a video topic or idea!")
    else:
        status_box = st.empty()
        
        try:
            # Step 1: Generate Script
            status_box.info("📝 Step 1/3: Writing professional script with Gemini AI...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={gemini_key}"
            prompt = f"Write a short, punchy YouTube voiceover script for: '{topic}'. Tone: {style}. Keep it concise and engaging. Output ONLY the plain text narration words."
            
            headers = {'Content-Type': 'application/json'}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            result = response.json()
            
            if response.status_code != 200:
                st.error(f"API Error: {result.get('error', {}).get('message', 'Unknown error')}")
                st.stop()
                
            script_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
            st.success("✅ Script Generated!")

            # Step 2: Generate Voiceover Audio
            status_box.info("🎙️ Step 2/3: Converting script into AI Voiceover (MP3)...")
            audio_file = "voiceover.mp3"
            tts = gTTS(text=script_text, lang='en', slow=False)
            tts.save(audio_file)
            
            # Play preview
            st.audio(audio_file)

            # Step 3: Generate Visual Graphic Slide (Poster / Video Frame)
            status_box.info("🎨 Step 3/3: Designing video graphics and rendering output package...")
            
            # Create a clean dynamic image frame for the video
            img = Image.new('RGB', (1280, 720), color=(15, 23, 42)) # Dark tech blue background
            d = ImageDraw.Draw(img)
            
            # Draw Title text onto the image canvas
            title_text = topic.upper()
            d.text((100, 300), title_text, fill=(255, 255, 255))
            
            image_path = "video_cover.png"
            img.save(image_path)

            status_box.success("🎉 All Assets Successfully Created In-House!")
            
            # Display assets
            st.image(image_path, caption="Generated Visual Frame", use_container_width=True)
            
            # Provide downloadable package bundle (Audio + Script + Frame)
            st.markdown("### 📦 Your In-House Production Package:")
            st.text_area("Generated Script Text:", script_text, height=150)
            
            with open(audio_file, "rb") as f:
                st.download_button(
                    label="⬇️ Download Voiceover Audio (MP3)",
                    data=f,
                    file_name="voiceover.mp3",
                    mime="audio/mp3",
                    use_container_width=True
                )
                
            with open(image_path, "img" if False else "rb") as f:
                st.download_button(
                    label="⬇️ Download Visual Backdrop (PNG)",
                    data=f,
                    file_name="visual_frame.png",
                    mime="image/png",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"An error occurred: {e}")
