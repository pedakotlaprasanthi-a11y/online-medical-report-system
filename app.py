import os
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "medical_reports.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

def initialize_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Enter both username and password.")
            return render_template("register.html")
        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password))
                )
            flash("Registration successful. Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That username already exists.")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.")
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    with get_db() as db:
        reports = db.execute(
            "SELECT * FROM reports WHERE user_id = ? ORDER BY uploaded_at DESC",
            (session["user_id"],)
        ).fetchall()
    return render_template("dashboard.html", reports=reports)

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    uploaded = request.files.get("report")
    title = request.form.get("title", "").strip()
    if not uploaded or uploaded.filename == "" or not title:
        flash("Enter a report title and choose a file.")
        return redirect(url_for("dashboard"))
    if not allowed_file(uploaded.filename):
        flash("Only PDF, PNG, JPG and JPEG files are allowed.")
        return redirect(url_for("dashboard"))

    safe_name = secure_filename(uploaded.filename)
    stored_name = f"{session['user_id']}_{safe_name}"
    uploaded.save(os.path.join(app.config["UPLOAD_FOLDER"], stored_name))
    with get_db() as db:
        db.execute(
            "INSERT INTO reports (user_id, title, filename) VALUES (?, ?, ?)",
            (session["user_id"], title, stored_name)
        )
    flash("Report uploaded successfully.")
    return redirect(url_for("dashboard"))

@app.route("/download/<int:report_id>")
@login_required
def download(report_id):
    with get_db() as db:
        report = db.execute(
            "SELECT * FROM reports WHERE id = ? AND user_id = ?",
            (report_id, session["user_id"])
        ).fetchone()
    if not report:
        abort(404)
    return send_from_directory(app.config["UPLOAD_FOLDER"], report["filename"], as_attachment=True)

@app.route("/delete/<int:report_id>", methods=["POST"])
@login_required
def delete(report_id):
    with get_db() as db:
        report = db.execute(
            "SELECT * FROM reports WHERE id = ? AND user_id = ?",
            (report_id, session["user_id"])
        ).fetchone()
        if not report:
            abort(404)
        db.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], report["filename"])
    if os.path.exists(file_path):
        os.remove(file_path)
    flash("Report deleted successfully.")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.errorhandler(413)
def too_large(_error):
    flash("File is too large. Maximum upload size is 10 MB.")
    return redirect(url_for("dashboard"))

initialize_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
