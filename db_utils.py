import sqlite3

def get_agent_and_customers(agent_number):
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT agent_name FROM agents WHERE whatsapp_number = ?", (agent_number,))
    agent = cursor.fetchone()
    customers = []
    if agent:
        cursor.execute("SELECT customer_name, due_amount, account_number, location FROM customers WHERE assigned_agent_number = ?", (agent_number,))
        customers = cursor.fetchall()
    connection.close()
    return agent, customers

# In db_utils.py

# In db_utils.py

def get_customer_history(account_number, agent_number):
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT c.customer_name, c.account_number, c.due_amount, c.location, h.total_loan, h.emis_paid, h.last_payment_date, h.payment_record, h.agent_notes
        FROM customers c
        JOIN account_history h ON c.account_number = h.account_number
        WHERE c.account_number = ? AND c.assigned_agent_number = ?
    ''', (account_number, agent_number))
    
    customer_details = cursor.fetchone()
    
    # --- THIS IS THE KEY FIX ---
    # Convert the sqlite3.Row object to a standard Python dictionary before returning
    if customer_details:
        customer_details = dict(customer_details)

    connection.close()
    return customer_details

def log_agent_notes(account_number, agent_number, notes):
    connection = sqlite3.connect('loan_recovery.db')
    cursor = connection.cursor()
    cursor.execute("SELECT customer_id FROM customers WHERE account_number = ? AND assigned_agent_number = ?", (account_number, agent_number))
    customer = cursor.fetchone()
    if customer:
        cursor.execute("UPDATE account_history SET agent_notes = ?, status = 'Pending Review' WHERE account_number = ?", (notes, account_number))
        connection.commit()
        connection.close()
        return True
    else:
        connection.close()
        return False

def get_all_data_for_agent(agent_number):
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute('''
        SELECT c.customer_name, c.due_amount, c.account_number, h.payment_record
        FROM customers c
        JOIN account_history h ON c.account_number = h.account_number
        WHERE c.assigned_agent_number = ?
    ''', (agent_number,))
    
    all_customer_data = cursor.fetchall()
    connection.close()
    return all_customer_data

def get_full_case_details(account_number, supervisor_number):
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute('''
        SELECT c.customer_name, c.account_number, c.due_amount, h.total_loan, h.agent_notes, h.payment_record
        FROM customers c
        JOIN account_history h ON c.account_number = h.account_number
        JOIN agents a ON c.assigned_agent_number = a.whatsapp_number
        WHERE c.account_number = ? AND a.supervisor_number = ?
    ''', (account_number, supervisor_number))
    
    details = cursor.fetchone()
    connection.close()
    return details