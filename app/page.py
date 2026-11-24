"""Pagina publica de enlaces: se genera en el servidor (rapida, sin JavaScript y sin cookies)."""
import html, json, time
from . import db
from .config import OWNER_NAME, CONTACT_EMAIL
from .version import VERSION

json_dumps = lambda v: json.dumps(v, ensure_ascii=False)
esc = lambda v: html.escape(str(v or ""), quote=True)

THEMES = {
    "noche":     {"n": "Noche", "bg": "#0f172a", "card": "#1e293b", "text": "#f8fafc", "cardText": "#f8fafc", "accent": "#38bdf8"},
    "papel":     {"n": "Papel", "bg": "#ffffff", "card": "#111111", "text": "#111111", "cardText": "#ffffff", "accent": "#e4002b"},
    "bosque":    {"n": "Bosque", "bg": "#14532d", "card": "#f0fdf4", "text": "#f0fdf4", "cardText": "#14532d", "accent": "#86efac"},
    "atardecer": {"n": "Atardecer", "bg": "linear-gradient(160deg,#f97316,#db2777)", "card": "#ffffff30", "text": "#ffffff", "cardText": "#ffffff", "accent": "#ffffff", "solid": "#db2777"},
    "arena":     {"n": "Arena", "bg": "#f5e9d7", "card": "#2b2118", "text": "#2b2118", "cardText": "#f5e9d7", "accent": "#c2410c"},
    "mar":       {"n": "Mar", "bg": "linear-gradient(180deg,#0c4a6e,#0e7490)", "card": "#ecfeff", "text": "#ecfeff", "cardText": "#0c4a6e", "accent": "#67e8f9", "solid": "#0c4a6e"},
    "lavanda":   {"n": "Lavanda", "bg": "#ede9fe", "card": "#ffffff", "text": "#3b0764", "cardText": "#3b0764", "accent": "#7c3aed"},
    "carbon":    {"n": "Carbón", "bg": "#0a0a0a", "card": "#0a0a0a", "text": "#fafafa", "cardText": "#fafafa", "accent": "#e4002b", "outline": True},
}
BUTTONS = {"redondo": "14px", "pastilla": "999px", "recto": "4px"}
SOCIALS = {  # nombre que se ve; el enlace lo pone el usuario
    "instagram": "Instagram", "tiktok": "TikTok", "youtube": "YouTube", "x": "X",
    "facebook": "Facebook", "whatsapp": "WhatsApp", "telegram": "Telegram", "linkedin": "LinkedIn",
    "github": "GitHub", "twitch": "Twitch", "spotify": "Spotify", "email": "Email", "web": "Web",
}
LOGO = ('<svg class="logo" viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" rx="11" fill="#e4002b"/>'
        '<g fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round"><path d="M17.5 22.5l5-5"/>'
        '<path d="M15.2 19.3l-2.6 2.6a4.6 4.6 0 0 0 6.5 6.5l2.6-2.6"/><path d="M24.8 20.7l2.6-2.6a4.6 4.6 0 0 0-6.5-6.5l-2.6 2.6"/></g></svg>')
COLOR_KEYS = ("bg", "card", "text", "cardText", "accent")


def theme_of(p) -> dict:
    style = db.jload(p["style"], {})
    t = dict(THEMES.get(p["theme"], THEMES["noche"]))
    if p["theme"] == "propio":
        t = {"n": "Propio", "bg": "#ffffff", "card": "#111111", "text": "#111111", "cardText": "#ffffff", "accent": "#e4002b"}
        for k in COLOR_KEYS:
            v = style.get(k, "")
            if isinstance(v, str) and len(v) == 7 and v[0] == "#":
                t[k] = v
    t["radius"] = BUTTONS.get(style.get("button"), "14px")
    t["outline"] = t.get("outline") or style.get("button") == "borde"
    return t


def initials(name: str) -> str:
    parts = (name or "").split()[:2]
    return ("".join(w[0] for w in parts) or "?").upper()


def visible_links(page_id: int):
    now = time.time()
    return [l for l in db.q("SELECT * FROM links WHERE page_id=? AND enabled=1 ORDER BY pos, id", page_id)
            if (not l["start_at"] or l["start_at"] <= now) and (not l["end_at"] or l["end_at"] > now)]


def _head(title, desc, t, extra=""):
    solid = t.get("solid") or (t["bg"] if t["bg"].startswith("#") else "#111")
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="{esc(solid)}">{extra}
<link rel="icon" href="/static/icons/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/static/page.css?v={esc(VERSION)}">
<style>:root{{--bg:{t['bg']};--card:{t['card']};--text:{t['text']};--ct:{t['cardText']};--acc:{t['accent']};--solid:{solid};--r:{t['radius']}}}</style>
</head>"""


def render(p, preview=False, base="") -> str:
    t = theme_of(p)
    slug = p["slug"]
    name = p["name"] or slug
    av = (f'<img src="/a/{esc(p["avatar"])}" alt="" width="96" height="96">' if p["avatar"]
          else esc(initials(name)))
    og = (f'<meta property="og:title" content="{esc(name)}"><meta property="og:description" content="{esc(p["bio"])}">'
          f'<meta property="og:type" content="profile">'
          + (f'<meta property="og:image" content="{esc(base)}/a/{esc(p["avatar"])}">' if p["avatar"] else ""))
    items = []
    for l in visible_links(p["id"]):
        if l["kind"] == "header":
            items.append(f'<h2 class="sec">{esc(l["title"])}</h2>')
            continue
        href = f'/go/{l["id"]}' + ("?vista=1" if preview else "")
        em = f'<span class="em" aria-hidden="true">{esc(l["emoji"])}</span>' if l["emoji"] else ""
        cls = "lk hi" if l["highlight"] else "lk"
        items.append(f'<a class="{cls}" href="{href}" rel="noopener nofollow">{em}<span>{esc(l["title"])}</span></a>')
    if not items:
        items.append('<p class="none">Aún no hay enlaces</p>')
    socials = ""
    soc = [s for s in db.jload(p["socials"], []) if isinstance(s, dict) and s.get("url")]
    if soc:
        socials = '<nav class="soc" aria-label="Redes">' + "".join(
            f'<a href="{esc(s["url"])}" rel="noopener nofollow me">{esc(SOCIALS.get(s.get("net"), "Web"))}</a>'
            for s in soc) + "</nav>"
    legal = f' · <a href="/{esc(slug)}/aviso-legal">Aviso legal</a>' if (p["legal"] or "").strip() else ""
    outline = " outline" if t["outline"] else ""
    banner = '<div class="draft">Vista previa: esta página no está publicada</div>' if not p["published"] else ""
    return _head(name, p["bio"] or name, t, og) + f"""<body class="pg{outline}">{banner}<main class="lp">
<div class="av">{av}</div><h1>{esc(name)}</h1>{f'<p class="bio">{esc(p["bio"])}</p>' if p["bio"] else ''}
{socials}<div class="links">{''.join(items)}</div>
<footer class="foot">{LOGO}<span>Hecho con <a href="https://github.com/pctecnikk/enlacespanel" rel="noopener">EnlacesPanel</a></span></footer>
<p class="legal-l"><a href="/privacidad">Privacidad</a>{legal}</p>
</main></body></html>"""


def render_legal(p) -> str:
    t = theme_of(p)
    body = "".join(f"<p>{esc(par)}</p>" for par in (p["legal"] or "").split("\n") if par.strip())
    return _head(f"Aviso legal · {p['name'] or p['slug']}", "Aviso legal", t) + f"""<body class="pg"><main class="lp doc">
<h1>Aviso legal</h1>{body}<p><a href="/{esc(p['slug'])}">← Volver</a></p></main></body></html>"""


def render_privacy() -> str:
    t = dict(THEMES["papel"], radius="14px")
    who = esc(OWNER_NAME) or "la persona que administra este servidor"
    mail = f' escribiendo a <a href="mailto:{esc(CONTACT_EMAIL)}">{esc(CONTACT_EMAIL)}</a>' if CONTACT_EMAIL else ""
    return _head("Privacidad", "Política de privacidad", t) + f"""<body class="pg"><main class="lp doc">
<h1>Privacidad</h1>
<p><b>Responsable:</b> {who}. Puedes ejercer tus derechos de acceso, rectificación, supresión, oposición,
limitación y portabilidad{mail}. También puedes reclamar ante la Agencia Española de Protección de Datos (aepd.es).</p>
<p><b>Si solo visitas una página:</b> no usamos cookies ni rastreadores, no cargamos nada de otras webs
(ni fuentes, ni analítica, ni publicidad) y no guardamos tu IP ni tu navegador. Solo sumamos 1 a un contador
de visitas y de clics por día, sin ningún dato que te identifique. Esos contadores se borran solos con el tiempo.</p>
<p><b>Si tienes cuenta para editar páginas:</b> guardamos tu nombre de usuario, tu contraseña cifrada (hash)
y lo que publiques (nombre, bio, foto y enlaces). Usamos una única cookie técnica para mantener tu sesión
iniciada; es necesaria para el servicio y por eso no pide consentimiento. Puedes borrar tus páginas y tu
cuenta cuando quieras desde el panel.</p>
<p><b>Base legal:</b> tu consentimiento al crear la cuenta y el interés legítimo en mantener el servicio seguro.
No cedemos datos a terceros. Los datos se guardan en el propio servidor.</p>
<p><b>Al pulsar un enlace</b> sales a otra web, que tiene su propia política de privacidad.</p>
<p><a href="/">← Volver</a></p></main></body></html>"""


def render_404() -> str:
    t = dict(THEMES["papel"], radius="14px")
    return _head("No encontrada", "", t) + """<body class="pg"><main class="lp doc">
<h1>Esta página no existe</h1><p>Puede que el enlace esté mal escrito o que la página se haya borrado.</p>
</main></body></html>"""
