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
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --bg: #f7f5ef;
        --surface: #ffffff;
        --surface-soft: #f1eee7;
        --border: #e5e0d7;
        --text: #20232a;
        --muted: #74777f;
        --accent: #ff5c5c;
        --purple: #7567e8;
        --green: #4e9b68;
    }

    .stApp {
        background:
            radial-gradient(circle at 5% 0%, rgba(255,92,92,.10), transparent 25%),
            radial-gradient(circle at 95% 100%, rgba(117,103,232,.10), transparent 28%),
            var(--bg);
        color: var(--text);
        font-family: "DM Sans", sans-serif;
    }

    [data-testid="stSidebar"] {
        background: #fffdf9;
        border-right: 1px solid var(--border);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 1.5rem;
        padding-bottom: 5rem;
    }

    h1,h2,h3 {
        font-family: "Space Grotesk", sans-serif !important;
        color: var(--text) !important;
        letter-spacing: -1.4px;
    }

    div.stButton > button {
        border-radius: 12px;
        border: 1px solid var(--border);
        background: white;
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

    .top-hero {
        background: linear-gradient(135deg, #fff 0%, #fff8f5 55%, #f2efff 100%);
        border: 1px solid var(--border);
        border-radius: 26px;
        padding: 30px;
        margin-bottom: 20px;
    }

    .hero-kicker {
        color: var(--accent);
        font-size: .72rem;
        font-weight: 800;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .hero-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: 42px;
        line-height: 1.03;
        font-weight: 700;
        letter-spacing: -2.5px;
        margin-top: 8px;
    }

    .hero-sub {
        color: var(--muted);
        max-width: 650px;
        font-size: 1.03rem;
        line-height: 1.65;
        margin-top: 10px;
    }

    .post-meta {
        color: var(--muted);
        font-size: .82rem;
    }

    .post-user {
        font-weight: 700;
    }

    .stat-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 18px;
        text-align: center;
    }

    .stat-number {
        font-family: "Space Grotesk", sans-serif;
        font-size: 28px;
        font-weight: 700;
    }

    .stat-label {
        color: var(--muted);
        font-size: .82rem;
    }

    .profile-hero {
        background: linear-gradient(135deg, #20232a, #3b394c);
        color: white;
        border-radius: 26px;
        padding: 30px;
        margin-bottom: 20px;
    }

    .profile-email {
        font-size: 1.35rem;
        font-weight: 700;
    }

    .profile-small {
        color: #c7c5cf;
        margin-top: 5px;
    }

    .comment-line {
        padding: 8px 0;
        border-bottom: 1px solid #eee9e0;
    }

    .comment-user {
        font-weight: 700;
        font-size: .88rem;
    }

    .comment-text {
        color: #4f5259;
        font-size: .92rem;
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
            <div class="top-hero">
                <div class="hero-kicker">POSTGRAM / SOCIAL</div>
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
                    "Enter Postgram →",
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
                    "Create account →",
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
    with st.expander("＋  Create a new moment", expanded=False):
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
            "Publish moment →",
            type="primary",
            use_container_width=True,
        ):
            if uploaded_file is None:
                st.warning("Choose a photo or video first.")
            elif upload_post(uploaded_file, caption):
                st.success("Your moment is live.")
                st.rerun()


def render_sidebar():
    with st.sidebar:
        st.markdown("## ✦ Postgram")
        st.caption("A visual social space.")
        st.divider()

        page = st.radio(
            "Navigate",
            ["Home", "Explore", "Create", "Profile"],
            index=[
                "Home", "Explore", "Create", "Profile"
            ].index(st.session_state.page),
        )

        if page != st.session_state.page:
            st.session_state.page = page
            st.rerun()

        st.divider()
        st.markdown("**Signed in as**")
        st.caption(st.session_state.email)

        if st.button("↻ Refresh", use_container_width=True):
            st.session_state.feed_cache = None
            st.session_state.profile_cache = None
            st.rerun()

        if st.button("Sign out", use_container_width=True):
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
            label = f"♥ {like_count}" if liked else f"♡ {like_count}"
            if st.button(
                label,
                key=f"like_{post['id']}",
                use_container_width=True,
            ):
                toggle_like(post["id"])
                st.rerun()

        with comment_col:
            st.caption(f"💬 {comment_count} comments")

        with file_col:
            st.caption(post.get("file_name", ""))

        if show_actions and post.get("is_owner"):
            edit_col, delete_col = st.columns(2)

            with edit_col:
                with st.popover("Edit caption"):
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
                    "Delete post",
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
                "Post comment",
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

    st.caption(f"Showing {len(filtered)} of {total} moments")

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

    st.caption(f"{len(results)} results")

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
    st.subheader("Your moments")

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
