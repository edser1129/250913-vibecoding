# app.py
import streamlit as st
from gtts import gTTS
from io import BytesIO

st.set_page_config(page_title="AAC - 우리 반", layout="wide")

# 문구와 그림(emoji) 매핑
PHRASES = [
    ("물 마시고 싶어요.", "🥤"),
    ("공부하기 싫어요.", "📚❌"),
    ("놀이하고 싶어요.", "🧸"),
    ("교실에 가고 싶어요.", "🏫"),
    ("배가 고파요.", "🍽️"),
    ("화장실에 갈래요.", "🚻"),
    ("친구와 같은 걸 하고 싶어요.", "🤝"),
    ("선생님이 말해 주세요.", "👩‍🏫"),
]

# --- 유틸: 한국어 TTS ---
def tts_bytes(text: str):
    mp3_fp = BytesIO()
    tts = gTTS(text=text, lang="ko")
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp.read()

st.title("우리 반 AAC")
st.markdown("버튼을 눌러 원하는 것을 표현하세요.")

# 버튼 그리드
cols = st.columns(2)
for i, (phrase, emoji) in enumerate(PHRASES):
    with cols[i % 2]:
        st.markdown(
            f"""
            <div style='text-align:center; font-size:80px;'>{emoji}</div>
            <div style='text-align:center; font-size:22px; margin:6px'>{phrase}</div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("말하기 ▶", key=f"btn_{i}"):
            st.audio(tts_bytes(phrase), format="audio/mp3")
