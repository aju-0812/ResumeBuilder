from flask import Flask, render_template, request, redirect, session, send_file, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from weasyprint import HTML
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")

# Upload Config
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Database Setup ---
def init_db():
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
        conn.commit()

init_db()

@app.route('/')
def index():
    return redirect(url_for('home_page'))

@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username'].strip()
        pwd = request.form['password']

        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE username = ?', (uname,))
            user = c.fetchone()

        if user and check_password_hash(user[2], pwd):
            session['user'] = uname
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form['username'].strip()
        pwd = request.form['password']

        if not uname or not pwd:
            return render_template('register.html', error='Username and password required')

        hashed_pwd = generate_password_hash(pwd)

        try:
            with sqlite3.connect('database.db') as conn:
                c = conn.cursor()
                c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (uname, hashed_pwd))
                conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Username already exists')

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['user'])

@app.route('/generateresume', methods=['POST'])
def generate_resume():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Form data
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()

    if not name or not email or not phone:
        return "Name, Email, and Phone are required!", 400

    linkedin = request.form.get('linkedin', '').strip()
    summary = request.form.get('summary', '').strip()
    skills = request.form.get('skills', '').strip()
    hsc_score = request.form.get('hscScore', '').strip()
    hsc_year = request.form.get('hscYear', '').strip()
    college_year = request.form.get('collegeYear', '').strip()
    cgpa = request.form.get('cgpa', '').strip()
    education = f"HSC Score: {hsc_score}, HSC Year: {hsc_year}, College Year: {college_year}, CGPA: {cgpa}"
    experience = request.form.get('internships', '').strip()
    projects = request.form.get('projects', '').strip()
    certifications = request.form.get('certifications', '').strip()
    achievements = request.form.get('achievements', '').strip()

    # Handle image upload
    image_url = ''
    image_file = request.files.get('image')
    if image_file and image_file.filename != '' and allowed_file(image_file.filename):
        image_folder = os.path.join(app.root_path, 'static', 'uploads')
        os.makedirs(image_folder, exist_ok=True)

        safe_name = secure_filename(name)
        ext = os.path.splitext(image_file.filename)[1]
        image_filename = f"{safe_name}_{uuid.uuid4().hex}{ext}"
        image_path = os.path.join(image_folder, image_filename)
        image_file.save(image_path)

        # ✅ Fixed for WeasyPrint
        image_url = url_for('static', filename=f'uploads/{image_filename}', _external=True)

    # Render template with all data
    html = render_template('template1.html',
                           name=name,
                           email=email,
                           phone=phone,
                           linkedin=linkedin,
                           summary=summary,
                           skills=skills,
                           education=education,
                           experience=experience,
                           projects=projects,
                           certifications=certifications,
                           achievements=achievements,
                           image_url=image_url)

    resumes_folder = os.path.join(app.root_path, 'resumes')
    os.makedirs(resumes_folder, exist_ok=True)
    pdf_filename = f"{secure_filename(name)}.pdf"
    pdf_path = os.path.join(resumes_folder, pdf_filename)

    try:
        HTML(string=html, base_url=app.root_path).write_pdf(pdf_path)
    except Exception as e:
        print(f"[ERROR] PDF generation failed: {e}")
        return "Internal Server Error: PDF generation failed", 500

    return send_file(pdf_path, as_attachment=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home_page'))

if __name__ == '__main__':
    app.run(debug=True)
