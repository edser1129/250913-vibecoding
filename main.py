# app.py
import streamlit as st
from gtts import gTTS
from io import BytesIO
from PIL import Image, ImageFilter, ImageOps
import numpy as np
import base64
import hashlib

st.set_page_config(page_title="AAC - 우리 반용", layout="wide", initial_sidebar_state="expanded")

# --- 기본 문장들 ---
DEFAULT_PHRASES = [
    "물 마시고 싶어요.",
    "공부하기 싫어요.",
    "놀이하고 싶어요.",
    "교실에 가고 싶어요.",
    "배가 고파요.",
    "화장실에 갈래요.",
    "친구와 같은 걸 하고 싶어요.",
    "선생님이 말해 주세요."
]

# --- 유틸: tts 생성 (캐시) ---
@st.cache_data(show_spinner=False)
def tts_bytes_korean(text: str):
    # gTTS 한국어 이용 (인터넷 필요)
    mp3_fp = BytesIO()
    tts = gTTS(text=text, lang="ko")
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp.read()

# --- 유틸: 사진을 '명료한 그림/스티커'로 변환 ---
@st.cache_data(show_spinner=False)
def make_sticker(pil_img: Image.Image, size=(300,300)):
    # 간단한 포스터라이즈 + 엣지 합성으로 '명료한 그림' 생성
    img = pil_img.convert("RGB")
    img = ImageOps.fit(img, size, method=Image.LANCZOS)
    # 작은 블러 -> 엣지
    edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
    edges = ImageOps.invert(edges).point(lambda p: 255 if p > 100 else 0)
    # 포스터화 (컬러 양자화)
    poster = img.quantize(colors=8, method=2).convert("RGB")
    # 밝기/컨트라스트 단순 보정 (선명하게)
    poster = poster.filter(ImageFilter.SHARPEN)
    # 합성: poster 위에 검정 테두리(엣지)
    edges_rgb = Image.merge("RGB", (edges, edges, edges))
    combined = Image.composite(poster, Image.new("RGB", size, (255,255,255)), edges_rgb)
    return combined

# --- 사이드바: 업로드 / 설정 ---
st.sidebar.title("설정")
uploaded = st.sidebar.file_uploader("학생 사진 업로드 (선택) — 사진으로 명확한 그림 만들기", type=["png","jpg","jpeg"])
btn_size = st.sidebar.slider("버튼/그림 크기(px)", 160, 520, 300, step=20)
font_size = st.sidebar.slider("문구 글자 크기(px)", 16, 28, 20)
repeat_tts = st.sidebar.checkbox("버튼 클릭 시 TTS 자동 재생", value=True)

st.sidebar.markdown("---")
st.sidebar.info("사진 업로드 시 개인정보 주의: 앱에 업로드한 사진은 Streamlit Cloud 저장소/세션에 따라 관리됩니다.")

# --- 메인: 문장 목록 편집/추가 ---
st.title("우리 반 AAC (간단판)")
st.markdown("큰 버튼을 눌러 학생이 원하는 것을 표현하고, 음성을 재생하세요.")

with st.expander("문구 목록 편집 / 추가", expanded=False):
    phrases = st.session_state.get("phrases", DEFAULT_PHRASES.copy())
    # init if not present
    if "phrases" not in st.session_state:
        st.session_state["phrases"] = phrases

    new_text = st.text_input("새 문구 추가", "")
    if st.button("추가"):
        if new_text.strip():
            st.session_state.phrases.append(new_text.strip())
            st.experimental_rerun()

    # 편집 가능한 리스트 (간단 삭제)
    st.write("현재 문구:")
    for i, p in enumerate(st.session_state.phrases):
        cols = st.columns([0.9, 0.1])
        cols[0].markdown(f"{i+1}. {p}")
        if cols[1].button("삭제", key=f"del_{i}"):
            st.session_state.phrases.pop(i)
            st.experimental_rerun()

# --- 아바타 생성(옵션) ---
st.write("### 학생 그림(아바타)")
if uploaded:
    pil = Image.open(uploaded).convert("RGBA")
    sticker = make_sticker(pil.convert("RGB"), size=(btn_size, btn_size))
    st.image(sticker, caption="생성된 스티커 미리보기", width=btn_size)
    # cache sticker bytes for display on buttons
    sticker_bytes = BytesIO()
    sticker.save(sticker_bytes, format="PNG")
    sticker_bytes = sticker_bytes.getvalue()
else:
    st.info("사진을 업로드하면 버튼용 그림을 학생처럼 보이도록 자동 변환합니다. 업로드하지 않으면 기본 아이콘(이모지)이 사용됩니다).")
    sticker_bytes = None

# --- AAC 그리드 표시 ---
phrases_to_show = st.session_state.get("phrases", DEFAULT_PHRASES)
cols_num = 2 if len(phrases_to_show) <= 4 else 3
grid_cols = st.columns(cols_num)

# helper to create deterministic filename for caching audio/images
def cache_key(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

for idx, phrase in enumerate(phrases_to_show):
    col = grid_cols[idx % cols_num]
    with col:
        # 그림 영역
        if sticker_bytes:
            # show same sticker but could be extended to personalize per phrase
            st.image(sticker_bytes, width=btn_size)
        else:
            # simple fallback pictogram using emoji + white bg
            emoji_map = ["🥤","📚","🧸","🏫","🍽️","🚻","🤝","👩‍🏫"]
            emoji = emoji_map[idx] if idx < len(emoji_map) else "🔔"
            placeholder = Image.new("RGB", (btn_size, btn_size), (255,255,255))
            # draw emoji as text -> PIL ImageFont might be missing, so use st.markdown big emoji
            st.markdown(f"<div style='font-size: {int(btn_size/2)}px; height:{btn_size}px; display:flex; align-items:center; justify-content:center'>{emoji}</div>", unsafe_allow_html=True)

        st.markdown(f"<div style='font-size:{font_size}px; text-align:center; margin-top:6px'>{phrase}</div>", unsafe_allow_html=True)

        # 버튼: 재생
        key = f"play-{cache_key(phrase)}"
        if st.button("말하기 ▶", key=key):
            audio_bytes = tts_bytes_korean(phrase)
            st.audio(audio_bytes, format="audio/mp3")
        # 자동 재생 옵션: invisible trigger
        if repeat_tts and st.button("▶ 자동 재생(캐시 재생)", key=f"auto-{key}"):
            audio_bytes = tts_bytes_korean(phrase)
            st.audio(audio_bytes, format="audio/mp3")

# 추가 UX: 큰 화면용 하나의 큰 버튼
st.markdown("---")
st.write("### 큰 표현 버튼 (클릭하면 음성 재생)")
big_cols = st.columns([0.6, 0.4])
with big_cols[0]:
    chosen = st.selectbox("큰 버튼으로 표시할 문구 선택", phrases_to_show)
    if st.button("클릭하여 말하기", key="bigbtn"):
        st.audio(tts_bytes_korean(chosen), format="audio/mp3")
with big_cols[1]:
    st.markdown("버튼을 누른 뒤, 필요하면 재생기에서 다시 재생하세요.")

st.write("앱 사용 팁: 학생이 직접 버튼을 누를 수 있게 크기를 크게 해 두고, 교실 환경(조명·반사)을 고려해 사진을 찍어 업로드하면 더 잘 인식되는 그림이 만들어집니다.")
