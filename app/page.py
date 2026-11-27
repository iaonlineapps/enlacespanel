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
    "atardecer": {"n": "Atardecer", "bg": "linear-gradient(160deg,#f97316,#db2777)", "card": "#ffffff30", "text": "#ffffff", "cardText": "#ffffff", "accent": "#ffffff", "solid": "#db2777", "glass": True},
    "arena":     {"n": "Arena", "bg": "#f5e9d7", "card": "#2b2118", "text": "#2b2118", "cardText": "#f5e9d7", "accent": "#c2410c"},
    "mar":       {"n": "Mar", "bg": "linear-gradient(180deg,#0c4a6e,#0e7490)", "card": "#ecfeff", "text": "#ecfeff", "cardText": "#0c4a6e", "accent": "#67e8f9", "solid": "#0c4a6e"},
    "lavanda":   {"n": "Lavanda", "bg": "#ede9fe", "card": "#ffffff", "text": "#3b0764", "cardText": "#3b0764", "accent": "#7c3aed"},
    "aurora":    {"n": "Aurora", "bg": "linear-gradient(135deg,#4c1d95,#1e40af,#0f766e,#7c3aed)", "card": "#ffffff22", "text": "#ffffff", "cardText": "#ffffff", "accent": "#a5f3fc", "solid": "#1e3a8a", "glass": True},
    "neon":      {"n": "Neón", "bg": "#05010d", "card": "#05010d", "text": "#f5f3ff", "cardText": "#f5f3ff", "accent": "#f0abfc", "outline": True, "glow": True},
    "carbon":    {"n": "Carbón", "bg": "#0a0a0a", "card": "#0a0a0a", "text": "#fafafa", "cardText": "#fafafa", "accent": "#e4002b", "outline": True},
}
BUTTONS = {"redondo": "14px", "pastilla": "999px", "recto": "4px"}
SOCIALS = {  # nombre que se ve; el enlace lo pone el usuario
    "instagram": "Instagram", "tiktok": "TikTok", "youtube": "YouTube", "x": "X",
    "facebook": "Facebook", "whatsapp": "WhatsApp", "telegram": "Telegram", "linkedin": "LinkedIn",
    "github": "GitHub", "twitch": "Twitch", "spotify": "Spotify", "email": "Correo", "phone": "Teléfono", "web": "Web",
}
# Iconos sencillos dibujados para EnlacesPanel (trazo de 24×24, usan el color del texto). No son los logotipos oficiales.
_I = {
    "instagram": '<rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.3" cy="6.7" r=".6" fill="currentColor"/>',
    "tiktok": '<path d="M14 3v11.5a3.5 3.5 0 1 1-3.5-3.5"/><path d="M14 3c.4 2.6 2.2 4.4 5 4.6"/>',
    "youtube": '<rect x="2.5" y="5.5" width="19" height="13" rx="4"/><path d="M10 9.2v5.6l4.8-2.8z" fill="currentColor"/>',
    "x": '<path d="M4.5 4h4l11 16h-4zM19.5 4l-6.3 7.2M4.5 20l6.3-7.2"/>',
    "facebook": '<path d="M14.5 21v-7.5h2.8l.4-3.2h-3.2V8.4c0-.9.3-1.6 1.6-1.6H18V4c-.5-.1-1.5-.2-2.6-.2-2.5 0-4.1 1.5-4.1 4.2v2.3H8.5v3.2h2.8V21"/>',
    "whatsapp": '<path d="M4 20l1.2-4A8.5 8.5 0 1 1 8.3 19z"/><path d="M9 8.5c0 3.5 3 6.5 6.5 6.5l1-1.4-2-1-1 .8a5 5 0 0 1-2.4-2.4l.8-1-1-2z" fill="currentColor" stroke-width="1"/>',
    "telegram": '<path d="M21 4L3 11l6 2.2L18 7l-7 7.5V20l3.2-3.6L18 19z"/>',
    "linkedin": '<rect x="3.5" y="3.5" width="17" height="17" rx="3"/><path d="M8 10.5V16M8 7.6v.1M11.5 16v-5.5M11.5 13c0-1.5 1-2.6 2.4-2.6 1.4 0 2.1 1 2.1 2.6V16"/>',
    "github": '<path d="M8.5 8 4.5 12l4 4M15.5 8l4 4-4 4M13.5 5.5l-3 13"/>',
    "twitch": '<path d="M5 3.5h15v10l-4 4h-3.5l-3 3v-3H5z"/><path d="M11 8v4M15.5 8v4"/>',
    "spotify": '<circle cx="12" cy="12" r="9"/><path d="M7.5 9.5c3-1 6.5-.7 9 .8M8 12.6c2.5-.7 5-.4 7 .7M8.6 15.4c1.8-.5 3.7-.3 5.2.5"/>',
    "email": '<rect x="3" y="5.5" width="18" height="13" rx="2.5"/><path d="M3.5 7l8.5 6.5L20.5 7"/>',
    "phone": '<path d="M6.5 3.5h3l1.5 4-2 1.3a10 10 0 0 0 6.2 6.2l1.3-2 4 1.5v3a2 2 0 0 1-2 2A16 16 0 0 1 4.5 5.5a2 2 0 0 1 2-2z"/>',
    "web": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.7 5.6 3.7 9s-1.2 6.4-3.7 9c-2.5-2.6-3.7-5.6-3.7-9S9.5 5.6 12 3z"/>',
}
ICONS = {k: f'<svg viewBox="0 0 24 24" aria-hidden="true">{v}</svg>' for k, v in _I.items()}
LOGO = ('<svg class="logo" viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" rx="11" fill="#e4002b"/>'
        '<g fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round"><path d="M17.5 22.5l5-5"/>'
        '<path d="M15.2 19.3l-2.6 2.6a4.6 4.6 0 0 0 6.5 6.5l2.6-2.6"/><path d="M24.8 20.7l2.6-2.6a4.6 4.6 0 0 0-6.5-6.5l-2.6 2.6"/></g></svg>')
ANIMS = {"suave": "Suave", "viva": "Viva", "no": "Sin animación"}
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
    t["socpos"] = "arriba" if style.get("soc") == "arriba" else "abajo"
    t["anim"] = style.get("anim") if style.get("anim") in ANIMS else "suave"
    return t


def initials(name: str) -> str:
    parts = (name or "").split()[:2]
    return ("".join(w[0] for w in parts) or "?").upper()


def visible_links(page_id: int):
    now = time.time()
    return [l for l in db.q("SELECT * FROM links WHERE page_id=? AND enabled=1 ORDER BY pos, id", page_id)
            if (not l["start_at"] or l["start_at"] <= now) and (not l["end_at"] or l["end_at"] > now)]


# Textos fijos de la página pública en inglés (el idioma se elige en Ajustes de cada página)
EN = {"Aún no hay enlaces": "No links yet", "Hecho con": "Made with", "Privacidad": "Privacy", "Aviso legal": "Legal notice",
      "Vista previa: esta página no está publicada": "Preview: this page is not published", "Redes y contacto": "Socials and contact",
      "← Volver": "← Back", "Correo": "Email", "Teléfono": "Phone", "No encontrada": "Not found"}
SOCIALS_EN = {"email": "Email", "phone": "Phone", "web": "Website"}


def tx(s: str, lang: str) -> str:
    return EN.get(s, s) if lang == "en" else s


def page_lang(p) -> str:
    return "en" if db.jload(p["style"], {}).get("lang") == "en" else "es"


def _head(title, desc, t, extra="", lang="es"):
    solid = t.get("solid") or (t["bg"] if t["bg"].startswith("#") else "#111")
    return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="{esc(solid)}">{extra}
<link rel="icon" href="/static/icons/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/static/page.css?v={esc(VERSION)}">
<style>:root{{--bg:{t['bg']};--card:{t['card']};--text:{t['text']};--ct:{t['cardText']};--acc:{t['accent']};--solid:{solid};--r:{t['radius']}}}</style>
</head>"""


def render(p, preview=False, base="") -> str:
    t = theme_of(p)
    lang = page_lang(p)
    q = "?lang=en" if lang == "en" else ""
    slug = p["slug"]
    name = p["name"] or slug
    av = (f'<img src="/a/{esc(p["avatar"])}" alt="" width="96" height="96">' if p["avatar"]
          else esc(initials(name)))
    og = (f'<meta property="og:title" content="{esc(name)}"><meta property="og:description" content="{esc(p["bio"])}">'
          f'<meta property="og:type" content="profile">'
          + (f'<meta property="og:image" content="{esc(base)}/a/{esc(p["avatar"])}">' if p["avatar"] else ""))
    items, n = [], 0
    for l in visible_links(p["id"]):
        if l["kind"] == "header":
            n += 1
            items.append(f'<h2 class="sec" style="--i:{n}">{esc(l["title"])}</h2>')
            continue
        href = f'/go/{l["id"]}' + ("?vista=1" if preview else "")
        if l["image"]:
            em = f'<img class="ic" src="/a/{esc(l["image"])}" alt="" width="44" height="44" loading="lazy">'
        elif l["emoji"]:
            em = f'<span class="ic em" aria-hidden="true">{esc(l["emoji"])}</span>'
        else:
            em = ""
        cls = "lk" + (" hi" if l["highlight"] else "") + (" wi" if em else "")
        n += 1
        items.append(f'<a class="{cls}" style="--i:{n}" href="{href}" rel="noopener nofollow">{em}<span class="tx">{esc(l["title"])}</span></a>')
    if not items:
        items.append(f'<p class="none">{tx("Aún no hay enlaces", lang)}</p>')
    socials = ""
    soc = [s for s in db.jload(p["socials"], []) if isinstance(s, dict) and s.get("url")]
    if soc:
        sname = lambda n: (SOCIALS_EN.get(n) if lang == "en" else None) or SOCIALS.get(n, "Web")
        socials = f'<nav class="soc" aria-label="{tx("Redes y contacto", lang)}">' + "".join(
            f'<a href="{esc(s["url"])}" rel="noopener nofollow me" aria-label="{esc(sname(s.get("net")))}" '
            f'title="{esc(sname(s.get("net")))}" style="--i:{i}">{ICONS.get(s.get("net"), ICONS["web"])}</a>'
            for i, s in enumerate(soc)) + "</nav>"
    legal = f' · <a href="/{esc(slug)}/aviso-legal">{tx("Aviso legal", lang)}</a>' if (p["legal"] or "").strip() else ""
    outline = (" outline" if t["outline"] else "") + f" anim-{t['anim']}"
    banner = f'<div class="draft">{tx("Vista previa: esta página no está publicada", lang)}</div>' if not p["published"] else ""
    if t.get("glass"):
        outline += " glass"
    if t.get("glow"):
        outline += " glow"
    if not t["bg"].startswith("#"):
        outline += " grad"
    return _head(name, p["bio"] or name, t, og, lang) + f"""<body class="pg{outline}">{banner}<main class="lp">
<div class="av">{av}</div><h1 class="nm">{esc(name)}</h1>{f'<p class="bio">{esc(p["bio"])}</p>' if p["bio"] else ''}
{socials if t["socpos"] == "arriba" else ""}<div class="links">{''.join(items)}</div>
{socials if t["socpos"] != "arriba" else ""}
<footer class="foot">{LOGO}<span>{tx("Hecho con", lang)} <a href="https://github.com/iaonlineapps/enlacespanel" rel="noopener">EnlacesPanel</a></span></footer>
<p class="legal-l"><a href="/privacidad{q}">{tx("Privacidad", lang)}</a>{legal}</p>
</main></body></html>"""


def render_legal(p) -> str:
    t = theme_of(p)
    lang = page_lang(p)
    body = "".join(f"<p>{esc(par)}</p>" for par in (p["legal"] or "").split("\n") if par.strip())
    title = tx("Aviso legal", lang)
    return _head(f"{title} · {p['name'] or p['slug']}", title, t, lang=lang) + f"""<body class="pg"><main class="lp doc">
<h1>{title}</h1>{body}<p><a href="/{esc(p['slug'])}">{tx("← Volver", lang)}</a></p></main></body></html>"""


def render_privacy(lang="es") -> str:
    t = dict(THEMES["papel"], radius="14px")
    if lang == "en":
        who = esc(OWNER_NAME) or "the person who runs this server"
        mail = f' by writing to <a href="mailto:{esc(CONTACT_EMAIL)}">{esc(CONTACT_EMAIL)}</a>' if CONTACT_EMAIL else ""
        return _head("Privacy", "Privacy policy", t, lang="en") + f"""<body class="pg"><main class="lp doc">
<h1>Privacy</h1>
<p><b>Data controller:</b> {who}. You can exercise your rights of access, rectification, erasure, objection,
restriction and portability{mail}. You can also complain to your data protection authority.</p>
<p><b>If you only visit a page:</b> we use no cookies or trackers, we load nothing from other websites
(no fonts, analytics or ads) and we do not store your IP or your browser. We only add 1 to a daily counter
of visits and clicks, with no data that identifies you. Those counters are deleted automatically over time.</p>
<p><b>If you have an account to edit pages:</b> we store your username, your encrypted password (hash)
and what you publish (name, bio, photo and links). We use a single technical cookie to keep you signed in;
it is needed for the service, so it does not ask for consent. You can delete your pages and your
account whenever you want from the panel.</p>
<p><b>Legal basis:</b> your consent when creating the account and the legitimate interest in keeping the service secure.
We do not share data with third parties. The data is stored on this server.</p>
<p><b>When you tap a link</b> you go to another website, which has its own privacy policy.</p>
<p><a href="/">← Back</a></p></main></body></html>"""
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


def render_404(lang="es") -> str:
    t = dict(THEMES["papel"], radius="14px")
    if lang == "en":
        return _head("Not found", "", t, lang="en") + """<body class="pg"><main class="lp doc">
<h1>This page does not exist</h1><p>The link may be mistyped or the page may have been deleted.</p>
</main></body></html>"""
    return _head("No encontrada", "", t) + """<body class="pg"><main class="lp doc">
<h1>Esta página no existe</h1><p>Puede que el enlace esté mal escrito o que la página se haya borrado.</p>
</main></body></html>"""
