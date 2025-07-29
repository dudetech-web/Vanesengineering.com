from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with your actual secret key

# Configure PostgreSQL connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    gst_number = db.Column(db.String(50))
    vendor_type = db.Column(db.String(50))
    communications = db.Column(JSON)
    bank_details = db.Column(JSON)

# Dummy users
USERS = {
    "admin": "admin123",
    "vendor1": "vendor123"
}

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if USERS.get(username) == password:
            flash('Login successful!', 'success')
            return redirect(url_for('register_vendor'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register-vendor', methods=['GET', 'POST'])
def register_vendor():
    if request.method == 'POST':
        name = request.form.get('vendor_name')
        gst = request.form.get('gst_number')
        vendor_type = request.form.get('vendor_type')

        # Communication details
        comm_names = request.form.getlist('comm_name')
        comm_desigs = request.form.getlist('comm_designation')
        comm_phones = request.form.getlist('comm_phone')
        comm_emails = request.form.getlist('comm_email')
        communications = [
            {"name": n, "designation": d, "phone": p, "email": e}
            for n, d, p, e in zip(comm_names, comm_desigs, comm_phones, comm_emails)
        ]

        # Bank details
        bank_details = {
            "account_holder": request.form.get('account_holder'),
            "account_number": request.form.get('account_number'),
            "ifsc": request.form.get('ifsc'),
            "bank_name": request.form.get('bank_name'),
            "branch": request.form.get('branch')
        }

        vendor = Vendor(
            name=name,
            gst_number=gst,
            vendor_type=vendor_type,
            communications=communications,
            bank_details=bank_details
        )
        db.session.add(vendor)
        db.session.commit()
        flash('Vendor registered successfully!', 'success')
        return redirect(url_for('register_vendor'))

    return render_template('register_vendor.html')

@app.route('/cancel', methods=['GET'])
def cancel():
    flash('Registration cancelled.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    
