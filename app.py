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
from io import BytesIO

# Page Configuration
st.set_page_config(page_title="A & W AI Video Creation Tool", page_icon="🎬", layout="wide")

st.title("🎬 A & W AI Video Creation Tool")
st.caption("Advanced AI Scripting, Smart Real Web HD Visuals, Voices, Subtitles & Smooth Motion Assembly.")

# Initialize Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

# Retrieve API Key from Streamlit Secrets
secret_gemini_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""

# Sidebar Configuration
st.sidebar.header("⚙️ Settings & Voices")
gemini_key = st.sidebar.text_input("Gemini API Key (Optional / AIza...)", value=secret_gemini_key, type="password")

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
    uploaded_file = st.file_uploader("Upload your own Image or Video (Optional):", type=["jpg", "jpeg", "png", "mp4"])

with col2:
    video_format = st.radio(
        "📱 Video Format / Type:",
        ["YouTube Short (30-59 sec)", "Long Video (1-15 min)"]
    )
    
    if video_format == "Long Video (1-15 min)":
        duration = st.slider("⏱️ Target Duration (Minutes):", 1.0, 15.0, 2.0, 0.5)
    else:
        duration = 0.75

enable_subtitles = st.checkbox("💬 Burn-in Dynamic Subtitles on Video", value=True)

generate_btn = st.button("🚀 Generate Smart Context Video", type="primary", use_container_width=True)

# Helper function to fetch guaranteed REAL HD photos directly from live web image providers
def fetch_guaranteed_web_photo(keyword, width, height, index=0):
    clean_kw = keyword.strip().replace(" ", ",").lower()
    try:
        url = f"https://loremflickr.com/{width}/{height}/{clean_kw}?lock={index + 10}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200 and len(res.content) > 10000:
            return Image.open(BytesIO(res.content)).convert("RGB")
    except:
        pass

    try:
        url_alt = f"https://picsum.photos/seed/{clean_kw}{index}/{width}/{height}"
        res_alt = requests.get(url_alt, timeout=6)
        if res_alt.status_code == 200 and len(res_alt.content) > 10000:
            return Image.open(BytesIO(res_alt.content)).convert("RGB")
    except:
        pass

    return None

# Helper to split text into short readable subtitle chunks
def split_script_into_chunks(script_text, max_words=4):
    words = script_text.split()
    chunks = []
    current_chunk = []
    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_words or word.endswith(('.', '!', '?', ',')):
            chunks.append(" ".join(current_chunk))
            current_chunk = []
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

if generate_btn:
    active_gemini_key = gemini_key if gemini_key else secret_gemini_key
    
    if not topic:
        st.warning("⚠️ Please provide a video topic or idea!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        start_time = time.time()
        
        try:
            is_short = (video_format == "YouTube Short (30-59 sec)")
            width, height = (720, 1280) if is_short else (1280, 720)
            target_words = int(duration * 135) if not is_short else int(duration * 60 * 2.2)
            
            status_text.text("📝 Step 1/4: Deep analyzing topic & writing tailored script... [Est: 5s]")
            progress_bar.progress(15)
            
            script_data = None
            
            # Use Gemini with advanced prompt engineering to avoid templates and copy-paste
            if active_gemini_key and active_gemini_key.startswith("AIza"):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={active_gemini_key}"
                    prompt = f"""
                    You are an elite, highly intelligent documentary scriptwriter and content creator. 
                    The user has provided this specific topic/idea: '{topic}'.
                    
                    CRITICAL INSTRUCTIONS:
                    - Do NOT use generic templates or copy-paste the topic blindly.
                    - Analyze the core meaning, arguments, or questions raised in the user's topic deeply.
                    - Write a fully custom, engaging, professional voiceover script in English that directly discusses, analyzes, and explores this exact topic in depth. Tone: {style}. Target Word Count MUST be around EXACTLY {target_words} words.
                    - Extract 8-10 specific, highly relevant English visual search keywords related directly to the concepts inside the topic.
                    - Generate 3 short viral hooks and comma-separated SEO tags.

                    Return JSON format strictly as follows (no markdown wrapping, no extra text):
                    {{
                        "hooks": ["Hook 1", "Hook 2", "Hook 3"],
                        "script": "Full custom tailored script analyzing the topic...",
                        "tags": "tag1, tag2, tag3",
                        "search_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8"]
                    }}
                    """
                    payload = {"contents": [{"parts": [{"text": prompt}]}]}
                    response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                    if response.status_code == 200:
                        result = response.json()
                        raw_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                        if raw_text.startswith("```json"):
                            raw_text = raw_text[7:-3].strip()
                        elif raw_text.startswith("```"):
                            raw_text = raw_text[3:-3].strip()
                        script_data = json.loads(raw_text)
                except:
                    pass
            
            # Smart Custom Fallback if Gemini key is missing
            if not script_data:
                clean_topic_words = [w for w in topic.split() if len(w) > 3]
                main_kw = clean_topic_words[0] if clean_topic_words else "innovation"
                sec_kw = clean_topic_words[1] if len(clean_topic_words) > 1 else "technology"
                
                custom_fallback_script = f"Let's talk about a major subject that everyone is discussing right now: {topic}. When looking closely at this idea, we need to break down what makes it so important today. Analysts and experts have pointed out multiple dimensions to this story. On one hand, the core concept challenges traditional thinking and opens doors to new possibilities. On the other hand, skeptics argue we must look at the practical realities, risks, and long-term implications before jumping to conclusions. As this situation continues to evolve, understanding the nuances behind {topic} will help us see the bigger picture of where things are heading next."
                
                while len(custom_fallback_script.split()) < target_words:
                    custom_fallback_script += f" Furthermore, looking deeper into {topic}, the underlying mechanics and market reactions show a clear shift in perspective. Stakeholders are weighing both the potential rewards and the hidden challenges."

                script_data = {
                    "hooks": [
                        f"The hidden reality behind {topic}!",
                        f"Why everyone is getting {topic} completely wrong!",
                        f"The ultimate breakdown of {topic}!"
                    ],
                    "script": custom_fallback_script,
                    "tags": f"{topic}, analysis, trending, insights, deep dive",
                    "search_keywords": [main_kw, sec_kw, "business", "innovation", "future", "strategy", "technology", "modern"]
                }
            
            data = script_data
            progress_bar.progress(30)

            # Step 2: Voiceover Generation
            status_text.text(f"🎙️ Step 2/4: Synthesizing voiceover ({target_words} words)... [Est: 10s]")
            audio_raw = "raw_voice.mp3"
            audio_final = "final_voice.mp3"
            
            selected_tld = tld_map.get(voice_option, "com")
            tts = gTTS(text=data['script'], lang='en', tld=selected_tld, slow=False)
            tts.save(audio_raw)

            cmd_audio = f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.05' {audio_final}"
            subprocess.run(cmd_audio, shell=True, check=True)

            probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            final_audio_dur = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
            progress_bar.progress(50)

            # Step 3: Fetch Real HD Photos
            status_text.text("🌐 Step 3/4: Downloading HD photos matching topic keywords... [Est: 10s]")
            
            fps = 24
            total_frames = int(fps * final_audio_dur)
            video_no_audio = "temp_video.mp4"
            video_with_subtitles = "temp_subtitles.mp4"
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

            if not custom_video_used:
                keywords = data.get("search_keywords", ["technology", "innovation", "future"])
                for idx, kw in enumerate(keywords):
                    img = fetch_guaranteed_web_photo(kw, width, height, index=idx)
                    if img:
                        scene_images.append(img)
                        
            if not custom_video_used and len(scene_images) == 0:
                for idx in range(6):
                    img = fetch_guaranteed_web_photo("technology", width, height, index=idx)
                    if img:
                        scene_images.append(img)

            # Step 4: Render Motion Video & Burn Subtitles
            status_text.text("🎥 Step 4/4: Rendering motion video & burning subtitles... [Est: 15s]")
            if not custom_video_used and len(scene_images) > 0:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(video_no_audio, fourcc, fps, (width, height))
                
                frames_per_scene = max(1, total_frames // len(scene_images))

                for frame_num in range(total_frames):
                    scene_idx = min(frame_num // frames_per_scene, len(scene_images) - 1)
                    scene_frame_offset = frame_num % frames_per_scene
                    
                    base_img = np.array(scene_images[scene_idx].resize((width + 100, height + 100), Image.Resampling.LANCZOS))
                    
                    progress_in_scene = scene_frame_offset / float(frames_per_scene)
                    shift_x = int(progress_in_scene * 80)
                    shift_y = int(progress_in_scene * 40)
                    
                    cropped_frame = base_img[shift_y:shift_y + height, shift_x:shift_x + width]
                    cv_bgr_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_RGB2BGR)
                    
                    out.write(cv_bgr_frame)
                    
                    if frame_num % 100 == 0:
                        current_p = 50 + int((frame_num / total_frames) * 35)
                        progress_bar.progress(min(current_p, 85))

                out.release()

                video_to_merge = video_no_audio
                if enable_subtitles:
                    try:
                        chunks = split_script_into_chunks(data['script'], max_words=4)
                        srt_content = ""
                        time_per_chunk = final_audio_dur / float(len(chunks))
                        
                        for idx, chunk in enumerate(chunks):
                            start_s = idx * time_per_chunk
                            end_s = (idx + 1) * time_per_chunk
                            
                            def fmt_time(s):
                                hrs = int(s // 3600)
                                mins = int((s % 3600) // 60)
                                secs = int(s % 60)
                                millis = int((s - int(s)) * 1000)
                                return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"
                                
                            srt_content += f"{idx + 1}\n{fmt_time(start_s)} --> {fmt_time(end_s)}\n{chunk.upper()}\n\n"
                            
                        with open("subtitles.srt", "w", encoding="utf-8") as f:
                            f.write(srt_content)
                            
                        font_size = 22 if is_short else 28
                        subtitle_filter = f"subtitles=subtitles.srt:force_style='FontSize={font_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4,Alignment=2,MarginV=60'"
                        
                        cmd_srt = f"ffmpeg -y -i {video_no_audio} -vf \"{subtitle_filter}\" -c:v libx264 {video_with_subtitles}"
                        subprocess.run(cmd_srt, shell=True, check=True)
                        video_to_merge = video_with_subtitles
                    except:
                        pass

                cmd_merge = f"ffmpeg -y -i {video_to_merge} -i {audio_final} -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest {final_mp4}"
                subprocess.run(cmd_merge, shell=True, check=True)

            progress_bar.progress(100)
            elapsed_time = time.time() - start_time
            status_text.success(f"🎉 Complete! Video Duration: {final_audio_dur:.1f}s (Rendered in {elapsed_time:.1f}s)")

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
