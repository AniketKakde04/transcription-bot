import sqlite3

def get_agent_and_customers(agent_number):
    """
    Fetches agent details and a list of their customers in one function.
    """
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row  # This allows us to access columns by name
    cursor = connection.cursor()
    
    # First, get the agent's name
    cursor.execute("SELECT agent_name FROM agents WHERE whatsapp_number = ?", (agent_number,))
    agent = cursor.fetchone()
    
    # If an agent was found, get their customers
    customers = []
    if agent:
        cursor.execute("SELECT customer_name, due_amount, account_number, location FROM customers WHERE assigned_agent_number = ?", (agent_number,))
        customers = cursor.fetchall()
    
    connection.close()
    
    # Return both the agent's data and their list of customers
    return agent, customers

def get_customer_history(account_number, agent_number):
    """
    Fetches combined details for a customer account, but only if it's 
    assigned to the requesting agent.
    """
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # --- THIS IS THE KEY CHANGE ---
    # The JOIN now ensures the account belongs to the agent asking for it.
    cursor.execute('''
        SELECT c.customer_name, c.due_amount, c.location, h.total_loan, h.emis_paid, h.last_payment_date, h.payment_record
        FROM customers c
        JOIN account_history h ON c.account_number = h.account_number
        WHERE c.account_number = ? AND c.assigned_agent_number = ?
    ''', (account_number, agent_number))
    
    customer_details = cursor.fetchone()
    connection.close()
    return customer_details

def log_agent_notes(account_number, agent_number, notes):
    """
    Logs notes for a specific account and sets its status to 'Pending Review'.
    First, it verifies the agent has permission to update this account.
    """
    connection = sqlite3.connect('loan_recovery.db')
    cursor = connection.cursor()

    # Security Check: Verify the customer is assigned to the agent
    cursor.execute("SELECT customer_id FROM customers WHERE account_number = ? AND assigned_agent_number = ?", (account_number, agent_number))
    customer = cursor.fetchone()

    if customer:
        # If authorized, update the account history
        cursor.execute('''
            UPDATE account_history
            SET agent_notes = ?, status = 'Pending Review'
            WHERE account_number = ?
        ''', (notes, account_number))
        connection.commit()
        connection.close()
        return True # Indicates success
    else:
        # If not authorized, do nothing
        connection.close()
        return False # Indicates failure
def get_all_data_for_agent(agent_number):
    """
    Fetches all combined customer and history data for every customer
    assigned to a specific agent.
    """
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute('''
        SELECT c.customer_name, c.due_amount, c.account_number, c.location, 
               h.total_loan, h.emis_paid, h.last_payment_date, h.payment_record
        FROM customers c
        JOIN account_history h ON c.account_number = h.account_number
        WHERE c.assigned_agent_number = ?
    ''', (agent_number,))
    
    all_customer_data = cursor.fetchall()
    connection.close()
    return all_customer_data

# In db_utils.py

# ... (keep the existing functions) ...

def get_full_case_details(account_number, supervisor_number):
    """
    Fetches all details for a specific case, but only if the customer
    is assigned to an agent that reports to the given supervisor.
    """
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # This secure query joins all tables and verifies the supervisor's authority
    cursor.execute('''
        SELECT c.customer_name, c.account_number, c.due_amount, c.location,
               h.total_loan, h.emis_paid, h.last_payment_date, h.payment_record, h.agent_notes
        FROM customers c
        JOIN account_history h ON c.account_number = h.account_number
        JOIN agents a ON c.assigned_agent_number = a.whatsapp_number
        WHERE c.account_number = ? AND a.supervisor_number = ?
    ''', (account_number, supervisor_number))
    
    details = cursor.fetchone()
    connection.close()
    return details