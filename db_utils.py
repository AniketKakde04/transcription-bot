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