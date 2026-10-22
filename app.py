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
st.caption("Professional AI Video Studio: Made by Eng. Ahmed El Naggar and his Sem Sem ❤️ | True Smart Recipe & Dynamic Generator.")

# Initialize Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

st.markdown("---")

# Main Control Dashboard
col_top1, col_top2 = st.columns([2, 1])

with col_top1:
    topic = st.text_input(
        "💡 What is your video about?", 
        value="",
        placeholder="Type naturally (e.g. tare2et 3amal el kofta, koshari, or any topic)..."
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

# Fully Dynamic Smart Intent & Step-by-Step Recipe Builder
def process_dynamic_intent(raw_text):
    text = raw_text.strip().lower()

    # Clean command prefixes
    for prefix in ["e3mely", "e3mly", "y3lemny", "tare2et", "3amal", "3ayez", "3ayz", "how to make", "video about", "اعملي", "يعلمني", "طريقة", "عمل", "عايز"]:
        text = text.replace(prefix, "")

    text_clean = text.strip()

    # Check for Kofta / Meatballs
    if any(w in text_clean for w in ["kofta", "kofta", "كفتة", "كفته"]):
        base_paragraphs = [
            "Today, I am going to show you step by step how to make juicy, perfectly seasoned homemade kofta right in your own kitchen!",
            "First, let's look at the essential ingredients you will need: 500 grams of minced beef or lamb, one finely grated onion, a handful of fresh parsley, salt, black pepper, and mixed spices.",
            "Step two: In a large mixing bowl, combine your minced meat, the squeezed onion pulp, fresh chopped parsley, and all your spices together.",
            "Step three: Knead the meat mixture thoroughly with your hands for at least five minutes until all the flavors blend and the meat becomes sticky and cohesive.",
            "Step four: Take handfuls of the meat mixture and mold them evenly around wooden skewers or shape them into neat oblong fingers.",
            "Step five: Preheat your grill or pan, lightly brush with oil, and cook the kofta skewers for about 8 to 10 minutes, turning frequently until nicely charred and juicy on the inside.",
            "Step six: Serve your hot, smoky homemade kofta immediately with fresh flatbread, tahini sauce, and chopped parsley. Enjoy!"
        ]
        search_keys = ["raw minced meat onions", "mixing meat spices bowl", "shaping kofta skewers", "grilling kofta on charcoal", "cooked juicy kofta plate"]
        hooks = [
            "The ultimate secret to juicy homemade kofta!",
            "How to make restaurant-style kofta at home step by step!",
            "You need to try this amazing homemade kofta recipe!"
        ]
        seo_tags = "homemade kofta, kofta recipe, grilled kofta, juicy meat skewers, middle eastern food, cooking at home, easy recipe, kofta tutorial, delicious meat dishes"
        return base_paragraphs, search_keys, hooks, seo_tags

    # Check for Eggs & Cheese (Bead & Gebna)
    if any(w in text_clean for w in ["bead", "beed", "egg", "eggs", "بيض"]) or any(w in text_clean for w in ["gebna", "cheese", "جبنة"]):
        base_paragraphs = [
            "Today, I am going to show you how to make the fluffiest and most delicious cheesy scrambled eggs right at home!",
            "First, gather your fresh ingredients: farm-fresh eggs, a splash of milk, butter, salt, pepper, and shredded cheese.",
            "Crack the eggs into a bowl, add milk, and whisk them thoroughly until light and airy.",
            "Melt butter in a non-stick pan over medium heat, then pour in the egg mixture.",
            "Gently stir with a spatula to create soft curds, and sprinkle generous cheese right on top to melt.",
            "Serve hot and enjoy your ultimate comfort breakfast!"
        ]
        search_keys = ["fluffy scrambled eggs", "melted cheese on eggs", "cooking eggs in skillet", "breakfast cheesy eggs"]
        hooks = ["The secret to fluffiest cheesy eggs!", "How to make restaurant-style cheesy eggs!"]
        seo_tags = "cheesy eggs, scrambled eggs recipe, breakfast ideas, eggs with cheese, easy cooking"
        return base_paragraphs, search_keys, hooks, seo_tags

    # Check for Burger
    if any(w in text_clean for w in ["burger", "برجر"]):
        base_paragraphs = [
            "Today, we are making the ultimate juicy homemade beef burger with melted cheese and a fried egg!",
            "You will need fresh ground beef patties, burger buns, cheddar cheese slices, eggs, lettuce, and tomatoes.",
            "Season your beef patties, grill or pan-sear them until juicy and golden brown.",
            "Melt cheddar cheese on top, fry an egg, and assemble your gourmet burger with fresh veggies and sauce."
        ]
        search_keys = ["juicy beef burger", "melted cheese burger", "fried egg on burger", "cooking burger skillet"]
        hooks = ["The ultimate homemade burger recipe!", "How to make gourmet burgers at home!"]
        seo_tags = "homemade burger, egg and cheese burger, juicy beef burger, gourmet recipe"
        return base_paragraphs, search_keys, hooks, seo_tags

    # Check for Cake & Chocolate
    if any(w in text_clean for w in ["cake", "cholate", "chocolate", "كيك", "شوكولاتة"]):
        base_paragraphs = [
            "Today, I'm going to show you how to bake a rich and moist homemade chocolate cake in your own kitchen!",
            "You will need eggs, sugar, flour, cocoa powder, milk, butter, and baking powder.",
            "Whisk dry ingredients, blend wet ingredients separately, combine into a smooth batter, and bake at 180C for 30 minutes."
        ]
        search_keys = ["chocolate cake", "baking ingredients", "mixing bowl cocoa", "oven baking cake"]
        hooks = ["The ultimate homemade chocolate cake recipe!", "How to bake a rich chocolate cake!"]
        seo_tags = "chocolate cake recipe, baking at home, easy dessert recipe, moist cake"
        return base_paragraphs, search_keys, hooks, seo_tags

    # Dynamic fallback for any other custom topic
    clean_words = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', text_clean)]
    subject = " ".join(clean_words[:3]) if clean_words else "this topic"

    base_paragraphs = [
        f"Welcome! Today we are covering a complete step-by-step guide on {subject}.",
        f"First, let's understand the core concept and what you need to get started with {subject}.",
        f"Next, we will walk through the main implementation phases clearly and thoroughly.",
        f"Finally, review your results, apply these expert tips, and let us know your feedback below!"
    ]
    search_keys = [subject, "step by step guide", "tutorial presentation"]
    hooks = [f"Complete step-by-step guide to {subject}!", f"How to master {subject} easily!"]
    seo_tags = f"{subject}, tutorial, guide, step by step, how to, viral video"
    return base_paragraphs, search_keys, hooks, seo_tags

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
            progress_bar.progress(percent)
            metric_container.metric(label="📊 Production Progress", value=f"{percent}%", delta=f"{percent} out of 100%")
            status_container.info(text)

        try:
            is_short = (video_format == "YouTube Short (30-59 sec)")
            width, height = (720, 1280) if is_short else (1280, 720)
            target_words = int(duration * 135) if not is_short else int(duration * 60 * 2.2)
            
            update_progress(10, "📝 Step 1/5: Smart Dynamic Engine building recipe script & steps...")
            
            base_paragraphs, search_keys, hooks, seo_tags = process_dynamic_intent(topic)

            custom_script = ""
            para_idx = 0
            words_count = 0
            
            while words_count < target_words:
                current_p = base_paragraphs[para_idx % len(base_paragraphs)]
                if para_idx >= len(base_paragraphs):
                    cycle_num = (para_idx // len(base_paragraphs)) + 1
                    current_p = f"Moving forward to next phase {cycle_num}, " + current_p[0].lower() + current_p[1:]
                
                custom_script += current_p + " "
                words_count = len(custom_script.split())
                para_idx += 1

            script_data = {
                "hooks": hooks,
                "script": custom_script.strip(),
                "tags": seo_tags,
                "search_keywords": search_keys
            }
            
            data = script_data
            update_progress(25, f"🎙️ Step 2/5: Synthesizing Realistic Human Voice ({selected_voice_code})...")

            audio_raw = "raw_human_voice.mp3"
            audio_final = "final_voice.mp3"
            
            asyncio.run(generate_human_voice(data['script'], selected_voice_code, audio_raw))

            cmd_audio = f"ffmpeg -y -i {audio_raw} -filter:a 'atempo=1.02' {audio_final}"
            subprocess.run(cmd_audio, shell=True, check=True)

            probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_final}"
            final_audio_dur = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
            
            update_progress(45, "🌐 Step 3/5: Downloading real HD photos matching ingredients & steps...")

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
                    cmd_vid_audio = f"ffmpeg -y -stream_loop -1 -i custom_input_vid.mp4 -i {audio_final} -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest {final_mp4}"
                    subprocess.run(cmd_vid_audio, shell=True, check=True)
                    custom_video_used = True

            if not custom_video_used:
                keywords = data.get("search_keywords", ["raw minced meat", "cooking food"])
                for idx, kw in enumerate(keywords):
                    img = fetch_guaranteed_web_photo(kw, width, height, index=idx)
                    if img:
                        scene_images.append(img)
                        
            if not custom_video_used and len(scene_images) == 0:
                for idx in range(6):
                    img = fetch_guaranteed_web_photo("cooking food", width, height, index=idx)
                    if img:
                        scene_images.append(img)

            update_progress(65, "🎵 Step 4/5: Mixing engaging background music...")
            
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

            update_progress(80, "🎥 Step 5/5: Rendering motion video & burning subtitles...")
            
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
                        inner_p = 80 + int((frame_num / total_frames) * 15)
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

                cmd_merge = f"ffmpeg -y -i {video_to_merge} -i {voice_to_use} -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest {final_mp4}"
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
