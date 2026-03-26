from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import math
import os
from pathlib import Path

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get("SECRET_KEY", "secret123")

# Database path - use /tmp for Vercel (ephemeral storage)
DB_PATH = "/tmp/database.db"

# For local development
if not os.path.exists("/tmp"):
    DB_PATH = "database.db"

# ---------- DATABASE ----------
def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    if os.path.exists(DB_PATH):
        return
    
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

# ---------- DISTANCE FUNCTION ----------
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c * 1000  # convert to meters

# Office location (New Delhi)
OFFICE_LAT = 28.36928653724523
OFFICE_LON = 77.5507754219189
ALLOWED_DISTANCE = 100  # 100 meters

# ---------- ROUTES ----------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/employee')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT id, name FROM users WHERE email=? AND password=?', 
                         (email, password)).fetchone()
        db.close()
        
        if user:
            session['user_id'] = user[0]
            session['name'] = user[1]
            return redirect('/employee')
        return "Invalid credentials"
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        salary = request.form['salary']
        
        db = get_db()
        db.execute('INSERT INTO users (name, email, password, salary_per_day) VALUES (?, ?, ?, ?)',
                  (name, email, password, salary))
        db.commit()
        db.close()
        
        return redirect('/login')
    
    return render_template('signup.html')

@app.route('/employee')
def employee():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    db = get_db()
    
    salary_per_day = db.execute('SELECT salary_per_day FROM users WHERE id=?', 
                               (user_id,)).fetchone()[0]
    
    attendance = db.execute('SELECT date, status FROM attendance WHERE user_id=? ORDER BY date DESC',
                           (user_id,)).fetchall()
    
    days = len([row for row in attendance if row[1] == "Present"])
    total_salary = days * salary_per_day
    
    db.close()
    
    return render_template('employee.html', days=days, salary=total_salary, data=attendance)

@app.route('/mark_location', methods=['POST'])
def mark_location():
    if 'user_id' not in session:
        return "Unauthorized", 401
    
    data = request.json
    user_lat = data['lat']
    user_lon = data['lon']
    
    distance = calculate_distance(OFFICE_LAT, OFFICE_LON, user_lat, user_lon)
    
    if distance > ALLOWED_DISTANCE:
        return f"You are {distance:.0f}m away from office. Minimum distance required: {ALLOWED_DISTANCE}m"
    
    today = datetime.now().strftime("%Y-%m-%d")
    user_id = session['user_id']
    
    db = get_db()
    existing = db.execute('SELECT id FROM attendance WHERE user_id=? AND date=?',
                         (user_id, today)).fetchone()
    
    if existing:
        return "Attendance already marked for today"
    
    db.execute('INSERT INTO attendance (user_id, date, status) VALUES (?, ?, ?)',
              (user_id, today, "Present"))
    db.commit()
    db.close()
    
    return "Attendance marked successfully ✓"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=False)
