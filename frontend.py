from fastapi.responses import HTMLResponse

FRONTEND_HTML = """<!doctype html><html><head><title>Postgram</title></head><body><h1>Postgram</h1></body></html>"""

def get_frontend_html():
    return FRONTEND_HTML
