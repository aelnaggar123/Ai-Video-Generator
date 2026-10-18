import streamlit as st
import requests
import json

# Page Configuration
st.set_page_config(page_title="AI Video Studio", page_icon="🎬", layout="wide")

# Main Title & Subtitle
st.title("🎬 AI Video Content Studio")
st.caption("Automated Scriptwriting, Scene Prompts & Production Pipeline")

# Sidebar Configuration
st.sidebar.header("🔑 API Credentials")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get your free key from Google AI Studio")

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
                # Using the active gemini-2.5-flash model endpoint
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                
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
                
                headers = {'Content-Type': 'application/json'}
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
                
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                result = response.json()
                
                if response.status_code == 200:
                    script_text = result['candidates'][0]['content']['parts'][0]['text']
                    st.success("✨ Script & Blueprint Generated Successfully!")
                    st.markdown("---")
                    st.markdown(script_text)
                else:
                    st.error(f"API Error: {result.get('error', {}).get('message', 'Unknown error')}")
                
            except Exception as e:
                st.error(f"Error connecting to service: {e}")
