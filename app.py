import os
import math
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd
from flask import send_file
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from flask_migrate import Migrate


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- PostgreSQL Config (Permanent Storage) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://duct_vendor_app_user:6F8CX3mCEBU8E4azRCf0s6gdQeWaL9bq@dpg-d243r9qli9vc73ca99ag-a.singapore-postgres.render.com/duct_vendor_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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

    # 🖋 Signature Fields
    prepared_by = db.Column(db.String(100))
    prepared_at = db.Column(db.DateTime)
    verified_by = db.Column(db.String(100))
    verified_at = db.Column(db.DateTime)
    approved_by = db.Column(db.String(100))
    approved_at = db.Column(db.DateTime)




class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow)
    emp_code = db.Column(db.String(20))
    emp_name = db.Column(db.String(100))
    father_name = db.Column(db.String(100))
    dob = db.Column(db.Date)
    doj = db.Column(db.Date)
    designation = db.Column(db.String(100))
    department = db.Column(db.String(100))
    work_location = db.Column(db.String(100))
    bank_name = db.Column(db.String(100))
    account_no = db.Column(db.String(50))
    ifsc = db.Column(db.String(20))
    branch = db.Column(db.String(100))
    contact_no = db.Column(db.String(15))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    aadhar_no = db.Column(db.String(20))
    pan_no = db.Column(db.String(20))
    blood_group = db.Column(db.String(5))
    medical_conditions = db.Column(db.String(200))
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_no = db.Column(db.String(15))
    reference_name = db.Column(db.String(100))
    reference_contact = db.Column(db.String(15))
    photo_filename = db.Column(db.String(100))
    signature_filename = db.Column(db.String(100))

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

    area_m2 = 0

    if duct_type == 'st':
        area_m2 = 2 * (w1 + h1) / 1000 * (length / 1000) * qty
    elif duct_type == 'red':
        area_m2 = (w1 + h1 + w2 + h2) / 1000 * (length / 1000) * qty * factor
    elif duct_type == 'dm':
        area_m2 = (w1 * h1) / 1_000_000 * qty
    elif duct_type == 'offset':
        area_m2 = (w1 + h1 + w2 + h2) / 1000 * ((length + degree) / 1000) * qty * factor
    elif duct_type == 'shoe':
        area_m2 = (w1 + h1) * 2 / 1000 * (length / 1000) * qty * factor
    elif duct_type == 'vanes':
        area_m2 = (w1 / 1000) * (2 * math.pi * (w1 / 1000) / 4) * qty
    elif duct_type == 'elb':
        area_m2 = 2 * (w1 + h1) / 1000 * (((h1 / 2) / 1000) + (length / 1000) * math.pi * (degree / 180)) * qty * factor

    # Convert m² to mm² for gauge classification
    # Determine gauge based on w1 and h1 (not area)
    if w1 <= 750 and h1 <= 750:
        gauge = '24g'
    elif w1 <= 1200 and h1 <= 1200:
        gauge = '22g'
    elif w1 <= 1800 and h1 <= 1800:
        gauge = '20g'
    else:
       gauge = '18g'

    

    g24 = area_m2 if gauge == '24g' else 0
    g22 = area_m2 if gauge == '22g' else 0
    g20 = area_m2 if gauge == '20g' else 0
    g18 = area_m2 if gauge == '18g' else 0

    gasket = (w1 + w2 + h1 + h2) / 1000 * qty
    corner_pieces = 0 if duct_type == 'dm' else 8
    cleat = 0
    if gauge == '24g':
        cleat = qty * 12
    elif gauge == '22g':
        cleat = qty * 10
    elif gauge == '20g':
        cleat = qty * 8
    elif gauge == '18g':
        cleat = qty * 4

    return area_m2, gauge, g24, g22, g20, g18, gasket, corner_pieces, cleat
# ------------------- ROUTES -------------------

# --- Auto-migrate on first request (TEMPORARY for Render) ---


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
    print("Received data:", data)  # Debug

    try:
        # Safe numeric parsing
        w1 = float(data.get('w1') or 0)
        h1 = float(data.get('h1') or 0)
        w2 = float(data.get('w2') or 0)
        h2 = float(data.get('h2') or 0)
        length = float(data.get('length') or 0)
        degree = float(data.get('degree') or 0)
        quantity = int(data.get('quantity') or 1)
        factor = float(data.get('factor') or 1)

        area, gauge, g24, g22, g20, g18, gasket, corner_pieces, cleat = calculate_area_and_gauge({
            **data,
            'w1': w1, 'h1': h1, 'w2': w2, 'h2': h2,
            'length': length, 'degree': degree,
            'quantity': quantity, 'factor': factor
        })

        measurement = Measurement(
            project_id=project_id,
            duct_no=data['duct_no'],
            duct_type=data['duct_type'],
            w1=w1,
            h1=h1,
            w2=w2,
            h2=h2,
            length=length,
            degree=degree,
            quantity=quantity,
            factor=factor,
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
    except Exception as e:
        print("Error:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
@app.route('/add_measurement_sheet', methods=['GET'])
def add_measurement_sheet():
    projects = Project.query.all()
    selected_project_id = request.args.get('project_id', type=int)
    measurements = []

    if selected_project_id:
        measurements = Measurement.query.filter_by(project_id=selected_project_id).all()

    return render_template(
        'add_measurement_sheet.html',
        projects=projects,
        selected_project_id=selected_project_id,
        measurements=measurements
    )


@app.route('/delete_measurement/<int:measurement_id>', methods=['DELETE'])
def delete_measurement(measurement_id):
    measurement = Measurement.query.get_or_404(measurement_id)
    db.session.delete(measurement)
    db.session.commit()
    return jsonify({'status': 'deleted'})


@app.route('/get_measurement/<int:id>')
def get_measurement(id):
    m = Measurement.query.get_or_404(id)
    return jsonify({
        'id': m.id,
        'duct_no': m.duct_no,
        'duct_type': m.duct_type,
        'w1': m.w1,
        'h1': m.h1,
        'w2': m.w2,
        'h2': m.h2,
        'length': m.length,
        'degree': m.degree,
        'quantity': m.quantity,
        'factor': m.factor
    })


@app.route('/update_measurement/<int:id>', methods=['PUT'])
def update_measurement(id):
    data = request.get_json()
    m = Measurement.query.get_or_404(id)

    m.duct_no = data['duct_no']
    m.duct_type = data['duct_type']
    m.w1 = data.get('w1', 0)
    m.h1 = data.get('h1', 0)
    m.w2 = data.get('w2', 0)
    m.h2 = data.get('h2', 0)
    m.length = data.get('length', 0)
    m.degree = data.get('degree', 0)
    m.quantity = data.get('quantity', 1)
    m.factor = data.get('factor', 1)

    # Recalculate area, gauge, etc.
    area, gauge, g24, g22, g20, g18, gasket, corner_pieces, cleat = calculate_area_and_gauge(data)
    m.area = area
    m.gauge = gauge
    m.g24 = g24
    m.g22 = g22
    m.g20 = g20
    m.g18 = g18
    m.gasket = gasket
    m.corner_pieces = corner_pieces
    m.cleat = cleat

    db.session.commit()
    return jsonify({'status': 'updated'})





@app.route('/employee_registration', methods=['GET', 'POST'])
def employee_registration():
    if request.method == 'POST':
        data = request.form
        photo = request.files.get('photo')
        signature = request.files.get('signature')

        photo_filename = secure_filename(photo.filename) if photo else None
        signature_filename = secure_filename(signature.filename) if signature else None

        if photo:
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
        if signature:
            signature.save(os.path.join(app.config['UPLOAD_FOLDER'], signature_filename))

        employee = Employee(
            date=datetime.strptime(data['date'], '%Y-%m-%d'),
            emp_code=data['emp_code'],
            emp_name=data['emp_name'],
            father_name=data['father_name'],
            dob=datetime.strptime(data['dob'], '%Y-%m-%d'),
            doj=datetime.strptime(data['doj'], '%Y-%m-%d'),
            designation=data['designation'],
            department=data['department'],
            work_location=data['work_location'],
            bank_name=data['bank_name'],
            account_no=data['account_no'],
            ifsc=data['ifsc'],
            branch=data['branch'],
            contact_no=data['contact_no'],
            email=data['email'],
            address=data['address'],
            aadhar_no=data['aadhar_no'],
            pan_no=data['pan_no'],
            blood_group=data['blood_group'],
            medical_conditions=data['medical_conditions'],
            emergency_contact_name=data['emergency_contact_name'],
            emergency_contact_no=data['emergency_contact_no'],
            reference_name=data['reference_name'],
            reference_contact=data['reference_contact'],
            photo_filename=photo_filename,
            signature_filename=signature_filename
        )
        db.session.add(employee)
        db.session.commit()
        flash('Employee registered successfully!', 'success')
        return redirect(url_for('employee_registration'))

    return render_template('employee_registration.html')



@app.route('/export_excel')
def export_excel():
    employees = Employee.query.all()
    data = [{
        'Date': emp.date,
        'Emp Code': emp.emp_code,
        'Name': emp.emp_name,
        'Father Name': emp.father_name,
        'DOB': emp.dob,
        'DOJ': emp.doj,
        'Designation': emp.designation,
        'Department': emp.department,
        'Work Location': emp.work_location,
        'Bank Name': emp.bank_name,
        'Account No': emp.account_no,
        'IFSC': emp.ifsc,
        'Branch': emp.branch,
        'Contact No': emp.contact_no,
        'Email': emp.email,
        'Address': emp.address,
        'Aadhar No': emp.aadhar_no,
        'PAN No': emp.pan_no,
        'Blood Group': emp.blood_group,
        'Medical Conditions': emp.medical_conditions,
        'Emergency Contact Name': emp.emergency_contact_name,
        'Emergency Contact No': emp.emergency_contact_no,
        'Reference Name': emp.reference_name,
        'Reference Contact': emp.reference_contact
    } for emp in employees]

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Employees')
    output.seek(0)
    return send_file(output, download_name="employee_data.xlsx", as_attachment=True)



@app.route('/export_pdf')
def export_pdf():
    employees = Employee.query.all()
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40

    for emp in employees:
        c.setFont("Helvetica", 10)
        c.drawString(40, y, f"{emp.emp_code} - {emp.emp_name}, Dept: {emp.department}, Ph: {emp.contact_no}")
        y -= 20
        if y < 60:
            c.showPage()
            y = height - 40

    c.save()
    buffer.seek(0)
    return send_file(buffer, download_name='employee_data.pdf', as_attachment=True)



# ------------------- INITIALIZE DB -------------------
# ------------------- AUTO-MIGRATE ON RENDER -------------------

# ------------------- AUTO MIGRATION INIT (MOBILE FRIENDLY) -------------------
import os
from flask_migrate import init, migrate, upgrade, stamp
from alembic.config import Config
import shutil

def auto_run_migrations():
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    if not os.path.exists(migrations_dir):
        # Create an Alembic configuration object programmatically
        cfg = Config()
        cfg.set_main_option("script_location", "migrations")
        cfg.set_main_option("sqlalchemy.url", app.config["SQLALCHEMY_DATABASE_URI"])

        # Initialize migrations folder
        init(directory=migrations_dir)
        stamp(directory=migrations_dir, revision="head")  # Mark DB as current
        migrate(directory=migrations_dir, message="Initial migration")
    upgrade(directory=migrations_dir)  # Apply the migration

with app.app_context():
    auto_run_migrations()


if __name__ == "__main__":
    app.run(debug=True)
