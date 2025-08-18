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
    ai_decision TEXT,
    FOREIGN KEY (account_number) REFERENCES customers(account_number)
)
''')

# --- UPDATED: 'customer_profile' table to match the training data ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS customer_profile (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_number TEXT NOT NULL UNIQUE,
    Age INTEGER,
    Income INTEGER,
    LoanAmount REAL,
    CreditScore INTEGER,
    MonthsEmployed INTEGER,
    NumCreditLines INTEGER,
    InterestRate REAL,
    LoanTerm INTEGER,
    DTIRatio REAL,
    Education TEXT,
    EmploymentType TEXT,
    MaritalStatus TEXT,
    HasMortgage TEXT,
    HasDependents TEXT,
    LoanPurpose TEXT,
    HasCoSigner TEXT,
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
    # (Agent and Supervisor data insertion remains the same)
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

    # (Customer insertion remains the same)
    all_customers_to_add = [
        ('Amit Sharma', 5200.00, 'ACC001', 'Mumbai', 'Regular', agent1_number),
        ('Priya Singh', 12000.00, 'ACC002', 'Pune', 'VIP', agent1_number)
    ]
    cursor.executemany(
        '''INSERT INTO customers (customer_name, due_amount, account_number, location, customer_type, assigned_agent_number)
           VALUES (?, ?, ?, ?, ?, ?)''', all_customers_to_add)
    
    # --- UPDATED: Add profile data for each customer that matches the model's needs ---
    profile_data_to_add = [
        # ACC001: A standard, low-risk profile
        ('ACC001', 35, 60000, 50000, 720, 60, 4, 12.5, 36, 0.5, "Bachelor's", 'Full-time', 'Married', 'Yes', 'Yes', 'Personal', 'No'),
        # ACC002: A slightly higher-risk profile
        ('ACC002', 28, 45000, 100000, 650, 24, 2, 18.0, 60, 0.8, "High School", 'Part-time', 'Single', 'No', 'No', 'Medical', 'No')
    ]
    cursor.executemany(
        '''INSERT INTO customer_profile (
            account_number, Age, Income, LoanAmount, CreditScore, MonthsEmployed, 
            NumCreditLines, InterestRate, LoanTerm, DTIRatio, Education, 
            EmploymentType, MaritalStatus, HasMortgage, HasDependents, LoanPurpose, HasCoSigner
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', profile_data_to_add)

    # (History data insertion remains the same)
    history_to_add = [
        ('ACC001', 50000, 5, '2025-06-15', 'Paid,Paid,Paid,Late,Paid', 'Open', None, None, None),
        ('ACC002', 100000, 8, '2025-07-01', 'Paid,Paid,Paid,Paid,Paid,Late,Paid,Paid', 'Open', None, None, None)
    ]
    cursor.executemany(
        '''INSERT INTO account_history (account_number, total_loan, emis_paid, last_payment_date, payment_record, status, agent_notes, supervisor_decision, ai_decision)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', history_to_add)

    print("Sample data added successfully.")
except sqlite3.IntegrityError:
    print("Sample data already exists, skipping insertion.")

connection.commit()
connection.close()