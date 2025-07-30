import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

# --- 1. IMPORT THE MISSING FUNCTIONS ---
from db_utils import get_pending_reports_for_supervisor, submit_supervisor_decision
from twilio_utils import send_whatsapp_message # <-- ADD THIS IMPORT

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key'

class LoginForm(FlaskForm):
    """A simple login form."""
    whatsapp_number = StringField('WhatsApp Number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        conn = sqlite3.connect('loan_recovery.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agents WHERE whatsapp_number = ? AND supervisor_number IS NULL", (form.whatsapp_number.data,))
        supervisor = cursor.fetchone()
        conn.close()
        
        if supervisor:
            session['supervisor_number'] = supervisor['whatsapp_number']
            session['supervisor_name'] = supervisor['agent_name']
            return redirect(url_for('dashboard'))
        else:
            return "Login Failed. Make sure you are a registered supervisor."
            
    return render_template('login.html', form=form)

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    if 'supervisor_number' not in session:
        return redirect(url_for('login'))

    supervisor_number = session['supervisor_number']
    supervisor_name = session['supervisor_name']

    # --- 2. THIS IS THE CORRECTED LOGIC ---
    if request.method == 'POST':
        comm_id = request.form.get('comm_id')
        decision = request.form.get('decision')
        if comm_id and decision:
            # The function now returns the agent's number and account number
            agent_to_notify, account_number = submit_supervisor_decision(comm_id, decision)
            
            if agent_to_notify:
                # If the decision was saved, send the notification
                notification_body = f"Your supervisor has reviewed the case for *{account_number}*.\n\n*Decision:* {decision}"
                send_whatsapp_message(agent_to_notify, notification_body)
            
            return redirect(url_for('dashboard'))

    # Fetch all pending reports for this supervisor
    reports = get_pending_reports_for_supervisor(supervisor_number)
    
    return render_template('dashboard.html', reports=reports, supervisor_name=supervisor_name)

if __name__ == '__main__':
    app.run(port=5001, debug=True)