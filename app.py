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


STYLE = """
<style>
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f0f2f5;
    color: #222;
}

.container {
    max-width: 430px;
    margin: auto;
    padding: 20px;
}

.card {
    background: white;
    padding: 25px;
    border-radius: 18px;
    box-shadow: 0 4px 15px rgba(0,0,0,.08);
}

h1 {
    color: #1877f2;
    text-align: center;
}

h2 {
    text-align: center;
}

input {
    width: 100%;
    box-sizing: border-box;
    padding: 13px;
    margin: 7px 0;
    border: 1px solid #ddd;
    border-radius: 10px;
    font-size: 16px;
}

button {
    width: 100%;
    padding: 13px;
    margin-top: 10px;
    border: 0;
    border-radius: 10px;
    background: #1877f2;
    color: white;
    font-size: 16px;
}

a {
    color: #1877f2;
    text-decoration: none;
}

.user {
    background: #f5f6f7;
    padding: 14px;
    margin: 8px 0;
    border-radius: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-box {
    background: white;
    padding: 15px;
    border-radius: 15px;
    min-height: 300px;
}

.message {
    padding: 10px 14px;
    margin: 8px 0;
    border-radius: 15px;
    max-width: 75%;
}

.mine {
    background: #1877f2;
    color: white;
    margin-left: auto;
}

.theirs {
    background: #e4e6eb;
    color: #222;
}

.back {
    display: block;
    margin-top: 15px;
    text-align: center;
}
</style>
"""


@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/users")

    return STYLE + """
    <div class="container">
        <div class="card">
            <h1>💬 Chiku's Messenger</h1>
            <p style="text-align:center;">
                Simple private messaging
            </p>

            <a href="/login">
                <button>Login</button>
            </a>

            <a href="/register">
                <button style="background:#42b72a;">
                    Create Account
                </button>
            </a>
        </div>
    </div>
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

            return STYLE + """
            <div class="container">
                <div class="card">
                    <h2>Username already exists!</h2>
                    <a href="/register">Try another username</a>
                </div>
            </div>
            """

    return STYLE + """
    <div class="container">
        <div class="card">

            <h1>💬 Chiku's Messenger</h1>
            <h2>Create Account</h2>

            <form method="POST">

                <input
                    name="username"
                    placeholder="Username"
                    required
                >

                <input
                    type="password"
                    name="password"
                    placeholder="Password"
                    required
                >

                <button>Create Account</button>

            </form>

            <p style="text-align:center;">
                Already have an account?
                <a href="/login">Login</a>
            </p>

        </div>
    </div>
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

        return STYLE + """
        <div class="container">
            <div class="card">

                <h2>Wrong username or password!</h2>

                <a href="/login">Try again</a>

            </div>
        </div>
        """

    return STYLE + """
    <div class="container">
        <div class="card">

            <h1>💬 Chiku's Messenger</h1>
            <h2>Login</h2>

            <form method="POST">

                <input
                    name="username"
                    placeholder="Username"
                    required
                >

                <input
                    type="password"
                    name="password"
                    placeholder="Password"
                    required
                >

                <button>Login</button>

            </form>

            <p style="text-align:center;">
                New user?
                <a href="/register">Create Account</a>
            </p>

        </div>
    </div>
    """


@app.route("/users")
def users():

    if "user_id" not in session:
        return redirect("/login")

    con = db()

    all_users = con.execute(
        "SELECT id, username FROM users WHERE id != ?",
        (session["user_id"],)
    ).fetchall()

    con.close()

    html = STYLE + f"""
    <div class="container">

        <div class="card">

            <h1>💬 Chiku's Messenger</h1>

            <p style="text-align:center;">
                Welcome, <b>{session["username"]}</b> 👋
            </p>

            <h3>People</h3>
    """

    if not all_users:

        html += """
        <p style="text-align:center;">
            No other users yet.
        </p>
        """

    for user in all_users:

        html += f"""
        <div class="user">

            <span>👤 {user[1]}</span>

            <a href="/chat/{user[0]}">
                Chat 💬
            </a>

        </div>
        """

    html += """
            <br>

            <a href="/logout">
                Logout
            </a>

        </div>

    </div>
    """

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
                (
                    session["user_id"],
                    user_id,
                    message
                )
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

    html = STYLE + f"""
    <div class="container">

        <div class="card">

            <h2>💬 {other_user[1]}</h2>

            <div class="chat-box">
    """

    for sender_id, message in messages:

        if sender_id == session["user_id"]:

            html += f"""
            <div class="message mine">
                {message}
            </div>
            """

        else:

            html += f"""
            <div class="message theirs">
                {message}
            </div>
            """

    html += """
            </div>

            <form method="POST">

                <input
                    name="message"
                    placeholder="Type a message..."
                    required
                >

                <button>Send 💬</button>

            </form>

            <a class="back" href="/users">
                ← Back to Users
            </a>

        </div>

    </div>
    """

    return html


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


init_db()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
