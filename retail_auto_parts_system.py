from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from getpass import getpass

app = Flask(__name__)
#secret key

# Database connection settings
DB_HOST = 'localhost'  # Or your remote DB host (e.g., 'db-host-name.com')
DB_USER = 'root'       # Database username
DB_PASSWORD = 'Ar4545325543'  # Replace with actual password
DB_NAME = 'auto_parts_db'  # Database name

# db connect
def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,   # << change this
        database=DB_NAME
    )

#TODO:
# get any store id
def get_store_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT store_id FROM Store LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0]
    return None

#TODO:
# get any employee id
def get_employee_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT employee_id FROM Employee LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0]
    return None

# customer login
def customer_login(un, pw):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    #SQL Query
    cur.execute("""
        SELECT customer_id, name
        FROM Customer
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
        FROM Employee
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

#TODO:
# show parts
def list_parts():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM AutoPart")
    parts = cur.fetchall()

    cur.close()
    conn.close()

    return parts

#TODO:
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
    cur.execute("SELECT price FROM AutoPart WHERE part_id = %s", (pid,))
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

#TODO:
# view customer orders
def view_customer_orders(customer_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT order_id, order_date, total_amount, payment_status
        FROM `Order`
        WHERE customer_id = %s
        ORDER BY order_date DESC
    """, (customer_id,))

    orders=cur.fetchall()

    cur.close()
    conn.close()
    return orders

#Flask routes:

# customer menu
@app.route('/customer_menu/<int:customer_id>')
def customer_menu(customer_id):

    #should go to the customer menu of the correct customer_id
    #NOTE: customer login redirects here, need to write HTML for customer_menu
    #relevant functions: list_parts, view_customer_orders, place_order
    parts = list_parts()
    orders=view_customer_orders(customer_id)
    return render_template('customer_menu.html', parts=parts, orders=orders)

#TODO:
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
        INSERT INTO AutoPart (part_name, category, price, stock_qty, condition, manufacturer)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (name, cat, price, qty, cond, manu))

    conn.commit()
    cur.close()
    conn.close()

    print("\nPart added.\n")

#TODO:
# view all orders
def view_all_orders():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT o.order_id, c.name AS Customer, s.store_name AS store,
               e.name AS employee, o.total_amount, o.payment_status
        FROM `Order` o
        LEFT JOIN Customer c ON o.customer_id = c.customer_id
        LEFT JOIN Store s ON o.store_id = s.store_id
        LEFT JOIN Employee e ON o.employee_id = e.employee_id
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
def store_menu(employee_id):

    #should go to the store menu of the employee_id
    #NOTE: employee login redirects here, need to write HTML for employee_menu
    return render_template('store_menu.html')

if __name__ == "__main__":
    app.run(debug = True)
