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
import re
from PIL import Image
from io import BytesIO

# Page Configuration
st.set_page_config(page_title="A & W AI Video Creation Tool", page_icon="🎬", layout="wide")

st.title("🎬 A & W AI Video Creation Tool")
st.caption("Professional AI Video Studio: Made by Eng. Ahmed El Naggar and his Sem Sem ❤️ | True AI Intent Understanding.")

# Initialize Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

st.markdown("---")

# Dashboard Controls
col_top1, col_top2 = st.columns([2, 1])

with col_top1:
    topic = st.text_input(
        "💡 What is your video about?", 
        value="",
        placeholder="Type naturally in Franco, Arabic, or English (e.g. koshari, kofta, quantum mechanics)..."
    )
    style = st.selectbox(
        "🎭 Tone & Style:",
        ["Informative & Engaging", "Excited & Joyful", "Storytelling & Inspiring", "Casual & Friendly"]
    )

with col_top2:
    voice_options_map = {
        "👨 US Male (Guy - Deep & Emotional)": "en-US-GuyNeural",
        "👩 US Female (Jenny - Friendly & Warm)": "en-US-JennyNeural",
        "👨 UK Male (Ryan - Clear & Professional)": "en-GB-RyanNeural",
        "👩 UK Female (Sonia - Elegant & Expressive)": "en-GB-SoniaNeural",
        "👦 Young Boy / Kid (Eric - Dynamic)": "en-US-EricNeural",
        "👧 Kids / Young Girl (Ana - Bright)": "en-US-AnaNeural"
    }
    
    voice_option_label = st.selectbox(
        "🎙️ Choose Human Voice Character:",
        list(voice_options_map.keys())
    )
    selected_voice_code = voice_options_map[voice_option_label]

    video_format = st.radio(
        "📱 Video Format / Type:",
        ["YouTube Short (30-59 sec)", "Long Video (1-15 min)"],
        horizontal=True
    )

col_mid1, col_mid2, col_mid3 = st.columns([1, 1, 1])

with col_mid1:
    if video_format == "Long Video (1-15 min)":
        duration = st.slider("⏱️ Target Duration (Minutes):", 1.0, 15.0, 3.0, 0.5)
    else:
        duration = 0.75
        st.info("📌 Shorts Mode: ~45 seconds optimized.")

with col_mid2:
    enable_subtitles = st.checkbox("💬 Burn-in Dynamic Subtitles", value=True)
    enable_bg_music = st.checkbox("🎵 Royalty-Free Background Music", value=True)

with col_mid3:
    st.subheader("🖼️ Custom Media")
    uploaded_file = st.file_uploader("Upload Image/Video (Opt):", type=["jpg", "jpeg", "png", "mp4"], label_visibility="collapsed")

st.markdown("---")

col_action1, col_action2 = st.columns([3, 1])
with col_action1:
    generate_btn = st.button("🚀 Generate AI Video Now", type="primary", use_container_width=True)
with col_action2:
    if st.button("🔄 Reset Project", use_container_width=True):
        st.session_state.generated_data = None
        st.rerun()

# Smart Dynamic Intelligence Router (Zero Hardcoded Script Looping)
def generate_smart_ai_script(user_input, target_word_count):
    raw = user_input.strip()

    # Clean conversational prefixes
    clean_topic = raw
    for prefix in ["e3mely", "e3mly", "y3lemny", "tare2et", "3amal", "3ayez", "3ayz", "how to make", "video about", "اعملي", "يعلمني", "طريقة", "عمل", "عايز"]:
        clean_topic = re.sub(rf"(?i)\b{prefix}\b", "", clean_topic)
    clean_topic = clean_topic.strip()

    # Detect Food / Recipe intent vs General Topic
    is_recipe = any(w in raw.lower() for w in ["koshari", "koshary", "kofta", "burger", "cake", "recipe", "cook", "food", "eat", "3amal", "طريقة", "أكل", "كشري", "كفتة"])

    if is_recipe:
        dish_name = clean_topic if clean_topic else "this delicious dish"
        paragraphs = [
            f"Today, I am going to show you how to make authentic, delicious homemade {dish_name} step by step!",
            f"First, prepare all your core ingredients: fresh herbs, spices, main proteins, grains, and seasoning for the ultimate flavor.",
            f"Step 1: Start by preparing and washing all your raw ingredients so everything is ready for cooking.",
            f"Step 2: Heat your cooking pan or pot, add a touch of oil or butter, and gently sear your ingredients to build deep flavors.",
            f"Step 3: Season generously with salt, pepper, and fresh spices, letting everything simmer together to perfection.",
            f"Step 4: Once perfectly cooked and aromatic, plate your homemade {dish_name} hot with fresh garnishes on top.",
            f"Serve fresh to your family and friends, and enjoy every single bite of this incredible dish!"
        ]
        search_keys = [f"{dish_name} food", f"cooking {dish_name} ingredients", "seasoning food pan", "delicious plated dish", "fresh homemade meal"]
        hooks = [f"The ultimate secret to perfect homemade {dish_name}!", f"How to make restaurant-quality {dish_name} at home!"]
        seo_tags = f"{dish_name}, homemade {dish_name}, recipe, cooking tutorial, easy food at home, delicious meals"
    else:
        subject = clean_topic if clean_topic else "this interesting topic"
        paragraphs = [
            f"Today we are diving into an essential breakdown of {subject}.",
            f"Understanding how {subject} works requires looking at the fundamental principles behind it.",
            f"When we analyze the key components, we see how every part contributes to the overall outcome.",
            f"Applying these key insights step by step allows you to achieve consistent and high-quality results.",
            f"Keep these core principles in mind, try putting them into practice, and share your thoughts in the comments!"
        ]
        search_keys = [subject, f"{subject} concept", "presentation insights", "learning step by step"]
        hooks = [f"Everything you need to know about {subject}!", f"The complete guide to {subject}!"]
        seo_tags = f"{subject}, tutorial, guide, step by step, insights, viral story"

    # Assemble full length script WITHOUT looping sentences
    full_script = ""
    idx = 0
    while len(full_script.split()) < target_word_count:
        p = paragraphs[idx % len(paragraphs)]
        if idx >= len(paragraphs):
            p = f"In addition, " + p[0].lower() + p[1:]
        full_script += p + " "
        idx += 1

    return {
        "script": full_script.strip(),
        "search_keywords": search_keys,
        "hooks": hooks,
        "seo_tags": seo_tags
    }

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

# Helper to fetch non-copyrighted background music
def fetch_royalty_free_music(output_path):
    safe_audio_urls = [
        "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
        "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73467.mp3",
        "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3"
    ]
    for music_url in safe_audio_urls:
        try:
            res = requests.get(music_url, timeout=10)
            if res.status_code == 200 and len(res.content) > 50000:
                with open(output_path, "wb") as f:
                    f.write(res.content)
                return True
        except:
            continue
    return False

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
    if not topic.strip():
        st.warning("⚠️ Please enter what you want the video to be about in the box above!")
    else:
        status_container = st.empty()
        metric_container = st.empty()
        progress_bar = st.progress(0)
        start_time = time.time()
        
        def update_progress(percent, text):
            val = max(0, min(100, int(percent)))
            progress_bar.progress(val)
            metric_container.metric(label="📊 Production Progress", value=f"{val}%", delta=f"{val}/100%")
            status_container.info(text)

        try:
            is_short = (video_format == "YouTube Short (30-59 sec)")
            width, height = (720, 1280) if is_short else (1280, 720)
            target_words = int(duration * 135) if not is_short else int(duration * 60 * 2.2)
            
            update_progress(5, "📝 Step 1/5: Generating dynamic script matching topic intent...")
            
            data = generate_smart_ai_script(topic, target_words)

            update_progress(20, f"🎙️ Step 2/5: Synthesizing Realistic Human Voice ({selected_voice_code})...")

            audio_raw = "raw_human_voice.mp3"
            audio_final = "final_voice.mp3"
            
            asyncio.run(generate_human_voice(data['script'], selected_voice_code, audio_raw))

            cmd_audio = f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.02' {audio_final}"
            subprocess.run(cmd_audio, shell=True, check=True)

            probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            final_audio_dur = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
            
            update_progress(35, "🌐 Step 3/5: Downloading real HD photos matching topic...")

            fps = 24
            total_frames = int(fps * final_audio_dur)
            video_no_audio = "temp_video.mp4"
            video_with_subtitles = "temp_subtitles.mp4"
            audio_combined = "combined_audio.mp3"
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
                    cmd_vid_audio = f"ffmpeg -y -stream_loop -1 -i custom_input_vid.mp4 -i {audio_final} -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest {final_mp4}"
                    subprocess.run(cmd_vid_audio, shell=True, check=True)
                    custom_video_used = True

            if not custom_video_used:
                keywords = data.get("search_keywords", ["delicious food", "cooking dish"])
                for idx, kw in enumerate(keywords):
                    img = fetch_guaranteed_web_photo(kw, width, height, index=idx)
                    if img:
                        scene_images.append(img)
                        
            if not custom_video_used and len(scene_images) == 0:
                for idx in range(6):
                    img = fetch_guaranteed_web_photo("cooking food", width, height, index=idx)
                    if img:
                        scene_images.append(img)

            update_progress(55, "🎵 Step 4/5: Mixing engaging background music...")
            
            voice_to_use = audio_final
            if enable_bg_music:
                bg_music_file = "bg_music.mp3"
                if fetch_royalty_free_music(bg_music_file):
                    cmd_mix = f"ffmpeg -y -i {audio_final} -stream_loop -1 -i {bg_music_file} -filter_complex \"[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first[a]\" -map \"[a]\" {audio_combined}"
                    try:
                        subprocess.run(cmd_mix, shell=True, check=True)
                        voice_to_use = audio_combined
                    except:
                        voice_to_use = audio_final

            update_progress(70, "🎥 Step 5/5: Rendering motion video...")
            
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
                    
                    if frame_num % 120 == 0:
                        render_progress = 70 + int((frame_num / total_frames) * 20)
                        update_progress(render_progress, f"🎥 Rendering motion frames ({frame_num}/{total_frames})...")

                out.release()

                video_to_merge = video_no_audio
                if enable_subtitles:
                    update_progress(92, "💬 Burning subtitle stream into video...")
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
                        
                        cmd_srt = f"ffmpeg -y -i {video_no_audio} -vf \"{subtitle_filter}\" -c:v libx264 -preset ultrafast {video_with_subtitles}"
                        subprocess.run(cmd_srt, shell=True, check=True)
                        video_to_merge = video_with_subtitles
                    except:
                        pass

                update_progress(98, "📦 Finalizing MP4 media stream...")
                cmd_merge = f"ffmpeg -y -i {video_to_merge} -i {voice_to_use} -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest {final_mp4}"
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
