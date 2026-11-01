
import os
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)

import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd


app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "change-this-development-secret"
)


# ---------------- DATABASE CONNECTION ----------------

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "Chaitum@1015V"),
        database=os.getenv("DB_NAME", "gstudent_portal")
    )


# ---------------- LOGIN PROTECTION ----------------

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if (
            "user_id" not in session
            or session.get("role") != "admin"
        ):
            flash("Admin access required.", "error")
            return redirect(url_for("login"))

        return fn(*args, **kwargs)

    return wrapper


# ---------------- HOME ----------------

@app.route("/")
def index():
    return redirect(url_for("login"))


# ---------------- STUDENT REGISTRATION ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        reg_no = request.form.get("reg_no", "").strip()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")

        if not reg_no or not full_name or len(password) < 8:
            flash(
                "Enter all fields. Password must be at least 8 characters.",
                "error"
            )
            return render_template("register.html")

        try:
            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO users
                (reg_no, full_name, password_hash, role, status)
                VALUES (%s, %s, %s, 'student', 'pending')
                """,
                (
                    reg_no,
                    full_name,
                    generate_password_hash(password)
                )
            )

            conn.commit()
            cur.close()
            conn.close()

            flash(
                "Registration submitted. Wait for admin approval.",
                "success"
            )

            return redirect(url_for("login"))

        except Error as e:
            app.logger.error("Registration DB error: %s", e)

            flash(
                "Registration failed. Registration number may already exist.",
                "error"
            )

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        reg_no = request.form.get("reg_no", "").strip()
        password = request.form.get("password", "")

        try:
            conn = get_db()
            cur = conn.cursor(dictionary=True)

            cur.execute(
                "SELECT * FROM users WHERE reg_no = %s",
                (reg_no,)
            )

            user = cur.fetchone()

            cur.close()
            conn.close()

        except Error as e:
            app.logger.error("Login DB error: %s", e)

            flash(
                "Cannot connect to MySQL. Check database settings.",
                "error"
            )

            return render_template("login.html")

        if not user or not check_password_hash(
            user["password_hash"], password
        ):

            flash(
                "Invalid registration number or password.",
                "error"
            )

        elif (
            user["role"] == "student"
            and user["status"] != "approved"
        ):

            flash(
                "Your account is not approved yet. Contact the administrator.",
                "error"
            )

        else:

            session.clear()

            session["user_id"] = user["id"]
            session["reg_no"] = user["reg_no"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin"))

            return redirect(url_for("dashboard"))

    return render_template("login.html")


# ---------------- STUDENT DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def dashboard():

    if session.get("role") == "admin":
        return redirect(url_for("admin"))

    return render_template(
        "dashboard.html",
        name=session.get("full_name"),
        reg_no=session.get("reg_no")
    )


# ---------------- ADMIN PORTAL ----------------

@app.route("/admin")
@admin_required
def admin():

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        """
        SELECT id, reg_no, full_name, status, created_at
        FROM users
        WHERE role = 'student'
        ORDER BY created_at DESC
        """
    )

    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin.html", students=students)


# ---------------- APPROVE STUDENT ----------------

@app.route("/admin/approve/<int:user_id>", methods=["POST"])
@admin_required
def approve(user_id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET status = 'approved'
        WHERE id = %s AND role = 'student'
        """,
        (user_id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    flash("Student approved.", "success")

    return redirect(url_for("admin"))


# ---------------- REJECT STUDENT ----------------

@app.route("/admin/reject/<int:user_id>", methods=["POST"])
@admin_required
def reject(user_id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET status = 'rejected'
        WHERE id = %s AND role = 'student'
        """,
        (user_id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    flash("Student rejected.", "success")

    return redirect(url_for("admin"))


# ---------------- LOAD MCQ DATASET ----------------

def load_questions():

    path = os.path.join(
        app.root_path,
        "data",
        "mcq_questions (1).csv"
    )

    df = pd.read_csv(
        path,
        encoding="cp1252"
    ).fillna("")

    df = df.rename(
        columns={"Unnamed: 7": "explanation"}
    )

    required = {
        "topic",
        "question",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "answer",
        "explanation"
    }

    if not required.issubset(set(df.columns)):
        raise ValueError(
            f"Missing dataset columns: {df.columns.tolist()}"
        )

    return df


# ---------------- QUIZ TOPICS PAGE ----------------

@app.route("/quiz")
@login_required
def quiz():

    try:
        df = load_questions()

        topics = sorted(
            df["topic"].astype(str).str.strip().unique().tolist()
        )

        return render_template(
            "quiz_topics.html",
            topics=topics
        )

    except Exception as e:

        app.logger.error("Question dataset error: %s", e)

        flash(
            "Could not load question dataset. Check your CSV file.",
            "error"
        )

        return redirect(url_for("dashboard"))


# ---------------- INDIVIDUAL TOPIC QUIZ ----------------

@app.route("/quiz/<path:topic>")
@login_required
def quiz_topic(topic):

    try:
        df = load_questions()

        df = df[
            df["topic"].astype(str).str.strip() == topic.strip()
        ]

        if df.empty:
            flash("No questions found for this topic.", "error")
            return redirect(url_for("quiz"))

        questions = []

        for _, row in df.iterrows():

            questions.append({
                "id": len(questions),

                "question": str(row["question"]),

                "options": [
                    {
                        "value": "A",
                        "label": str(row["option_a"])
                    },
                    {
                        "value": "B",
                        "label": str(row["option_b"])
                    },
                    {
                        "value": "C",
                        "label": str(row["option_c"])
                    },
                    {
                        "value": "D",
                        "label": str(row["option_d"])
                    }
                ],

                "answer": str(row["answer"]).strip().upper(),

                "explanation": str(row["explanation"])
            })

        return render_template(
            "quiz.html",
            topic=topic,
            questions=questions
        )

    except Exception as e:

        app.logger.error("Quiz error: %s", e)

        flash(
            "Unable to load quiz. Please check your CSV file.",
            "error"
        )

        return redirect(url_for("quiz"))


# ---------------- AI CHATBOT ----------------

@app.route("/api/chat", methods=["POST"])
@login_required
def chat():

    question = (
        request.json.get("message", "").strip()
        if request.is_json and request.json
        else ""
    )

    if not question:
        return jsonify({
            "reply": "Type a question and I will try to help."
        })

    msg = question.lower()

    if "quiz" in msg or "practice" in msg:

        reply = (
            "Open Practice Quizzes, choose a topic, "
            "and answer the questions."
        )

    elif (
        "login" in msg
        or "approval" in msg
        or "register" in msg
    ):

        reply = (
            "Register using your registration number "
            "and a password of at least 8 characters. "
            "An administrator must approve your account "
            "before student login."
        )

    elif "tcp" in msg:

        reply = (
            "TCP is a connection-oriented transport protocol "
            "that provides reliable and ordered data delivery."
        )

    elif "pca" in msg:

        reply = (
            "PCA (Principal Component Analysis) reduces the "
            "number of features by transforming data into "
            "components that capture as much variance as possible."
        )

    else:

        reply = (
            "I am your G-Student Learning Assistant. "
            "Ask me about quizzes, login, TCP or PCA."
        )

    return jsonify({"reply": reply})


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)
