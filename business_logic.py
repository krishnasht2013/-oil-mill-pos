from db_manager import DatabaseManager
from datetime import datetime

class InventoryManager:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def add_product(self, name, unit, default_price):
        """Adds a new product and initializes its inventory."""
        # Use RETURNING id for PostgreSQL
        result = self.db.execute_query(
            "INSERT INTO products (name, unit, default_price) VALUES (%s, %s, %s) RETURNING id",
            (name, unit, default_price)
        )
        product_id = result[0][0] if result else None
        if product_id:
            self.db.execute_query(
                "INSERT INTO inventory (product_id, quantity) VALUES (%s, 0)",
                (product_id,)
            )
        return product_id

    def update_stock(self, product_id, amount):
        """Updates the quantity of a product in stock."""
        self.db.execute_query(
            "UPDATE inventory SET quantity = quantity + %s WHERE product_id = %s",
            (amount, product_id)
        )

    def get_stock(self, product_id=None):
        """Returns stock for a specific product or all products."""
        if product_id:
            row = self.db.fetch_one(
                "SELECT p.name, i.quantity, p.unit FROM inventory i JOIN products p ON i.product_id = p.id WHERE p.id = %s",
                (product_id,)
            )
            return row
        return self.db.fetch_all("SELECT p.name, i.quantity, p.unit FROM inventory i JOIN products p ON i.product_id = p.id")

class ProductionManager:
    def __init__(self, db: DatabaseManager, inv_manager: InventoryManager):
        self.db = db
        self.inv_manager = inv_manager

    def record_production(self, seeds_used, oil_produced, cake_produced):
        """Records production and updates inventory for seeds, oil, and cake."""
        # 1. Log the production
        self.db.execute_query(
            "INSERT INTO production (seeds_used, oil_produced, cake_produced) VALUES (%s, %s, %s)",
            (seeds_used, oil_produced, cake_produced)
        )

        # 2. Update inventories
        seed_prod = self.db.fetch_one("SELECT id FROM products WHERE name LIKE '%Seed%'")
        oil_prod = self.db.fetch_one("SELECT id FROM products WHERE name LIKE '%Oil%'")
        cake_prod = self.db.fetch_one("SELECT id FROM products WHERE name LIKE '%Cake%'")

        if seed_prod:
            self.inv_manager.update_stock(seed_prod['id'], -seeds_used)
        if oil_prod:
            self.inv_manager.update_stock(oil_prod['id'], oil_produced)
        if cake_prod:
            self.inv_manager.update_stock(cake_prod['id'], cake_produced)

        return True

class CustomerManager:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def add_customer(self, name, phone):
        # Use RETURNING id for PostgreSQL
        result = self.db.execute_query(
            "INSERT INTO customers (name, phone) VALUES (%s, %s) RETURNING id",
            (name, phone)
        )
        return result[0][0] if result else None

    def update_balance(self, customer_id, amount):
        """Adds to customer balance (credit). Positive amount = owes more, negative = paid."""
        self.db.execute_query(
            "UPDATE customers SET current_balance = current_balance + %s WHERE id = %s",
            (amount, customer_id)
        )

    def get_customer_details(self, customer_id):
        return self.db.fetch_one("SELECT * FROM customers WHERE id = %s", (customer_id,))

class SalesManager:
    def __init__(self, db: DatabaseManager, inv_manager: InventoryManager, cust_manager: CustomerManager):
        self.db = db
        self.inv_manager = inv_manager
        self.cust_manager = cust_manager

    def create_sale(self, customer_id, items, payment_status='Paid'):
        """
        items: List of tuples (product_id, quantity, unit_price)
        """
        total_amount = sum(item[1] * item[2] for item in items)

        # 1. Create Sale Header - Use RETURNING id for PostgreSQL
        result = self.db.execute_query(
            "INSERT INTO sales (customer_id, total_amount, payment_status) VALUES (%s, %s, %s) RETURNING id",
            (customer_id, total_amount, payment_status)
        )
        sale_id = result[0][0] if result else None

        # 2. Create Sale Items & Update Inventory
        for product_id, quantity, unit_price in items:
            self.db.execute_query(
                "INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                (sale_id, product_id, quantity, unit_price)
            )
            self.inv_manager.update_stock(product_id, -quantity)

        # 3. Handle Credit
        if payment_status == 'Credit':
            self.cust_manager.update_balance(customer_id, total_amount)
        elif payment_status == 'Partial':
            pass

        return sale_id
