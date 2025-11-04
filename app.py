import os
import sqlite3
import requests
from flask import Flask, render_template, request, url_for, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey"  # needed for session


# LOGIN CHECK DECORATOR
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            session['next'] = request.url
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ROUTES 
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/health_camps")
def health_camps():
    return render_template("health_camps.html")

@app.route("/schemes")
def schemes():
    return render_template("government_schemes.html")

@app.route("/upload_report")
@login_required
def upload_report():
    return render_template("upload_report.html")

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")


# REGISTER 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      username TEXT, email TEXT UNIQUE, password TEXT)''')

        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return "Email already registered. <a href='/login'>Login here</a>"

        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                  (username, email, password))
        conn.commit()
        conn.close()
        return "Registration successful! <a href='/login'>Login here</a>"

    return render_template('register.html')


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            next_page = session.pop('next', None)
            return redirect(next_page or url_for('home'))
        else:
            return "Invalid email or password. <a href='/login'>Try again</a>"

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# CHATBOT 
@app.route("/get", methods=["POST"])
def chat():
    msg = request.form.get("msg")
    return get_chat_response(msg)

def get_chat_response(text):
    api_key = "YOUR_GEMINI_API_KEY"
    API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent?key={api_key}"

    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": text}]}]}

    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"Error {response.status_code}: {response.text}"


if __name__ == '__main__':
    app.run(debug=True, port=8000)
