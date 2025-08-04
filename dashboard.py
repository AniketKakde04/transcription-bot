import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import bcrypt

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
# ...existing code...

# ...existing code...

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = None  # Add this line
    if form.validate_on_submit():
        conn = sqlite3.connect('loan_recovery.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM supervisors WHERE whatsapp_number = ?", (form.whatsapp_number.data,))
        supervisor = cursor.fetchone()
        conn.close()

        if supervisor:
            password_bytes = form.password.data.encode('utf-8')
            stored_hash = supervisor['password_hash'].encode('utf-8')
            if bcrypt.checkpw(password_bytes, stored_hash):
                # Fetch supervisor name from agents table
                conn = sqlite3.connect('loan_recovery.db')
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT agent_name FROM agents WHERE whatsapp_number = ?", (form.whatsapp_number.data,))
                agent_row = cursor.fetchone()
                conn.close()
                supervisor_name = agent_row['agent_name'] if agent_row else "Supervisor"
                session['supervisor_number'] = supervisor['whatsapp_number']
                session['supervisor_name'] = supervisor_name
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid password."  # Set error message
        else:
            error = "Supervisor not found."  # Set error message
    return render_template('login.html', form=form, error=error)
# ...existing code...
# ...existing code...

# ...existing code...

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'supervisor_number' not in session:
        return redirect(url_for('login'))

    supervisor_number = session['supervisor_number']
    supervisor_name = session['supervisor_name']

    if request.method == 'POST':
        comm_id = request.form.get('comm_id')
        decision = request.form.get('decision')
        if comm_id and decision:
            agent_to_notify, account_number = submit_supervisor_decision(comm_id, decision)
            if agent_to_notify:
                notification_body = f"Your supervisor has reviewed the case for *{account_number}*.\n\n*Decision:* {decision}"
                send_whatsapp_message(agent_to_notify, notification_body)
            return redirect(url_for('dashboard'))

    reports = get_pending_reports_for_supervisor(supervisor_number)
    return render_template('dashboard.html', reports=reports, supervisor_name=supervisor_name)

# Optionally, redirect '/' to '/dashboard'
@app.route('/')
def home():
    return redirect(url_for('dashboard'))

# ...existing code...

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(port=5001, debug=True)