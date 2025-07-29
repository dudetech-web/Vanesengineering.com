import os
import math
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- PostgreSQL Config (Permanent Storage) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://duct_vendor_app_user:6F8CX3mCEBU8E4azRCf0s6gdQeWaL9bq@dpg-d243r9qli9vc73ca99ag-a.singapore-postgres.render.com/duct_vendor_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- File Upload Path ---
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Dummy Login Credentials ---
DUMMY_USER = 'admin'
DUMMY_PASS = 'admin123'

# ------------------- MODELS -------------------

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    gst = db.Column(db.String(20))
    address = db.Column(db.String(200))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enquiry_id = db.Column(db.String(50), unique=True, nullable=False)
    quotation = db.Column(db.String(100))
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    location = db.Column(db.String(100))
    source_drawing = db.Column(db.String(200))
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'))
    vendor = db.relationship('Vendor', backref='projects')
    gst_no = db.Column(db.String(20))
    address = db.Column(db.String(200))
    notes = db.Column(db.String(200))
    email = db.Column(db.String(100))
    contact = db.Column(db.String(20))
    incharge = db.Column(db.String(100))

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    tag_file = db.Column(db.String(200))
    duct_no = db.Column(db.String(50))
    duct_type = db.Column(db.String(50))
    w1 = db.Column(db.Float)
    h1 = db.Column(db.Float)
    w2 = db.Column(db.Float)
    h2 = db.Column(db.Float)
    length = db.Column(db.Float)
    degree = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    factor = db.Column(db.Float)
    area = db.Column(db.Float)
    gauge = db.Column(db.String(10))
    g24 = db.Column(db.Float)
    g22 = db.Column(db.Float)
    g20 = db.Column(db.Float)
    g18 = db.Column(db.Float)
    gasket = db.Column(db.Integer)
    corner_pieces = db.Column(db.Integer)
    cleat = db.Column(db.Float)

# ------------------- CALCULATION FUNCTION -------------------

def calculate_area_and_gauge(data):
    w1 = float(data.get('w1', 0))
    h1 = float(data.get('h1', 0))
    w2 = float(data.get('w2', 0))
    h2 = float(data.get('h2', 0))
    length = float(data.get('length', 0))
    degree = float(data.get('degree', 0))
    qty = int(data.get('quantity', 0))
    factor = float(data.get('factor', 1))
    duct_type = data.get('duct_type', '').lower()

    area = 0

    if duct_type == 'st':
        area = 2 * (w1 + h1) / 1000 * (length / 1000) * qty
    elif duct_type == 'red':
        area = (w1 + h1 + w2 + h2) / 1000 * (length / 1000) * qty * factor
    elif duct_type == 'dm':
        area = (w1 / 1000 + h1 / 1000) * qty
    elif duct_type == 'offset':
        area = (w1 + h1 + w2 + h2) / 1000 * ((length + degree) / 1000) * qty * factor
    elif duct_type == 'shoe':
        area = (w1 + h1) * 2 / 1000 * (length / 1000) * qty * factor
    elif duct_type == 'vanes':
        area = (w1 / 1000) * (2 * math.pi * (w1 / 1000) / 4) * qty
    elif duct_type == 'elb':
        area = 2 * (w1 + h1) / 1000 * ((h1 / 2) / 1000 + (length / 1000) * math.pi * (degree / 180)) * qty * factor

    if area <= 0.75:
        gauge = '24g'
    elif area <= 1.20:
        gauge = '22g'
    elif area <= 1.80:
        gauge = '20g'
    else:
        gauge = '18g'

    g24 = area if gauge == '24g' else 0
    g22 = area if gauge == '22g' else 0
    g20 = area if gauge == '20g' else 0
    g18 = area if gauge == '18g' else 0

    # Final formula (based on image you sent):
    gasket = qty * 2
    corner_pieces = qty * 4
    cleat = qty * 1.2

    return area, gauge, g24, g22, g20, g18, gasket, corner_pieces, cleat

# ------------------- ROUTES -------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if uname == DUMMY_USER and pwd == DUMMY_PASS:
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/register_vendor', methods=['GET', 'POST'])
def register_vendor():
    if request.method == 'POST':
        name = request.form.get('name')
        gst = request.form.get('gst')
        address = request.form.get('address')
        if name:
            vendor = Vendor(name=name, gst=gst, address=address)
            db.session.add(vendor)
            db.session.commit()
            flash('Vendor saved successfully!', 'success')
        else:
            flash('Vendor name is required.', 'error')
        return redirect(url_for('register_vendor'))
    return render_template('register_vendor.html')

@app.route('/new_project', methods=['GET', 'POST'])
def new_project():
    vendors = Vendor.query.all()
    projects = Project.query.all()
    count = Project.query.count() + 1
    next_enquiry_id = f"VE/TN/2526/E{str(count).zfill(3)}"

    if request.method == 'POST':
        vendor_id = request.form['vendor_id']
        file = request.files.get('drawing')
        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        project = Project(
            enquiry_id=next_enquiry_id,
            quotation=request.form['quotation'],
            start_date=request.form['start_date'],
            end_date=request.form['end_date'],
            location=request.form['location'],
            source_drawing=filename,
            vendor_id=vendor_id,
            gst_no=request.form['gst_no'],
            address=request.form['address'],
            notes=request.form['notes'],
            email=request.form['email'],
            contact=request.form['contact'],
            incharge=request.form['incharge']
        )
        db.session.add(project)
        db.session.commit()
        flash(f'Project saved! Enquiry ID: {next_enquiry_id}', 'success')
        projects = Project.query.all()
        return render_template('new_project.html', vendors=vendors, projects=projects, enquiry_id_created=next_enquiry_id)

    return render_template('new_project.html', vendors=vendors, projects=projects, enquiry_id_created=next_enquiry_id)

@app.route('/delete_project/<int:project_id>')
def delete_project(project_id):
    proj = Project.query.get_or_404(project_id)
    db.session.delete(proj)
    db.session.commit()
    flash('Project deleted!', 'success')
    return redirect(url_for('new_project'))

@app.route('/update_project/<int:project_id>', methods=['POST'])
def update_project(project_id):
    proj = Project.query.get_or_404(project_id)
    data = request.get_json()
    proj.quotation = data.get('quotation')
    proj.start_date = data.get('start_date')
    proj.end_date = data.get('end_date')
    proj.location = data.get('location')
    proj.incharge = data.get('incharge')
    proj.contact = data.get('contact')
    proj.email = data.get('email')
    proj.notes = data.get('notes')
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/add_measurement/<int:project_id>', methods=['POST'])
def add_measurement(project_id):
    data = request.get_json()

    area, gauge, g24, g22, g20, g18, gasket, corner_pieces, cleat = calculate_area_and_gauge(data)

    measurement = Measurement(
        project_id=project_id,
        duct_no=data['duct_no'],
        duct_type=data['duct_type'],
        w1=data['w1'],
        h1=data['h1'],
        w2=data['w2'],
        h2=data['h2'],
        length=data['length'],
        degree=data['degree'],
        quantity=data['quantity'],
        factor=data['factor'],
        area=area,
        gauge=gauge,
        g24=g24,
        g22=g22,
        g20=g20,
        g18=g18,
        gasket=gasket,
        corner_pieces=corner_pieces,
        cleat=cleat
    )
    db.session.add(measurement)
    db.session.commit()
    return jsonify({'status': 'saved'})

# ------------------- INITIALIZE DB -------------------
with app.app_context():
    db.create_all()
    if not Vendor.query.first():
        db.session.add(Vendor(name="ABC Corp", gst="GST123", address="Chennai"))
        db.session.add(Vendor(name="XYZ Ltd", gst="GST456", address="Bangalore"))
        db.session.commit()

# ------------------- MAIN -------------------
if __name__ == '__main__':
    app.run(debug=True)
