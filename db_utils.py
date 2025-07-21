import sqlite3

def get_customers_by_agent(agent_number):
    """"Fetches a list of customers assigned to a specific agent."""
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT customer_name,due_amount,account_number,location FROM customers WHERE assigned_agent_number =?", (agent_number,)) 
    customers = cursor.fetchall()
    connection.close()
    return customers