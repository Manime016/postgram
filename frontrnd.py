import os
from datetime import datetime

import requests
import streamlit as st

API_URL = os.getenv("POSTGRAM_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Postgram", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#090b0f;--panel:#11151c;--panel2:#171c25;--line:#252b35;--text:#f5f7fa;--muted:#89919f;--lime:#b5ff62}
.stApp{background:radial-gradient(circle at 8% 0%,#b5ff6212,transparent 27%),radial-gradient(circle at 92% 90%,#7568ff12,transparent 30%),var(--bg);color:var(--text);font-family:"DM Sans",sans-serif}
[data-testid="stHeader"]{background:rgba(9,11,15,.78)}.block-container{max-width:1120px;padding-top:2rem;padding-bottom:4rem}
h1,h2,h3{font-family:"Space Grotesk",sans-serif!important;letter-spacing:-1.5px}.brand{display:flex;align-items:center;gap:10px;margin-bottom:2rem;font:700 24px "Space Grotesk"}
.brand-mark{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;background:var(--lime);color:#090b0f;font-weight:800}.hero{padding:3.5rem 0 2rem}.eyebrow{color:var(--lime);font-size:.72rem;font-weight:700;letter-spacing:2px}
.hero-title{font:700 clamp(3.8rem,8vw,7rem)/.88 "Space Grotesk";letter-spacing:-6px;margin:1rem 0 1.4rem}.hero-title span{color:var(--lime)}.hero-copy{color:var(--muted);font-size:1.05rem;line-height:1.7;max-width:500px}
.glass{background:rgba(17,21,28,.88);border:1px solid var(--line);border-radius:24px;padding:1.5rem;box-shadow:0 25px 80px rgba(0,0,0,.28)}.post-card{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:0 0 1rem;overflow:hidden;margin-bottom:1.4rem}.post-info{padding:1rem 1.1rem 0}.post-user{font-weight:600;color:#e5e8ed}.post-date{color:var(--muted);font-size:.78rem}.caption{color:#d9dde4;line-height:1.55;margin-top:.7rem}
div.stButton>button{border-radius:11px;border:1px solid var(--line);background:var(--panel2);color:var(--text);font-weight:600}div.stButton>button:hover{border-color:#b5ff6266;color:var(--lime)}div.stButton>button[kind="primary"]{background:var(--lime);color:#090b0f;border:0}.stTextInput input,.stTextArea textarea{background:#090b0f;color:var(--text);border-color:var(--line);border-radius:11px}
[data-testid="stFileUploader"]{background:#090b0f;border:1px dashed #b5ff6255;border-radius:14px;padding:.5rem}.empty{text-align:center;padding:5rem 1rem;border:1px dashed var(--line);border-radius:22px;color:var(--muted)}.empty-star{color:var(--lime);font-size:2.5rem}
</style>
""", unsafe_allow_html=True)


def init_state():
    for key, value in {"token": None, "email": None, "logged_in": False}.items():
        if key not in st.session_state:
            st.session_state[key] = value


def api_request(method, path, **kwargs):
    headers = kwargs.pop("headers", {})
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return requests.request(method, f"{API_URL}{path}", headers=headers, timeout=60, **kwargs)


def login(email, password):
    response = requests.post(f"{API_URL}/auth/jwt/login", data={"username": email, "password": password}, timeout=30)
    if response.ok:
        data = response.json()
        st.session_state.token = data["access_token"]
        st.session_state.email = email
        st.session_state.logged_in = True
        st.rerun()
    try:
        detail = response.json().get("detail", "Login failed")
    except ValueError:
        detail = "Login failed"
    st.error(detail)


def register(email, password):
    response = requests.post(f"{API_URL}/auth/register", json={"email": email, "password": password}, timeout=30)
    if response.ok:
        st.success("Account created. You can sign in now.")
        return
    try:
        detail = response.json().get("detail", "Registration failed")
    except ValueError:
        detail = "Registration failed"
    st.error(detail)


def logout():
    st.session_state.token = None
    st.session_state.email = None
    st.session_state.logged_in = False
    st.rerun()


def format_date(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d %b %Y · %I:%M %p")
    except (ValueError, AttributeError):
        return value


def load_feed():
    response = api_request("GET", "/feed")
    if response.status_code == 401:
        logout()
    response.raise_for_status()
    return response.json().get("posts", [])


def upload_post(uploaded_file, caption):
    response = api_request("POST", "/upload", files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}, data={"caption": caption})
    if response.ok:
        st.success("Your moment is live.")
        return True
    try:
        st.error(response.json().get("detail", "Upload failed"))
    except ValueError:
        st.error("Upload failed")
    return False


def delete_post(post_id):
    response = api_request("DELETE", f"/delete/{post_id}")
    if response.ok:
        st.toast("Post deleted")
        st.rerun()
    try:
        body = response.json()
        st.error(body.get("detail", body.get("message", "Delete failed")))
    except ValueError:
        st.error("Delete failed")


def auth_screen():
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        st.markdown("""
        <div class="hero">
            <div class="eyebrow">YOUR MOMENTS. YOUR SPACE.</div>
            <div class="hero-title">Share what<br><span>matters.</span></div>
            <div class="hero-copy">A clean, modern space for the moments you want to keep. Share photos and videos with your Postgram community.</div>
        </div>
        """, unsafe_allow_html=True)
    with right:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        login_tab, register_tab = st.tabs(["Sign in", "Create account"])
        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Enter Postgram →", type="primary", use_container_width=True)
            if submitted:
                if not email or not password:
                    st.warning("Enter your email and password.")
                else:
                    login(email, password)
        with register_tab:
            with st.form("register_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", placeholder="At least 8 characters")
                submitted = st.form_submit_button("Create account →", type="primary", use_container_width=True)
            if submitted:
                if not email or not password:
                    st.warning("Enter your email and password.")
                elif len(password) < 8:
                    st.warning("Password must be at least 8 characters.")
                else:
                    register(email, password)
        st.markdown('</div>', unsafe_allow_html=True)


def create_post_panel():
    with st.expander("＋  Create a new moment", expanded=False):
        uploaded_file = st.file_uploader("Choose a photo or video", type=["jpg", "jpeg", "png", "webp", "gif", "mp4", "mov", "webm", "mkv"], help="Images and videos are supported.")
        caption = st.text_area("Caption", max_chars=255, placeholder="Say something about this moment...")
        if st.button("Publish moment →", type="primary", use_container_width=True):
            if uploaded_file is None:
                st.warning("Choose a photo or video first.")
            elif upload_post(uploaded_file, caption):
                st.rerun()


def feed_screen():
    st.markdown('<div class="brand"><span class="brand-mark">P</span><span>postgram</span></div>', unsafe_allow_html=True)
    header_left, header_right = st.columns([5, 1], vertical_alignment="bottom")
    with header_left:
        st.markdown('<div class="eyebrow">YOUR FEED</div><h1>Moments</h1>', unsafe_allow_html=True)
    with header_right:
        if st.button("Sign out", use_container_width=True):
            logout()
    create_post_panel()
    try:
        posts = load_feed()
    except requests.RequestException:
        st.error(f"Could not connect to Postgram API at {API_URL}. Make sure the FastAPI server is running.")
        return
    if not posts:
        st.markdown('<div class="empty"><div class="empty-star">✦</div><h2>Your feed is quiet.</h2><p>Share the first moment and make it yours.</p></div>', unsafe_allow_html=True)
        return
    for post in posts:
        st.markdown('<div class="post-card">', unsafe_allow_html=True)
        if post["file_type"] == "video":
            st.video(post["url"])
        else:
            st.image(post["url"], use_container_width=True)
        st.markdown('<div class="post-info">', unsafe_allow_html=True)
        meta_left, meta_right = st.columns([3, 2])
        with meta_left:
            st.markdown(f'<span class="post-user">{post.get("email", "Postgram user")}</span>', unsafe_allow_html=True)
        with meta_right:
            st.markdown(f'<span class="post-date">{format_date(post["created_at"])}</span>', unsafe_allow_html=True)
        if post.get("caption"):
            st.markdown(f'<div class="caption">{post["caption"]}</div>', unsafe_allow_html=True)
        if post.get("is_owner"):
            if st.button("Delete post", key=f'delete_{post["id"]}'):
                delete_post(post["id"])
        st.markdown('</div></div>', unsafe_allow_html=True)


init_state()
if st.session_state.logged_in:
    feed_screen()
else:
    auth_screen()
