from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from getpass import getpass

app = Flask(__name__)
app.secret_key = "change_this_secret"  # secret key needed for session

# Database connection settings
DB_HOST = 'localhost'  # Or remote DB host if not run locally
DB_USER = 'root'       # Database username
DB_PASSWORD = 'Ar4545325543'  # Replace with actual password
DB_NAME = 'auto_parts_db'  # Database name

# db connect
def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def get_store_id(employee_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT store_id
        FROM Employee
        WHERE employee_id = %s
    """, (employee_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row['store_id']
    return None

#get any store to ship a part
def get_part_store():
    conn = get_connection()
    cur = conn.cursor()

    # Query to get any store_id (without filtering by part_id)
    cur.execute("""
        SELECT store_id 
        FROM Store
        LIMIT 1
    """)

    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return row[0]  # Return the store_id
    return None  # If no store found

# get any employee id from store
def get_employee_id(store_id):
    conn = get_connection()
    cur = conn.cursor()

    # Query to get an employee from the specified store_id
    cur.execute("""
        SELECT employee_id 
        FROM Employee 
        WHERE store_id = %s
        LIMIT 1
    """, (store_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return row[0]  # Return the employee_id
    return None  # If no employee found in the store

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

#customer login: routes to customer mode
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

#employee login: routes to store mode
@app.route('/emp_login', methods=['GET', 'POST'])
def emp_login():
    if request.method =='POST':
        username = request.form['username']
        password = request.form['password']
        user = employee_login(username, password)
        if user:
            return redirect(url_for('store_menu', employee_id=user['employee_id']))
        else:
            flash("Login failed.")
    return render_template('employee_login.html')

# show parts
def list_parts():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM AutoPart")
    parts = cur.fetchall()

    cur.close()
    conn.close()

    return parts

# place order
@app.route('/customer/<int:customer_id>/order', methods=['GET', 'POST'])
def place_order(customer_id):
    if request.method == 'POST':
        pid = request.form['part_id'].strip()
        quantity_str = request.form['quantity'].strip()

        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            parts = list_parts()
            return render_template(
                'place_order.html',
                customer_id=customer_id,
                parts=parts,
                message="Invalid quantity."
            )

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT price FROM AutoPart WHERE part_id = %s", (pid,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            parts = list_parts()
            return render_template(
                'place_order.html',
                customer_id=customer_id,
                parts=parts,
                message="Invalid part ID."
            )

        price = row[0]
        total = price * quantity

        store_id = get_part_store()
        emp_id = get_employee_id(store_id)
        if not store_id or not emp_id:
            cur.close()
            conn.close()
            parts = list_parts()
            return render_template(
                'place_order.html',
                customer_id=customer_id,
                parts=parts,
                message="No store/employee found in DB."
            )

        # insert order + details...
    cur.execute("""
            INSERT INTO `Order`
            (customer_id, store_id, employee_id, order_date, delivery_date, total_amount, payment_status)
            VALUES (%s, %s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 3 DAY), %s, %s)
    """, (customer_id, store_id, emp_id, total, "Pending"))
    order_id = cur.lastrowid

    cur.execute("""
            INSERT INTO OrderDetail (order_id, part_id, quantity, subtotal)
            VALUES (%s, %s, %s, %s)
    """, (order_id, pid, quantity, total))

    conn.commit()
    cur.close()
    conn.close()

    flash(f"Order placed successfully! Order ID: {order_id} | Total: ${total}")
    return redirect(url_for('customer_menu', customer_id=customer_id))

    # GET: show form
    parts = list_parts()
    return render_template('place_order.html', customer_id=customer_id, parts=parts)

    # Show success message
    return render_template('place_order.html', customer_id=customer_id, message=f"Order placed successfully! Order ID: {order_id} | Total: ${total}")
    # Handle GET request (display form)
    return render_template('place_order.html', customer_id=customer_id)

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
    #relevant functions: list_parts, view_customer_orders, place_order
    #TODO: add button to place_order
    parts = list_parts()
    orders=view_customer_orders(customer_id)
    return render_template('customer_menu.html', parts=parts, orders=orders,   customer_id=customer_id)

# add part
@app.route('/add_part', methods=['GET', 'POST'])
def add_part():
    if request.method == 'POST':
        # Get form data from the HTML form
        name = request.form['name'].strip()
        cat = request.form['category'].strip()
        price_str = request.form['price'].strip()
        qty_str = request.form['quantity'].strip()
        cond = request.form['condition'].strip()
        

        # Validate numeric fields
        try:
            price = float(price_str)
            qty = int(qty_str)
        except ValueError:
            # Re-render the form with an error message
            return render_template(
                'add_part.html',
                message="Invalid price or quantity. Please enter numeric values.",
                name=name,
                category=cat,
                price=price_str,
                quantity=qty_str,
                condition=cond,
                
            )

        # Insert into database
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO AutoPart (part_name, category, price, stock_qty, `condition`)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, cat, price, qty, cond))

        conn.commit()
        cur.close()
        conn.close()

        # Show success message and clear form
        return render_template('add_part.html', message="Part added successfully!")

    # GET request → just show the empty form
    return render_template('add_part.html')


# view all orders
@app.route('/all_orders/<int:employee_id>')
def view_all_orders(employee_id):
    conn = get_connection()
    # dictionary=True is IMPORTANT so we can use order.customer_name, etc.
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            o.order_id,
            o.order_date,
            c.name       AS customer_name,
            s.store_name AS store_name,
            e.name       AS employee_name,
            p.part_name  AS part_name,
            od.quantity  AS quantity,
            od.subtotal  AS line_subtotal,
            o.total_amount,
            o.payment_status
        FROM `Order` o
        LEFT JOIN Customer    c  ON o.customer_id = c.customer_id
        LEFT JOIN Store       s  ON o.store_id    = s.store_id
        LEFT JOIN Employee    e  ON o.employee_id = e.employee_id
        LEFT JOIN OrderDetail od ON o.order_id    = od.order_id   -- CHANGE name if needed
        LEFT JOIN AutoPart    p  ON od.part_id    = p.part_id
        ORDER BY o.order_id DESC
    """)

    orders = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        'all_orders.html',
        orders=orders,
        employee_id=employee_id
    )
@app.route('/store_menu/<int:employee_id>')
def store_menu(employee_id):
    store_id = get_store_id(employee_id)
    return render_template('store_menu.html', store_id=store_id, employee_id=employee_id)

if __name__ == "__main__":
    app.run(debug = True)
