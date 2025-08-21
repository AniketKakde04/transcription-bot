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

# In db_utils.py

def get_customer_history(account_number, agent_number):
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    # --- THIS IS THE CORRECTED QUERY ---
    # It now includes c.customer_type in the SELECT statement
    cursor.execute('''
        SELECT c.customer_name, c.account_number, c.due_amount, c.location, c.customer_type, 
               h.total_loan, h.emis_paid, h.last_payment_date, h.payment_record, h.agent_notes
        FROM customers c
        JOIN account_history h ON c.account_number = h.account_number
        WHERE c.account_number = ? AND c.assigned_agent_number = ?
    ''', (account_number, agent_number))
    
    customer_details = cursor.fetchone()
    
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

# In db_utils.py

# (get_agent_and_customers, get_customer_history, and log_agent_notes remain the same)
# ...

def get_all_data_for_agent(agent_number):
    """
    Fetches all the feature data for every customer assigned to a specific agent,
    ready for the predictive model.
    """
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # --- UPDATED QUERY to fetch all features from the customer_profile table ---
    cursor.execute('''
        SELECT 
            c.customer_name, c.account_number,
            p.Age, p.Income, p.LoanAmount, p.CreditScore, p.MonthsEmployed, 
            p.NumCreditLines, p.InterestRate, p.LoanTerm, p.DTIRatio, p.Education,
            p.EmploymentType, p.MaritalStatus, p.HasMortgage, p.HasDependents, 
            p.LoanPurpose, p.HasCoSigner
        FROM customers c
        JOIN customer_profile p ON c.account_number = p.account_number
        WHERE c.assigned_agent_number = ?
    ''', (agent_number,))
    
    all_data = cursor.fetchall()
    connection.close()
    
    return [dict(row) for row in all_data]

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

# In db_utils.py

def create_communication_record(account_number, agent_number, supervisor_number, summary_report):
    """
    Creates a new record in the communications table for a supervisor to review.
    """
    connection = sqlite3.connect('loan_recovery.db')
    cursor = connection.cursor()

    try:
        cursor.execute('''
            INSERT INTO communications (account_number, agent_number, supervisor_number, summary_report)
            VALUES (?, ?, ?, ?)
        ''', (account_number, agent_number, supervisor_number, summary_report))
        connection.commit()
        success = True
    except Exception as e:
        print(f"Database Error creating communication record: {e}")
        success = False
    finally:
        connection.close()
    
    return success

# In db_utils.py

def get_pending_reports_for_supervisor(supervisor_number):
    """
    Fetches all communication records with a 'Pending' status for a specific supervisor.
    """
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT comm_id, account_number, agent_number, summary_report 
        FROM communications 
        WHERE supervisor_number = ? AND status = 'Pending'
    ''', (supervisor_number,))
    
    reports = cursor.fetchall()
    connection.close()
    return reports

# In db_utils.py

def submit_supervisor_decision(comm_id, decision):
    """
    Updates a communication record with the supervisor's decision, sets the 
    status to 'Resolved', and returns the details needed for notification.
    """
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Get the original agent's number and account number before updating
    cursor.execute("SELECT agent_number, account_number FROM communications WHERE comm_id = ?", (comm_id,))
    comm_details = cursor.fetchone()

    if not comm_details:
        connection.close()
        return None, None # Return nothing if the report ID is invalid

    try:
        # Update the communications table
        cursor.execute("UPDATE communications SET supervisor_decision = ?, status = 'Resolved' WHERE comm_id = ?", (decision, comm_id))
        
        # Also, update the main account_history table
        cursor.execute("UPDATE account_history SET supervisor_decision = ?, status = 'Resolved' WHERE account_number = ?", (decision, comm_details['account_number']))

        connection.commit()
        success = True
    except Exception as e:
        print(f"Database Error submitting decision: {e}")
        success = False
    finally:
        connection.close()
    
    if success:
        return comm_details['agent_number'], comm_details['account_number']
    else:
        return None, None
    
# --- NEW: Function to get all details for the triage logic ---
# In db_utils.py

# In db_utils.py

def get_supervisor_for_agent(agent_number):
    """Fetches the supervisor's number for a given agent."""
    connection = sqlite3.connect('loan_recovery.db')
    cursor = connection.cursor()
    cursor.execute("SELECT supervisor_number FROM agents WHERE whatsapp_number = ?", (agent_number,))
    supervisor_info = cursor.fetchone()
    connection.close()
    if supervisor_info:
        return supervisor_info[0]
    return None

def get_triage_details(account_number):
    """Fetches the necessary details for the triage logic, including the credit score."""
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute('''
        SELECT c.customer_type, p.CreditScore
        FROM customers c
        JOIN customer_profile p ON c.account_number = p.account_number
        WHERE c.account_number = ?
    ''', (account_number,))
    
    details = cursor.fetchone()
    connection.close()
    
    if details:
        return dict(details)
    return None

# --- NEW: Function to save the AI's decision ---
def save_ai_decision(account_number, decision):
    """Saves the AI's decision to the database and resolves the case."""
    connection = sqlite3.connect('loan_recovery.db')
    cursor = connection.cursor()
    try:
        cursor.execute('''
            UPDATE account_history
            SET ai_decision = ?, status = 'Resolved by AI'
            WHERE account_number = ?
        ''', (decision, account_number))
        connection.commit()
        success = True
    except Exception as e:
        print(f"Database Error saving AI decision: {e}")
        success = False
    finally:
        connection.close()
    return success

# In db_utils.py



def get_data_for_prediction(account_number):
    """
    Fetches all the feature data for a single customer, ready for the predictive model.
    """
    connection = sqlite3.connect('loan_recovery.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # --- UPDATED QUERY to fetch the correct columns from the new profile table ---
    cursor.execute('''
        SELECT 
            p.Age, p.Income, p.LoanAmount, p.CreditScore, p.MonthsEmployed, 
            p.NumCreditLines, p.InterestRate, p.LoanTerm, p.DTIRatio, p.Education,
            p.EmploymentType, p.MaritalStatus, p.HasMortgage, p.HasDependents, 
            p.LoanPurpose, p.HasCoSigner
        FROM customer_profile p
        WHERE p.account_number = ?
    ''', (account_number,))
    
    data = cursor.fetchone()
    connection.close()
    
    if data:
        return dict(data)
    return None