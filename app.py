from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import math
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("database.db")

def init_db():
    db = get_db()

    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT,
        salary_per_day INTEGER
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        status TEXT
    )''')

    # default user
    db.execute("INSERT OR IGNORE INTO users VALUES (1,'Employee','emp@mail.com','123',500)")

    db.commit()

init_db()

# ---------------- DISTANCE FUNCTION ----------------
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c * 1000  # meters


# ---------------- LOGIN ----------------
@app.route('/')
def home():
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()

    if user:
        session['user_id'] = user[0]
        return redirect('/employee')

    return "Invalid Login"


# ---------------- SIGNUP ----------------
@app.route('/signup')
def signup():
    return render_template("signup.html")

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    salary = request.form['salary']

    db = get_db()
    db.execute("INSERT INTO users (name, email, password, salary_per_day) VALUES (?, ?, ?, ?)",
               (name, email, password, salary))
    db.commit()

    return redirect('/')


# ---------------- EMPLOYEE ----------------
@app.route('/employee')
def employee():
    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']
    db = get_db()

    month = datetime.now().strftime('%Y-%m')

    data = db.execute("""
        SELECT date, status FROM attendance
        WHERE user_id=? AND date LIKE ?
    """, (user_id, f"{month}%")).fetchall()

    total_days = db.execute("""
        SELECT COUNT(*) FROM attendance
        WHERE user_id=? AND status='approved' AND date LIKE ?
    """, (user_id, f"{month}%")).fetchone()[0]

    salary = db.execute("SELECT salary_per_day FROM users WHERE id=?", (user_id,)).fetchone()[0]

    total_salary = total_days * salary

    return render_template("employee.html", data=data, days=total_days, salary=total_salary)


# ---------------- MARK ATTENDANCE (GPS) ----------------
@app.route('/mark_location', methods=['POST'])
def mark_location():
    user_id = session['user_id']
    data = request.get_json()

    user_lat = data['lat']
    user_lon = data['lon']

    # 🔴 SET YOUR LOCATION HERE
    office_lat = 28.36928653724523
    office_lon = 77.5507754219189

    dist = calculate_distance(user_lat, user_lon, office_lat, office_lon)

    if dist > 1000:
        return "❌ You are not in office location"

    today = datetime.now().strftime('%Y-%m-%d')
    db = get_db()

    existing = db.execute("SELECT * FROM attendance WHERE user_id=? AND date=?", (user_id, today)).fetchone()

    if existing:
        return "⚠️ Already marked today"

    db.execute("INSERT INTO attendance (user_id, date, status) VALUES (?, ?, 'approved')",
               (user_id, today))
    db.commit()

    return "✅ Attendance Marked Successfully"


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5001)), debug=True)