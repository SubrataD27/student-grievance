from flask import Flask, render_template, request, redirect, url_for, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import InputRequired
from flask_wtf.csrf import CSRFProtect

# ============================
# Firebase Initialization
# ============================
cred = credentials.Certificate('serviceAccount.json')
try:
    firebase_admin.initialize_app(cred)
except ValueError:
    pass  # Avoid re-initializing Firebase if already initialized
  
# Initialize Firestore client
db = firestore.client()

# ============================
# Flask App Initialization
# ============================
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for CSRF protection
csrf = CSRFProtect(app)  # Enable CSRF protection

# ============================
# Grievance Form Class
# ============================
class GrievanceForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired()])
    category = SelectField('Category', choices=[('Academics', 'Academics'), ('Facilities', 'Facilities'), ('Administration', 'Administration')], validators=[InputRequired()])
    description = TextAreaField('Description', validators=[InputRequired()])
    anonymous = SubmitField('Submit Anonymously')
    submit = SubmitField('Submit Grievance')

# ============================
# Routes
# ============================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['GET', 'POST'])
def submit_grievance():
    form = GrievanceForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        category = form.category.data
        description = form.description.data
        anonymous = form.anonymous.data

        grievance = {
            "name": name if not anonymous else "Anonymous",
            "email": email if not anonymous else "",
            "category": category,
            "description": description,
            "status": "Pending",
            "anonymous": anonymous
        }

        db.collection('grievances').add(grievance)
        print("Grievance submitted successfully!")
        return redirect(url_for('index'))

    return render_template('submit.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    try:
        grievances = db.collection('grievances').get()
        grievance_list = [{"id": g.id, **g.to_dict()} for g in grievances]

        if request.method == 'POST':
            grievance_id = request.form['grievance_id']
            new_status = request.form['status']

            grievance_ref = db.collection('grievances').document(grievance_id)
            grievance_ref.update({"status": new_status})

            grievance = grievance_ref.get().to_dict()
            grievance['id'] = grievance_id

            send_email_notification(grievance)
            print("Grievance status updated and email sent!")
            return redirect(url_for('dashboard'))

        return render_template('dashboard.html', grievances=grievance_list)

    except Exception as e:
        print(f"Error fetching grievances: {e}")
        return "An error occurred while fetching grievances.", 500

@app.route('/grievance/<grievance_id>')
def grievance_details(grievance_id):
    try:
        grievance_ref = db.collection('grievances').document(grievance_id)
        grievance = grievance_ref.get().to_dict()
        if not grievance:
            return "Grievance not found", 404

        return render_template('grievance.html', grievance=grievance)
    except Exception as e:
        print(f"Error fetching grievance details: {e}")
        return "An error occurred while fetching grievance details.", 500

@app.route('/report')
def generate_report():
    try:
        grievances = db.collection('grievances').get()
        grievance_list = [{"id": g.id, **g.to_dict()} for g in grievances]

        report_data = {
            "total_grievances": len(grievance_list),
            "status_count": {
                "Pending": sum(1 for g in grievance_list if g['status'] == 'Pending'),
                "Resolved": sum(1 for g in grievance_list if g['status'] == 'Resolved'),
                "In Progress": sum(1 for g in grievance_list if g['status'] == 'In Progress')
            },
            "category_count": {}
        }
        for g in grievance_list:
            category = g['category']
            report_data["category_count"][category] = report_data["category_count"].get(category, 0) + 1

        return render_template('report.html', report=report_data)
    except Exception as e:
        print(f"Error generating report: {e}")
        return "An error occurred while generating the report.", 500

def send_email_notification(grievance):
    recipient_email = grievance.get("email")
    if not recipient_email:
        print("No email provided for this grievance. Skipping notification.")
        return

    sender_email = "subratadhibargcsj@gmail.com"
    sender_password = "rqpl leqz syon idtv"
    subject = "Grievance Status Update"
    body = f"""
    Hello {grievance.get('name')},

    Your grievance status has been updated to: {grievance.get('status')}.
    Category: {grievance.get('category')}
    Description: {grievance.get('description')}

    Thank you,
    Grievance Management Team
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
    finally:
        server.quit()

if __name__ == "__main__":
    app.run(debug=True)
