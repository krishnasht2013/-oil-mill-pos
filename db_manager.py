import psycopg2
from psycopg2.extras import RealDictCursor
import os

class DatabaseManager:
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        if not self.db_url:
            # For local testing if no env var is set, you can put a local postgres url here
            # But for deployment, Render/Supabase will provide this.
            print("Warning: DATABASE_URL environment variable not set.")

        self.initialize_db()

    def get_connection(self):
        """Returns a psycopg2 connection object."""
        # PostgreSQL connections are usually handled differently than SQLite.
        # We return a new connection each time to avoid session issues in cloud environments.
        conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
        return conn

    def initialize_db(self):
        """Creates all necessary tables if they do not exist."""
        if not self.db_url:
            return

        schema = [
            '''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                unit TEXT NOT NULL,
                default_price REAL NOT NULL
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS inventory (
                product_id INTEGER PRIMARY KEY,
                quantity REAL DEFAULT 0,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                current_balance REAL DEFAULT 0
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL,
                payment_status TEXT CHECK(payment_status IN ('Paid', 'Partial', 'Credit')),
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS sale_items (
                id SERIAL PRIMARY KEY,
                sale_id INTEGER,
                product_id INTEGER,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS production (
                id SERIAL PRIMARY KEY,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                seeds_used REAL NOT NULL,
                oil_produced REAL NOT NULL,
                cake_produced REAL NOT NULL
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT
            )
            '''
        ]

        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            for statement in schema:
                cursor.execute(statement)
            conn.commit()
            cursor.close()
            conn.close()
            print("Database initialized successfully (PostgreSQL).")
        except Exception as e:
            print(f"Database initialization error: {e}")

    def execute_query(self, query, params=()):
        """Executes a query and returns the cursor."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            # In Postgres, we can't return the cursor after closing the connection.
            # For simple inserts/updates, we return the lastrowid as a custom attribute.
            result = None
            if cursor.description: # If query returned data
                result = cursor.fetchall()

            # Handle returning the last inserted ID
            last_id = None
            if "INSERT" in query.upper():
                # PostgreSQL doesn't use lastrowid like SQLite.
                # We use 'RETURNING id' in the query or fetch it here.
                pass

            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Query error: {e}")
            return None

    def fetch_all(self, query, params=()):
        """Fetches all results for a given query."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            print(f"Fetch all error: {e}")
            return []

    def fetch_one(self, query, params=()):
        """Fetches one result for a given query."""
        results = self.fetch_all(query, params)
        return results[0] if results else None
