from flask import Flask, request, jsonify, render_template, abort
import sqlite3, secrets, datetime, ipaddress

app = Flask(__name__)
DB = "osint.db"

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.execute("""CREATE TABLE IF NOT EXISTS links(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS visits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT NOT NULL,
        ip TEXT,
        user_agent TEXT,
        latitude REAL,
        longitude REAL,
        accuracy REAL,
        geo_consent INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )""")
    con.commit()
    con.close()

def clean_ip(value):
    value = (value or "").split(",")[0].strip()
    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        return None

@app.route("/")
def dashboard():
    con = db()
    links = con.execute("SELECT * FROM links ORDER BY id DESC").fetchall()
    visits = con.execute("""SELECT visits.*, links.title
        FROM visits LEFT JOIN links ON visits.token=links.token
        ORDER BY visits.id DESC LIMIT 500""").fetchall()
    con.close()
    return render_template("dashboard.html", links=links, visits=visits)

@app.post("/api/link")
def create_link():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title") or "Consent landing page").strip()[:120]
    token = secrets.token_urlsafe(12)
    con = db()
    con.execute("INSERT INTO links(token,title,created_at) VALUES(?,?,?)",
                (token, title, datetime.datetime.now(datetime.timezone.utc).isoformat()))
    con.commit()
    con.close()
    return jsonify({"token": token, "url": f"/c/{token}"})

@app.route("/c/<token>")
def consent_page(token):
    con = db()
    link = con.execute("SELECT * FROM links WHERE token=?", (token,)).fetchone()
    con.close()
    if not link:
        abort(404)
    return render_template("consent.html", token=token, title=link["title"])

@app.post("/api/visit/<token>")
def record_visit(token):
    con = db()
    if not con.execute("SELECT 1 FROM links WHERE token=?", (token,)).fetchone():
        con.close()
        abort(404)

    data = request.get_json(silent=True) or {}
    ip = clean_ip(request.headers.get("X-Forwarded-For") or request.remote_addr)
    consent = bool(data.get("geo_consent"))
    lat = data.get("latitude") if consent else None
    lon = data.get("longitude") if consent else None
    accuracy = data.get("accuracy") if consent else None

    con.execute("""INSERT INTO visits
        (token,ip,user_agent,latitude,longitude,accuracy,geo_consent,created_at)
        VALUES(?,?,?,?,?,?,?,?)""",
        (token, ip, request.headers.get("User-Agent","")[:500],
         lat, lon, accuracy, 1 if consent else 0,
         datetime.datetime.now(datetime.timezone.utc).isoformat()))
    con.commit()
    con.close()
    return jsonify({"ok": True})

@app.get("/api/visits")
def get_visits():
    con = db()
    rows = [dict(x) for x in con.execute(
        "SELECT * FROM visits ORDER BY id DESC LIMIT 500").fetchall()]
    con.close()
    return jsonify(rows)

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)
