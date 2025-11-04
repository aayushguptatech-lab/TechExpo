import os
import sqlite3
import requests
from flask import Flask, render_template, request, url_for, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyPDF2 import PdfReader
from Utils.Agent import Cardiologist, Psychologist, Pulmonologist, MultidisciplinaryTeam


app = Flask(__name__)
app.secret_key = "supersecretkey"  # needed for session

UPLOAD_FOLDER = 'uploads'
RESULT_PATH = 'results/final_diagnosis.txt'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)

# ---------------- LOGIN SYSTEM ---------------- #
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            session['next'] = request.url
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/health_camps")
def health_camps():
    return render_template("health_camps.html")

@app.route("/schemes")
def schemes():
    return render_template("government_schemes.html")

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")


# ---------------- LOGIN & REGISTER ---------------- #
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


# ---------------- CHATBOT ---------------- #
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


# ---------------- REPORT UPLOAD (merged) ---------------- #
@app.route("/upload_report", methods=['GET', 'POST'])
@login_required
def upload_report():
    if request.method == 'POST':
        file = request.files['report']
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            medical_report = ""
            if file.filename.endswith('.txt'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    medical_report = f.read()
            elif file.filename.endswith('.pdf'):
                reader = PdfReader(filepath)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        medical_report += text
            else:
                return render_template("upload_report.html", error="Please upload a .txt or .pdf file.")

            # Run specialist agents
            agents = {
                "Cardiologist": Cardiologist(medical_report),
                "Psychologist": Psychologist(medical_report),
                "Pulmonologist": Pulmonologist(medical_report)
            }

            responses = {}
            with ThreadPoolExecutor() as executor:
                futures = {executor.submit(agent.run): name for name, agent in agents.items()}
                for future in as_completed(futures):
                    agent_name = futures[future]
                    responses[agent_name] = future.result()

            # Team diagnosis
            team_agent = MultidisciplinaryTeam(
                cardiologist_report=responses["Cardiologist"],
                psychologist_report=responses["Psychologist"],
                pulmonologist_report=responses["Pulmonologist"]
            )
            final_diagnosis = team_agent.run()
            print("Team agent output:", final_diagnosis)

            final_diagnosis_text = "### Final Diagnosis:\n\n" + str(final_diagnosis or "No diagnosis generated.")
            with open(RESULT_PATH, 'w') as result_file:
                result_file.write(final_diagnosis_text)

            return render_template("upload_report.html", diagnosis=final_diagnosis_text)

    return render_template("upload_report.html")


# ---------------- RUN APP ---------------- #
if __name__ == '__main__':
    app.run(debug=True, port=8000)
