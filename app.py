import sqlite3, random
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "doxachkaa_secret_key_888"

ADMIN_ID = "1"
ADMIN_PASS = "admin888"

SECTORS = [
    {"label": "0 UC",    "uc": 0,    "weight": 55, "color": "#1a1a2e"},
    {"label": "60 UC",   "uc": 60,   "weight": 28, "color": "#16213e"},
    {"label": "120 UC",  "uc": 120,  "weight": 11, "color": "#0f3460"},
    {"label": "325 UC",  "uc": 325,  "weight": 3,  "color": "#533483"},
    {"label": "385 UC",  "uc": 385,  "weight": 2,  "color": "#e94560"},
    {"label": "1000 UC", "uc": 1000, "weight": 1,  "color": "#ff2a85"}
]

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, pin TEXT, rub INTEGER DEFAULT 0, uc INTEGER DEFAULT 0, banned INTEGER DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, user_id INTEGER, action TEXT)")
    conn.commit()
    conn.close()

init_db()

def add_log(uid, act):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO logs (time, user_id, action) VALUES (?, ?, ?)", (datetime.now().strftime("%d.%m %H:%M"), uid, act))
    conn.commit()
    conn.close()

HTML = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Doxachkaa UC</title><style>
*{box-sizing:border-box;font-family:sans-serif}
body{margin:0;padding:15px;min-height:100vh;background:radial-gradient(circle at top,#1b0026,#09000d 80%);color:#fff;display:flex;justify-content:center;align-items:center}
.box{width:100%;max-width:440px;background:rgba(15,10,25,.95);border:3px solid #ff1e42;box-shadow:0 0 25px #ff1e42,inset 0 0 15px rgba(255,30,66,.5);border-radius:20px;padding:20px;text-align:center}
h1{margin:0 0 15px;font-size:28px;text-transform:uppercase;text-shadow:0 0 10px #ff1e42,0 0 20px #ff1e42}
.stats{display:flex;justify-content:space-between;background:#140c24;padding:10px 15px;border-radius:12px;border:1px solid #ff1e42;margin-bottom:20px;font-weight:bold}
.wbox{position:relative;width:290px;height:290px;margin:0 auto 20px}
canvas{width:100%;height:100%;border-radius:50%;box-shadow:0 0 20px #00f3ff,0 0 40px #ff007f;border:4px solid #00f3ff;transition:transform 4s cubic-bezier(.17,.67,.12,.99)}
.ptr{position:absolute;top:-12px;left:50%;transform:translateX(-50%);border-left:15px solid transparent;border-right:15px solid transparent;border-top:25px solid #ff1e42;filter:drop-shadow(0 0 8px #ff1e42);z-index:10}
.btn{width:100%;padding:14px;font-size:17px;font-weight:bold;color:#fff;background:linear-gradient(45deg,#ff1e42,#ff007f);border:none;border-radius:12px;cursor:pointer;box-shadow:0 0 15px #ff1e42}
.btn:disabled{background:#444;box-shadow:none}
input{width:100%;padding:12px;margin:8px 0;border-radius:10px;border:1px solid #ff1e42;background:#1a0f2e;color:#fff;font-size:16px}
.msg{margin-top:15px;font-size:16px;min-height:24px;color:#00f3ff;font-weight:bold}
.adm{margin-top:25px;padding-top:15px;border-top:2px dashed #ff1e42;text-align:left}
.badge{background:#ff1e42;padding:4px 10px;border-radius:6px;font-size:12px;font-weight:bold}
.logs{max-height:150px;overflow-y:auto;background:#090512;padding:10px;border-radius:8px;font-size:12px;margin-top:10px;border:1px solid #333}
.row{display:flex;gap:6px}
</style></head><body><div class="box"><h1>Doxachkaa UC</h1>
{% if not user %}
<p>Вход / Регистрация по ID (1 — 100.000.000)</p>
<form method="POST" action="/login">
<input type="number" name="user_id" min="1" max="100000000" placeholder="Ваш игровой ID" required>
<input type="password" name="pin" placeholder="ПИН-код" required>
<button class="btn" type="submit">Войти в игру</button></form>
{% if error %}<div class="msg" style="color:#ff1e42">{{ error }}</div>{% endif %}
{% else %}
<div class="stats"><span>ID: {{ user[0] }}</span><span>Баланс: <b id="rub">{{ user[2] }}</b> ₽</span><span>UC: <b id="uc">{{ user[3] }}</b></span></div>
{% if user[4] == 1 %}<div class="msg" style="color:#ff1e42;font-size:20px">ВАШ АККАУНТ ЗАБАНЕН</div>
{% else %}
<div class="wbox"><div class="ptr"></div><canvas id="wheel" width="300" height="300"></canvas></div>
<button id="spinBtn" class="btn" onclick="spin()">КРУТИТЬ ЗА 100 ₽</button>
<div class="msg" id="resultMsg"></div>
{% endif %}
<div style="margin-top:15px"><a href="/logout" style="color:#888;font-size:13px">Выйти</a></div>
{% if is_admin %}
<div class="adm"><span class="badge">УРОВЕНЬ 8: ОСНОВАТЕЛЬ</span>
<form method="POST" action="/admin" style="margin-top:10px">
<input type="number" name="tid" placeholder="ID игрока" required>
<input type="number" name="amt" placeholder="Сумма ₽">
<div class="row">
<button class="btn" name="act" value="add" style="font-size:12px;padding:10px">+ Пополнить ₽</button>
<button class="btn" name="act" value="ban" style="font-size:12px;padding:10px;background:#b30000">Бан ID</button>
<button class="btn" name="act" value="unban" style="font-size:12px;padding:10px;background:#00802b">Снять бан</button>
</div></form>
<div style="margin-top:12px;font-weight:bold;font-size:14px">Лог действий:</div>
<div class="logs">{% for l in logs %}<div style="border-bottom:1px solid #222;padding:3px 0">[{{ l[1] }}] <b>ID {{ l[2] }}</b>: {{ l[3] }}</div>{% endfor %}</div>
</div>{% endif %}{% endif %}</div>
<script>
const sectors={{ sectors|tojson }};const c=document.getElementById("wheel");let rot=0;
if(c){const ctx=c.getContext("2d");const arc=(2*Math.PI)/sectors.length;
sectors.forEach((s,i)=>{const a=i*arc;ctx.beginPath();ctx.fillStyle=s.color;ctx.moveTo(150,150);ctx.arc(150,150,150,a,a+arc);ctx.fill();ctx.strokeStyle="#00f3ff";ctx.lineWidth=2;ctx.stroke();ctx.save();ctx.translate(150,150);ctx.rotate(a+arc/2);ctx.fillStyle="#fff";ctx.font="bold 16px sans-serif";ctx.fillText(s.label,55,6);ctx.restore()})}
function spin(){const b=document.getElementById("spinBtn"),m=document.getElementById("resultMsg");b.disabled=true;m.innerText="Крутим...";
fetch("/spin",{method:"POST"}).then(r=>r.json()).then(d=>{if(d.error){m.style.color="#ff1e42";m.innerText=d.error;b.disabled=false;return}
const sd=360/sectors.length,td=360-(d.index*sd)-(sd/2)-90;rot+=1800+(td-(rot%360)+360)%360;c.style.transform=`rotate(${rot}deg)`;
setTimeout(()=>{document.getElementById("rub").innerText=d.rub;document.getElementById("uc").innerText=d.uc;m.style.color="#00f3ff";m.innerText=`Выпало: ${d.label}!`;b.disabled=false},4100)})}
</script></body></html>"""

@app.route("/")
def index():
    init_db()
    uid = session.get("user_id")
    user, is_admin, logs = None, False, []
    if uid:
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=?", (uid,))
        user = c.fetchone()
        if str(uid) == ADMIN_ID and session.get("is_admin"):
            is_admin = True
            c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 30")
            logs = c.fetchall()
        conn.close()
    return render_template_string(HTML, user=user, sectors=SECTORS, is_admin=is_admin, logs=logs, error=request.args.get("error"))

@app.route("/login", methods=["POST"])
def login():
    init_db()
    uid = int(request.form["user_id"])
    pin = request.form["pin"]
    if uid < 1 or uid > 100000000:
        return redirect(url_for("index", error="ID от 1 до 100.000.000"))
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (uid,))
    user = c.fetchone()
    if user:
        if user[1] != pin:
            conn.close()
            return redirect(url_for("index", error="Неверный ПИН-код!"))
    else:
        c.execute("INSERT INTO users (id, pin, rub, uc, banned) VALUES (?, ?, 0, 0, 0)", (uid, pin))
        conn.commit()
        add_log(uid, "Регистрация нового ID")
    conn.close()
    session["user_id"] = uid
    session["is_admin"] = (str(uid) == ADMIN_ID and pin == ADMIN_PASS)
    return redirect(url_for("index"))

@app.route("/spin", methods=["POST"])
def spin():
    uid = session.get("user_id")
    if not uid: return jsonify({"error": "Войдите в аккаунт!"})
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT rub, uc, banned FROM users WHERE id=?", (uid,))
    row = c.fetchone()
    if row[2] == 1:
        conn.close()
        return jsonify({"error": "Аккаунт заблокирован!"})
    if row[0] < 100:
        conn.close()
        return jsonify({"error": "Недостаточно средств! Нужно 100 ₽"})
    idx = random.choices(range(len(SECTORS)), weights=[s["weight"] for s in SECTORS], k=1)[0]
    prize = SECTORS[idx]
    nrub, nuc = row[0] - 100, row[1] + prize["uc"]
    c.execute("UPDATE users SET rub=?, uc=? WHERE id=?", (nrub, nuc, uid))
    conn.commit()
    conn.close()
    add_log(uid, f"Прокрут (-100₽) -> {prize['label']}")
    return jsonify({"index": idx, "label": prize["label"], "rub": nrub, "uc": nuc})

@app.route("/admin", methods=["POST"])
def admin():
    if not session.get("is_admin"): return redirect(url_for("index"))
    tid, act = int(request.form["tid"]), request.form["act"]
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    if act == "add":
        amt = int(request.form.get("amt") or 0)
        c.execute("UPDATE users SET rub = rub + ? WHERE id=?", (amt, tid))
        add_log(ADMIN_ID, f"Пополнил ID {tid} на {amt} ₽")
    elif act == "ban":
        c.execute("UPDATE users SET banned = 1 WHERE id=?", (tid,))
        add_log(ADMIN_ID, f"Забанил ID {tid}")
    elif act == "unban":
        c.execute("UPDATE users SET banned = 0 WHERE id=?", (tid,))
        add_log(ADMIN_ID, f"Разбанил ID {tid}")
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
