import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- Database Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///local.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- File Upload Path ---
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Dummy Credentials ---
DUMMY_USER = 'admin'
DUMMY_PASS = 'admin123'

# --- Models ---
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


# --- Routes ---

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

    if request.method == 'POST':
        vendor_id = request.form['vendor_id']
        count = Project.query.count() + 1
        enquiry_id = f"VE/TN/2526/E{str(count).zfill(3)}"

        file = request.files.get('drawing')
        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(upload_path)

        project = Project(
            enquiry_id=enquiry_id,
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
        flash('Project saved successfully!', 'success')
        return redirect(url_for('new_project'))

    return render_template('new_project.html', vendors=vendors, projects=projects)


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


@app.route('/cancel')
def cancel():
    flash('Action cancelled.', 'info')
    return redirect(url_for('login'))


# --- Create Tables on First Run ---
@app.before_first_request
def create_tables():
    db.create_all()
    if not Vendor.query.first():
        # Dummy vendors for dropdown
        db.session.add(Vendor(name="ABC Corp", gst="GST123", address="Chennai"))
        db.session.add(Vendor(name="XYZ Ltd", gst="GST456", address="Bangalore"))
        db.session.commit()

# --- Main ---
if __name__ == '__main__':
    app.run(debug=True)
