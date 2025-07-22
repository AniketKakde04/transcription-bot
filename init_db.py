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

agent1_number = 'whatsapp:+918766806290'
agent2_number = 'whatsapp:+917410736635'

# --- Add sample data ---
try:

    agents_to_add = [(agent1_number, 'Aniket Kakde'),(agent2_number,'Hrutanshu Kunarkar')]

    cursor.executemany(
        "INSERT INTO agents (whatsapp_number, agent_name) VALUES (?, ?)",
        (agents_to_add)
    )

    all_customers_to_add = [
        ('Amit Sharma', 5200.00, 'ACC001', 'Mumbai', agent1_number),
        ('Rahul Raut', 6200.00, 'ACC002', 'Nashik', agent1_number),

        ('Priya Singh', 12000.00, 'ACC003', 'Pune', agent2_number),
        ('Rahul Sharma', 5200.00, 'ACC004', 'Nagpur', agent2_number),
    ]

    cursor.executemany(
        '''INSERT INTO customers (customer_name, due_amount, account_number, location, assigned_agent_number)
           VALUES (?, ?, ?, ?, ?)''',
        all_customers_to_add
    )
    print("Sample data added to 'customers' table successfully")

except sqlite3.IntegrityError:
    print("Sample data already exists, skipping insertion.")

# Save changes and close connection
connection.commit()
connection.close()
