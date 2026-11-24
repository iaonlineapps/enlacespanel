"""Base de datos SQLite: usuarios, sesiones, paginas, enlaces y estadisticas."""
import hashlib, hmac, json, os, secrets, sqlite3, threading, time
from .config import CONFIG, ADMIN_USER, ADMIN_PASSWORD, SESSION_DAYS, STATS_DAYS

DB_PATH = CONFIG / "enlacespanel.db"
_local = threading.local()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL COLLATE NOCASE,
  pw_hash TEXT NOT NULL, is_admin INTEGER DEFAULT 0,
  status TEXT DEFAULT 'pending', created REAL);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER, expires REAL);
CREATE TABLE IF NOT EXISTS pages(
  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, slug TEXT UNIQUE NOT NULL COLLATE NOCASE,
  name TEXT DEFAULT '', bio TEXT DEFAULT '', avatar TEXT DEFAULT '', theme TEXT DEFAULT 'noche',
  style TEXT DEFAULT '{}', socials TEXT DEFAULT '[]', legal TEXT DEFAULT '',
  published INTEGER DEFAULT 1, created REAL, updated REAL);
CREATE TABLE IF NOT EXISTS links(
  id INTEGER PRIMARY KEY, page_id INTEGER NOT NULL, pos INTEGER DEFAULT 0,
  kind TEXT DEFAULT 'link', title TEXT DEFAULT '', url TEXT DEFAULT '', emoji TEXT DEFAULT '',
  enabled INTEGER DEFAULT 1, highlight INTEGER DEFAULT 0,
  start_at REAL, end_at REAL, created REAL);
CREATE INDEX IF NOT EXISTS links_page ON links(page_id, pos);
-- Estadisticas sin datos personales: solo contadores por dia (link_id 0 = visitas)
CREATE TABLE IF NOT EXISTS stats(
  page_id INTEGER, link_id INTEGER, day TEXT, n INTEGER DEFAULT 0,
  PRIMARY KEY(page_id, link_id, day));
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
"""


def conn():
    c = getattr(_local, "c", None)
    if c is None:
        c = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA foreign_keys=ON")
        _local.c = c
    return c


def q(sql, *args):
    return conn().execute(sql, args).fetchall()


def q1(sql, *args):
    return conn().execute(sql, args).fetchone()


def run(sql, *args):
    return conn().execute(sql, args)


# --- contrasenas -----------------------------------------------------------
ITER = 120_000


def hash_pw(pw: str) -> str:
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, ITER)
    return f"pbkdf2${ITER}${salt.hex()}${h.hex()}"


def check_pw(pw: str, stored: str) -> bool:
    try:
        _, it, salt, h = stored.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), int(it))
        return hmac.compare_digest(calc.hex(), h)
    except Exception:
        return False


# --- sesiones --------------------------------------------------------------
def new_session(user_id: int) -> str:
    tok = secrets.token_urlsafe(32)
    run("INSERT INTO sessions VALUES(?,?,?)", tok, user_id, time.time() + SESSION_DAYS * 86400)
    return tok


def session_user(tok: str):
    if not tok:
        return None
    u = q1("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id "
           "WHERE s.token=? AND s.expires>?", tok, time.time())
    if u and u["status"] == "approved":
        return u
    return None


# --- ajustes ---------------------------------------------------------------
def get_setting(key, default=""):
    r = q1("SELECT value FROM settings WHERE key=?", key)
    return r["value"] if r else default


def set_setting(key, value):
    run("INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        key, value)


# --- estadisticas ----------------------------------------------------------
def count(page_id: int, link_id: int = 0):
    day = time.strftime("%Y-%m-%d")
    run("INSERT INTO stats VALUES(?,?,?,1) ON CONFLICT(page_id,link_id,day) DO UPDATE SET n=n+1",
        page_id, link_id, day)


def purge_old_stats():
    limit = time.strftime("%Y-%m-%d", time.localtime(time.time() - STATS_DAYS * 86400))
    run("DELETE FROM stats WHERE day<?", limit)
    run("DELETE FROM sessions WHERE expires<?", time.time())


def init():
    conn().executescript(SCHEMA)
    if ADMIN_USER and ADMIN_PASSWORD and not q1("SELECT 1 FROM users WHERE username=?", ADMIN_USER):
        run("INSERT INTO users(username,pw_hash,is_admin,status,created) VALUES(?,?,1,'approved',?)",
            ADMIN_USER, hash_pw(ADMIN_PASSWORD), time.time())
    purge_old_stats()


def jload(s, default):
    try:
        v = json.loads(s or "")
        return v if isinstance(v, type(default)) else default
    except ValueError:
        return default
