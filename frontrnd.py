import os
from datetime import datetime

import requests
import streamlit as st


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


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --bg: #09090b;
        --surface: #111114;
        --surface-2: #17171c;
        --surface-3: #1d1d23;
        --line: #292930;
        --text: #f4f4ee;
        --muted: #92929c;
        --acid: #d7ff3f;
        --acid-soft: rgba(215,255,63,.12);
        --violet: #8b72ff;
        --danger: #ff6678;
    }

    html, body, [class*="css"] {
        font-family: "DM Sans", sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 8% 0%, rgba(215,255,63,.055), transparent 23%),
            radial-gradient(circle at 96% 8%, rgba(139,114,255,.075), transparent 24%),
            var(--bg);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: rgba(9,9,11,.72);
        backdrop-filter: blur(18px);
    }

    [data-testid="stSidebar"] {
        background: rgba(13,13,16,.96);
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.2rem;
    }

    .block-container {
        max-width: 1120px;
        padding: 2.2rem 2.5rem 6rem;
    }

    h1, h2, h3, h4 {
        font-family: "Space Grotesk", sans-serif !important;
        color: var(--text) !important;
        letter-spacing: -1.8px;
    }

    p, label, .stMarkdown, .stCaption {
        color: var(--text);
    }

    .brand-mark {
        display: flex;
        align-items: center;
        gap: 11px;
        margin: 0 0 6px;
    }

    .brand-symbol {
        width: 34px;
        height: 34px;
        display: grid;
        place-items: center;
        background: var(--acid);
        color: #0b0b0d;
        font-family: "Space Grotesk", sans-serif;
        font-weight: 700;
        border-radius: 9px;
        box-shadow: 0 0 28px rgba(215,255,63,.14);
    }

    .brand-name {
        font-family: "Space Grotesk", sans-serif;
        font-size: 1.12rem;
        font-weight: 700;
        letter-spacing: -.5px;
        color: var(--text);
    }

    .brand-sub {
        margin-left: 45px;
        color: var(--muted);
        font-family: "DM Mono", monospace;
        font-size: .62rem;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }

    .section-kicker {
        color: var(--acid);
        font-family: "DM Mono", monospace;
        font-size: .66rem;
        font-weight: 500;
        letter-spacing: 1.8px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(145deg, #121216 0%, #101014 60%, #16141e 100%);
        border: 1px solid var(--line);
        border-radius: 24px;
        padding: 34px 36px;
        margin-bottom: 24px;
        box-shadow: 0 20px 60px rgba(0,0,0,.18);
    }

    .hero:after {
        content: "✦";
        position: absolute;
        right: 34px;
        top: 24px;
        color: var(--acid);
        font-size: 78px;
        line-height: 1;
        opacity: .09;
        transform: rotate(15deg);
    }

    .hero-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: clamp(2.6rem, 6vw, 4.6rem);
        line-height: .94;
        font-weight: 700;
        letter-spacing: -4px;
        max-width: 760px;
        color: var(--text);
    }

    .hero-sub {
        color: var(--muted);
        max-width: 650px;
        font-size: .98rem;
        line-height: 1.65;
        margin-top: 16px;
    }

    .eyebrow {
        color: var(--acid);
        font-family: "DM Mono", monospace;
        font-size: .64rem;
        letter-spacing: 1.6px;
        text-transform: uppercase;
    }

    div.stButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        border-radius: 10px;
        min-height: 42px;
        border: 1px solid var(--line);
        background: var(--surface-2);
        color: var(--text);
        font-weight: 600;
        transition: .18s ease;
    }

    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        border-color: var(--acid);
        color: var(--acid);
        transform: translateY(-1px);
    }

    div.stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: var(--acid);
        color: #0a0a0c;
        border-color: var(--acid);
        box-shadow: 0 8px 28px rgba(215,255,63,.10);
    }

    div.stButton > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
        color: #0a0a0c;
        background: #e1ff68;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stFileUploaderDropzone"] {
        background: var(--surface-2) !important;
        color: var(--text) !important;
        border-color: var(--line) !important;
        border-radius: 10px !important;
    }

    [data-baseweb="select"] > div,
    [data-baseweb="popover"] {
        background: var(--surface-2);
        border-color: var(--line);
        color: var(--text);
    }

    [data-testid="stExpander"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 14px;
    }

    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 14px 16px;
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted) !important;
        font-family: "DM Mono", monospace;
        font-size: .64rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    [data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-family: "Space Grotesk", sans-serif;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface);
        border-color: var(--line) !important;
        border-radius: 18px !important;
    }

    .post-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        padding: 2px 2px 12px;
    }

    .post-user {
        font-family: "Space Grotesk", sans-serif;
        font-weight: 600;
        color: var(--text);
    }

    .post-meta {
        color: var(--muted);
        font-family: "DM Mono", monospace;
        font-size: .62rem;
        letter-spacing: .2px;
    }

    .post-caption {
        font-size: .95rem;
        line-height: 1.6;
        padding: 12px 2px 4px;
    }

    .action-row {
        color: var(--muted);
        font-family: "DM Mono", monospace;
        font-size: .66rem;
        letter-spacing: .4px;
        text-transform: uppercase;
    }

    .stat-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 18px;
    }

    .stat-number {
        font-family: "Space Grotesk", sans-serif;
        font-size: 30px;
        font-weight: 700;
        color: var(--text);
    }

    .stat-label {
        color: var(--muted);
        font-family: "DM Mono", monospace;
        font-size: .62rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 3px;
    }

    .profile-hero {
        background:
            radial-gradient(circle at 90% 20%, rgba(139,114,255,.25), transparent 28%),
            linear-gradient(135deg, #141418, #0d0d10);
        border: 1px solid var(--line);
        border-radius: 24px;
        padding: 32px;
        margin-bottom: 22px;
    }

    .profile-email {
        font-family: "Space Grotesk", sans-serif;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -1.5px;
    }

    .profile-small {
        color: var(--muted);
        margin-top: 7px;
    }

    .comment-line {
        padding: 10px 0;
        border-bottom: 1px solid var(--line);
    }

    .comment-user {
        font-weight: 700;
        font-size: .86rem;
    }

    .comment-text {
        color: #c0c0c8;
        font-size: .9rem;
    }

    .mono {
        font-family: "DM Mono", monospace;
    }

    [data-testid="stSidebar"] .stRadio label {
        border-radius: 9px;
        padding: 5px 8px;
    }

    [data-testid="stSidebar"] .stRadio label:hover {
        background: var(--acid-soft);
    }

    [data-testid="stSidebar"] [aria-checked="true"] + div {
        color: var(--acid);
    }

    .divider-line {
        height: 1px;
        background: var(--line);
        margin: 20px 0;
    }

    @media (max-width: 800px) {
        .block-container {
            padding: 1.2rem 1rem 4rem;
        }
        .hero {
            padding: 26px 22px;
            border-radius: 18px;
        }
        .hero-title {
            font-size: 3rem;
            letter-spacing: -2.6px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state():
    defaults = {
        "token": None,
        "email": None,
        "logged_in": False,
        "page_size": 20,
        "feed_cache": None,
        "profile_cache": None,
        "page": "Home",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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
        st.error("Could not reach the Postgram server.")
        return

    if response.ok:
        data = response.json()
        st.session_state.token = data["access_token"]
        st.session_state.email = email
        st.session_state.logged_in = True
        st.session_state.feed_cache = None
        st.session_state.profile_cache = None
        st.session_state.page = "Home"
        st.rerun()

    try:
        detail = response.json().get("detail", "Login failed.")
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
        st.error("Could not reach the Postgram server.")
        return

    if response.ok:
        st.success("Account created. Sign in to continue.")
        return

    try:
        detail = response.json().get("detail", "Registration failed.")
    except ValueError:
        detail = "Registration failed."

    st.error(detail)


def logout():
    for key, value in {
        "token": None,
        "email": None,
        "logged_in": False,
        "feed_cache": None,
        "profile_cache": None,
        "page": "Home",
    }.items():
        st.session_state[key] = value
    st.rerun()


def format_date(value):
    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
        return parsed.strftime("%d %b %Y · %I:%M %p")
    except (ValueError, AttributeError):
        return value


def is_video(post):
    return post.get("file_type") == "video"


def handle_401(response):
    if response.status_code == 401:
        logout()


def load_feed(force=False):
    if st.session_state.feed_cache is not None and not force:
        return st.session_state.feed_cache

    response = api_request(
        "GET",
        "/feed",
        params={
            "limit": st.session_state.page_size,
            "offset": 0,
        },
    )

    handle_401(response)
    response.raise_for_status()

    data = response.json()
    st.session_state.feed_cache = data
    return data


def load_profile(force=False):
    if st.session_state.profile_cache is not None and not force:
        return st.session_state.profile_cache

    response = api_request("GET", "/profile/me")
    handle_401(response)
    response.raise_for_status()

    data = response.json()
    st.session_state.profile_cache = data
    return data


def upload_post(uploaded_file, caption):
    if uploaded_file.size > MAX_UPLOAD_MB * 1024 * 1024:
        st.error(
            f"File is too large. Maximum size is {MAX_UPLOAD_MB} MB."
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
        data={"caption": caption.strip()},
    )

    if response.ok:
        st.session_state.feed_cache = None
        st.session_state.profile_cache = None
        return True

    try:
        detail = response.json().get("detail", "Upload failed.")
    except ValueError:
        detail = "Upload failed."

    st.error(detail)
    return False


def toggle_like(post_id):
    response = api_request(
        "POST",
        f"/posts/{post_id}/like",
    )

    if response.ok:
        st.session_state.feed_cache = None
        return response.json()

    try:
        detail = response.json().get("detail", "Like failed.")
    except ValueError:
        detail = "Like failed."

    st.error(detail)
    return None


def get_comments(post_id):
    response = api_request(
        "GET",
        f"/posts/{post_id}/comments",
    )

    if response.ok:
        return response.json()

    return []


def add_comment(post_id, content):
    response = api_request(
        "POST",
        f"/posts/{post_id}/comments",
        json={"content": content},
    )

    if response.ok:
        st.session_state.feed_cache = None
        return True

    try:
        detail = response.json().get("detail", "Comment failed.")
    except ValueError:
        detail = "Comment failed."

    st.error(detail)
    return False


def delete_comment(comment_id):
    response = api_request(
        "DELETE",
        f"/comments/{comment_id}",
    )

    if response.ok:
        st.session_state.feed_cache = None
        st.toast("Comment deleted.", icon="🗑️")
        return True

    st.error("Could not delete comment.")
    return False


def edit_post(post_id, caption):
    response = api_request(
        "PATCH",
        f"/posts/{post_id}",
        json={"caption": caption},
    )

    if response.ok:
        st.session_state.feed_cache = None
        st.session_state.profile_cache = None
        st.toast("Post updated.", icon="✓")
        return True

    try:
        detail = response.json().get("detail", "Update failed.")
    except ValueError:
        detail = "Update failed."

    st.error(detail)
    return False


def delete_post(post_id):
    response = api_request(
        "DELETE",
        f"/delete/{post_id}",
    )

    if response.ok:
        st.session_state.feed_cache = None
        st.session_state.profile_cache = None
        st.toast("Post deleted.", icon="🗑️")
        st.rerun()

    try:
        body = response.json()
        st.error(body.get("detail", "Delete failed."))
    except ValueError:
        st.error("Delete failed.")


def auth_screen():
    left, right = st.columns([1.2, .8], gap="large")

    with left:
        st.markdown(
            """
            <div class="hero">
                <div class="section-kicker">POSTGRAM / SOCIAL</div>
                <div class="hero-title">Your moments.<br>One visual home.</div>
                <div class="hero-sub">
                    Share photos and videos, collect reactions,
                    talk in comments, and keep your own profile
                    organized in one place.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        a, b, c = st.columns(3)
        with a:
            st.metric("01", "Share")
        with b:
            st.metric("02", "React")
        with c:
            st.metric("03", "Connect")

    with right:
        st.write("")
        login_tab, register_tab = st.tabs(["Sign in", "Create account"])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input(
                    "Email",
                    placeholder="you@example.com",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Your password",
                )
                submitted = st.form_submit_button(
                    "→  Enter Postgram",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                if not email or not password:
                    st.warning("Enter your email and password.")
                else:
                    login(email, password)

        with register_tab:
            with st.form("register_form"):
                email = st.text_input(
                    "Email",
                    placeholder="you@example.com",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="At least 8 characters",
                )
                submitted = st.form_submit_button(
                    "✦  Create account",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                if not email or not password:
                    st.warning("Enter your email and password.")
                elif len(password) < 8:
                    st.warning("Password must be at least 8 characters.")
                else:
                    register(email, password)


def create_post_panel():
    with st.expander("✦  Create a new moment", expanded=False):
        uploaded_file = st.file_uploader(
            "Choose a photo or video",
            type=[
                "jpg", "jpeg", "png", "webp", "gif",
                "mp4", "mov", "webm", "mkv",
            ],
            help=f"Images and videos up to {MAX_UPLOAD_MB} MB.",
            max_upload_size=MAX_UPLOAD_MB,
        )

        if uploaded_file:
            st.caption(
                f"Selected: {uploaded_file.name} · "
                f"{uploaded_file.size / 1024 / 1024:.1f} MB"
            )

            if uploaded_file.type.startswith("image/"):
                st.image(
                    uploaded_file,
                    caption="Preview",
                    use_container_width=True,
                )
            else:
                st.video(uploaded_file)

        caption = st.text_area(
            "Caption",
            max_chars=255,
            placeholder="Say something about this moment...",
        )

        if st.button(
            "✦  Publish moment",
            type="primary",
            use_container_width=True,
        ):
            if uploaded_file is None:
                st.warning("Choose a photo or video first.")
            elif upload_post(uploaded_file, caption):
                st.success("Your moment is live.")
                st.rerun()


def render_sidebar():
    nav_items = {
        "⌂  Home": "Home",
        "⌕  Explore": "Explore",
        "＋  Create": "Create",
        "◉  Profile": "Profile",
    }

    labels = list(nav_items.keys())

    with st.sidebar:
        st.markdown(
            '''
            <div class="brand-mark">
                <div class="brand-symbol">✦</div>
                <div class="brand-name">POSTGRAM</div>
            </div>
            <div class="brand-sub">visual social space</div>
            <div class="divider-line"></div>
            ''',
            unsafe_allow_html=True,
        )

        current_label = next(
            label
            for label, value in nav_items.items()
            if value == st.session_state.page
        )

        page = st.radio(
            "NAVIGATION",
            labels,
            index=labels.index(current_label),
            label_visibility="visible",
        )

        selected_page = nav_items[page]

        if selected_page != st.session_state.page:
            st.session_state.page = selected_page
            st.rerun()

        st.markdown(
            '<div class="divider-line"></div>'
            '<span class="eyebrow">SIGNED IN AS</span>',
            unsafe_allow_html=True,
        )
        st.caption(st.session_state.email)

        if st.button(
            "↻  Refresh",
            use_container_width=True,
        ):
            st.session_state.feed_cache = None
            st.session_state.profile_cache = None
            st.rerun()

        if st.button(
            "↪  Sign out",
            use_container_width=True,
        ):
            logout()


def render_post(post, show_actions=True):
    with st.container(border=True):
        left, right = st.columns([4, 2], vertical_alignment="center")

        with left:
            st.markdown(
                f"**{post.get('email', 'Postgram user')}**"
            )

        with right:
            st.caption(format_date(post["created_at"]))

        if is_video(post):
            st.video(post["url"])
        else:
            st.image(
                post["url"],
                use_container_width=True,
            )

        if post.get("caption"):
            st.markdown(post["caption"])

        like_count = post.get("likes_count", 0)
        comment_count = post.get("comments_count", 0)
        liked = post.get("liked_by_me", False)

        like_col, comment_col, file_col = st.columns(
            [1.1, 1.3, 3],
            vertical_alignment="center",
        )

        with like_col:
            label = f"♥  {like_count}" if liked else f"♡  {like_count}"
            if st.button(
                label,
                key=f"like_{post['id']}",
                use_container_width=True,
            ):
                toggle_like(post["id"])
                st.rerun()

        with comment_col:
            st.caption(f"◌  {comment_count} comments")

        with file_col:
            st.caption(post.get("file_name", ""))

        if show_actions and post.get("is_owner"):
            edit_col, delete_col = st.columns(2)

            with edit_col:
                with st.popover("✎  Edit caption"):
                    new_caption = st.text_area(
                        "Caption",
                        value=post.get("caption") or "",
                        max_chars=255,
                        key=f"caption_edit_{post['id']}",
                    )
                    if st.button(
                        "Save changes",
                        key=f"save_edit_{post['id']}",
                        type="primary",
                    ):
                        if edit_post(post["id"], new_caption):
                            st.rerun()

            with delete_col:
                if st.button(
                    "⌫  Delete post",
                    key=f"delete_{post['id']}",
                    use_container_width=True,
                ):
                    delete_post(post["id"])

        with st.expander(
            f"Comments · {comment_count}",
            expanded=False,
        ):
            comments = get_comments(post["id"])

            if not comments:
                st.caption("No comments yet. Start the conversation.")

            for comment in comments:
                c1, c2 = st.columns([5, 1])

                with c1:
                    st.markdown(
                        f"**{comment.get('email', 'User')}**  "
                        f"{comment.get('content', '')}"
                    )
                    st.caption(
                        format_date(comment["created_at"])
                    )

                with c2:
                    if comment.get("is_owner"):
                        if st.button(
                            "Delete",
                            key=f"comment_delete_{comment['id']}",
                        ):
                            delete_comment(comment["id"])
                            st.rerun()

            comment_text = st.text_input(
                "Add a comment",
                max_chars=500,
                placeholder="Write something...",
                key=f"comment_input_{post['id']}",
            )

            if st.button(
                "➜  Post comment",
                key=f"comment_send_{post['id']}",
                type="primary",
            ):
                if not comment_text.strip():
                    st.warning("Comment cannot be empty.")
                elif add_comment(post["id"], comment_text):
                    st.rerun()


def home_screen():
    try:
        feed_data = load_feed()
    except requests.RequestException:
        st.error(f"Could not connect to Postgram API at {API_URL}.")
        return

    posts = feed_data.get("posts", [])
    total = feed_data.get("total", len(posts))

    render_sidebar()

    st.markdown(
        """
        <div class="top-hero">
            <div class="hero-kicker">YOUR FEED</div>
            <div class="hero-title">See what's happening.</div>
            <div class="hero-sub">
                Your latest moments, reactions, and conversations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Moments", total)
    with m2:
        st.metric(
            "Photos",
            sum(not is_video(p) for p in posts),
        )
    with m3:
        st.metric(
            "Videos",
            sum(is_video(p) for p in posts),
        )

    create_post_panel()

    search_col, filter_col = st.columns([3, 1])

    with search_col:
        search = st.text_input(
            "Search",
            placeholder="Search captions or creators...",
            label_visibility="collapsed",
        )

    with filter_col:
        filter_type = st.selectbox(
            "Filter",
            ["All", "Photos", "Videos", "Liked by me", "My posts"],
            label_visibility="collapsed",
        )

    search_value = search.strip().lower()
    filtered = []

    for post in posts:
        if filter_type == "Photos" and is_video(post):
            continue
        if filter_type == "Videos" and not is_video(post):
            continue
        if filter_type == "Liked by me" and not post.get("liked_by_me"):
            continue
        if filter_type == "My posts" and not post.get("is_owner"):
            continue

        if search_value:
            haystack = (
                f"{post.get('caption') or ''} "
                f"{post.get('email') or ''}"
            ).lower()
            if search_value not in haystack:
                continue

        filtered.append(post)

    st.markdown(f'<div class="mono" style="color:#92929c;font-size:.68rem;letter-spacing:.6px;text-transform:uppercase;margin:18px 0 10px;">Showing {len(filtered)} of {total} moments</div>', unsafe_allow_html=True)

    if not filtered:
        st.info("No moments match this view.")
        return

    for post in filtered:
        render_post(post)


def explore_screen():
    try:
        feed_data = load_feed()
    except requests.RequestException:
        st.error("Could not connect to Postgram API.")
        return

    posts = feed_data.get("posts", [])

    render_sidebar()

    st.markdown(
        """
        <div class="top-hero">
            <div class="hero-kicker">EXPLORE</div>
            <div class="hero-title">Find something worth seeing.</div>
            <div class="hero-sub">
                Search across the current Postgram community and
                discover photos, videos, and creators.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Explore",
        placeholder="Search captions or creators...",
        label_visibility="collapsed",
    ).strip().lower()

    media = st.segmented_control(
        "Media",
        ["All", "Photos", "Videos"],
        default="All",
    )

    results = []

    for post in posts:
        if media == "Photos" and is_video(post):
            continue
        if media == "Videos" and not is_video(post):
            continue

        haystack = (
            f"{post.get('caption') or ''} "
            f"{post.get('email') or ''}"
        ).lower()

        if query and query not in haystack:
            continue

        results.append(post)

    if not results:
        st.info("Nothing found in the current feed.")
        return

    st.markdown(f'<div class="mono" style="color:#92929c;font-size:.68rem;letter-spacing:.6px;text-transform:uppercase;margin:18px 0 10px;">{len(results)} results</div>', unsafe_allow_html=True)

    for post in results:
        render_post(post, show_actions=False)


def create_screen():
    render_sidebar()

    st.markdown(
        """
        <div class="top-hero">
            <div class="hero-kicker">CREATE</div>
            <div class="hero-title">Publish a new moment.</div>
            <div class="hero-sub">
                Upload a photo or video and add a caption.
                Your post will appear immediately in the feed.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    create_post_panel()


def profile_screen():
    try:
        profile = load_profile()
    except requests.RequestException:
        st.error("Could not load your profile.")
        return

    render_sidebar()

    st.markdown(
        f"""
        <div class="profile-hero">
            <div class="hero-kicker">YOUR PROFILE</div>
            <div class="profile-email">{profile.get('email', '')}</div>
            <div class="profile-small">
                Your Postgram activity at a glance.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    s1, s2, s3 = st.columns(3)

    with s1:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{profile.get("post_count", 0)}</div><div class="stat-label">Posts</div></div>',
            unsafe_allow_html=True,
        )

    with s2:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{profile.get("likes_received", 0)}</div><div class="stat-label">Likes received</div></div>',
            unsafe_allow_html=True,
        )

    with s3:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{len(profile.get("posts", []))}</div><div class="stat-label">Visible moments</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown("<div class=\"section-kicker\">ARCHIVE</div><h2>Your moments</h2>", unsafe_allow_html=True)

    profile_posts = profile.get("posts", [])

    if not profile_posts:
        st.info("You have not published anything yet.")
        return

    cols = st.columns(3)

    for index, post in enumerate(profile_posts):
        with cols[index % 3]:
            with st.container(border=True):
                if is_video(post):
                    st.video(post["url"])
                else:
                    st.image(
                        post["url"],
                        use_container_width=True,
                    )

                if post.get("caption"):
                    st.caption(post["caption"])

                st.caption(format_date(post["created_at"]))


init_state()

if st.session_state.logged_in:
    if st.session_state.page == "Explore":
        explore_screen()
    elif st.session_state.page == "Create":
        create_screen()
    elif st.session_state.page == "Profile":
        profile_screen()
    else:
        home_screen()
else:
    auth_screen()
