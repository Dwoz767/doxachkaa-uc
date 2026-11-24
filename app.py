import sqlite3
import random
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'doxachkaa_super_secret_key_change_me'

# НАСТРОЙКИ АДМИНА (Твой секретный ID и пароль)
ADMIN_ID = "1"          # Твой ID (от 1 до 100000000)
ADMIN_PASS = "admin888" # Пароль для входа в админку

# СЕКТОРА И ШАНСЫ (Чем больше weight, тем чаще выпадает)
SECTORS = [
    {"label": "0 UC",    "uc": 0,    "weight": 55, "color": "#1a1a2e"},
    {"label": "60 UC",   "uc": 60,   "weight": 28, "color": "#16213e"},
    {"label": "120 UC",  "uc": 120,  "weight": 11, "color": "#0f3460"},
    {"label": "325 UC",  "uc": 325,  "weight": 3,  "color": "#533483"},
    {"label": "385 UC",  "uc": 385,  "weight": 2,  "color": "#e94560"},
    {"label": "1000 UC", "uc": 1000, "weight": 1,  "color": "#ff2a85"}
]

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        pin TEXT NOT NULL,
        rub INTEGER DEFAULT 0,
        uc INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT,
        user_id INTEGER,
        action TEXT
    )''')
    conn.commit()
    conn.close()

def add_log(user_id, action):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    now = datetime.now().strftime("%d.%m %H:%M:%S")
    c.execute("INSERT INTO logs (time, user_id, action) VALUES (?, ?, ?)", (now, user_id, action))
    conn.commit()
    conn.close()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Doxachkaa UC</title>
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
        body {
            margin: 0; padding: 15px; min-height: 100vh;
            background: radial-gradient(circle at top, #1b0026, #09000d 80%);
            color: #fff; display: flex; justify-content: center; align-items: center;
        }
        .main-frame {
            width: 100%; max-width: 440px;
            background: rgba(15, 10, 25, 0.9);
            border: 3px solid #ff1e42;
            box-shadow: 0 0 25px #ff1e42, inset 0 0 15px rgba(255, 30, 66, 0.5);
            border-radius: 20px; padding: 20px; text-align: center;
        }
        h1 {
            margin: 0 0 15px; font-size: 28px; text-transform: uppercase;
            color: #fff; text-shadow: 0 0 10px #ff1e42, 0 0 20px #ff1e42;
        }
        .stats {
            display: flex; justify-content: space-between; background: #140c24;
            padding: 10px 15px; border-radius: 12px; border: 1px solid #ff1e42;
            margin-bottom: 20px; font-weight: bold;
        }
        .wheel-box {
            position: relative; width: 300px; height: 300px; margin: 0 auto 20px;
        }
        canvas {
            width: 100%; height: 100%; border-radius: 50%;
            box-shadow: 0 0 20px #00f3ff, 0 0 40px #ff007f;
            border: 4px solid #00f3ff;
            transition: transform 4s cubic-bezier(0.17, 0.67, 0.12, 0.99);
        }
        .pointer {
            position: absolute; top: -12px; left: 50%; transform: translateX(-50%);
            width: 0; height: 0; border-left: 15px solid transparent;
            border-right: 15px solid transparent; border-top: 25px solid #ff1e42;
            filter: drop-shadow(0 0 8px #ff1e42); z-index: 10;
        }
        .btn {
            width: 100%; padding: 14px; font-size: 18px; font-weight: bold;
            color: #fff; background: linear-gradient(45deg, #ff1e42, #ff007f);
            border: none; border-radius: 12px; cursor: pointer;
            box-shadow: 0 0 15px #ff1e42; transition: 0.2s;
        }
        .btn:disabled { background: #444; box-shadow: none; cursor: not-allowed; }
        input {
            width: 100%; padding: 12px; margin: 8px 0; border-radius: 10px;
            border: 1px solid #ff1e42; background: #1a0f2e; color: #fff; font-size: 16px;
        }
        .msg { margin-top: 15px; font-size: 16px; min-height: 24px; color: #00f3ff; font-weight: bold; }
        .admin-box {
            margin-top: 25px; padding-top: 15px; border-top: 2px dashed #ff1e42; text-align: left;
        }
        .admin-badge {
            background: #ff1e42; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;
        }
        .logs {
            max-height: 150px; overflow-y: auto; background: #090512; padding: 10px;
            border-radius: 8px; font-size: 12px; margin-top: 10px; border: 1px solid #333;
        }
        .log-item { border-bottom: 1px solid #222; padding: 4px 0; }
        .row { display: flex; gap: 8px; }
    </style>
</head>
<body>
<div class="main-frame">
    <h1>Doxachkaa UC</h1>

    {% if not user %}
        <p>Вход / Регистрация по личному ID (1 — 100.000.000)</p>
        <form method="POST" action="/login">
            <input type="number" name="user_id" min="1" max="100000000" placeholder="Ваш игровой ID" required>
            <input type="password" name="pin" placeholder="Придумайте или введите ПИН-код" required>
            <button class="btn" type="submit">Войти в игру</button>
        </form>
        {% if error %}<div class="msg" style="color:#ff1e42;">{{ error }}</div>{% endif %}
    {% else %}
        <div class="stats">
            <span>ID: {{ user[0] }}</span>
            <span>Баланс: <b id="rub">{{ user[2] }}</b> ₽</span>
            <span>UC: <b id="uc">{{ user[3] }}</b></span>
        </div>

        {% if user[4] == 1 %}
            <div class="msg" style="color:#ff1e42; font-size:20px;">ВАШ АККАУНТ ЗАБАНЕН ОСНОВАТЕЛЕМ</div>
        {% else %}
            <div class="wheel-box">
                <div class="pointer"></div>
                <canvas id="wheel" width="300" height="300"></canvas>
            </div>
            <button id="spinBtn" class="btn" onclick="spin()">КРУТИТЬ ЗА 100 ₽</button>
            <div class="msg" id="resultMsg"></div>
        {% endif %}

        <div style="margin-top:15px;">
            <a href="/logout" style="color:#888; font-size:13px;">Выйти из аккаунта</a>
        </div>

        <!-- СКРЫТАЯ АДМИН-ПАНЕЛЬ 8 УРОВНЯ (Видна ТОЛЬКО Основателю) -->
        {% if is_admin %}
        <div class="admin-box">
            <div><span class="admin-badge">УРОВЕНЬ 8: ОСНОВАТЕЛЬ</span></div>
            <form method="POST" action="/admin/action" style="margin-top:10px;">
                <input type="number" name="target_id" placeholder="ID игрока" required>
                <input type="number" name="amount" placeholder="Сумма ₽ (для пополнения)">
                <div class="row">
                    <button class="btn" name="act" value="add_rub" style="font-size:13px; padding:10px;">+ Пополнить ₽</button>
                    <button class="btn" name="act" value="ban" style="font-size:13px; padding:10px; background:#b30000;">Бан ID</button>
                    <button class="btn" name="act" value="unban" style="font-size:13px; padding:10px; background:#00802b;">Снять бан</button>
                </div>
            </form>
            <div style="margin-top:12px; font-weight:bold; font-size:14px;">Лог действий игроков:</div>
            <div class="logs">
                {% for log in logs %}
                    <div class="log-item">[{{ log[1] }}] <b>ID {{ log[2] }}</b>: {{ log[3] }}</div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    {% endif %}
</div>

<script>
const sectors = {{ sectors | tojson }};
const canvas = document.getElementById('wheel');
let currentRotation = 0;

if (canvas) {
    const ctx = canvas.getContext('2d');
    const arc = (2 * Math.PI) / sectors.length;
    sectors.forEach((sec, i) => {
        const angle = i * arc;
        ctx.beginPath();
        ctx.fillStyle = sec.color;
        ctx.moveTo(150, 150);
        ctx.arc(150, 150, 150, angle, angle + arc);
        ctx.fill();
        ctx.strokeStyle = "#00f3ff";
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.save();
        ctx.translate(150, 150);
        ctx.rotate(angle + arc / 2);
        ctx.fillStyle = "#fff";
        ctx.font = "bold 16px sans-serif";
        ctx.shadowColor = "#ff007f";
        ctx.shadowBlur = 6;
        ctx.fillText(sec.label, 55, 6);
        ctx.restore();
    });
}

function spin() {
    const btn = document.getElementById('spinBtn');
    const msg = document.getElementById('resultMsg');
    btn.disabled = true;
    msg.innerText = "Крутим барабан...";

    fetch('/spin', { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            msg.style.color = "#ff1e42";
            msg.innerText = data.error;
            btn.disabled = false;
            return;
        }
        const sliceDeg = 360 / sectors.length;
        const targetDeg = 360 - (data.index * sliceDeg) - (sliceDeg / 2) - 90;
        currentRotation += 1800 + (targetDeg - (currentRotation % 360) + 360) % 360;
        canvas.style.transform = `rotate(${currentRotation}deg)`;

        setTimeout(() => {
            document.getElementById('rub').innerText = data.rub;
            document.getElementById('uc').innerText = data.uc;
            msg.style.color = "#00f3ff";
            msg.innerText = `Выпало: ${data.label}!`;
            btn.disabled = false;
        }, 4100);
    });
}
</script>
</body>
</html>
'''

@app.route('/')
def index():
    user_id = session.get('user_id')
    user = None
    is_admin = False
    logs = []
    if user_id:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=?", (user_id,))
        user = c.fetchone()
        if str(user_id) == ADMIN_ID and session.get('is_admin'):
            is_admin = True

