from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import math
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- DISTANCE FUNCTION ----------------

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

# ---------------- HOME ----------------

@app.route('/')
def home():
    return render_template("login.html")

# ---------------- LOGIN ----------------

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email=? AND password=?",
                      (email, password)).fetchone()

    if user:
        session['user_id'] = user['id']
        return redirect('/employee')
    else:
        return "Invalid login"

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
    db.execute(
        "INSERT INTO users (name, email, password, salary_per_day) VALUES (?, ?, ?, ?)",
        (name, email, password, salary)
    )
    db.commit()

    return redirect('/')

# ---------------- EMPLOYEE DASHBOARD ----------------

@app.route('/employee')
def employee():
    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']
    db = get_db()

    current_month = datetime.now().strftime('%Y-%m')

    present_days = db.execute("""
        SELECT COUNT(*) FROM attendance
        WHERE user_id = ?
        AND status = 'Present'
        AND date LIKE ?
    """, (user_id, current_month + '%')).fetchone()[0]

    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    if not user:
        return "User not found"

    total_salary = present_days * user['salary_per_day']
    month_name = datetime.now().strftime('%B %Y')

    return render_template(
        "employee.html",
        present_days=present_days,
        total_salary=total_salary,
        month_name=month_name
    )

# ---------------- MARK ATTENDANCE ----------------

@app.route('/mark_location', methods=['POST'])
def mark_location():
    if 'user_id' not in session:
        return "Not logged in"

    data = request.get_json()
    user_lat = data['lat']
    user_lon = data['lon']

    # 🔴 SET YOUR OFFICE LOCATION HERE
    office_lat = 28.36928653724523
    office_lon = 77.5507754219189

    distance = calculate_distance(user_lat, user_lon, office_lat, office_lon)

    if distance > 100:
        return "❌ You are not in office location"

    db = get_db()

    today = datetime.now().strftime('%Y-%m-%d')

    # check already marked
    existing = db.execute("""
        SELECT * FROM attendance
        WHERE user_id=? AND date=?
    """, (session['user_id'], today)).fetchone()

    if existing:
        return "⚠ Already marked"

    db.execute("""
        INSERT INTO attendance (user_id, date, status)
        VALUES (?, ?, 'Present')
    """, (session['user_id'], today))

    db.commit()

    return "✅ Attendance marked"

# ---------------- HISTORY ----------------

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect('/')

    db = get_db()

    records = db.execute("""
        SELECT * FROM attendance
        WHERE user_id=?
        ORDER BY date DESC
    """, (session['user_id'],)).fetchall()

    return render_template("history.html", records=records)

# ---------------- ADMIN ----------------

@app.route('/admin')
def admin():
    db = get_db()

    users = db.execute("SELECT * FROM users").fetchall()

    attendance = db.execute("""
        SELECT attendance.*, users.name
        FROM attendance
        JOIN users ON attendance.user_id = users.id
        ORDER BY date DESC
    """).fetchall()

    return render_template("admin.html", users=users, attendance=attendance)

# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)