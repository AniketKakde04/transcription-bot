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