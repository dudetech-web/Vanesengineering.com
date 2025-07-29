import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database config: use PostgreSQL from Render or fallback to SQLite for local use
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///local.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Dummy login credentials
DUMMY_USER = 'admin'
DUMMY_PASS = 'admin123'

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if uname == DUMMY_USER and pwd == DUMMY_PASS:
            flash('Login successful!', 'success')
            return redirect(url_for('register_vendor'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/register_vendor', methods=['GET', 'POST'])
def register_vendor():
    if request.method == 'POST':
        flash('Vendor saved successfully!', 'success')
        return redirect(url_for('register_vendor'))
    return render_template('register_vendor.html')

@app.route('/cancel')
def cancel():
    flash('Action cancelled.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
