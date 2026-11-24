"""Configuracion leida de variables de entorno (ver .env.example)."""
import os
from pathlib import Path


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


DATA = Path(os.environ.get("ENLACESPANEL_DATA", "./data")).resolve()
CONFIG = DATA / "config"
AVATARS = DATA / "avatars"
for p in (CONFIG, AVATARS):
    p.mkdir(parents=True, exist_ok=True)

ADMIN_USER = os.environ.get("ADMIN_USER", "").strip()
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
ALLOW_REGISTER = os.environ.get("ALLOW_REGISTER", "1") == "1"
MAX_PAGES = max(1, _int("MAX_PAGES", 5))          # paginas por usuario
MAX_LINKS = max(1, _int("MAX_LINKS", 100))        # enlaces por pagina
STATS_DAYS = max(7, _int("STATS_DAYS", 400))      # dias que se guardan las estadisticas
SESSION_DAYS = 30
# Datos del responsable para el aviso de privacidad (RGPD)
OWNER_NAME = os.environ.get("OWNER_NAME", "").strip()
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "").strip()
# Dirección pública del servidor (por ejemplo https://enlaces.midominio.com). También se puede
# poner desde el panel (Ajustes → Servidor); lo del panel tiene preferencia.
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").strip().rstrip("/")
