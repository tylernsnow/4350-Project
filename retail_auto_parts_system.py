from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from getpass import getpass

app = Flask(__name__)
#secret key

# Database connection settings
DB_HOST = 'localhost'  # Or your remote DB host (e.g., 'db-host-name.com')
DB_USER = 'root'       # Database username
DB_PASSWORD = 'password'  # Replace with actual password
DB_NAME = 'auto_parts_db'  # Database name

# db connect
def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,   # << change this
        database=DB_NAME
    )

# get any store id
def get_store_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT store_id FROM store LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0]
    return None

# get any employee id
def get_employee_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT employee_id FROM employee LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0]
    return None

#functions to be changed to work with Flask (return data, no print):
# customer login
def customer_login(un, pw):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    #SQL Query
    cur.execute("""
        SELECT customer_id, name
        FROM customers
        WHERE username = %s AND password = %s
    """, (un, pw))

    row = cur.fetchone()
    cur.close()
    conn.close()

    return row

# employee login
def employee_login(un, pw):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT employee_id, name
        FROM employee
        WHERE username = %s AND password = %s
    """, (un, pw))

    row = cur.fetchone()
    cur.close()
    conn.close()

    return row

@app.route('/')
def home():
    return render_template('home.html')

#configure: direct to employee or customer login
@app.route('/cus_login', methods=['GET', 'POST'])
def cus_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = customer_login(username, password)
        if user:
            return redirect(url_for('customer_menu', customer_id=user['customer_id']))
        else:
            flash("Login failed.")
    return render_template('customer_login.html')

@app.route('/emp_login', methods=['GET', 'POST'])
def emp_login():
    if request.method =='POST':
        username = request.form['username']
        password = request.form['password']
        user = employee_login(username, password)
        if user:
            return redirect(url_for('employee_menu', employee_id=user['employee_id']))
        else:
            flash("Login failed.")
    return render_template('employee_login.html')

# show parts
def list_parts():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM autopart")
    print("\n--- Parts ---")
    for x in cur:
        print(f"{x['part_id']}: {x['part_name']} | {x['category']} | ${x['price']} | {x['stock_qty']} left")
    print("-------------\n")

    cur.close()
    conn.close()

# place order
def place_order(cid):
    list_parts()
    pid = input("Part ID: ").strip()
    qty_str = input("Qty: ").strip()

    try:
        qty = int(qty_str)
    except ValueError:
        print("Invalid quantity.\n")
        return

    conn = get_connection()
    cur = conn.cursor()

    # get price
    cur.execute("SELECT price FROM autopart WHERE part_id = %s", (pid,))
    row = cur.fetchone()
    if not row:
        print("Invalid part.\n")
        cur.close()
        conn.close()
        return

    price = row[0]
    total = price * qty

    # pick store and employee
    store_id = get_store_id()
    emp_id = get_employee_id()
    if not store_id or not emp_id:
        print("No store/employee found in DB.\n")
        cur.close()
        conn.close()
        return

    # insert into Order (table name uses backticks)
    cur.execute("""
        INSERT INTO `Order`
        (customer_id, store_id, employee_id, order_date, delivery_date, total_amount, payment_status)
        VALUES (%s, %s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 3 DAY), %s, %s)
    """, (cid, store_id, emp_id, total, "Pending"))

    oid = cur.lastrowid

    # order detail
    cur.execute("""
        INSERT INTO orderdetail (order_id, part_id, quantity, subtotal)
        VALUES (%s, %s, %s, %s)
    """, (oid, pid, qty, total))

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nOrder placed. ID: {oid} | Total: ${total}\n")

# view customer orders
def view_customer_orders(cid):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT order_id, order_date, total_amount, payment_status
        FROM `Order`
        WHERE customer_id = %s
        ORDER BY order_date DESC
    """, (cid,))

    print("\n--- Your Orders ---")
    for x in cur:
        print(f"{x['order_id']} | ${x['total_amount']} | {x['payment_status']}")
    print("-------------------\n")

    cur.close()
    conn.close()

#Flask routes:

# customer menu
@app.route('/customer_menu/<int:customer_id>')
def customer_menu(customer_id):
    cid = customer_login()
    if not cid:
        return

    parts = list_parts()
    return render_template('customer_menu.html', parts=parts)

# add part
def add_part():
    name = input("Name: ")
    cat = input("Category: ")
    price_str = input("Price: ").strip()
    qty_str = input("Qty: ").strip()
    cond = input("Condition: ")
    manu = input("Manufacturer: ")

    try:
        price = float(price_str)
        qty = int(qty_str)
    except ValueError:
        print("Invalid price or qty.\n")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO autopart (part_name, category, price, stock_qty, condition, manufacturer)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (name, cat, price, qty, cond, manu))

    conn.commit()
    cur.close()
    conn.close()

    print("\nPart added.\n")

# view all orders
def view_all_orders():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT o.order_id, c.name AS customer, s.store_name AS store,
               e.name AS employee, o.total_amount, o.payment_status
        FROM `Order` o
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN store s ON o.store_id = s.store_id
        LEFT JOIN employee e ON o.employee_id = e.employee_id
        ORDER BY o.order_id DESC
    """)

    print("\n--- All Orders ---")
    for x in cur:
        print(f"{x['order_id']} | {x['customer']} | {x['store']} | {x['employee']} | ${x['total_amount']} | {x['payment_status']}")
    print("------------------\n")

    cur.close()
    conn.close()

@app.route('/store_menu')
# store menu
def store_menu():
    eid = employee_login()
    if not eid:
        return

    while True:
        print("1. View Parts")
        print("2. Add Part")
        print("3. View Orders")
        print("4. Logout")
        ch = input("Choose: ").strip()

        if ch == "1":
            list_parts()
        elif ch == "2":
            add_part()
        elif ch == "3":
            view_all_orders()
        elif ch == "4":
            break
        else:
            print("Invalid.\n")

# main
def main_menu():
    while True:
        print("\n=== Retail Auto Parts System ===")
        print("1. Customer Mode")
        print("2. Store Mode")
        print("3. Exit")
        ch = input("Choose: ").strip()

        if ch == "1":
            customer_menu()
        elif ch == "2":
            store_menu()
        elif ch == "3":
            print("Bye.")
            break
        else:
            print("Invalid.\n")

if __name__ == "__main__":
    main_menu()
