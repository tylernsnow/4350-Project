from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "change_this_secret"  # needed for session

DB_PASSWORD = "password"  # TODO: replace with real MySQL password


# ---------------- DB CONNECTION ----------------

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=DB_PASSWORD,
        database="auto_parts_db"
    )


# ---------------- EMPLOYEE LOGIN ----------------

@app.route("/employee/login", methods=["GET", "POST"])
def employee_login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT employee_id, name
            FROM employee
            WHERE username = %s AND password = %s
            """,
            (u, p),
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session["employee_id"] = user["employee_id"]
            session["employee_name"] = user["name"]
            return redirect(url_for("employee_dashboard"))
        else:
            flash("Invalid username or password.")
            return redirect(url_for("employee_login"))

    return render_template("employee_login.html")  # GET request


# ---------------- EMPLOYEE DASHBOARD ----------------

@app.route("/employee/dashboard")
def employee_dashboard():
    if "employee_id" not in session:
        return redirect(url_for("employee_login"))

    return render_template(
        "employee_dashboard.html",
        employee_name=session.get("employee_name")
    )


# ---------------- VIEW PARTS ----------------

@app.route("/employee/parts")
def employee_parts():
    if "employee_id" not in session:
        return redirect(url_for("employee_login"))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM autopart")
    parts = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("employee_parts.html", parts=parts)


# ---------------- ADD PART ----------------

@app.route("/employee/parts/add", methods=["GET", "POST"])
def employee_add_part():
    if "employee_id" not in session:
        return redirect(url_for("employee_login"))

    if request.method == "POST":
        name = request.form.get("part_name")
        cat = request.form.get("category")
        price = request.form.get("price")
        qty = request.form.get("stock_qty")
        cond = request.form.get("condition")
        manu = request.form.get("manufacturer")

        if not name or not cat or not price or not qty:
            flash("Please fill in all required fields.")
            return redirect(url_for("employee_add_part"))

        try:
            price_val = float(price)
            qty_val = int(qty)
        except ValueError:
            flash("Price must be a number and quantity must be an integer.")
            return redirect(url_for("employee_add_part"))

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO autopart
            (part_name, category, price, stock_qty, condition, manufacturer)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (name, cat, price_val, qty_val, cond, manu),
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("Part added successfully.")
        return redirect(url_for("employee_parts"))

    return render_template("employee_add_part.html")


# ---------------- VIEW ALL ORDERS ----------------

@app.route("/employee/orders")
def employee_orders():
    if "employee_id" not in session:
        return redirect(url_for("employee_login"))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT o.order_id,
               c.name AS customer,
               s.store_name AS store,
               e.name AS employee,
               o.total_amount,
               o.payment_status,
               o.order_date
        FROM `Order` o
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN store s ON o.store_id = s.store_id
        LEFT JOIN employee e ON o.employee_id = e.employee_id
        ORDER BY o.order_id DESC
        """
    )
    orders = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("employee_orders.html", orders=orders)


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)
