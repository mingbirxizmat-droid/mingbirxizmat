import os, time, pytest
os.environ.update(MX_DEV="1", MX_DB="/tmp/mx_test.db", MX_SUPERADMIN_PHONE="+998900000001")
if os.path.exists("/tmp/mx_test.db"): os.remove("/tmp/mx_test.db")
from fastapi.testclient import TestClient
from app.main import app
cl = TestClient(app)


def login(phone):
    r = cl.post("/auth/request-otp", json={"phone": phone}); assert r.status_code == 200
    r = cl.post("/auth/verify", json={"phone": phone, "code": r.json()["dev_code"]}); assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["token"]}, r.json()["user"]["id"]


SA, SAID = login("+998900000001")
def mk(phone, role):
    h, i = login(phone)
    assert cl.put(f"/admin/users/{i}/role", json={"role": role}, headers=SA).status_code == 200
    return h, i
U, UID = login("+998901111111")
W1, W1ID = mk("+998902222221", "worker"); W2, W2ID = mk("+998902222222", "worker")
OP, _ = mk("+998903333333", "operator"); MG, _ = mk("+998904444444", "manager"); AD, _ = mk("+998905555555", "admin")
for w in (W1, W2): assert cl.put("/worker/state", json={"online": True, "modes": ["hay", "kur", "ust"], "lat": 41.31, "lon": 69.28}, headers=w).status_code == 200


def order(cat="Ustalar", **kw):
    return cl.post("/orders", json={"cat": cat, "sub": "Santexnik", "addr": "Chilonzor 5", "lat": 41.32, "lon": 69.27, **kw}, headers=U)


def test_auth_and_validation():
    assert cl.get("/orders/mine").status_code == 401
    assert cl.get("/orders/mine", headers={"Authorization": "Bearer x"}).status_code == 401
    assert cl.post("/auth/request-otp", json={"phone": "123"}).status_code == 422
    p = "+998907777777"; code = cl.post("/auth/request-otp", json={"phone": p}).json()["dev_code"]
    bad = "000000" if code != "000000" else "111111"
    for _ in range(5): assert cl.post("/auth/verify", json={"phone": p, "code": bad}).status_code == 400
    assert cl.post("/auth/verify", json={"phone": p, "code": code}).status_code == 429  # bloklandi


def test_otp_rate_limit():
    p = "+998908888888"
    for _ in range(3): assert cl.post("/auth/request-otp", json={"phone": p}).status_code == 200
    assert cl.post("/auth/request-otp", json={"phone": p}).status_code == 429


def test_rbac():
    assert cl.get("/admin/users", headers=U).status_code == 403
    assert cl.get("/reports", headers=U).status_code == 403
    assert cl.get("/reports?period=week", headers=MG).status_code == 200
    assert cl.get("/admin/audit", headers=OP).status_code == 403
    assert cl.get("/worker/orders/nearby", headers=U).status_code == 403
    assert cl.put(f"/admin/users/{UID}/role", json={"role": "admin"}, headers=AD).status_code == 403  # faqat super admin
    assert cl.put(f"/admin/users/{SAID}/role", json={"role": "user"}, headers=SA).status_code == 409  # o'zini tushira olmaydi


def test_locked_category_and_toggle():
    assert order("Bank").status_code == 403
    assert cl.put("/admin/categories/Bank", json={"active": True}, headers=AD).status_code == 200
    assert order("Bank").status_code == 201
    assert cl.put("/admin/categories/Bank", json={"active": False}, headers=AD).status_code == 200


def test_order_flow_race_rating():
    oid = order().json()["id"]
    assert oid in [o["id"] for o in cl.get("/worker/orders/nearby", headers=W1).json()]
    a, b = cl.post(f"/worker/orders/{oid}/accept", json={}, headers=W1), cl.post(f"/worker/orders/{oid}/accept", json={}, headers=W2)
    assert sorted([a.status_code, b.status_code]) == [200, 409]  # faqat bittasi olsin
    w = W1 if a.status_code == 200 else W2; other = W2 if w is W1 else W1
    assert cl.post(f"/worker/orders/{oid}/advance", json={}, headers=other).status_code == 403
    assert cl.post(f"/orders/{oid}/rate", json={"stars": 5}, headers=U).status_code == 409  # hali bajarilmagan
    assert cl.post(f"/worker/orders/{oid}/advance", json={}, headers=w).json()["status"] == 2
    assert cl.post(f"/worker/orders/{oid}/advance", json={"price": 100000}, headers=w).json()["status"] == 3
    assert cl.post(f"/orders/{oid}/rate", json={"stars": 4, "comment": "yaxshi"}, headers=U).status_code == 200
    assert cl.post(f"/orders/{oid}/rate", json={"stars": 5}, headers=U).status_code == 409
    assert cl.post(f"/orders/{oid}/rate", json={"stars": 6}, headers=U).status_code == 422
    assert cl.post(f"/worker/orders/{oid}/rate-client", json={"stars": 5}, headers=w).status_code == 200
    r = cl.get("/reports?period=day", headers=MG).json()
    assert r["done"] >= 1 and r["gross"] >= 100000 and r["avg_rating"]


def test_idor_and_cancel():
    oid = order().json()["id"]
    other, _ = login("+998909999999")
    assert cl.post(f"/orders/{oid}/cancel", headers=other).status_code == 403
    assert cl.post(f"/orders/{oid}/cancel", headers=U).status_code == 200
    assert cl.post(f"/orders/{oid}/cancel", headers=U).status_code == 409
    assert cl.post(f"/worker/orders/{oid}/accept", json={}, headers=W1).status_code == 409  # bekor qilingan


def test_cafe_eta_flow():
    oid = order("Taomlar").json()["id"]
    assert cl.post(f"/worker/orders/{oid}/accept", json={}, headers=W1).status_code == 422
    assert cl.post(f"/worker/orders/{oid}/accept", json={"eta_minutes": 7}, headers=W1).status_code == 422
    assert cl.post(f"/worker/orders/{oid}/accept", json={"eta_minutes": 20}, headers=W1).status_code == 200
    assert cl.post(f"/worker/orders/{oid}/extend", headers=W1).status_code == 200
    assert cl.post(f"/worker/orders/{oid}/decline-late", headers=W1).status_code == 409  # hali 10 daqiqa o'tmagan
    msgs = cl.get("/messages", headers=U).json()
    assert any("tayyor" in m["text"] for m in msgs)


def test_own_order_and_offline_worker():
    oid = order().json()["id"]
    assert cl.put("/worker/state", json={"online": False, "modes": []}, headers=W2).status_code == 200
    assert cl.get("/worker/orders/nearby", headers=W2).status_code == 403
    assert cl.post(f"/worker/orders/{oid}/accept", json={}, headers=W2).status_code == 403
    cl.put("/worker/state", json={"online": True, "modes": ["hay"], "lat": 41.3, "lon": 69.2}, headers=W2)
    assert all(o["cat"] == "Taksi" for o in cl.get("/worker/orders/nearby", headers=W2).json())  # faqat o'z rejimi


def test_operator_chat_assign_audit():
    assert cl.post("/messages", json={"text": "Yordam kerak"}, headers=U).status_code == 201
    assert any(t["user_id"] == UID for t in cl.get("/operator/threads", headers=OP).json())
    assert cl.post("/operator/reply", json={"user_id": UID, "text": "Salom!"}, headers=OP).status_code == 200
    assert any(m["sender"] == "operator" for m in cl.get("/messages", headers=U).json())
    oid = order().json()["id"]
    assert cl.post(f"/operator/orders/{oid}/assign", json={"worker_id": UID}, headers=OP).status_code == 422
    assert cl.post(f"/operator/orders/{oid}/assign", json={"worker_id": W1ID}, headers=OP).status_code == 200
    assert any(a["action"] == "order.assign" for a in cl.get("/admin/audit", headers=AD).json())


def test_sql_injection_and_headers():
    r = cl.post("/orders", json={"cat": "Ustalar' OR '1'='1", "sub": "x", "addr": "y"}, headers=U); assert r.status_code == 404
    assert cl.get("/health").headers["x-content-type-options"] == "nosniff"


def test_nearby_workers_and_tracking():
    r = cl.get("/nearby/workers?lat=41.31&lon=69.28&mode=kur", headers=U)
    assert r.status_code == 200 and r.json() and all(set(x) == {"lat", "lon", "distance_km"} for x in r.json())
    assert cl.get("/nearby/workers?lat=95&lon=69&mode=kur", headers=U).status_code == 422
    oid = order().json()["id"]
    assert cl.get(f"/orders/{oid}/track", headers=U).status_code == 409  # hali ishchi yo'q
    assert cl.post(f"/worker/orders/{oid}/accept", json={}, headers=W1).status_code in (200, 409)
    other, _ = login("+998906060606")
    assert cl.get(f"/orders/{oid}/track", headers=other).status_code == 403
