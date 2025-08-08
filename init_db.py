import sqlite3
import bcrypt

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
CREATE TABLE IF NOT EXISTS supervisors (
    whatsapp_number TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    FOREIGN KEY (whatsapp_number) REFERENCES agents(whatsapp_number)
)
''')

# UPDATED: 'customers' table now includes 'customer_type'
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    due_amount REAL NOT NULL,
    account_number TEXT NOT NULL UNIQUE,
    location TEXT,
    customer_type TEXT DEFAULT 'Regular',
    assigned_agent_number TEXT,
    FOREIGN KEY (assigned_agent_number) REFERENCES agents(whatsapp_number)
)
''')

# UPDATED: 'account_history' table now includes 'ai_decision'
cursor.execute('''
CREATE TABLE IF NOT EXISTS account_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_number TEXT NOT NULL UNIQUE,
    total_loan REAL NOT NULL,
    emis_paid INTEGER NOT NULL,
    last_payment_date TEXT,
    payment_record TEXT,
    status TEXT DEFAULT 'Open',
    agent_notes TEXT,
    supervisor_decision TEXT,
    ai_decision TEXT, -- NEW: To store the AI's decision
    FOREIGN KEY (account_number) REFERENCES customers(account_number)
)
''')
# (communications table remains the same)
cursor.execute('''
CREATE TABLE IF NOT EXISTS communications (
    comm_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_number TEXT NOT NULL,
    agent_number TEXT NOT NULL,
    supervisor_number TEXT NOT NULL,
    summary_report TEXT NOT NULL,
    supervisor_decision TEXT,
    status TEXT DEFAULT 'Pending',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_number) REFERENCES customers(account_number),
    FOREIGN KEY (agent_number) REFERENCES agents(whatsapp_number),
    FOREIGN KEY (supervisor_number) REFERENCES agents(whatsapp_number)
)
''')

print("Tables checked/created successfully.")

# --- Add sample data ---
try:
    agent1_number = 'whatsapp:+918766806290'
    agent2_number = 'whatsapp:+918149394348'
    supervisor_number = 'whatsapp:+918793217557'
    supervisor_password = 'root@123'

    agents_to_add = [
        (agent1_number, 'Aniket Kakde', supervisor_number),
        (agent2_number, 'Hrishikesh Kakde', supervisor_number),
        (supervisor_number, 'Supervisor Name', None)
    ]
    cursor.executemany("INSERT INTO agents (whatsapp_number, agent_name, supervisor_number) VALUES (?, ?, ?)", agents_to_add)

    password_bytes = supervisor_password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
    cursor.execute("INSERT INTO supervisors (whatsapp_number, password_hash) VALUES (?, ?)",(supervisor_number, hashed_password))

    all_customers_to_add = [
        ('Amit Sharma', 5200.00, 'ACC001', 'Mumbai', 'Regular', agent1_number),
        ('Priya Singh', 12000.00, 'ACC002', 'Pune', 'VIP', agent1_number),
        ('Kavita Rao', 18000.00, 'ACC003', 'Nagpur', 'Staff', agent1_number),
        ('Sanjay Gupta', 8100.75, 'ACC004', 'Delhi', 'Regular', agent2_number),
        ('Meera Devi', 4350.00, 'ACC005', 'Jaipur', 'VIP', agent2_number)
    ]
    cursor.executemany(
        '''INSERT INTO customers (customer_name, due_amount, account_number, location, customer_type, assigned_agent_number)
           VALUES (?, ?, ?, ?, ?, ?)''', all_customers_to_add)

    history_to_add = [
        ('ACC001', 50000, 5, '2025-06-15', 'Paid,Paid,Paid,Late,Paid', 'Open', None, None, None),
        ('ACC002', 100000, 8, '2025-07-01', 'Paid,Paid,Paid,Paid,Paid,Late,Paid,Paid', 'Open', None, None, None),
        ('ACC003', 200000, 10, '2025-07-05', 'Paid,Paid,Paid,Paid,Paid,Paid,Paid,Paid,Paid,Paid', 'Open', None, None, None),
        ('ACC004', 75000, 12, '2025-07-10', 'Paid,Paid,Paid,Paid,Paid,Paid,Paid,Paid,Paid,Paid,Paid,Paid', 'Open', None, None, None),
        ('ACC005', 20000, 2, '2025-05-20', 'Paid,Late', 'Open', None, None, None)
    ]
    cursor.executemany(
        '''INSERT INTO account_history (account_number, total_loan, emis_paid, last_payment_date, payment_record, status, agent_notes, supervisor_decision, ai_decision)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', history_to_add)
    
    print("Sample data added successfully.")
except sqlite3.IntegrityError:
    print("Sample data already exists, skipping insertion.")

connection.commit()
connection.close()