import streamlit as st
import requests
import json
import os
import cv2
import subprocess
import time
import asyncio
import edge_tts
import numpy as np
from PIL import Image
from io import BytesIO

# Page Configuration
st.set_page_config(page_title="A & W AI Video Creation Tool", page_icon="🎬", layout="wide")

st.title("🎬 A & W AI Video Creation Tool")
st.caption("Ultra-Realistic Human Neural Voices, Real HD Visuals, Subtitles & Smooth Motion.")

# Initialize Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

# Sidebar Configuration
st.sidebar.header("⚙️ Settings & Realistic Human Voices")
gemini_key = st.sidebar.text_input("Gemini API Key (Optional / AIza...)", value="", type="password")

# High-Quality Human Neural Voice Mapping (Microsoft Edge Neural Engine)
voice_options_map = {
    "👧 Kids / Young Girl (Ana - Bright & Natural)": "en-US-AnaNeural",
    "👦 Young Boy / Kid (Eric - Playful & Dynamic)": "en-US-EricNeural",
    "👧 Young Girl / Storyteller (Maisie - Soft & Warm)": "en-GB-MaisieNeural",
    "👩 US Female (Jenny - Friendly & Energetic)": "en-US-JennyNeural",
    "👨 US Male (Guy - Deep & Natural Narration)": "en-US-GuyNeural",
    "👩 UK Female (Sonia - Elegant & Expressive)": "en-GB-SoniaNeural",
    "👨 UK Male (Ryan - Clear & Professional)": "en-GB-RyanNeural",
    "👨 Australian Male (William - Casual & Warm)": "en-AU-WilliamNeural",
    "👩 Canadian Female (Clara - Smooth & Clear)": "en-CA-ClaraNeural"
}

voice_option_label = st.sidebar.selectbox(
    "🎙️ Choose Human Voice Character:",
    list(voice_options_map.keys())
)

selected_voice_code = voice_options_map[voice_option_label]

if st.sidebar.button("🔄 Start New Project", use_container_width=True):
    st.session_state.generated_data = None
    st.rerun()

# Main Layout
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("💡 Video Topic / Idea (Franco, Arabic, or English):", value="Kids educational video teaching ABCD letters in a fun and fast way")
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
        duration = st.slider("⏱️ Target Duration (Minutes):", 1.0, 15.0, 1.0, 0.5)
    else:
        duration = 0.75

enable_subtitles = st.checkbox("💬 Burn-in Dynamic Subtitles on Video", value=True)

generate_btn = st.button("🚀 Generate Video with Realistic Human Voice", type="primary", use_container_width=True)

# Helper function to fetch guaranteed REAL HD photos
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

# Async Generator for Edge Realistic Human Voice
async def generate_human_voice(text, voice_code, output_file):
    communicate = edge_tts.Communicate(text, voice_code)
    await communicate.save(output_file)

if generate_btn:
    if not topic:
        st.warning("⚠️ Please provide a video topic or idea!")
    else:
        status_container = st.empty()
        metric_container = st.empty()
        progress_bar = st.progress(0)
        start_time = time.time()
        
        def update_progress(percent, text):
            progress_bar.progress(percent)
            metric_container.metric(label="📊 Production Progress", value=f"{percent}%", delta=f"{percent} out of 100%")
            status_container.info(text)

        try:
            is_short = (video_format == "YouTube Short (30-59 sec)")
            width, height = (720, 1280) if is_short else (1280, 720)
            target_words = int(duration * 135) if not is_short else int(duration * 60 * 2.2)
            
            update_progress(10, "📝 Step 1/4: Generating professional script & analyzing keywords...")
            
            script_data = None
            
            if gemini_key and gemini_key.startswith("AIza"):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                    prompt = f"""
                    Create a custom, engaging voiceover script in English about this topic: '{topic}'. 
                    Tone: {style}. Target Word Count around {target_words} words.
                    Also extract 6 English visual keywords for image search, 3 viral hooks, and SEO tags.
                    Return JSON strictly:
                    {{
                        "hooks": ["Hook 1", "Hook 2", "Hook 3"],
                        "script": "Full script...",
                        "tags": "tag1, tag2",
                        "search_keywords": ["keyword1", "keyword2", "keyword3", "keyword4"]
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
            
            if not script_data:
                clean_topic_words = [w for w in topic.split() if len(w) > 3]
                kw1 = clean_topic_words[0] if len(clean_topic_words) > 0 else "children"
                kw2 = clean_topic_words[1] if len(clean_topic_words) > 1 else "learning"
                
                custom_script = f"Hello everyone! Today we are exploring an incredible topic that is capturing so much attention: {topic}. When we take a closer look, it brings amazing insights and practical ideas. Let's dive right in and break down everything you need to know step by step."
                
                while len(custom_script.split()) < target_words:
                    custom_script += f" Furthermore, exploring more about {topic}, people everywhere are sharing their wonderful experiences and unique perspectives today."

                script_data = {
                    "hooks": [
                        f"The amazing truth about {topic}!",
                        f"Why everyone is loving {topic} right now!",
                        f"Everything you need to know about {topic}!"
                    ],
                    "script": custom_script,
                    "tags": f"{topic}, viral, kids, learning, trending",
                    "search_keywords": [kw1, kw2, "kids learning", "happy people", "children smiling", "colorful"]
                }
            
            data = script_data
            update_progress(30, f"🎙️ Step 2/4: Synthesizing Realistic Human Voice ({selected_voice_code})...")

            # Step 2: Realistic Human Voiceover Generation using Edge-TTS
            audio_raw = "raw_human_voice.mp3"
            audio_final = "final_voice.mp3"
            
            asyncio.run(generate_human_voice(data['script'], selected_voice_code, audio_raw))

            cmd_audio = f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.02' {audio_final}"
            subprocess.run(cmd_audio, shell=True, check=True)

            probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            final_audio_dur = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
            
            update_progress(50, "🌐 Step 3/4: Downloading real HD photos matching topic...")

            # Step 3: Fetch Real HD Photos
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
                keywords = data.get("search_keywords", ["children", "learning"])
                for idx, kw in enumerate(keywords):
                    img = fetch_guaranteed_web_photo(kw, width, height, index=idx)
                    if img:
                        scene_images.append(img)
                        
            if not custom_video_used and len(scene_images) == 0:
                for idx in range(6):
                    img = fetch_guaranteed_web_photo("children", width, height, index=idx)
                    if img:
                        scene_images.append(img)

            # Step 4: Render Motion Video & Burn Subtitles
            update_progress(70, "🎥 Step 4/4: Rendering motion video & burning subtitles...")
            
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
                        inner_p = 70 + int((frame_num / total_frames) * 20)
                        progress_bar.progress(inner_p)

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

            update_progress(100, "🎉 Production Complete Successfully!")
            elapsed_time = time.time() - start_time
            
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
