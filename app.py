from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)

app.secret_key = "my-blog-secret-key"


def create_database():
    connection = sqlite3.connect("blog.db")

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL
        )
    """)
    connection.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT NOT NULL
    )
""")

    connection.commit()
    connection.close()


@app.route("/")
def home():
    return render_template("home.html")
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]

        connection = sqlite3.connect("blog.db")

        connection.execute(
            "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
            (name, email, message)
        )

        connection.commit()
        connection.close()

        return "Message sent successfully!"

    return render_template("contact.html")
# Messages
@app.route("/messages")
def messages():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect("blog.db")
    connection.row_factory = sqlite3.Row

    messages = connection.execute(
        "SELECT * FROM messages ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template("messages.html", messages=messages)


@app.route("/blog")
def blog():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect("blog.db")
    connection.row_factory = sqlite3.Row

    posts = connection.execute(
        "SELECT * FROM posts WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template("blog.html", posts=posts)

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect("blog.db")
        connection.row_factory = sqlite3.Row

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()
        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return render_template(

             "dashboard.html",
             username=user["username"]
           )

        else:
            return "Invalid email or password!"

    return render_template("login.html")
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        connection = sqlite3.connect("blog.db")

        try:
            connection.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.close()
            return render_template(
                "register.html",
                error="Email already registered. Please use another email."
            )

        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=session.get("username")
    )
@app.route("/create-post", methods=["GET", "POST"])
def create_post():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        connection = sqlite3.connect("blog.db")

        connection.execute(
            "INSERT INTO posts (title, content, user_id) VALUES (?, ?, ?)",
            (title, content, session["user_id"])
        )

        connection.commit()
        connection.close()

        return redirect(url_for("blog"))

    return render_template("create_post.html")

# Edit Post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
   
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect("blog.db")
    connection.row_factory = sqlite3.Row

    post = connection.execute(
        "SELECT * FROM posts WHERE id = ? AND user_id = ?",
        (post_id, session["user_id"])
    ).fetchone()

    if post is None:
        connection.close()
        return "Post not found!"

    if request.method == "POST":

        title = request.form["title"]
        content = request.form["content"]

        connection.execute(
            "UPDATE posts SET title = ?, content = ? WHERE id = ? AND user_id = ?",
            (title, content, post_id, session["user_id"])
        )

        connection.commit()
        connection.close()

        return redirect(url_for("blog"))

    connection.close()

    return render_template("edit_post.html", post=post)


# Delete Post
@app.route("/delete-post/<int:post_id>")
def delete_post(post_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect("blog.db")

    connection.execute(
        "DELETE FROM posts WHERE id = ? AND user_id = ?",
        (post_id, session["user_id"])
    )

    connection.commit()
    connection.close()

    return redirect(url_for("blog"))
    
if __name__ == "__main__":
 create_database()
app.run(debug=True)
      