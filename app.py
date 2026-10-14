import streamlit as st
from google import genai
import requests

# Page Configuration
st.set_page_config(page_title="AI Video Studio", page_icon="🎬", layout="wide")

# Main Title & Subtitle
st.title("🎬 AI Video Content Studio")
st.caption("Automated Scriptwriting, Scene Prompts & Production Pipeline")

# Sidebar Configuration
st.sidebar.header("🔑 API Credentials")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get your free key from Google AI Studio")
eleven_key = st.sidebar.text_input("ElevenLabs API Key (Optional)", type="password", help="For AI voice generation")

# Input Layout
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("💡 Video Topic / Idea:", placeholder="e.g., The Untold Story of Apple in 3 Minutes")
    style = st.selectbox(
        "🎭 Tone & Style:",
        ["Engaging & Dramatic", "Educational & Simple", "Storytelling & Inspiring", "Professional & Formal", "Fast-Paced & Energetic"]
    )

with col2:
    duration = st.slider("⏱️ Target Duration (Minutes):", 1, 10, 3)

generate_btn = st.button("🚀 Generate Script & Production Plan", type="primary", use_container_width=True)

# Main Generation Logic
if generate_btn:
    if not gemini_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar first!")
    elif not topic:
        st.warning("⚠️ Please provide a video topic or idea!")
    else:
        with st.spinner("Generating script and visual direction with Gemini AI..."):
            try:
                # Initialize Gemini API Client
                client = genai.Client(api_key=gemini_key)
                
                prompt = f"""
                You are an expert YouTube content creator and scriptwriter. 
                Create a comprehensive YouTube video blueprint for the topic: '{topic}'.
                Target Duration: {duration} minutes.
                Tone & Style: {style}.

                Structure your output clearly with the following sections:
                1. 🎯 Catchy Titles & Clickable Hook Options
                2. 🎙️ Complete Voiceover Script (timestamps and scene-by-scene breakdown)
                3. 🎥 Visual Prompts & B-Roll Ideas (detailed prompts for stock footage or AI image generators)
                4. 📌 Suggested YouTube Tags & SEO Keywords
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                
                st.success("✨ Script & Blueprint Generated Successfully!")
                st.markdown("---")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Error connecting to service: {e}")
