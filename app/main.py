"""EnlacesPanel: tu página de enlaces autoalojada (API + páginas públicas)."""
import base64, io, re, secrets, time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

import segno
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import (FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response)
from fastapi.staticfiles import StaticFiles

from . import db, page
from .config import AVATARS, ALLOW_REGISTER, MAX_LINKS, MAX_PAGES, PUBLIC_URL, STATS_DAYS
from .version import VERSION

STATIC = Path(__file__).parent / "static"
COOKIE = "enlacespanel_sesion"


@asynccontextmanager
async def lifespan(_app):
    db.init()
    yield


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")

RESERVED = {"api", "static", "panel", "go", "qr", "a", "privacidad", "admin", "login", "entrar",
            "registro", "manifest", "favicon", "robots", "sitemap", "salud", "enlacespanel", "www"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,31}$")
USER_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
BOT_RE = re.compile(r"bot|crawl|spider|slurp|preview|facebookexternalhit|whatsapp|telegram|discord|curl|wget|python", re.I)
CSP = ("default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; "
       "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'self'")


@app.middleware("http")
async def security(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.method not in ("GET", "HEAD"):
        # cabecera propia: un formulario de otra web no puede enviarla (protección CSRF)
        if request.headers.get("x-enlacespanel") != "1":
            return JSONResponse({"detail": "Petición no permitida"}, status_code=403)
    r = await call_next(request)
    r.headers.setdefault("X-Content-Type-Options", "nosniff")
    r.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    r.headers.setdefault("Content-Security-Policy", CSP)
    r.headers.setdefault("Permissions-Policy", "interest-cohort=(), browsing-topics=()")
    return r


# --- utilidades ------------------------------------------------------------
def err(code, msg):
    raise HTTPException(code, msg)


def user_or_401(request: Request):
    u = db.session_user(request.cookies.get(COOKIE, ""))
    if not u:
        err(401, "Tienes que entrar")
    return u


def admin_or_403(request: Request):
    u = user_or_401(request)
    if not u["is_admin"]:
        err(403, "Solo para el administrador")
    return u


def own_page(u, page_id: int):
    p = db.q1("SELECT * FROM pages WHERE id=?", page_id)
    if not p or (p["user_id"] != u["id"] and not u["is_admin"]):
        err(404, "Página no encontrada")
    return p


def base_url(request: Request) -> str:
    """Dirección pública del servidor: la de Ajustes, la de PUBLIC_URL o la que use el navegador."""
    pub = db.get_setting("public_url") or PUBLIC_URL
    if pub:
        return pub
    return f"{request.url.scheme}://{request.headers.get('host', request.url.netloc)}"


def page_url(p, base: str) -> str:
    """Dirección para compartir una página: su dominio propio o servidor/direccion."""
    if p["domain"]:
        return f"https://{p['domain']}"
    return f"{base}/{p['slug']}"


def registration_open() -> bool:
    v = db.get_setting("allow_register")
    return ALLOW_REGISTER if v == "" else v == "1"


DOMAIN_RE = re.compile(r"^(?=.{4,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


def clean_public_url(raw) -> str:
    u = str(raw or "").strip().rstrip("/")
    if not u:
        return ""
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u
    parts = urlsplit(u)
    if not parts.hostname or parts.path not in ("", "/") or parts.query or " " in u:
        err(400, "Escribe solo la dirección, por ejemplo https://enlaces.midominio.com")
    return f"{parts.scheme.lower()}://{parts.netloc.lower()}"


def clean_domain(raw) -> str:
    d = str(raw or "").strip().lower()
    d = re.sub(r"^https?://", "", d).split("/")[0]
    if not d:
        return ""
    if not DOMAIN_RE.match(d):
        err(400, "Ese dominio no parece válido. Escríbelo así: laura.com o enlaces.laura.com")
    return d


def social_url(net: str, raw) -> str:
    """Convierte lo que escribe el usuario (número, @usuario, correo) en el enlace que abre la app."""
    v = str(raw or "").strip()
    if not re.match(r"^[a-z][a-z0-9+.-]*:", v, re.I) and not re.match(r"^(www\.)?[\w-]+\.[a-z]{2,}/", v, re.I):
        if net == "whatsapp":
            digits = re.sub(r"[^\d]", "", v)
            if len(digits) == 9:          # número español sin prefijo
                digits = "34" + digits
            if not 8 <= len(digits) <= 15:
                err(400, "Pon el número de WhatsApp con prefijo, por ejemplo +34 600 123 456")
            return f"https://wa.me/{digits}"
        if net == "telegram":
            name = v.lstrip("@")
            if not re.match(r"^[A-Za-z0-9_]{4,32}$", name):
                err(400, "Pon tu usuario de Telegram, por ejemplo @tunombre")
            return f"https://t.me/{name}"
        if net == "email":
            return clean_url("mailto:" + v)
        if net == "phone":
            return clean_url("tel:" + re.sub(r"[^\d+]", "", v))
        handle = v.lstrip("@")
        if re.match(r"^[A-Za-z0-9_.]{1,40}$", handle) and net in SOCIAL_HOSTS:
            return SOCIAL_HOSTS[net].format(handle)
    return clean_url(v)


SOCIAL_HOSTS = {"instagram": "https://instagram.com/{}", "tiktok": "https://tiktok.com/@{}", "youtube": "https://youtube.com/@{}",
                "x": "https://x.com/{}", "github": "https://github.com/{}", "twitch": "https://twitch.tv/{}",
                "facebook": "https://facebook.com/{}", "linkedin": "https://linkedin.com/in/{}"}


def clean_url(raw) -> str:
    u = str(raw or "").strip()
    if not u:
        err(400, "Falta la dirección")
    if len(u) > 2000:
        err(400, "La dirección es demasiado larga")
    if not re.match(r"^[a-z][a-z0-9+.-]*:", u, re.I):
        u = "https://" + u
    scheme = u.split(":", 1)[0].lower()
    if scheme in ("http", "https"):
        parts = urlsplit(u)
        host = parts.hostname or ""
        if not host or ("." not in host and host != "localhost") or " " in u:
            err(400, "Esa dirección no parece válida")
    elif scheme == "mailto":
        if not re.match(r"^mailto:[^@\s]+@[^@\s]+\.[^@\s]+$", u, re.I):
            err(400, "Ese correo no parece válido")
    elif scheme == "tel":
        if not re.match(r"^tel:\+?[\d\s-]{3,20}$", u, re.I):
            err(400, "Ese teléfono no parece válido")
    else:
        err(400, "Solo se permiten direcciones web, correos (mailto:) o teléfonos (tel:)")
    return u


def text(v, n) -> str:
    return str(v or "").strip()[:n]


def ts(v):
    try:
        v = float(v)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def page_json(p, base=""):
    return {"id": p["id"], "slug": p["slug"], "domain": p["domain"] or "", "url": page_url(p, base) if base else "", "name": p["name"], "bio": p["bio"],
            "avatar": f"/a/{p['avatar']}" if p["avatar"] else "", "theme": p["theme"],
            "style": db.jload(p["style"], {}), "socials": db.jload(p["socials"], []),
            "legal": p["legal"], "published": bool(p["published"])}


def link_json(l):
    return {k: l[k] for k in ("id", "kind", "title", "url", "emoji", "start_at", "end_at")} | {
        "enabled": bool(l["enabled"]), "highlight": bool(l["highlight"]),
        "image": f"/a/{l['image']}" if l["image"] else ""}


# --- límite de intentos de entrada -----------------------------------------
_fails: dict = {}


def _client(request: Request) -> str:
    return request.client.host if request.client else "?"


def check_rate(request: Request):
    f = _fails.get(_client(request))
    if f and f[0] >= 5 and f[1] > time.time():
        err(429, "Demasiados intentos. Espera unos minutos.")


def note_fail(request: Request):
    ip = _client(request)
    n, until = _fails.get(ip, (0, 0))
    if until < time.time():
        n = 0
    _fails[ip] = (n + 1, time.time() + 600)


# --- cuenta ----------------------------------------------------------------
@app.get("/api/me")
def me(request: Request):
    u = db.session_user(request.cookies.get(COOKIE, ""))
    no_users = db.q1("SELECT COUNT(*) n FROM users")["n"] == 0
    info = {"version": VERSION, "allow_register": registration_open() or no_users, "first_user": no_users,
            "max_pages": MAX_PAGES, "socials": page.SOCIALS,
            "themes": {k: {"n": t["n"], "bg": t["bg"], "text": t["text"]} for k, t in page.THEMES.items()},
            "anims": page.ANIMS}
    if not u:
        return info | {"user": None}
    return info | {"user": {"id": u["id"], "username": u["username"], "is_admin": bool(u["is_admin"])}}


@app.post("/api/login")
async def login(request: Request):
    check_rate(request)
    d = await request.json()
    u = db.q1("SELECT * FROM users WHERE username=?", text(d.get("username"), 64))
    if not u or not db.check_pw(str(d.get("password") or ""), u["pw_hash"]):
        note_fail(request)
        err(401, "Usuario o contraseña incorrectos")
    if u["status"] != "approved":
        err(403, "Tu cuenta está pendiente de que el administrador la apruebe")
    _fails.pop(_client(request), None)
    r = JSONResponse({"ok": True})
    r.set_cookie(COOKIE, db.new_session(u["id"]), max_age=30 * 86400, httponly=True, samesite="lax",
                 secure=request.url.scheme == "https")
    return r


@app.post("/api/logout")
def logout(request: Request):
    db.run("DELETE FROM sessions WHERE token=?", request.cookies.get(COOKIE, ""))
    r = JSONResponse({"ok": True})
    r.delete_cookie(COOKIE)
    return r


@app.post("/api/register")
async def register(request: Request):
    check_rate(request)
    first = db.q1("SELECT COUNT(*) n FROM users")["n"] == 0
    if not registration_open() and not first:
        err(403, "El registro está cerrado")
    d = await request.json()
    name, pw = text(d.get("username"), 64), str(d.get("password") or "")
    if not USER_RE.match(name):
        err(400, "El usuario debe tener de 3 a 32 letras, números, puntos, guiones o _")
    if len(pw) < 8:
        err(400, "La contraseña debe tener al menos 8 caracteres")
    if not d.get("accept"):
        err(400, "Tienes que aceptar la política de privacidad")
    if db.q1("SELECT 1 FROM users WHERE username=?", name):
        note_fail(request)
        err(409, "Ese usuario ya existe")
    db.run("INSERT INTO users(username,pw_hash,is_admin,status,created) VALUES(?,?,?,?,?)",
           name, db.hash_pw(pw), int(first), "approved" if first else "pending", time.time())
    return {"ok": True, "approved": first}


@app.post("/api/password")
async def change_password(request: Request):
    u = user_or_401(request)
    d = await request.json()
    if not db.check_pw(str(d.get("old") or ""), u["pw_hash"]):
        err(400, "La contraseña actual no es correcta")
    new = str(d.get("new") or "")
    if len(new) < 8:
        err(400, "La contraseña nueva debe tener al menos 8 caracteres")
    db.run("UPDATE users SET pw_hash=? WHERE id=?", db.hash_pw(new), u["id"])
    db.run("DELETE FROM sessions WHERE user_id=? AND token<>?", u["id"], request.cookies.get(COOKIE, ""))
    return {"ok": True}


def _delete_user_data(user_id: int):
    for p in db.q("SELECT id, avatar FROM pages WHERE user_id=?", user_id):
        _delete_page(p)
    db.run("DELETE FROM sessions WHERE user_id=?", user_id)
    db.run("DELETE FROM users WHERE id=?", user_id)


@app.post("/api/account/delete")
async def delete_account(request: Request):
    u = user_or_401(request)
    d = await request.json()
    if not db.check_pw(str(d.get("password") or ""), u["pw_hash"]):
        err(400, "La contraseña no es correcta")
    if u["is_admin"] and db.q1("SELECT COUNT(*) n FROM users WHERE is_admin=1")["n"] == 1 \
            and db.q1("SELECT COUNT(*) n FROM users")["n"] > 1:
        err(400, "Eres el único administrador: nombra antes a otro")
    _delete_user_data(u["id"])
    r = JSONResponse({"ok": True})
    r.delete_cookie(COOKIE)
    return r


@app.get("/api/export")
def export(request: Request):
    """Descarga de todos tus datos (derecho de portabilidad del RGPD)."""
    u = user_or_401(request)
    pages = []
    for p in db.q("SELECT * FROM pages WHERE user_id=? ORDER BY id", u["id"]):
        links = [link_json(l) for l in db.q("SELECT * FROM links WHERE page_id=? ORDER BY pos,id", p["id"])]
        pages.append(page_json(p) | {"links": links})
    data = {"usuario": u["username"], "creado": u["created"], "paginas": pages, "app": f"EnlacesPanel {VERSION}"}
    return JSONResponse(data, headers={"Content-Disposition": 'attachment; filename="enlacespanel-mis-datos.json"'})


# --- páginas ---------------------------------------------------------------
@app.get("/api/pages")
def list_pages(request: Request):
    u = user_or_401(request)
    b = base_url(request)
    return [page_json(p, b) for p in db.q("SELECT * FROM pages WHERE user_id=? ORDER BY id", u["id"])]


def check_slug(slug: str, page_id: int = 0) -> str:
    slug = text(slug, 32).lower()
    if not SLUG_RE.match(slug) or slug in RESERVED:
        err(400, "La dirección debe tener de 2 a 32 letras minúsculas, números, - o _ (y no ser una palabra reservada)")
    if db.q1("SELECT 1 FROM pages WHERE slug=? AND id<>?", slug, page_id):
        err(409, "Esa dirección ya está cogida")
    return slug


@app.post("/api/pages")
async def create_page(request: Request):
    u = user_or_401(request)
    if db.q1("SELECT COUNT(*) n FROM pages WHERE user_id=?", u["id"])["n"] >= MAX_PAGES:
        err(400, f"Puedes tener como mucho {MAX_PAGES} páginas")
    d = await request.json()
    if d.get("auto"):
        slug = free_slug(u["username"])
    else:
        slug = check_slug(d.get("slug") or "")
    now = time.time()
    cur = db.run("INSERT INTO pages(user_id,slug,name,theme,created,updated) VALUES(?,?,?,?,?,?)",
                 u["id"], slug, text(d.get("name"), 60) or u["username"], "noche", now, now)
    return page_json(db.q1("SELECT * FROM pages WHERE id=?", cur.lastrowid), base_url(request))


def free_slug(name: str) -> str:
    """Primera dirección libre a partir del nombre de usuario (david, david-2, david-3...)."""
    base = re.sub(r"[^a-z0-9_-]", "", name.lower().replace(".", "-"))[:28] or "mi-pagina"
    if len(base) < 2 or not base[0].isalnum():
        base = "pagina-" + base
    for i in range(1, 1000):
        s = base if i == 1 else f"{base}-{i}"
        if s not in RESERVED and not db.q1("SELECT 1 FROM pages WHERE slug=?", s):
            return s
    return "pagina-" + secrets.token_hex(3)


@app.get("/api/pages/{page_id}")
def get_page(page_id: int, request: Request):
    p = own_page(user_or_401(request), page_id)
    links = [link_json(l) for l in db.q("SELECT * FROM links WHERE page_id=? ORDER BY pos,id", page_id)]
    return page_json(p, base_url(request)) | {"links": links}


@app.put("/api/pages/{page_id}")
async def update_page(page_id: int, request: Request):
    p = own_page(user_or_401(request), page_id)
    d = await request.json()
    f = {}
    if "slug" in d:
        f["slug"] = check_slug(d["slug"], page_id)
    if "domain" in d:
        dom = clean_domain(d["domain"])
        if dom and db.q1("SELECT 1 FROM pages WHERE domain=? AND id<>?", dom, page_id):
            err(409, "Ese dominio ya lo usa otra página")
        f["domain"] = dom
    for k, n in (("name", 60), ("bio", 160), ("legal", 3000)):
        if k in d:
            f[k] = text(d[k], n)
    if "theme" in d:
        if d["theme"] not in page.THEMES and d["theme"] != "propio":
            err(400, "Tema desconocido")
        f["theme"] = d["theme"]
    if "published" in d:
        f["published"] = int(bool(d["published"]))
    if "style" in d and isinstance(d["style"], dict):
        st = {k: v for k, v in d["style"].items() if k in page.COLOR_KEYS and isinstance(v, str) and HEX_RE.match(v)}
        if d["style"].get("button") in ("redondo", "pastilla", "recto", "borde"):
            st["button"] = d["style"]["button"]
        if d["style"].get("soc") in ("arriba", "abajo"):
            st["soc"] = d["style"]["soc"]
        if d["style"].get("anim") in page.ANIMS:
            st["anim"] = d["style"]["anim"]
        f["style"] = page.json_dumps(st)
    if "socials" in d and isinstance(d["socials"], list):
        socs = []
        for s in d["socials"][:20]:
            if isinstance(s, dict) and s.get("net") in page.SOCIALS and s.get("url"):
                socs.append({"net": s["net"], "url": social_url(s["net"], s["url"])})
        f["socials"] = page.json_dumps(socs)
    if f:
        f["updated"] = time.time()
        db.run(f"UPDATE pages SET {', '.join(k + '=?' for k in f)} WHERE id=?", *f.values(), p["id"])
    return page_json(db.q1("SELECT * FROM pages WHERE id=?", page_id), base_url(request))


def _delete_page(p):
    if p["avatar"]:
        (AVATARS / p["avatar"]).unlink(missing_ok=True)
    for l in db.q("SELECT image FROM links WHERE page_id=? AND image<>''", p["id"]):
        (AVATARS / l["image"]).unlink(missing_ok=True)
    db.run("DELETE FROM links WHERE page_id=?", p["id"])
    db.run("DELETE FROM stats WHERE page_id=?", p["id"])
    db.run("DELETE FROM pages WHERE id=?", p["id"])


@app.delete("/api/pages/{page_id}")
def delete_page(page_id: int, request: Request):
    _delete_page(own_page(user_or_401(request), page_id))
    return {"ok": True}


MAGIC = {b"\xff\xd8\xff": "jpg", b"\x89PNG\r\n\x1a\n": "png"}


def read_image(d) -> tuple:
    """Devuelve (bytes, extensión) de una imagen enviada en base64, o (b"", "") si viene vacía."""
    data = str(d.get("data") or "")
    if not data:
        return b"", ""
    try:
        raw = base64.b64decode(data.split(",", 1)[-1], validate=True)
    except ValueError:
        err(400, "Imagen no válida")
    if len(raw) > 1_500_000:
        err(400, "La imagen es demasiado grande")
    ext = next((e for m, e in MAGIC.items() if raw.startswith(m)), None)
    if not ext:
        ext = "webp" if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP" else None
    if not ext:
        err(400, "La imagen debe ser JPG, PNG o WebP")
    return raw, ext


@app.post("/api/pages/{page_id}/avatar")
async def set_avatar(page_id: int, request: Request):
    p = own_page(user_or_401(request), page_id)
    raw, ext = read_image(await request.json())
    new = ""
    if raw:
        new = f"{p['id']}-{secrets.token_hex(6)}.{ext}"
        (AVATARS / new).write_bytes(raw)
    if p["avatar"]:
        (AVATARS / p["avatar"]).unlink(missing_ok=True)
    db.run("UPDATE pages SET avatar=?, updated=? WHERE id=?", new, time.time(), p["id"])
    return {"avatar": f"/a/{new}" if new else ""}


# --- enlaces ---------------------------------------------------------------
def link_fields(d, kind):
    f = {}
    if "title" in d:
        f["title"] = text(d["title"], 80)
    if kind == "link" and "url" in d:
        f["url"] = clean_url(d["url"])
    if "emoji" in d:
        f["emoji"] = text(d["emoji"], 8)
    for k in ("enabled", "highlight"):
        if k in d:
            f[k] = int(bool(d[k]))
    for k in ("start_at", "end_at"):
        if k in d:
            f[k] = ts(d[k])
    return f


@app.post("/api/pages/{page_id}/links")
async def add_link(page_id: int, request: Request):
    p = own_page(user_or_401(request), page_id)
    if db.q1("SELECT COUNT(*) n FROM links WHERE page_id=?", page_id)["n"] >= MAX_LINKS:
        err(400, f"Puedes tener como mucho {MAX_LINKS} enlaces por página")
    d = await request.json()
    kind = "header" if d.get("kind") == "header" else "link"
    f = link_fields(d, kind)
    if not f.get("title"):
        err(400, "Ponle un título")
    if kind == "link" and not f.get("url"):
        err(400, "Falta la dirección")
    pos = (db.q1("SELECT MAX(pos) m FROM links WHERE page_id=?", page_id)["m"] or 0) + 1
    if d.get("top"):
        db.run("UPDATE links SET pos=pos+1 WHERE page_id=?", page_id)
        pos = 0
    f |= {"page_id": p["id"], "kind": kind, "pos": pos, "created": time.time()}
    cur = db.run(f"INSERT INTO links({','.join(f)}) VALUES({','.join('?' * len(f))})", *f.values())
    return link_json(db.q1("SELECT * FROM links WHERE id=?", cur.lastrowid))


def own_link(u, link_id):
    l = db.q1("SELECT * FROM links WHERE id=?", link_id)
    if not l:
        err(404, "Enlace no encontrado")
    own_page(u, l["page_id"])
    return l


@app.put("/api/links/{link_id}")
async def update_link(link_id: int, request: Request):
    l = own_link(user_or_401(request), link_id)
    f = link_fields(await request.json(), l["kind"])
    if "title" in f and not f["title"]:
        err(400, "Ponle un título")
    if f:
        db.run(f"UPDATE links SET {', '.join(k + '=?' for k in f)} WHERE id=?", *f.values(), link_id)
    return link_json(db.q1("SELECT * FROM links WHERE id=?", link_id))


@app.post("/api/links/{link_id}/image")
async def set_link_image(link_id: int, request: Request):
    """Foto o logo del botón (sustituye al emoji)."""
    l = own_link(user_or_401(request), link_id)
    raw, ext = read_image(await request.json())
    new = ""
    if raw:
        new = f"l{l['id']}-{secrets.token_hex(6)}.{ext}"
        (AVATARS / new).write_bytes(raw)
    if l["image"]:
        (AVATARS / l["image"]).unlink(missing_ok=True)
    db.run("UPDATE links SET image=?, emoji=CASE WHEN ?<>'' THEN '' ELSE emoji END WHERE id=?", new, new, link_id)
    return link_json(db.q1("SELECT * FROM links WHERE id=?", link_id))


@app.delete("/api/links/{link_id}")
def delete_link(link_id: int, request: Request):
    l = own_link(user_or_401(request), link_id)
    if l["image"]:
        (AVATARS / l["image"]).unlink(missing_ok=True)
    db.run("DELETE FROM links WHERE id=?", link_id)
    db.run("DELETE FROM stats WHERE link_id=?", link_id)
    return {"ok": True}


@app.post("/api/pages/{page_id}/order")
async def reorder(page_id: int, request: Request):
    own_page(user_or_401(request), page_id)
    ids = (await request.json()).get("ids") or []
    mine = {r["id"] for r in db.q("SELECT id FROM links WHERE page_id=?", page_id)}
    for i, lid in enumerate(x for x in ids if x in mine):
        db.run("UPDATE links SET pos=? WHERE id=?", i, lid)
    return {"ok": True}


# --- estadísticas ----------------------------------------------------------
@app.get("/api/pages/{page_id}/stats")
def stats(page_id: int, request: Request, days: int = 30):
    own_page(user_or_401(request), page_id)
    days = max(1, min(days, STATS_DAYS))
    since = time.strftime("%Y-%m-%d", time.localtime(time.time() - (days - 1) * 86400))
    series = {}
    for i in range(days):
        series[time.strftime("%Y-%m-%d", time.localtime(time.time() - (days - 1 - i) * 86400))] = [0, 0]
    per_link = {}
    for r in db.q("SELECT link_id, day, n FROM stats WHERE page_id=? AND day>=?", page_id, since):
        if r["day"] in series:
            series[r["day"]][0 if r["link_id"] == 0 else 1] += r["n"]
        if r["link_id"]:
            per_link[r["link_id"]] = per_link.get(r["link_id"], 0) + r["n"]
    links = [{"id": l["id"], "title": l["title"], "clicks": per_link.get(l["id"], 0)}
             for l in db.q("SELECT id,title FROM links WHERE page_id=? AND kind='link' ORDER BY pos,id", page_id)]
    views = sum(v[0] for v in series.values())
    clicks = sum(v[1] for v in series.values())
    return {"days": [{"day": k, "views": v[0], "clicks": v[1]} for k, v in series.items()],
            "views": views, "clicks": clicks, "links": links}


# --- administración --------------------------------------------------------
@app.get("/api/admin/users")
def admin_users(request: Request):
    admin_or_403(request)
    return [{"id": u["id"], "username": u["username"], "is_admin": bool(u["is_admin"]), "status": u["status"],
             "created": u["created"], "pages": u["pages"]}
            for u in db.q("SELECT u.*, (SELECT COUNT(*) FROM pages p WHERE p.user_id=u.id) pages "
                          "FROM users u ORDER BY u.status='approved', u.id")]


@app.post("/api/admin/users")
async def admin_create_user(request: Request):
    """El administrador crea una cuenta ya aprobada (con su contraseña)."""
    admin_or_403(request)
    d = await request.json()
    name, pw = text(d.get("username"), 64), str(d.get("password") or "")
    if not USER_RE.match(name):
        err(400, "El usuario debe tener de 3 a 32 letras, números, puntos, guiones o _")
    if len(pw) < 8:
        err(400, "La contraseña debe tener al menos 8 caracteres")
    if db.q1("SELECT 1 FROM users WHERE username=?", name):
        err(409, "Ese usuario ya existe")
    db.run("INSERT INTO users(username,pw_hash,is_admin,status,created) VALUES(?,?,?,'approved',?)",
           name, db.hash_pw(pw), int(bool(d.get("is_admin"))), time.time())
    return {"ok": True}


@app.post("/api/admin/users/{user_id}")
async def admin_user(user_id: int, request: Request):
    me_ = admin_or_403(request)
    d = await request.json()
    action = d.get("action")
    if user_id == me_["id"] and action in ("disable", "unadmin", "delete"):
        err(400, "No puedes hacerte eso a ti mismo")
    if not db.q1("SELECT 1 FROM users WHERE id=?", user_id):
        err(404, "Usuario no encontrado")
    if action == "approve":
        db.run("UPDATE users SET status='approved' WHERE id=?", user_id)
    elif action == "disable":
        db.run("UPDATE users SET status='disabled' WHERE id=?", user_id)
        db.run("DELETE FROM sessions WHERE user_id=?", user_id)
    elif action in ("admin", "unadmin"):
        db.run("UPDATE users SET is_admin=? WHERE id=?", int(action == "admin"), user_id)
    elif action == "delete":
        _delete_user_data(user_id)
    elif action == "password":
        pw = str(d.get("password") or "")
        if len(pw) < 8:
            err(400, "La contraseña debe tener al menos 8 caracteres")
        db.run("UPDATE users SET pw_hash=? WHERE id=?", db.hash_pw(pw), user_id)
        db.run("DELETE FROM sessions WHERE user_id=?", user_id)
    else:
        err(400, "Acción desconocida")
    return {"ok": True}


@app.get("/api/novedades")
def novedades(request: Request):
    """Lista de cambios de la web (app/NOVEDADES.md), para el aviso tras actualizar."""
    user_or_401(request)
    out, cur = [], None
    for line in (Path(__file__).parent / "NOVEDADES.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            cur = {"version": line[3:].strip(), "items": []}
            out.append(cur)
        elif cur is not None and line.startswith("- "):
            cur["items"].append(line[2:].strip())
        elif cur is not None and line.startswith("  ") and cur["items"]:
            cur["items"][-1] += " " + line.strip()
    return {"version": VERSION, "novedades": out}


@app.get("/api/admin/settings")
def admin_settings(request: Request):
    admin_or_403(request)
    return {"home": db.get_setting("home"), "public_url": db.get_setting("public_url") or PUBLIC_URL,
            "allow_register": registration_open()}


@app.put("/api/admin/settings")
async def admin_settings_put(request: Request):
    admin_or_403(request)
    d = await request.json()
    if "home" in d:
        home = text(d.get("home"), 32).lower()
        if home and not db.q1("SELECT 1 FROM pages WHERE slug=?", home):
            err(400, "No hay ninguna página con esa dirección")
        db.set_setting("home", home)
    if "public_url" in d:
        db.set_setting("public_url", clean_public_url(d["public_url"]))
    if "allow_register" in d:
        db.set_setting("allow_register", "1" if d["allow_register"] else "0")
    return admin_settings(request)


# --- QR --------------------------------------------------------------------
@app.get("/qr/{slug}.{fmt}")
def qr(slug: str, fmt: str, request: Request, color: str = "#111111", fondo: str = "#ffffff"):
    p = db.q1("SELECT slug, domain FROM pages WHERE slug=?", slug.lower())
    if not p or fmt not in ("svg", "png"):
        err(404, "No encontrado")
    dark = color if HEX_RE.match(color) else "#111111"
    light = fondo if HEX_RE.match(fondo) else "#ffffff"
    buf = io.BytesIO()
    segno.make(page_url(p, base_url(request)), error="m").save(
        buf, kind=fmt, scale=12 if fmt == "png" else 10, border=2, dark=dark, light=light)
    media = "image/svg+xml" if fmt == "svg" else "image/png"
    return Response(buf.getvalue(), media_type=media, headers={
        "Content-Disposition": f'inline; filename="qr-{p["slug"]}.{fmt}"', "Cache-Control": "no-cache"})


# --- público ---------------------------------------------------------------
@app.get("/salud")
def health():
    return {"ok": True, "version": VERSION}


@app.get("/robots.txt")
def robots():
    return Response("User-agent: *\nDisallow: /api/\nDisallow: /go/\nDisallow: /panel\n", media_type="text/plain")


@app.get("/panel", response_class=HTMLResponse)
def panel():
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/privacidad", response_class=HTMLResponse)
def privacy():
    return page.render_privacy()


@app.get("/a/{name}")
def avatar(name: str):
    if not re.match(r"^l?\d+-[0-9a-f]{12}\.(jpg|png|webp)$", name) or not (AVATARS / name).is_file():
        err(404, "No encontrado")
    return FileResponse(AVATARS / name, headers={"Cache-Control": "public, max-age=31536000, immutable"})


def is_bot(request: Request) -> bool:
    return bool(BOT_RE.search(request.headers.get("user-agent", "")))


@app.get("/go/{link_id}")
def go(link_id: int, request: Request, vista: int = 0):
    l = db.q1("SELECT l.*, p.published, p.id pid FROM links l JOIN pages p ON p.id=l.page_id WHERE l.id=?", link_id)
    if not l or l["kind"] != "link" or not l["enabled"]:
        return HTMLResponse(page.render_404(), status_code=404)
    if not l["published"]:
        u = db.session_user(request.cookies.get(COOKIE, ""))
        owner = db.q1("SELECT user_id FROM pages WHERE id=?", l["pid"])["user_id"]
        if not (vista and u and (u["id"] == owner or u["is_admin"])):
            return HTMLResponse(page.render_404(), status_code=404)
    if not vista and not is_bot(request):
        db.count(l["pid"], l["id"])
    return RedirectResponse(l["url"], status_code=302)


def _show(request: Request, p, preview: bool):
    if not p:
        return HTMLResponse(page.render_404(), status_code=404)
    if not p["published"]:
        u = db.session_user(request.cookies.get(COOKIE, ""))
        if not (preview and u and (u["id"] == p["user_id"] or u["is_admin"])):
            return HTMLResponse(page.render_404(), status_code=404)
    if not preview and not is_bot(request) and request.method == "GET":
        db.count(p["id"], 0)
    return HTMLResponse(page.render(p, preview, base_url(request)),
                        headers={"Cache-Control": "no-cache"})


@app.get("/", response_class=HTMLResponse)
def home(request: Request, vista: int = 0):
    # Dominio propio de una página (laura.com → su página)
    host = (request.headers.get("host") or "").split(":")[0].lower()
    if host:
        p = db.q1("SELECT * FROM pages WHERE domain=?", host)
        if p:
            return _show(request, p, bool(vista))
    slug = db.get_setting("home")
    p = db.q1("SELECT * FROM pages WHERE slug=?", slug) if slug else None
    if not p or not p["published"]:
        return RedirectResponse("/panel", status_code=302)
    return _show(request, p, bool(vista))


@app.get("/{slug}/aviso-legal", response_class=HTMLResponse)
def legal(slug: str):
    p = db.q1("SELECT * FROM pages WHERE slug=?", slug.lower())
    if not p or not p["published"] or not (p["legal"] or "").strip():
        return HTMLResponse(page.render_404(), status_code=404)
    return page.render_legal(p)


@app.get("/{slug}", response_class=HTMLResponse)
def public_page(slug: str, request: Request, vista: int = 0):
    return _show(request, db.q1("SELECT * FROM pages WHERE slug=?", slug.lower()), bool(vista))
