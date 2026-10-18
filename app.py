import streamlit as st
import requests
import json
import base64
from gtts import gTTS

# Page Configuration
st.set_page_config(page_title="AI Video Content Studio", page_icon="🎬", layout="wide")

st.title("🎬 AI Video Automation Studio")
st.caption("Generate Script, Audio Voiceover, Visual Prompts & SEO Metadata instantly!")

# Sidebar Credentials
st.sidebar.header("🔑 API Credentials")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get your free key from Google AI Studio")

# Layout Inputs
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("💡 Video Topic / Idea:", placeholder="e.g., The Truth Behind Tesla's Flying Roadster")
    style = st.selectbox(
        "🎭 Tone & Style:",
        ["Engaging & Dramatic", "Educational & Simple", "Storytelling & Inspiring", "Fast-Paced & Energetic"]
    )

with col2:
    duration = st.slider("⏱️ Target Duration (Minutes):", 1, 5, 2)

generate_btn = st.button("🚀 Generate Script & Audio Voiceover", type="primary", use_container_width=True)

if generate_btn:
    if not gemini_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar first!")
    elif not topic:
        st.warning("⚠️ Please provide a video topic or idea!")
    else:
        with st.spinner("⚡ Step 1/2: Generating High-Retention Script & Visual Blueprint..."):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={gemini_key}"
                
                prompt = f"""
                You are an expert YouTube content creator. Create a complete viral video blueprint for: '{topic}'.
                Target Duration: {duration} minutes. Tone: {style}.

                Structure the response clearly into these sections:
                1. 🎯 Catchy Titles & Clickable Hook Options
                2. 🎙️ Complete Voiceover Script (Plain text narrative, engaging pacing)
                3. 🎥 Scene-by-Scene Visual Prompts (Prompts for Midjourney / Runway / Stock footage)
                4. 📌 Suggested YouTube Tags & SEO Keywords
                """

                headers = {'Content-Type': 'application/json'}
                payload = {"contents": [{"parts": [{"text": prompt}]}]}

                response = requests.post(url, headers=headers, data=json.dumps(payload))
                result = response.json()

                if response.status_code != 200:
                    st.error(f"API Error: {result.get('error', {}).get('message', 'Unknown error')}")
                    st.stop()

                script_text = result['candidates'][0]['content']['parts'][0]['text']

                st.success("✨ Script & Production Plan Generated!")
                st.markdown("---")

                # Step 2: Generate Voiceover
                st.subheader("🎙️ AI Voiceover Audio (Generated)")
                with st.spinner("⚡ Step 2/2: Converting Script to Voiceover MP3..."):
                    # Extract roughly the narration part for gTTS
                    clean_text_for_audio = topic + ". " + script_text[:1000] # Clean sample preview for audio
                    tts = gTTS(text=clean_text_for_audio, lang='en', slow=False)
                    audio_filename = "voiceover.mp3"
                    tts.save(audio_filename)

                    # Display Audio Player
                    st.audio(audio_filename)

                    # Download Audio Button
                    with open(audio_filename, "rb") as file:
                        st.download_button(
                            label="⬇️ Download Voiceover (MP3)",
                            data=file,
                            file_name=f"{topic.replace(' ', '_')}_voiceover.mp3",
                            mime="audio/mp3",
                            use_container_width=True
                        )

                st.markdown("---")
                st.markdown(script_text)

            except Exception as e:
                st.error(f"An error occurred: {e}")
