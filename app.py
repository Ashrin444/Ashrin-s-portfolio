import os
import re
from datetime import datetime

import requests
from flask import Flask, render_template, request
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy

# ===============================
# FLASK APP CONFIGURATION
# ===============================

app = Flask(__name__)

# Secret Key (from environment)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')

# ===============================
# DATABASE CONFIGURATION
# ===============================

# SQLite is OK for portfolio (Render filesystem is ephemeral but works)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ===============================
# EMAIL CONFIGURATION (ENV VARS)
# ===============================

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# ===============================
# DATABASE MODEL
# ===============================

class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(13), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    reason = db.Column(db.String(300), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Contact {self.name}>"

# ===============================
# CREATE TABLES (SAFE)
# ===============================

with app.app_context():
    db.create_all()

# ===============================
# HELPER FUNCTIONS
# ===============================

def get_projects():
    try:
        api_url = "https://api.github.com/users/Ashrin444/repos"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []

# ===============================
# ERROR HANDLERS
# ===============================

@app.errorhandler(404)
def err_404(error):
    return render_template('error.html', message='404 Page Not Found'), 404

@app.errorhandler(500)
def err_500(error):
    return render_template('error.html', message='Internal Server Error'), 500

# ===============================
# ROUTES
# ===============================

@app.route('/')
def main_page():
    return render_template('index.html', title='Ashrin Lazer A - Homepage')

@app.route('/contact', methods=['GET', 'POST'])
def contact_page():
    contact_status = None

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        reason = request.form.get('reason', '').strip()

        # Validation
        if not (name and email and phone and reason):
            return render_template('contact.html', title='Contact', contact_status=False)

        if not re.fullmatch(r'^\d{10,13}$', phone):
            return render_template('contact.html', title='Contact', contact_status=False)

        # Save to database
        entry = Contact(name=name, phone=phone, email=email, reason=reason)
        db.session.add(entry)
        db.session.commit()

        # Send email (only if env vars exist)
        if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
            try:
                msg = Message(
                    subject="New Contact Form Submission",
                    recipients=[app.config['MAIL_USERNAME']],
                    body=f"""
New Contact Form Submission

Name: {name}
Email: {email}
Phone: {phone}
Reason: {reason}
Date: {datetime.utcnow()}
"""
                )
                mail.send(msg)
            except Exception as e:
                print("Email sending failed:", e)

        contact_status = True

    return render_template('contact.html', title='Contact', contact_status=contact_status)

@app.route('/projects')
def projects_page():
    return render_template(
        'projects.html',
        title="Projects",
        cards=get_projects()
    )

# ===============================
# HEALTH CHECK (IMPORTANT FOR RENDER)
# ===============================

@app.route('/health')
def health():
    return "OK", 200
