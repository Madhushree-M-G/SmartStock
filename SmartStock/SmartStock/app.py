from flask import *
import sqlite3
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import sqlite3
from datetime import datetime

def generate_bill_reportlab(row, output_filename="static/bill.pdf"):
    
    category, item, location, description, price = row
    
    # Create PDF
    c = canvas.Canvas(output_filename, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height-50, "INVOICE / BILL")
    
    # Bill info
    c.setFont("Helvetica", 12)
    c.drawString(50, height-80, f"Bill Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Item details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height-130, "Item Details:")
    
    c.setFont("Helvetica", 12)
    y_position = height-160
    details = [
        ("Item:", category),
        ("Category:", item),
        ("Location:", location),
        ("Description:", description),
        ("Price:", f"Rs. {price}")
    ]
    
    for label, value in details:
        c.drawString(50, y_position, f"{label} {value}")
        y_position -= 20
    
    # Total
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position-30, f"Total: ${price}")
    
    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(width/2, 50, "Thank you for your business!")
    
    # Save
    c.save()
    print(f"Bill generated successfully: {output_filename}")

conn = sqlite3.connect("inventory.db")
cursor = conn.cursor()

# Create the table
create_table_query = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    item TEXT,
    quantity INTEGER,
    location TEXT,
    description TEXT,
    price TEXT,
    image TEXT
);
"""
cursor.execute(create_table_query)

create_table_query = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    password TEXT
);
"""
cursor.execute(create_table_query)

create_table_query = """
CREATE TABLE IF NOT EXISTS orders (
    id TEXT,
    category TEXT,
    item TEXT,
    quantity INTEGER,
    location TEXT,
    description TEXT,
    price TEXT,
    image TEXT,
    email TEXT
);
"""
cursor.execute(create_table_query)

conn.commit()
conn.close()


app = Flask(__name__)
app.secret_key = 'qwertyuiopasdfghjklzxcvbnm'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user_login', methods=['POST', 'GET'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()
        cursor.execute("select * from users where email = ? and password = ?", [email, password])
        result = cursor.fetchall()
        if result:
            session['email'] = email
            return redirect(url_for('user_dashboard'))
        else:
            return render_template('user_login.html')
    return render_template('user_login.html')

@app.route('/user_signup', methods=['POST', 'GET'])
def user_signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()
        cursor.execute("insert into users values (NULL,?,?)", [email, password])
        conn.commit()
        conn.close()
        return render_template('user_login.html')
    return render_template('user_signup.html')

@app.route('/user_dashboard')
def user_dashboard():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    from datetime import datetime
    current_date = datetime.now()
    formatted_date = current_date.strftime("%B %d, %Y")
    print(formatted_date)

    cursor.execute("select * from orders where email = '"+session['email']+"' ")
    result = cursor.fetchall()

    cursor.execute("select * from items")
    items = cursor.fetchall()

    cursor.execute("select * from users")
    users = cursor.fetchall()
    return render_template('user_dashboard.html', total_users = len(users), email = session['email'], formatted_date=formatted_date, result=result, total_orders = len(result), total_items=len(items))

@app.route('/user_inventory')
def user_inventory():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("select * from items")
    result = cursor.fetchall()
    if result:
        return render_template('user_inventory.html', result=result, total_items=len(result))
    else:
        return render_template('user_inventory.html', result=result, total_items=0)

@app.route('/admin_login', methods=['POST', 'GET'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == 'admin@gmail.com' and password == 'admin123':
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html')
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():

    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("select * from items")
    items = cursor.fetchall()

    cursor.execute("select * from users")
    users = cursor.fetchall()

    cursor.execute("select * from orders")
    orders = cursor.fetchall()

    cursor.execute("select * from items where description = 'low stock'")
    low_stocks = cursor.fetchall()

    cursor.execute("select * from items where description = 'in stock'")
    in_stocks = cursor.fetchall()

    cursor.execute("select * from items where description = 'out of stock'")
    out_stocks = cursor.fetchall()
    return render_template('admin_dashboard.html', outofstocs = len(out_stocks), lowstocs = len(low_stocks), instocs = len(in_stocks), total_users = len(users), total_orders = len(orders), total_items=len(items))

@app.route('/admin_inventory')
def admin_inventory():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("select * from items")
    result = cursor.fetchall()
    if result:
        return render_template('admin_inventory.html', result=result, total_items=len(result))
    else:
        return render_template('admin_inventory.html', result=result, total_items=0)

@app.route('/delete_item/<item_id>')
def delete_item(item_id):
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("delete from items where id = ?", [item_id])
    conn.commit()
    conn.close()
    return redirect(url_for('admin_inventory'))

@app.route('/add_item', methods=['POST', 'GET'])
def add_item():
    if request.method == 'POST':
        data = request.form

        values = []
        for key in data:
            values.append(data[key])
        print(values)

        f = request.files['image']
        file_content = f.read()
        my_string = base64.b64encode(file_content).decode('utf-8')
        values.append(my_string)

        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()

        
        print(values[0], values[1])
        cursor.execute("select * from items where category = ? and item = ?", [values[1], values[0]])
        res = cursor.fetchone()

        if res:
            q = int(res[3])
            q1 = q + int(values[2])

            if q1 <= 0:
                st = 'out of stock'
            elif q1 > 0 and q1 < 100:
                st = 'low stock'
            else:
                st = 'in stock'

            cursor.execute("update items set quantity = ?, description = ? where id = ?", [q1, st, res[0]])
        else:
            insert_query = """
            INSERT INTO items (item, category, quantity, location, description, price, image)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """
            cursor.execute(insert_query, values)
        conn.commit()
        conn.close()
        return redirect(url_for('admin_inventory'))
    return redirect(url_for('admin_inventory'))

@app.route('/buy_item/<item_id>')
def buy_item(item_id):
    session['item_id'] = item_id
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("select * from items where id = ?", [item_id])
    row = list(cursor.fetchone())

    amount = row[6]
    conn.close()
    return render_template('payment.html', amount=amount)

@app.route('/payment', methods=['POST'])
def payment():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    item_id = session['item_id']

    cursor.execute("select * from items where id = ?", [item_id])
    row = list(cursor.fetchone())

    q = int(row[3])
    q1 = q - 1

    if q1 <= 0:
        st = 'out of stock'
    elif q1 > 0 and q1 < 100:
        st = 'low stock'
    else:
        st = 'in stock'

    cursor.execute("update items set quantity = ?, description = ? where id = ?", [q1, st, item_id])
    conn.commit()

    row.append(session['email'])
    cursor.execute("insert into orders values (?,?,?,?,?,?,?,?,?)", row)
    conn.commit()

    cursor.execute("select category, item, location, description, price from items where id = ?", [item_id])
    row = list(cursor.fetchone())
    generate_bill_reportlab(row)
    cursor.execute("select * from items")
    result = cursor.fetchall()
    conn.close()
    if result:
        return render_template('user_inventory.html', result=result, total_items=len(result), bill='http://127.0.0.1:5000/static/bill.pdf')
    else:
        return render_template('user_inventory.html', result=result, total_items=0, bill='http://127.0.0.1:5000/static/bill.pdf')

if __name__ =="__main__":
    app.run(debug=True)