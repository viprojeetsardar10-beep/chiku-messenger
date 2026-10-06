from flask import Flask, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "chiku-secret-key"


def db():
    return sqlite3.connect("messenger.db")


def init_db():
    con = db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()


@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/users")

    return """
    <h1>💬 Chiku's Messenger</h1>
    <a href="/login">Login</a><br>
    <a href="/register">Register</a>
    """


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        con = db()

        try:
            con.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
            con.commit()
            con.close()
            return redirect("/login")

        except sqlite3.IntegrityError:
            con.close()
            return "Username already exists!"

    return """
    <h2>Register</h2>
    <form method="POST">
        Username:<br>
        <input name="username"><br><br>

        Password:<br>
        <input type="password" name="password"><br><br>

        <button>Register</button>
    </form>
    <br>
    <a href="/login">Login</a>
    """


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        con = db()
        user = con.execute(
            "SELECT id, username, password FROM users WHERE username=?",
            (username,)
        ).fetchone()
        con.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect("/users")

        return "Wrong username or password!"

    return """
    <h2>Login</h2>
    <form method="POST">
        Username:<br>
        <input name="username"><br><br>

        Password:<br>
        <input type="password" name="password"><br><br>

        <button>Login</button>
    </form>
    <br>
    <a href="/register">Create account</a>
    """


@app.route("/users")
def users():
    if "user_id" not in session:
        return redirect("/login")

    con = db()
    users = con.execute(
        "SELECT id, username FROM users WHERE id != ?",
        (session["user_id"],)
    ).fetchall()
    con.close()

    html = f"""
    <h1>💬 Chiku's Messenger</h1>
    <p>Welcome, {session["username"]} 👋</p>
    <h3>Users</h3>
    """

    for user in users:
        html += f"""
        <p>👤 {user[1]}
        <a href="/chat/{user[0]}">Chat</a></p>
        """

    html += '<br><a href="/logout">Logout</a>'

    return html


@app.route("/chat/<int:user_id>", methods=["GET", "POST"])
def chat(user_id):
    if "user_id" not in session:
        return redirect("/login")

    con = db()

    other_user = con.execute(
        "SELECT id, username FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    if not other_user:
        con.close()
        return "User not found!"

    if request.method == "POST":
        message = request.form["message"]

        if message.strip():
            con.execute(
                """
                INSERT INTO messages
                (sender_id, receiver_id, message)
                VALUES (?, ?, ?)
                """,
                (session["user_id"], user_id, message)
            )
            con.commit()

    messages = con.execute(
        """
        SELECT sender_id, message
        FROM messages
        WHERE
        (sender_id=? AND receiver_id=?)
        OR
        (sender_id=? AND receiver_id=?)
        ORDER BY id
        """,
        (
            session["user_id"],
            user_id,
            user_id,
            session["user_id"]
        )
    ).fetchall()

    con.close()

    html = f"<h2>💬 Chat with {other_user[1]}</h2>"

    for sender_id, message in messages:
        if sender_id == session["user_id"]:
            html += f"<p><b>You:</b> {message}</p>"
        else:
            html += f"<p><b>{other_user[1]}:</b> {message}</p>"

    html += """
    <form method="POST">
        <input name="message" placeholder="Type message..." required>
        <button>Send</button>
    </form>
    <br>
    <a href="/users">← Back to Users</a>
    """

    return html


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
