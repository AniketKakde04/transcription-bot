import sqlite3

# Connect to the database (this will create the database file if it doesn't exist)
connection = sqlite3.connect('loan_recovery.db')
cursor = connection.cursor()

# --- Create agent table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS agents (
    whatsapp_number TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL
)
''')
print("'agents' table created successfully")

# --- Create customer table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    due_amount REAL NOT NULL,
    account_number TEXT NOT NULL,
    location TEXT,
    assigned_agent_number TEXT,
    FOREIGN KEY (assigned_agent_number) REFERENCES agents(whatsapp_number)
)
''')
print("'customers' table created successfully")

# --- Add sample data ---
try:
    cursor.execute(
        "INSERT INTO agents (whatsapp_number, agent_name) VALUES (?, ?)",
        ('whatsapp: +918766806290', 'Aniket Kakde')
    )

    customers_to_add = [
        ('Amit Sharma', 5200.00, 'ACC001', 'Mumbai', '+918766806290'),
        ('Priya Singh', 12000.00, 'ACC002', 'Pune', '+918766806290'),
        ('Rahul Sharma', 5200.00, 'ACC003', 'Nagpur', '+918766806290'),
    ]

    cursor.executemany(
        '''INSERT INTO customers (customer_name, due_amount, account_number, location, assigned_agent_number)
           VALUES (?, ?, ?, ?, ?)''',
        customers_to_add
    )
    print("Sample data added to 'customers' table successfully")

except sqlite3.IntegrityError:
    print("Sample data already exists, skipping insertion.")

# Save changes and close connection
connection.commit()
connection.close()
