import os
from datetime import datetime

import requests
import streamlit as st


# ============================================================
# CONFIG
# ============================================================

API_URL = os.getenv(
    "POSTGRAM_API_URL",
    "http://127.0.0.1:8000",
)

MAX_UPLOAD_MB = 50

st.set_page_config(
    page_title="Postgram",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# LIGHT UI
# ============================================================

st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap'
    );

    :root {
        --bg: #f7f5ef;
        --surface: #ffffff;
        --surface-soft: #f1eee7;
        --border: #e5e0d7;
        --text: #20232a;
        --muted: #74777f;
        --accent: #ff5c5c;
        --accent-soft: #fff0ef;
        --purple: #7567e8;
        --green: #5b9b68;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 5% 0%,
                rgba(255, 92, 92, 0.08),
                transparent 25%
            ),
            radial-gradient(
                circle at 95% 100%,
                rgba(117, 103, 232, 0.08),
                transparent 28%
            ),
            var(--bg);

        color: var(--text);
        font-family: "DM Sans", sans-serif;
    }

    [data-testid="stHeader"] {
        background: rgba(247, 245, 239, 0.82);
    }

    [data-testid="stSidebar"] {
        background: #fffdf9;
        border-right: 1px solid var(--border);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    h1,
    h2,
    h3 {
        font-family: "Space Grotesk", sans-serif !important;
        color: var(--text) !important;
        letter-spacing: -1.4px;
    }

    .stMarkdown,
    .stCaption,
    label {
        color: var(--text);
    }

    div.stButton > button {
        border-radius: 12px;
        border: 1px solid var(--border);
        background: var(--surface);
        color: var(--text);
        font-weight: 600;
        min-height: 42px;
    }

    div.stButton > button:hover {
        border-color: var(--accent);
        color: var(--accent);
    }

    div.stButton > button[kind="primary"] {
        background: var(--accent);
        color: white;
        border: 0;
    }

    .stTextInput input,
    .stTextArea textarea {
        background: var(--surface) !important;
        color: var(--text) !important;
        border-color: var(--border) !important;
        border-radius: 12px !important;
    }

    [data-testid="stFileUploader"] {
        background: var(--surface);
        border: 1px dashed #d8d0c5;
        border-radius: 14px;
        padding: 8px;
    }

    [data-testid="stExpander"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
    }

    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 16px;
    }

    [data-testid="stTabs"] button {
        font-weight: 600;
    }

    .brand-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: 30px;
        font-weight: 700;
        letter-spacing: -1.5px;
    }

    .brand-mark {
        display: inline-flex;
        width: 40px;
        height: 40px;
        margin-right: 10px;
        align-items: center;
        justify-content: center;
        border-radius: 13px;
        background: var(--text);
        color: white;
        font-weight: 800;
    }

    .eyebrow {
        color: var(--accent);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .hero-copy {
        max-width: 560px;
        color: var(--muted);
        font-size: 1.05rem;
        line-height: 1.7;
    }

    .feature-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 22px;
    }

    .feature-number {
        color: var(--accent);
        font-family: "Space Grotesk", sans-serif;
        font-size: 28px;
        font-weight: 700;
    }

    .feature-title {
        font-weight: 700;
        margin-top: 8px;
    }

    .feature-copy {
        color: var(--muted);
        line-height: 1.5;
        margin-top: 6px;
    }

    .post-shell {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 16px;
        margin-bottom: 18px;
        box-shadow: 0 10px 30px rgba(36, 32, 25, 0.04);
    }

    .post-user {
        font-weight: 700;
    }

    .post-date {
        color: var(--muted);
        font-size: 0.82rem;
    }

    .post-caption {
        color: #4f5259;
        line-height: 1.6;
        font-size: 0.98rem;
    }

    .soft-note {
        color: var(--muted);
        font-size: 0.88rem;
    }

    .profile-box {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 18px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION
# ============================================================

def init_state():
    defaults = {
        "token": None,
        "email": None,
        "logged_in": False,
        "page_size": 20,
        "feed_cache": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# API
# ============================================================

def api_request(method, path, **kwargs):
    headers = kwargs.pop("headers", {})

    if st.session_state.token:
        headers["Authorization"] = (
            f"Bearer {st.session_state.token}"
        )

    return requests.request(
        method,
        f"{API_URL}{path}",
        headers=headers,
        timeout=60,
        **kwargs,
    )


# ============================================================
# AUTH
# ============================================================

def login(email, password):
    try:
        response = requests.post(
            f"{API_URL}/auth/jwt/login",
            data={
                "username": email,
                "password": password,
            },
            timeout=30,
        )
    except requests.RequestException:
        st.error(
            "Could not reach the Postgram server."
        )
        return

    if response.ok:
        data = response.json()

        st.session_state.token = (
            data["access_token"]
        )
        st.session_state.email = email
        st.session_state.logged_in = True
        st.session_state.feed_cache = None

        st.rerun()

    try:
        detail = response.json().get(
            "detail",
            "Login failed.",
        )
    except ValueError:
        detail = "Login failed."

    st.error(detail)


def register(email, password):
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json={
                "email": email,
                "password": password,
            },
            timeout=30,
        )
    except requests.RequestException:
        st.error(
            "Could not reach the Postgram server."
        )
        return

    if response.ok:
        st.success(
            "Account created. Sign in to continue."
        )
        return

    try:
        detail = response.json().get(
            "detail",
            "Registration failed.",
        )
    except ValueError:
        detail = "Registration failed."

    st.error(detail)


def logout():
    st.session_state.token = None
    st.session_state.email = None
    st.session_state.logged_in = False
    st.session_state.feed_cache = None

    st.rerun()


# ============================================================
# HELPERS
# ============================================================

def format_date(value):
    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        return parsed.strftime(
            "%d %b %Y · %I:%M %p"
        )

    except (ValueError, AttributeError):
        return value


def is_video(post):
    return post.get("file_type") == "video"


# ============================================================
# FEED
# ============================================================

def load_feed(force=False):
    if (
        st.session_state.feed_cache is not None
        and not force
    ):
        return st.session_state.feed_cache

    response = api_request(
        "GET",
        "/feed",
        params={
            "limit": st.session_state.page_size,
            "offset": 0,
        },
    )

    if response.status_code == 401:
        logout()

    response.raise_for_status()

    data = response.json()

    st.session_state.feed_cache = data

    return data


# ============================================================
# UPLOAD
# ============================================================

def upload_post(
    uploaded_file,
    caption,
):
    if uploaded_file.size > (
        MAX_UPLOAD_MB * 1024 * 1024
    ):
        st.error(
            f"File is too large. "
            f"Maximum size is {MAX_UPLOAD_MB} MB."
        )
        return False

    response = api_request(
        "POST",
        "/upload",
        files={
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type,
            )
        },
        data={
            "caption": caption.strip(),
        },
    )

    if response.ok:
        st.session_state.feed_cache = None
        return True

    try:
        detail = response.json().get(
            "detail",
            "Upload failed.",
        )
    except ValueError:
        detail = "Upload failed."

    st.error(detail)

    return False


# ============================================================
# DELETE
# ============================================================

def delete_post(post_id):
    response = api_request(
        "DELETE",
        f"/delete/{post_id}",
    )

    if response.ok:
        st.session_state.feed_cache = None
        st.toast(
            "Post deleted.",
            icon="🗑️",
        )
        st.rerun()

    try:
        body = response.json()

        st.error(
            body.get(
                "detail",
                body.get(
                    "message",
                    "Delete failed.",
                ),
            )
        )

    except ValueError:
        st.error("Delete failed.")


# ============================================================
# AUTH SCREEN
# ============================================================

def auth_screen():

    left, right = st.columns(
        [1.15, 0.85],
        gap="large",
    )

    with left:

        st.write("")
        st.write("")

        st.markdown(
            "### POSTGRAM"
        )

        st.markdown(
            "# Share what matters."
        )

        st.markdown(
            """
            <div class="hero-copy">
                A simple, modern space for your photos
                and videos. Create moments, keep them
                organized, and share them with your community.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")

        feature_1, feature_2 = st.columns(2)

        with feature_1:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-number">01</div>
                    <div class="feature-title">
                        Capture
                    </div>
                    <div class="feature-copy">
                        Upload photos and videos
                        in seconds.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with feature_2:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-number">02</div>
                    <div class="feature-title">
                        Remember
                    </div>
                    <div class="feature-copy">
                        Keep your moments together
                        in one clean feed.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right:

        st.write("")
        st.write("")

        login_tab, register_tab = st.tabs(
            [
                "Sign in",
                "Create account",
            ]
        )

        with login_tab:

            with st.form(
                "login_form"
            ):

                email = st.text_input(
                    "Email",
                    placeholder="you@example.com",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Your password",
                )

                submitted = (
                    st.form_submit_button(
                        "Enter Postgram →",
                        type="primary",
                        use_container_width=True,
                    )
                )

            if submitted:

                if not email or not password:

                    st.warning(
                        "Enter your email and password."
                    )

                else:

                    login(
                        email,
                        password,
                    )

        with register_tab:

            with st.form(
                "register_form"
            ):

                email = st.text_input(
                    "Email",
                    placeholder="you@example.com",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="At least 8 characters",
                )

                submitted = (
                    st.form_submit_button(
                        "Create account →",
                        type="primary",
                        use_container_width=True,
                    )
                )

            if submitted:

                if not email or not password:

                    st.warning(
                        "Enter your email and password."
                    )

                elif len(password) < 8:

                    st.warning(
                        "Password must be at least 8 characters."
                    )

                else:

                    register(
                        email,
                        password,
                    )


# ============================================================
# CREATE POST
# ============================================================

def create_post_panel():

    with st.expander(
        "＋  Create a new moment",
        expanded=False,
    ):

        uploaded_file = st.file_uploader(
            "Choose a photo or video",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
                "gif",
                "mp4",
                "mov",
                "webm",
                "mkv",
            ],
            help=(
                f"Images and videos up to "
                f"{MAX_UPLOAD_MB} MB."
            ),
        )

        if uploaded_file:

            st.caption(
                f"Selected: {uploaded_file.name} "
                f"· {uploaded_file.size / 1024 / 1024:.1f} MB"
            )

            if uploaded_file.type.startswith(
                "image/"
            ):
                st.image(
                    uploaded_file,
                    caption="Preview",
                    use_container_width=True,
                )

            elif uploaded_file.type.startswith(
                "video/"
            ):
                st.video(
                    uploaded_file
                )

        caption = st.text_area(
            "Caption",
            max_chars=255,
            placeholder=(
                "What's happening?"
            ),
        )

        publish = st.button(
            "Publish moment →",
            type="primary",
            use_container_width=True,
        )

        if publish:

            if uploaded_file is None:

                st.warning(
                    "Choose a photo or video first."
                )

            elif upload_post(
                uploaded_file,
                caption,
            ):

                st.success(
                    "Your moment is live."
                )

                st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar(total_posts):

    with st.sidebar:

        st.markdown(
            "## ✦ Postgram"
        )

        st.caption(
            "Your visual space."
        )

        st.divider()

        st.markdown(
            "**Signed in as**"
        )

        st.write(
            st.session_state.email
        )

        st.divider()

        st.metric(
            "Moments",
            total_posts,
        )

        st.divider()

        if st.button(
            "↻ Refresh feed",
            use_container_width=True,
        ):

            st.session_state.feed_cache = None
            st.rerun()

        if st.button(
            "Sign out",
            use_container_width=True,
        ):

            logout()


# ============================================================
# FEED SCREEN
# ============================================================

def feed_screen():

    try:

        feed_data = load_feed()

    except requests.RequestException:

        st.error(
            f"Could not connect to Postgram API "
            f"at {API_URL}."
        )

        return

    posts = feed_data.get(
        "posts",
        [],
    )

    total = feed_data.get(
        "total",
        len(posts),
    )

    render_sidebar(total)

    # --------------------------------------------------------
    # TOP BAR
    # --------------------------------------------------------

    brand_col, action_col = st.columns(
        [5, 1],
        vertical_alignment="center",
    )

    with brand_col:

        st.markdown(
            "### ✦ Postgram"
        )

        st.caption(
            f"Welcome back, "
            f"{st.session_state.email}"
        )

    with action_col:

        if st.button(
            "Refresh",
            use_container_width=True,
        ):

            st.session_state.feed_cache = None
            st.rerun()

    st.divider()

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    image_count = sum(
        not is_video(post)
        for post in posts
    )

    video_count = sum(
        is_video(post)
        for post in posts
    )

    metric_1, metric_2, metric_3 = st.columns(3)

    with metric_1:
        st.metric(
            "Total moments",
            total,
        )

    with metric_2:
        st.metric(
            "Photos",
            image_count,
        )

    with metric_3:
        st.metric(
            "Videos",
            video_count,
        )

    st.write("")

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    create_post_panel()

    st.write("")

    # --------------------------------------------------------
    # SEARCH / FILTER
    # --------------------------------------------------------

    search_col, filter_col = st.columns(
        [3, 1],
        vertical_alignment="bottom",
    )

    with search_col:

        search = st.text_input(
            "Search your feed",
            placeholder=(
                "Search captions or email..."
            ),
            label_visibility="collapsed",
        )

    with filter_col:

        filter_type = st.selectbox(
            "Filter",
            [
                "All",
                "Photos",
                "Videos",
                "My posts",
            ],
            label_visibility="collapsed",
        )

    # --------------------------------------------------------
    # FILTER POSTS
    # --------------------------------------------------------

    filtered_posts = []

    search_value = search.strip().lower()

    for post in posts:

        if filter_type == "Photos" and is_video(post):
            continue

        if filter_type == "Videos" and not is_video(post):
            continue

        if (
            filter_type == "My posts"
            and not post.get("is_owner")
        ):
            continue

        if search_value:

            caption = (
                post.get("caption") or ""
            ).lower()

            email = (
                post.get("email") or ""
            ).lower()

            if (
                search_value not in caption
                and search_value not in email
            ):
                continue

        filtered_posts.append(post)

    st.caption(
        f"Showing {len(filtered_posts)} "
        f"of {total} moments"
    )

    # --------------------------------------------------------
    # EMPTY
    # --------------------------------------------------------

    if not filtered_posts:

        if total == 0:

            st.info(
                "✦ Your feed is empty. "
                "Create your first moment above."
            )

        else:

            st.info(
                "No moments match your current filter."
            )

        return

    # --------------------------------------------------------
    # POSTS
    # --------------------------------------------------------

    for post in filtered_posts:

        with st.container(
            border=True,
        ):

            header_left, header_right = st.columns(
                [4, 2],
                vertical_alignment="center",
            )

            with header_left:

                st.markdown(
                    f"**{post.get('email', 'Postgram user')}**"
                )

            with header_right:

                st.caption(
                    format_date(
                        post["created_at"]
                    )
                )

            if post["file_type"] == "video":

                st.video(
                    post["url"]
                )

            else:

                st.image(
                    post["url"],
                    use_container_width=True,
                )

            if post.get("caption"):

                st.markdown(
                    post["caption"]
                )

            footer_left, footer_right = st.columns(
                [4, 1],
                vertical_alignment="center",
            )

            with footer_left:

                st.caption(
                    post["file_name"]
                )

            with footer_right:

                if post.get("is_owner"):

                    if st.button(
                        "Delete",
                        key=f"delete_{post['id']}",
                        use_container_width=True,
                    ):

                        delete_post(
                            post["id"]
                        )


# ============================================================
# START
# ============================================================

init_state()

if st.session_state.logged_in:

    feed_screen()

else:

    auth_screen()
