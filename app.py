import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, PlacementDrive, User

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"), static_folder=os.path.join(BASE_DIR, "static"))
app.secret_key = "mad1-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placement.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


    admin = User.query.filter_by(role="admin").first()
    if not admin:
        admin_user = User(
            name="Admin",
            email="admin@iitm.ac.in",
            password=generate_password_hash("admin123"),
            role="admin",
            approved=True
        )
        db.session.add(admin_user)
        db.session.commit()


@app.route("/admin/companies")
def admin_companies():
    if session.get("role") != "admin":
        return redirect("/login")
    companies = User.query.filter_by(role="company").all()
    return render_template("admin/companies.html", companies=companies)


@app.route("/admin/approve_company/<int:user_id>")
def approve_company(user_id):
    if session.get("role") != "admin":
        return redirect("/login")
    company = User.query.get(user_id)
    if company:
        company.approved = True
        db.session.commit()
    return redirect("/admin/companies")


@app.route("/company/dashboard")
def company_dashboard():
    if session.get("role") != "company":
        return redirect("/login")
    if not session.get("approved"):
        return "Waiting for admin approval"
    return render_template("company/dashboard.html")


@app.route("/company/create-drive", methods=["GET", "POST"])
def create_drive():
    if session.get("role") != "company":
        return redirect("/login")
    
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["description"]

        new_drive = PlacementDrive(
            title=title,
            description=desc,
            company_id=session.get("user_id")
        )

        db.session.add(new_drive)
        db.session.commit()

        flash("Drive created successfully!")
        return redirect("/company/dashboard")
    return render_template("company/create_drive.html")


@app.route("/")
def home():
    return "Placement Portal Running"


@app.route("/admin/students")
def admin_students():
    if session.get("role") != "admin":
        return redirect("/login")
    students = User.query.filter_by(role="student").all()
    return render_template("admin/students.html", students=students)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if user.role == "company" and not user.approved:
                flash("Company not approved by admin yet")
                return redirect("/login")
            
            session["user_id"] = user.id
            session["role"] = user.role
            session["approved"] = user.approved

            if user.role == "admin":
                return redirect("/admin/dashboard")
            elif user.role == "company":
                return redirect("/company/dashboard")
            else:
                return redirect("/student/dashboard")
        flash("Invalid credentials")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        role = request.form["role"]

        if role == "admin":
            flash("Admin registration not allowed")
            return redirect("/register")
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email alreay registered")
            return redirect("/register")
        
        user = User(
            name=name,
            email=email,
            password=password,
            role=role,
            approved=True if role == "student" else False
        )

        db.session.add(user)
        db.session.commit()
 
        flash("Registration successful. Please login.")
        return redirect("/login")
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/login")
    
    total_students = User.query.filter_by(role="student").count()
    total_companies = User.query.filter_by(role="company").count()
    total_users = User.query.count()

    return render_template("admin/dashboard.html",
                           students_count=total_students,
                           companies_count=total_companies,
                           users_count=total_users)

@app.route("/admin/drives")
def admin_drives():
    if session.get("role") != "admin":
        return redirect("/login")
    
    drives = PlacementDrive.query.all()
    return render_template("admin/drives.html", drives=drives)


@app.route("/admin/approve-drive/<int:drive_id>")
def approve_drive(drive_id):
    if session.get("role") != "admin":
        return redirect("/login")
    
    drive = PlacementDrive.query.get(drive_id)
    if drive:
        drive.status = "Approved"
        db.session.commit()

    return redirect("/admin/drives")

@app.route("/admin/reject-drive/<int:drive_id>")
def reject_drive(drive_id):
    if session.get("role") != "admin":
        return redirect("/login")
    
    drive = PlacementDrive.query.get(drive_id)
    if drive:
        drive.status = "Rejected"
        db.session.commit()

    return redirect("/admin/drives")



@app.route("/admin/deactivate/<int:user_id>")
def deactivate_user(user_id):
    if session.get("role") != "admin":
        return redirect("/login")
    
    user = User.query.get(user_id)
    if user:
        user.active = False
        db.session.commit()

    return redirect("/admin/students")


@app.route("/admin/activate/<int:user_id>")
def activate_user(user_id):
    if session.get("role") != "admin":
        return redirect("/login")
    
    user = User.query.get(user_id)
    if user:
        user.active = True
        db.session.commit()
    return redirect("/admin/students")


@app.route("/student/dashboard")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/login")
    return render_template("student/dashboard.html")

            
    

if __name__ == "__main__":
    app.run(debug=True)

