import os, re, time, hmac, hashlib, secrets, sqlite3, json, math
from typing import Optional, List
import jwt
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .integrations import get_sms

DEV = os.getenv("MX_DEV", "0") == "1"
SECRET = os.getenv("MX_SECRET") or (secrets.token_hex(32) if DEV else None)
if not SECRET:
    raise RuntimeError("MX_SECRET o'rnatilmagan (ishlab chiqarishda majburiy)")
DB = os.getenv("MX_DB", "mx.db")
SUPER = os.getenv("MX_SUPERADMIN_PHONE", "")
COMMISSION = float(os.getenv("MX_COMMISSION", "0.10"))  # namunaviy; biznes qoidasi belgilanadi
ROLES = ["user", "worker", "operator", "manager", "admin", "superadmin"]
OPS, MGR, ADM = {"operator", "admin", "superadmin"}, {"manager", "admin", "superadmin"}, {"admin", "superadmin"}
ETAS = set(range(5, 61, 5))
CATS = [  # nom, faol, rejim (hay=haydovchi, kur=kuryer, ust=usta), oila
    ("Taksi", 1, "hay", "Yo'l"), ("Yetkazib berish", 1, "kur", "Yo'l"), ("Ustalar", 1, "ust", "Xizmatlar"),
    ("Taomlar", 1, "kur", "Xarid"), ("Marketplace", 1, "kur", "Xarid"),
    ("Transport", 0, "", "Yo'l"), ("Logistika", 0, "", "Yo'l"), ("Ulgurji", 0, "", "Savdo turlari"),
    ("Auksion", 0, "", "Savdo turlari"), ("Tender", 0, "", "Savdo turlari"), ("Ijara", 0, "", "Savdo turlari"),
    ("Onlayn navbat", 0, "", "Xizmatlar"), ("Ta'lim", 0, "", "Xizmatlar"), ("IT", 0, "", "Xizmatlar"),
    ("Bank", 0, "", "Moliya"), ("Lizing", 0, "", "Moliya"), ("Sug'urta", 0, "", "Moliya"),
    ("Ishlab chiqaruvchilar", 0, "", "Ishlab chiqarish"), ("Zavodlar", 0, "", "Ishlab chiqarish"),
    ("Fabrikalar", 0, "", "Ishlab chiqarish"), ("Hunarmandlar", 0, "", "Ishlab chiqarish"),
    ("Dehqonlar", 0, "", "Qishloq xo'jaligi"), ("Chorvachilik", 0, "", "Qishloq xo'jaligi"),
    ("Hayriya", 0, "", "Xayriya"), ("Ehson", 0, "", "Xayriya"), ("Ezgu ishlar", 0, "", "Xayriya"),
]
SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, phone TEXT UNIQUE NOT NULL, name TEXT DEFAULT '', role TEXT DEFAULT 'user', created REAL);
CREATE TABLE IF NOT EXISTS otps(id INTEGER PRIMARY KEY, phone TEXT, code_hash TEXT, exp REAL, tries INTEGER DEFAULT 0, created REAL);
CREATE TABLE IF NOT EXISTS categories(name TEXT PRIMARY KEY, active INTEGER, mode TEXT, family TEXT);
CREATE TABLE IF NOT EXISTS workers(user_id INTEGER PRIMARY KEY, modes TEXT DEFAULT '[]', online INTEGER DEFAULT 0, lat REAL, lon REAL, updated REAL);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, user_id INTEGER, worker_id INTEGER, cat TEXT, sub TEXT, addr TEXT, dest TEXT, lat REAL, lon REAL,
  pay TEXT, tip INTEGER DEFAULT 0, note TEXT, status INTEGER DEFAULT 0, eta REAL, price INTEGER, rating INTEGER, rcomment TEXT, client_rating INTEGER,
  created REAL, updated REAL);
CREATE INDEX IF NOT EXISTS ix_orders_status ON orders(status, cat);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, user_id INTEGER, sender TEXT, text TEXT, created REAL, read INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, actor INTEGER, action TEXT, detail TEXT, created REAL);
"""


def connect():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_db():
    c = connect()
    c.executescript(SCHEMA)
    for n, a, m, f in CATS:
        c.execute("INSERT OR IGNORE INTO categories VALUES(?,?,?,?)", (n, a, m, f))
    c.commit(); c.close()


init_db()
app = FastAPI(title="1001 Xizmat API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=[o for o in os.getenv("MX_CORS", "").split(",") if o],
                   allow_methods=["*"], allow_headers=["Authorization", "Content-Type"])


@app.middleware("http")
async def sec_headers(request: Request, call_next):
    r = await call_next(request)
    r.headers.update({"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
                      "Cache-Control": "no-store"})
    return r


def db():
    c = connect()
    try:
        yield c
    finally:
        c.close()


def norm_phone(p: str) -> str:
    d = re.sub(r"\D", "", p or "")
    if len(d) == 9: d = "998" + d
    if not (len(d) == 12 and d.startswith("998")): raise HTTPException(422, "Telefon raqami noto'g'ri (+998XXXXXXXXX)")
    return "+" + d


def audit(c, actor, action, detail=""):
    c.execute("INSERT INTO audit(actor,action,detail,created) VALUES(?,?,?,?)", (actor, action, detail, time.time()))


def tell(c, user_id, text, sender="system"):
    c.execute("INSERT INTO messages(user_id,sender,text,created) VALUES(?,?,?,?)", (user_id, sender, text, time.time()))


def user(request: Request, c=Depends(db)):
    h = request.headers.get("Authorization", "")
    if not h.startswith("Bearer "): raise HTTPException(401, "Kirish talab qilinadi")
    try:
        uid = int(jwt.decode(h[7:], SECRET, algorithms=["HS256"])["sub"])
    except Exception:
        raise HTTPException(401, "Token yaroqsiz yoki muddati tugagan")
    u = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not u: raise HTTPException(401, "Foydalanuvchi topilmadi")
    return dict(u)


def need(*roles):
    def dep(u=Depends(user)):
        if u["role"] not in roles: raise HTTPException(403, "Ruxsat yo'q")
        return u
    return dep


# ---------- Auth ----------
class PhoneIn(BaseModel): phone: str
class VerifyIn(BaseModel): phone: str; code: str = Field(min_length=6, max_length=6)


def code_hash(phone, code): return hmac.new(SECRET.encode(), f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()


@app.post("/auth/request-otp")
def request_otp(b: PhoneIn, c=Depends(db)):
    p, now = norm_phone(b.phone), time.time()
    if c.execute("SELECT COUNT(*) FROM otps WHERE phone=? AND created>?", (p, now - 600)).fetchone()[0] >= 3:
        raise HTTPException(429, "Juda ko'p urinish. 10 daqiqadan keyin qayta urinib ko'ring")
    code = f"{secrets.randbelow(10**6):06d}"
    c.execute("INSERT INTO otps(phone,code_hash,exp,created) VALUES(?,?,?,?)", (p, code_hash(p, code), now + 300, now)); c.commit()
    get_sms().send(p, f"1001 Xizmat tasdiqlash kodi: {code}")
    return {"ok": True, **({"dev_code": code} if DEV else {})}


@app.post("/auth/verify")
def verify(b: VerifyIn, c=Depends(db)):
    p, now = norm_phone(b.phone), time.time()
    o = c.execute("SELECT * FROM otps WHERE phone=? ORDER BY id DESC LIMIT 1", (p,)).fetchone()
    if not o or o["exp"] < now: raise HTTPException(400, "Kod topilmadi yoki muddati tugagan")
    if o["tries"] >= 5: raise HTTPException(429, "Urinishlar tugadi. Yangi kod so'rang")
    c.execute("UPDATE otps SET tries=tries+1 WHERE id=?", (o["id"],)); c.commit()
    if not hmac.compare_digest(o["code_hash"], code_hash(p, b.code)): raise HTTPException(400, "Kod noto'g'ri")
    c.execute("DELETE FROM otps WHERE phone=?", (p,))
    c.execute("INSERT OR IGNORE INTO users(phone,role,created) VALUES(?,?,?)", (p, "superadmin" if p == SUPER else "user", now))
    u = c.execute("SELECT * FROM users WHERE phone=?", (p,)).fetchone(); c.commit()
    tok = jwt.encode({"sub": str(u["id"]), "exp": now + 12 * 3600}, SECRET, algorithm="HS256")
    return {"token": tok, "user": {"id": u["id"], "phone": p, "role": u["role"], "name": u["name"]}}


class ProfileIn(BaseModel): name: str = Field(min_length=1, max_length=60)


@app.put("/me")
def set_me(b: ProfileIn, u=Depends(user), c=Depends(db)):
    c.execute("UPDATE users SET name=? WHERE id=?", (b.name.strip(), u["id"])); c.commit(); return {"ok": True}


@app.get("/me")
def me(u=Depends(user)): return {k: u[k] for k in ("id", "phone", "name", "role")}


@app.get("/health")
def health(): return {"ok": True}


@app.get("/categories")
def categories(c=Depends(db)): return [dict(r) for r in c.execute("SELECT name,active,family FROM categories ORDER BY active DESC, family, name")]


# ---------- Buyurtmalar (mijoz) ----------
class OrderIn(BaseModel):
    cat: str
    sub: str = Field(min_length=1, max_length=80)
    addr: str = Field(min_length=1, max_length=200)
    dest: str = Field("", max_length=200)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    pay: str = Field("cash", pattern="^(cash|card)$")
    tip: int = Field(0, ge=0, le=10_000_000)
    note: str = Field("", max_length=300)


@app.post("/orders", status_code=201)
def create_order(b: OrderIn, u=Depends(user), c=Depends(db)):
    cat = c.execute("SELECT * FROM categories WHERE name=?", (b.cat,)).fetchone()
    if not cat: raise HTTPException(404, "Bo'lim topilmadi")
    if not cat["active"]: raise HTTPException(403, "Bu bo'lim yaqin kunda ishga tushadi")
    now = time.time()
    cur = c.execute("INSERT INTO orders(user_id,cat,sub,addr,dest,lat,lon,pay,tip,note,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (u["id"], b.cat, b.sub, b.addr, b.dest, b.lat, b.lon, b.pay, b.tip, b.note, now, now))
    tell(c, u["id"], f"Buyurtmangiz yuborildi: {b.sub}. Ishchi qidirilmoqda."); c.commit()
    return {"id": cur.lastrowid, "status": 0}


@app.get("/orders/mine")
def my_orders(u=Depends(user), c=Depends(db)):
    return [dict(r) for r in c.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC", (u["id"],))]


def get_order(c, oid):
    o = c.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    if not o: raise HTTPException(404, "Buyurtma topilmadi")
    return dict(o)


@app.post("/orders/{oid}/cancel")
def cancel(oid: int, u=Depends(user), c=Depends(db)):
    o = get_order(c, oid)
    staff = u["role"] in OPS
    if o["user_id"] != u["id"] and not staff: raise HTTPException(403, "Bu buyurtma sizniki emas")
    if o["status"] >= (3 if staff else 2): raise HTTPException(409, "Buyurtmani endi bekor qilib bo'lmaydi")
    c.execute("UPDATE orders SET status=4, updated=? WHERE id=?", (time.time(), oid))
    tell(c, o["user_id"], f"Buyurtma bekor qilindi: {o['sub']}")
    if o["worker_id"]: tell(c, o["worker_id"], f"Buyurtma bekor qilindi: {o['sub']}")
    if staff and o["user_id"] != u["id"]: audit(c, u["id"], "order.cancel", str(oid))
    c.commit(); return {"ok": True}


class RateIn(BaseModel): stars: int = Field(ge=1, le=5); comment: str = Field("", max_length=300)


@app.post("/orders/{oid}/rate")
def rate(oid: int, b: RateIn, u=Depends(user), c=Depends(db)):
    o = get_order(c, oid)
    if o["user_id"] != u["id"]: raise HTTPException(403, "Bu buyurtma sizniki emas")
    if o["status"] != 3: raise HTTPException(409, "Faqat bajarilgan buyurtmani baholash mumkin")
    if o["rating"]: raise HTTPException(409, "Allaqachon baholangan")
    c.execute("UPDATE orders SET rating=?, rcomment=? WHERE id=?", (b.stars, b.comment, oid)); c.commit(); return {"ok": True}


# ---------- Ishchi ----------
class WorkerIn(BaseModel):
    online: bool
    modes: List[str] = Field(default_factory=list)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)


@app.put("/worker/state")
def worker_state(b: WorkerIn, u=Depends(need("worker")), c=Depends(db)):
    if any(m not in ("hay", "kur", "ust") for m in b.modes): raise HTTPException(422, "Rejim noto'g'ri")
    c.execute("INSERT INTO workers(user_id,modes,online,lat,lon,updated) VALUES(?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET modes=excluded.modes,online=excluded.online,lat=excluded.lat,lon=excluded.lon,updated=excluded.updated",
              (u["id"], json.dumps(b.modes), int(b.online), b.lat, b.lon, time.time())); c.commit(); return {"ok": True}


def km(a, b, c_, d):
    p = math.pi / 180
    x = math.sin((c_ - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c_ * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))


def wstate(c, uid):
    w = c.execute("SELECT * FROM workers WHERE user_id=?", (uid,)).fetchone()
    return (dict(w), json.loads(w["modes"])) if w else (None, [])


@app.get("/worker/orders/nearby")
def nearby(radius_km: float = Query(10, gt=0, le=100), u=Depends(need("worker")), c=Depends(db)):
    w, modes = wstate(c, u["id"])
    if not w or not w["online"]: raise HTTPException(403, "Buyurtma olish uchun onlayn bo'ling")
    rows = c.execute("SELECT o.*, c.mode FROM orders o JOIN categories c ON c.name=o.cat WHERE o.status=0 AND o.user_id<>?", (u["id"],)).fetchall()
    out = []
    for r in rows:
        if r["mode"] not in modes: continue
        d = km(w["lat"], w["lon"], r["lat"], r["lon"]) if None not in (w["lat"], w["lon"], r["lat"], r["lon"]) else None
        if d is not None and d > radius_km: continue
        out.append({**dict(r), "distance_km": None if d is None else round(d, 2)})
    return sorted(out, key=lambda x: (x["distance_km"] is None, x["distance_km"] or 0, -x["tip"]))


class AcceptIn(BaseModel): eta_minutes: Optional[int] = None


@app.post("/worker/orders/{oid}/accept")
def accept(oid: int, b: AcceptIn, u=Depends(need("worker")), c=Depends(db)):
    o = get_order(c, oid); w, modes = wstate(c, u["id"])
    mode = c.execute("SELECT mode FROM categories WHERE name=?", (o["cat"],)).fetchone()["mode"]
    if not w or not w["online"] or mode not in modes: raise HTTPException(403, "Onlayn bo'ling va mos rejimni yoqing")
    if o["user_id"] == u["id"]: raise HTTPException(403, "O'z buyurtmangizni qabul qila olmaysiz")
    eta = None
    if o["cat"] == "Taomlar":
        if b.eta_minutes not in ETAS: raise HTTPException(422, "Taom tayyor bo'lish vaqti 5 dan 60 gacha (5 daqiqa qadam bilan)")
        eta = time.time() + b.eta_minutes * 60
    cur = c.execute("UPDATE orders SET worker_id=?, status=1, eta=?, updated=? WHERE id=? AND status=0", (u["id"], eta, time.time(), oid))
    if cur.rowcount != 1: raise HTTPException(409, "Buyurtmani boshqa ishchi qabul qilib bo'ldi")
    tell(c, o["user_id"], "Buyurtma qabul qilindi" + (f". Taom taxminan {b.eta_minutes} daqiqada tayyor bo'ladi." if eta else "."))
    c.commit(); return {"ok": True}


def mine(c, oid, u):
    o = get_order(c, oid)
    if o["worker_id"] != u["id"]: raise HTTPException(403, "Bu buyurtma sizga biriktirilmagan")
    return o


class AdvanceIn(BaseModel): price: Optional[int] = Field(None, ge=0, le=1_000_000_000)


@app.post("/worker/orders/{oid}/advance")
def advance(oid: int, b: AdvanceIn, u=Depends(need("worker")), c=Depends(db)):
    o = mine(c, oid, u)
    if o["status"] not in (1, 2): raise HTTPException(409, "Holatni o'zgartirib bo'lmaydi")
    ns = o["status"] + 1
    c.execute("UPDATE orders SET status=?, price=COALESCE(?,price), updated=? WHERE id=?", (ns, b.price if ns == 3 else None, time.time(), oid))
    tell(c, o["user_id"], "Buyurtma holati: " + ("Yo'lda" if ns == 2 else "Bajarildi")); c.commit(); return {"status": ns}


@app.post("/worker/orders/{oid}/extend")
def extend(oid: int, u=Depends(need("worker")), c=Depends(db)):
    o = mine(c, oid, u)
    if not o["eta"] or o["status"] >= 3: raise HTTPException(409, "Vaqtni uzaytirib bo'lmaydi")
    c.execute("UPDATE orders SET eta=MAX(eta,?)+300 WHERE id=?", (time.time(), oid))
    tell(c, o["user_id"], "Oshxona tayyorlash vaqtini 5 daqiqaga uzaytirdi."); c.commit(); return {"ok": True}


@app.post("/worker/orders/{oid}/decline-late")
def decline_late(oid: int, u=Depends(need("worker")), c=Depends(db)):
    o = mine(c, oid, u)
    if not o["eta"] or o["status"] >= 3 or time.time() < o["eta"] + 600: raise HTTPException(409, "Jarimasiz rad etish uchun tayyorlash vaqtidan 10 daqiqa o'tishi kerak")
    c.execute("UPDATE orders SET status=4, updated=? WHERE id=?", (time.time(), oid))
    tell(c, o["user_id"], "Oshxona kechikkani uchun kuryer buyurtmadan jarimasiz voz kechdi.")
    audit(c, u["id"], "order.decline_late", str(oid)); c.commit(); return {"ok": True}


@app.post("/worker/orders/{oid}/rate-client")
def rate_client(oid: int, b: RateIn, u=Depends(need("worker")), c=Depends(db)):
    o = mine(c, oid, u)
    if o["status"] != 3 or o["client_rating"]: raise HTTPException(409, "Baholab bo'lmaydi")
    c.execute("UPDATE orders SET client_rating=? WHERE id=?", (b.stars, oid)); c.commit(); return {"ok": True}


# ---------- Xabarlar ----------
class MsgIn(BaseModel): text: str = Field(min_length=1, max_length=1000)


@app.post("/messages", status_code=201)
def send_msg(b: MsgIn, u=Depends(user), c=Depends(db)):
    tell(c, u["id"], b.text.strip(), sender="user"); c.commit(); return {"ok": True}


@app.get("/messages")
def my_msgs(u=Depends(user), c=Depends(db)):
    rows = [dict(r) for r in c.execute("SELECT * FROM messages WHERE user_id=? ORDER BY id", (u["id"],))]
    c.execute("UPDATE messages SET read=1 WHERE user_id=? AND sender<>'user'", (u["id"],)); c.commit(); return rows


@app.get("/operator/threads")
def threads(u=Depends(need(*OPS)), c=Depends(db)):
    return [dict(r) for r in c.execute("SELECT user_id, COUNT(*) n, MAX(created) last FROM messages WHERE sender='user' GROUP BY user_id ORDER BY last DESC LIMIT 100")]


class ReplyIn(BaseModel): user_id: int; text: str = Field(min_length=1, max_length=1000)


@app.post("/operator/reply")
def reply(b: ReplyIn, u=Depends(need(*OPS)), c=Depends(db)):
    if not c.execute("SELECT 1 FROM users WHERE id=?", (b.user_id,)).fetchone(): raise HTTPException(404, "Foydalanuvchi topilmadi")
    tell(c, b.user_id, b.text.strip(), sender="operator"); audit(c, u["id"], "operator.reply", str(b.user_id)); c.commit(); return {"ok": True}


class AssignIn(BaseModel): worker_id: int


@app.post("/operator/orders/{oid}/assign")
def assign(oid: int, b: AssignIn, u=Depends(need(*OPS)), c=Depends(db)):
    o = get_order(c, oid)
    w = c.execute("SELECT role FROM users WHERE id=?", (b.worker_id,)).fetchone()
    if not w or w["role"] != "worker": raise HTTPException(422, "Bu foydalanuvchi ishchi emas")
    if o["cat"] == "Taomlar": raise HTTPException(409, "Taom buyurtmasini oshxona o'zi qabul qilib, vaqt qo'yishi kerak")
    cur = c.execute("UPDATE orders SET worker_id=?, status=1, updated=? WHERE id=? AND status=0", (b.worker_id, time.time(), oid))
    if cur.rowcount != 1: raise HTTPException(409, "Buyurtma allaqachon qabul qilingan")
    tell(c, o["user_id"], "Buyurtmangizga ishchi tayinlandi."); tell(c, b.worker_id, f"Sizga buyurtma tayinlandi: {o['sub']}")
    audit(c, u["id"], "order.assign", f"{oid}->{b.worker_id}"); c.commit(); return {"ok": True}


# ---------- Yaqin atrofdagi ishchilar va kuzatuv ----------
@app.get("/nearby/workers")
def nearby_workers(lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180), mode: str = Query("hay", pattern="^(hay|kur|ust)$"),
                   radius_km: float = Query(5, gt=0, le=50), u=Depends(user), c=Depends(db)):
    out = []  # maxfiylik uchun koordinatalar ~1 km aniqlikda yaxlitlanadi
    for w in c.execute("SELECT * FROM workers WHERE online=1 AND lat IS NOT NULL AND updated>?", (time.time() - 300,)):
        d = km(lat, lon, w["lat"], w["lon"])
        if mode in json.loads(w["modes"]) and d <= radius_km: out.append({"lat": round(w["lat"], 2), "lon": round(w["lon"], 2), "distance_km": round(d, 1)})
    return sorted(out, key=lambda x: x["distance_km"])[:20]


@app.get("/orders/{oid}/track")
def track(oid: int, u=Depends(user), c=Depends(db)):
    o = get_order(c, oid)
    if o["user_id"] != u["id"] and u["role"] not in OPS: raise HTTPException(403, "Bu buyurtma sizniki emas")
    if o["status"] not in (1, 2) or not o["worker_id"]: raise HTTPException(409, "Kuzatuv faqat qabul qilingan buyurtma uchun")
    w = c.execute("SELECT lat,lon,updated FROM workers WHERE user_id=?", (o["worker_id"],)).fetchone()
    return dict(w) if w else {}


# ---------- Admin / hisobotlar ----------
class CatIn(BaseModel): active: bool


@app.put("/admin/categories/{name}")
def toggle(name: str, b: CatIn, u=Depends(need(*ADM)), c=Depends(db)):
    if c.execute("UPDATE categories SET active=? WHERE name=?", (int(b.active), name)).rowcount != 1: raise HTTPException(404, "Bo'lim topilmadi")
    audit(c, u["id"], "category.toggle", f"{name}={b.active}"); c.commit(); return {"ok": True}


class RoleIn(BaseModel): role: str


@app.put("/admin/users/{uid}/role")
def set_role(uid: int, b: RoleIn, u=Depends(need("superadmin")), c=Depends(db)):
    if b.role not in ROLES: raise HTTPException(422, "Rol noto'g'ri")
    if uid == u["id"]: raise HTTPException(409, "O'z rolingizni o'zgartira olmaysiz")
    if c.execute("UPDATE users SET role=? WHERE id=?", (b.role, uid)).rowcount != 1: raise HTTPException(404, "Foydalanuvchi topilmadi")
    audit(c, u["id"], "user.role", f"{uid}={b.role}"); c.commit(); return {"ok": True}


@app.get("/admin/users")
def users(u=Depends(need(*ADM)), c=Depends(db)): return [dict(r) for r in c.execute("SELECT id,phone,name,role,created FROM users ORDER BY id DESC LIMIT 500")]


@app.get("/admin/orders")
def all_orders(status: Optional[int] = None, u=Depends(need(*(OPS | MGR))), c=Depends(db)):
    q, a = "SELECT * FROM orders", ()
    if status is not None: q, a = q + " WHERE status=?", (status,)
    return [dict(r) for r in c.execute(q + " ORDER BY id DESC LIMIT 500", a)]


@app.get("/admin/audit")
def audit_log(u=Depends(need(*ADM)), c=Depends(db)): return [dict(r) for r in c.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 200")]


@app.get("/reports")
def reports(period: str = Query("day", pattern="^(day|week|month|quarter|year)$"), u=Depends(need(*MGR)), c=Depends(db)):
    days = {"day": 1, "week": 7, "month": 30, "quarter": 90, "year": 365}[period]
    since = time.time() - days * 86400
    rows = [dict(r) for r in c.execute("SELECT * FROM orders WHERE created>=?", (since,))]
    done = [r for r in rows if r["status"] == 3]
    rated = [r["rating"] for r in rows if r["rating"]]
    gross = sum(r["price"] or 0 for r in done)
    by = {}
    for r in rows: by.setdefault(r["cat"], {"total": 0, "done": 0}); by[r["cat"]]["total"] += 1; by[r["cat"]]["done"] += r["status"] == 3
    return {"period": period, "total": len(rows), "done": len(done), "cancelled": sum(r["status"] == 4 for r in rows),
            "completion_rate": round(len(done) / len(rows), 3) if rows else 0, "avg_rating": round(sum(rated) / len(rated), 2) if rated else None,
            "gross": gross, "commission_est": round(gross * COMMISSION), "by_category": by,
            "note": "Soliq hisoboti uchun buxgalter tasdiqlagan qoidalar va soliq organi integratsiyasi kerak."}
