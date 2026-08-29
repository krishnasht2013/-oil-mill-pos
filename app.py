from flask import Flask, render_template, request, redirect, url_for, flash
from db_manager import DatabaseManager
from business_logic import InventoryManager, ProductionManager, CustomerManager, SalesManager

app = Flask(__name__)
app.secret_key = "oil_mill_secret_key"

# Initialize Business Logic
try:
    db = DatabaseManager()
    inv = InventoryManager(db)
    prod = ProductionManager(db, inv)
    cust = CustomerManager(db)
    sales = SalesManager(db, inv, cust)

    # Initialize products if empty
    # We wrap this in a try block so it doesn't crash the app if DB is briefly unavailable
    try:
        if not db.fetch_all("SELECT * FROM products"):
            print("Seeding initial products...")
            inv.add_product("Mustard Seeds", "Kg", 0.0)
            inv.add_product("Mustard Oil", "Litre", 160.0)
            inv.add_product("Oil Cake (Khal)", "Kg", 30.0)
            print("Initial products seeded successfully.")
    except Exception as e:
        print(f"Warning: Could not seed initial products: {e}")

except Exception as e:
    print(f"Critical Error during app initialization: {e}")
    # We keep the variables defined as None or similar to avoid NameError in routes,
    # but the app will likely return 500s on routes which is expected if DB is down.
    db = inv = prod = cust = sales = None

@app.route('/')
def index():
    if db is None:
        return "Critical Error: Database connection not established. Please check Render logs.", 500
    stock = inv.get_stock()
    total_sales_row = db.fetch_one("SELECT SUM(total_amount) as total FROM sales")
    total_sales = total_sales_row['total'] if total_sales_row and total_sales_row['total'] else 0
    total_credit_row = db.fetch_one("SELECT SUM(current_balance) as total FROM customers")
    total_credit = total_credit_row['total'] if total_credit_row and total_credit_row['total'] else 0
    return render_template('index.html', stock=stock, total_sales=total_sales, total_credit=total_credit)

@app.route('/production', methods=['GET', 'POST'])
def production():
    if request.method == 'POST':
        seeds = float(request.form['seeds'])
        oil = float(request.form['oil'])
        cake = float(request.form['cake'])
        prod.record_production(seeds, oil, cake)
        flash("Production recorded successfully!")
        return redirect(url_for('index'))
    return render_template('production.html')

@app.route('/sales', methods=['GET', 'POST'])
def sales_page():
    if request.method == 'POST':
        cust_id = int(request.form['customer_id'])
        qty = float(request.form['quantity'])
        price = float(request.form['price'])
        status = request.form['status']

        # Defaulting to Mustard Oil (ID 2) for this simple version
        sales.create_sale(cust_id, [(2, qty, price)], payment_status=status)
        flash("Sale completed!")
        return redirect(url_for('index'))

    customers = db.fetch_all("SELECT * FROM customers")
    return render_template('sales.html', customers=customers)

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        cust.add_customer(name, phone)
        flash("Customer added!")
        return redirect(url_for('customers'))

    customer_list = db.fetch_all("SELECT * FROM customers")
    return render_template('customers.html', customers=customer_list)

@app.route('/inventory')
def inventory():
    stock = inv.get_stock()
    return render_template('inventory.html', stock=stock)

if __name__ == '__main__':
    app.run(debug=True)
