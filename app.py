import streamlit as st
from google import genai
import requests

# ضبط إعدادات الصفحة
st.set_page_config(page_title="AI Video Studio", page_icon="🎬", layout="wide")

st.title("🎬 مولد محتوى الفيديوهات الذكي (AI Video Generator)")
st.caption("أداة توليد السكربتات والصوتيات ومقاطع الفيديو أوتوماتيكياً")

# الشريط الجانبي لإدخال المفاتيح (API Keys)
st.sidebar.header("🔑 إعدادات المفاتيح (API Keys)")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", help="احصل عليه مجاناً من Google AI Studio")
eleven_key = st.sidebar.text_input("ElevenLabs API Key (اختياري)", type="password")

# واجهة المدخلات الرئيسية
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input("💡 فكرة الفيديو أو الموضوع:", placeholder="مثال: قصة نجاح شركة أبل في 3 دقائق")
    style = st.selectbox("🎭 نبرة السكربت:", ["تشويقي وحماسي", "تعليمي ومبسط", "قصصي ومشرق", "احترافي ورسمي"])

with col2:
    duration = st.slider("⏱️ مدة الفيديو التقديرية (بالدقائق):", 1, 10, 3)

generate_btn = st.button("🚀 إنشاء السكربت والخطة", type="primary", use_container_width=True)

if generate_btn:
    if not gemini_key:
        st.error("⚠️ يرجى إدخال Gemini API Key في الشريط الجانبي أولاً للبدء!")
    elif not topic:
        st.warning("⚠️ يرجى كتابة فكرة أو موضوع الفيديو!")
    else:
        with st.spinner("جاري توليد السكربت والخطة البصرية باستخدام الذكاء الاصطناعي..."):
            try:
                # الاتصال بـ Gemini API
                client = genai.Client(api_key=gemini_key)
                
                prompt = f"""
                أنت خبير محتوى يوتيوب متمرس. قم بكتابة خطة وفيديو كامل لموضوع: '{topic}'.
                المدة المطلوبة: {duration} دقائق.
                النبرة: {style}.
                
                يرجى تقديم الإجابة بأسلوب منظم يحتوي على:
                1. عنوان جذاب للفيديو (Hook Title)
                2. نص السكربت الصوتي (Voiceover Script) مقسم لفقرات
                3. وصف بصري لكل مشهد (Visual Prompts/Stock Footage Ideas)
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                
                st.success("✨ تم إنشاء السكربت بنجاح!")
                st.markdown("---")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"حدث خطأ أثناء الاتصال بالخدمة: {e}")
