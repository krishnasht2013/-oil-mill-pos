from db_manager import DatabaseManager
from business_logic import InventoryManager, ProductionManager, CustomerManager, SalesManager

def main():
    db = DatabaseManager()
    inv = InventoryManager(db)
    prod = ProductionManager(db, inv)
    cust = CustomerManager(db)
    sales = SalesManager(db, inv, cust)

    # Initialize basic products if none exist
    if not db.fetch_all("SELECT * FROM products"):
        print("Initializing basic product list...")
        inv.add_product("Mustard Seeds", "Kg", 0.0) # Raw material, price usually internal
        inv.add_product("Mustard Oil", "Litre", 160.0)
        inv.add_product("Oil Cake (Khal)", "Kg", 30.0)

    while True:
        print("\n--- MUSTARD OIL MILL POS ---")
        print("1. Record Production")
        print("2. New Sale")
        print("3. Add Customer")
        print("4. Check Inventory")
        print("5. Customer Balances")
        print("6. Exit")

        choice = input("Select an option: ")

        if choice == '1':
            seeds = float(input("Enter Seeds Used (Kg): "))
            oil = float(input("Enter Oil Produced (L): "))
            cake = float(input("Enter Cake Produced (Kg): "))
            prod.record_production(seeds, oil, cake)
            print("Production recorded successfully!")

        elif choice == '2':
            cust_id = int(input("Enter Customer ID (or 0 for Guest): "))
            # For simplicity, we'll sell Mustard Oil (Product ID 2)
            qty = float(input("Quantity of Oil (L): "))
            price = float(input("Price per Litre: "))
            status = input("Payment Status (Paid/Credit): ")

            # Assuming Product ID 2 is Mustard Oil
            sales.create_sale(cust_id, [(2, qty, price)], payment_status=status)
            print("Sale completed!")

        elif choice == '3':
            name = input("Customer Name: ")
            phone = input("Phone Number: ")
            cid = cust.add_customer(name, phone)
            print(f"Customer added with ID: {cid}")

        elif choice == '4':
            stock = inv.get_stock()
            print("\n--- Current Inventory ---")
            for item in stock:
                print(f"{item['name']}: {item['quantity']} {item['unit']}")

        elif choice == '5':
            customers = db.fetch_all("SELECT * FROM customers")
            print("\n--- Customer Balances ---")
            for c in customers:
                print(f"ID: {c['id']} | {c['name']} | Balance: {c['current_balance']}")

        elif choice == '6':
            print("Exiting...")
            db.close()
            break
        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    main()
