# Prueba rápida de la API. Uso: pip install -r requirements.txt httpx && python tests/prueba_api.py
import os, sys, base64
import tempfile; os.environ["ENLACESPANEL_DATA"]=tempfile.mkdtemp()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from app.main import app
H={"X-EnlacesPanel":"1"}
def ok(r, code=200):
    assert r.status_code==code, (r.status_code, r.text); return r
with TestClient(app) as c:
    ok(c.post("/api/register", json={"username":"david","password":"12345678","accept":1}), 403)  # CSRF
    ok(c.post("/api/register", headers=H, json={"username":"david","password":"12345678","accept":1}))
    ok(c.post("/api/register", headers=H, json={"username":"ana","password":"12345678","accept":1}))
    ok(c.post("/api/login", headers=H, json={"username":"ana","password":"12345678"}), 403)  # pendiente
    ok(c.post("/api/login", headers=H, json={"username":"david","password":"12345678"}))
    me=ok(c.get("/api/me")).json(); assert me["user"]["is_admin"]
    ok(c.post("/api/pages", headers=H, json={"slug":"panel"}), 400)
    p=ok(c.post("/api/pages", headers=H, json={"slug":"david","name":"David"})).json()
    ok(c.put(f"/api/pages/{p['id']}", headers=H, json={"bio":"Hola <script>","theme":"bosque","socials":[{"net":"instagram","url":"instagram.com/x"}],"style":{"button":"pastilla","bg":"#zzzzzz"}}))
    ok(c.post(f"/api/pages/{p['id']}/links", headers=H, json={"title":"Mal","url":"javascript:alert(1)"}), 400)
    l=ok(c.post(f"/api/pages/{p['id']}/links", headers=H, json={"title":"Web","url":"ejemplo.com","emoji":"🌐"})).json()
    assert l["url"]=="https://ejemplo.com"
    ok(c.post(f"/api/pages/{p['id']}/links", headers=H, json={"kind":"header","title":"Tienda"}))
    l3=ok(c.post(f"/api/pages/{p['id']}/links", headers=H, json={"title":"Futuro","url":"https://a.es","start_at":9999999999})).json()
    jpg=base64.b64encode(b"\xff\xd8\xff"+b"0"*100).decode()
    av=ok(c.post(f"/api/pages/{p['id']}/avatar", headers=H, json={"data":"data:image/jpeg;base64,"+jpg})).json()["avatar"]
    ok(c.post(f"/api/pages/{p['id']}/avatar", headers=H, json={"data":base64.b64encode(b"<svg>").decode()}), 400)
    ok(c.get(av))
    pub=ok(c.get("/david")).text
    assert "Hola &lt;script&gt;" in pub and "Tienda" in pub and "Futuro" not in pub and "Instagram" in pub, pub
    ok(c.get("/david?vista=1"))
    r=c.get(f"/go/{l['id']}", follow_redirects=False); assert r.status_code==302 and r.headers["location"]=="https://ejemplo.com"
    s=ok(c.get(f"/api/pages/{p['id']}/stats?days=7")).json(); assert s["views"]==1 and s["clicks"]==1, s
    ok(c.get("/qr/david.svg")); assert ok(c.get("/qr/david.png")).content[:4]==b"\x89PNG"
    ok(c.post(f"/api/pages/{p['id']}/order", headers=H, json={"ids":[l3["id"], l["id"]]}))
    ok(c.put(f"/api/pages/{p['id']}", headers=H, json={"published":False}))
    c2=TestClient(app); ok(c2.get("/david"), 404); ok(c2.get(f"/go/{l['id']}?vista=1", follow_redirects=False), 404)
    ok(c.get("/david?vista=1"))
    ok(c.put(f"/api/pages/{p['id']}", headers=H, json={"published":True,"legal":"Titular: X"}))
    ok(c.put("/api/admin/settings", headers=H, json={"home":"david"}))
    assert "David" in ok(c2.get("/")).text
    ok(c2.get("/david/aviso-legal")); ok(c2.get("/privacidad")); ok(c2.get("/panel"))
    ok(c2.get(f"/api/pages/{p['id']}"), 401)
    users=ok(c.get("/api/admin/users")).json(); ana=[u for u in users if u["username"]=="ana"][0]
    ok(c.post(f"/api/admin/users/{ana['id']}", headers=H, json={"action":"approve"}))
    ok(c2.post("/api/login", headers=H, json={"username":"ana","password":"12345678"}))
    ok(c2.get(f"/api/pages/{p['id']}"), 404)  # no es suya
    ok(c2.put(f"/api/pages/{p['id']}", headers=H, json={"name":"hack"}), 404)
    ok(c2.post("/api/pages", headers=H, json={"slug":"David"}), 409)
    e=ok(c.get("/api/export")).json(); assert e["paginas"][0]["links"]
    for i in range(6): c2.post("/api/login", headers=H, json={"username":"x","password":"y"})
    ok(c2.post("/api/login", headers=H, json={"username":"ana","password":"12345678"}), 429)
    ok(c2.post("/api/account/delete", headers=H, json={"password":"12345678"}))
    # página automática, dominios y ajustes del servidor
    import app.main as M; M._fails.clear()
    c3=TestClient(app)
    ok(c3.post("/api/register", headers=H, json={"username":"Pepe.Luis","password":"12345678","accept":1}))
    ok(c.post(f"/api/admin/users/{[u for u in ok(c.get('/api/admin/users')).json() if u['username']=='Pepe.Luis'][0]['id']}", headers=H, json={"action":"approve"}))
    ok(c3.post("/api/login", headers=H, json={"username":"Pepe.Luis","password":"12345678"}))
    ap=ok(c3.post("/api/pages", headers=H, json={"auto":True})).json(); assert ap["slug"]=="pepe-luis", ap
    ok(c3.put(f"/api/pages/{ap['id']}", headers=H, json={"domain":"no valido"}), 400)
    ap=ok(c3.put(f"/api/pages/{ap['id']}", headers=H, json={"domain":"https://Pepe.ES/"})).json(); assert ap["domain"]=="pepe.es" and ap["url"]=="https://pepe.es", ap
    assert "Pepe.Luis" in ok(TestClient(app).get("/", headers={"host":"pepe.es"})).text
    ok(c3.put("/api/admin/settings", headers=H, json={"public_url":"x"}), 403)
    ok(c.put("/api/admin/settings", headers=H, json={"public_url":"enlaces.midominio.com/x"}), 400)
    s=ok(c.put("/api/admin/settings", headers=H, json={"public_url":"enlaces.midominio.com","allow_register":False})).json()
    assert s["public_url"]=="https://enlaces.midominio.com" and s["allow_register"] is False, s
    assert ok(c.get(f"/api/pages/{p['id']}")).json()["url"]=="https://enlaces.midominio.com/david"
    ok(TestClient(app).post("/api/register", headers=H, json={"username":"otro","password":"12345678","accept":1}), 403)
    print("TODO OK", r.headers.get("content-security-policy") is not None)
