import sqlite3

connection = sqlite3.connect('loan_recovery.db')
cursor = connection.cursor()

# --- Create tables ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS agents (
    whatsapp_number TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    supervisor_number TEXT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    due_amount REAL NOT NULL,
    account_number TEXT NOT NULL UNIQUE,
    location TEXT,
    assigned_agent_number TEXT,
    FOREIGN KEY (assigned_agent_number) REFERENCES agents(whatsapp_number)
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS account_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_number TEXT NOT NULL UNIQUE,
    total_loan REAL NOT NULL,
    emis_paid INTEGER NOT NULL,
    last_payment_date TEXT,
    status TEXT DEFAULT 'Open',
    agent_notes TEXT,
    supervisor_decision TEXT,
    FOREIGN KEY (account_number) REFERENCES customers(account_number)
)
''')

# --- NEW: Create a detailed 'payments' table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_number TEXT NOT NULL,
    payment_date TEXT NOT NULL,
    amount_paid REAL NOT NULL,
    status TEXT NOT NULL,  -- e.g., 'On-Time', 'Late', 'Missed'
    FOREIGN KEY (account_number) REFERENCES customers(account_number)
)
''')

print("Tables checked/created successfully.")

# --- Add sample data ---
try:
    # Define the three agent numbers you provided
    agent1_number = 'whatsapp:+918766806290'
    agent2_number = 'whatsapp:+918149394348'
    supervisor_number = 'whatsapp:+918793217557'

    # 1. Add all agents to the 'agents' table
    agents_to_add = [
        (agent1_number, 'Aniket Kakde', supervisor_number),
        (agent2_number, 'Hrishikesh Kakde', supervisor_number),
        (supervisor_number, 'Supervisor Name', None) # Supervisor has no supervisor
    ]
    cursor.executemany("INSERT INTO agents (whatsapp_number, agent_name, supervisor_number) VALUES (?, ?, ?)", agents_to_add)

    # 2. Add all customers, assigning them to the correct agent
    all_customers_to_add = [
        # Customers for Agent 1 (Aniket)
        ('Amit Sharma', 5200.00, 'ACC001', 'Mumbai', agent1_number),
        ('Priya Singh', 12000.00, 'ACC002', 'Pune', agent1_number),

        # Customers for Agent 2 (Hrishikesh)
        ('Sanjay Gupta', 8100.75, 'ACC004', 'Delhi', agent2_number),
        ('Meera Devi', 4350.00, 'ACC005', 'Jaipur', agent2_number)
    ]
    cursor.executemany(
        '''INSERT INTO customers (customer_name, due_amount, account_number, location, assigned_agent_number)
           VALUES (?, ?, ?, ?, ?)''', all_customers_to_add)

    # 3. Add account history for all customers (without payment_record)
    history_to_add = [
        ('ACC001', 50000, 5, '2025-06-15', 'Open', None, None),
        ('ACC002', 100000, 8, '2025-07-01', 'Open', None, None),
        ('ACC004', 75000, 12, '2025-07-10', 'Open', None, None),
        ('ACC005', 20000, 2, '2025-05-20', 'Open', None, None)
    ]
    cursor.executemany(
        '''INSERT INTO account_history (account_number, total_loan, emis_paid, last_payment_date, status, agent_notes, supervisor_decision)
           VALUES (?, ?, ?, ?, ?, ?, ?)''', history_to_add)

    # 4. Add detailed payment history for each customer
    payments_to_add = [
        # Payments for ACC001
        ('ACC001', '2025-02-05', 5000, 'On-Time'),
        ('ACC001', '2025-03-05', 5000, 'On-Time'),
        ('ACC001', '2025-04-05', 5000, 'On-Time'),
        ('ACC001', '2025-05-10', 4800, 'Late'),
        ('ACC001', '2025-06-15', 5200, 'On-Time'),
        # Payments for ACC002
        ('ACC002', '2024-12-01', 10000, 'On-Time'),
        ('ACC002', '2025-01-01', 10000, 'On-Time'),
        ('ACC002', '2025-02-01', 10000, 'On-Time'),
        ('ACC002', '2025-03-01', 10000, 'On-Time'),
        ('ACC002', '2025-04-01', 10000, 'On-Time'),
        ('ACC002', '2025-05-08', 9000, 'Late'),
        ('ACC002', '2025-06-01', 10000, 'On-Time'),
        ('ACC002', '2025-07-01', 10000, 'On-Time'),
        # Payments for ACC004 and ACC005
        ('ACC004', '2025-07-10', 6250, 'On-Time'),
        ('ACC005', '2025-05-20', 10000, 'Late')
    ]
    cursor.executemany( '''INSERT INTO payments (account_number, payment_date, amount_paid, status) VALUES (?, ?, ?, ?)''', payments_to_add)
    
    print("Sample data for multiple agents added successfully.")
except sqlite3.IntegrityError:
    print("Sample data already exists, skipping insertion.")

connection.commit()
connection.close()