from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "secretkey"


def connect_db():
    conn = sqlite3.connect("expenses.db")
    conn.row_factory = sqlite3.Row
    return conn


with connect_db() as conn:

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        amount REAL,
        category TEXT,
        date TEXT,
        user_id INTEGER
    )
    """)



@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = connect_db()

        try:
            conn.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (username,password)
            )

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists"

        conn.close()

        return redirect("/login")


    return render_template("register.html")





@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]


        conn = connect_db()


        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        ).fetchone()


        conn.close()


        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect("/")


        return "Invalid username or password"



    return render_template("login.html")






@app.route("/")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")


    conn = connect_db()



    expenses = conn.execute(
        "SELECT * FROM expenses WHERE user_id=? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()



    categories = []
    amounts = []


    for expense in expenses:

        categories.append(expense["category"])
        amounts.append(expense["amount"])




    total = conn.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id=?",
        (session["user_id"],)
    ).fetchone()[0]



    monthly = conn.execute(
        """
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id=?
        AND strftime('%m',date)=strftime('%m','now')
        """,
        (session["user_id"],)
    ).fetchone()[0]




    monthly_data = conn.execute(
        """
        SELECT strftime('%m',date) as month,
        SUM(amount) as total
        FROM expenses
        WHERE user_id=?
        GROUP BY month
        """,
        (session["user_id"],)
    ).fetchall()



    months = []
    monthly_amounts = []


    for item in monthly_data:

        months.append(item["month"])
        monthly_amounts.append(item["total"])



    conn.close()



    if total is None:
        total = 0


    if monthly is None:
        monthly = 0




    return render_template(
        "dashboard.html",
        expenses=expenses,
        total=total,
        monthly=monthly,
        categories=categories,
        amounts=amounts,
        monthly_labels=months,
        monthly_amounts=monthly_amounts
    )






@app.route("/add", methods=["POST"])
def add_expense():

    if "user_id" not in session:
        return redirect("/login")


    name = request.form["name"]
    amount = request.form["amount"]
    category = request.form["category"]



    conn = connect_db()


    conn.execute(
        """
        INSERT INTO expenses
        (name,amount,category,date,user_id)
        VALUES(?,?,?,?,?)
        """,
        (
            name,
            amount,
            category,
            str(date.today()),
            session["user_id"]
        )
    )


    conn.commit()
    conn.close()


    return redirect("/")






@app.route("/delete/<int:id>")
def delete_expense(id):

    if "user_id" not in session:
        return redirect("/login")



    conn = connect_db()


    conn.execute(
        "DELETE FROM expenses WHERE id=? AND user_id=?",
        (id,session["user_id"])
    )


    conn.commit()
    conn.close()


    return redirect("/")







@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")






if __name__ == "__main__":
    app.run(debug=True)