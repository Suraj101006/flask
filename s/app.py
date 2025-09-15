import csv
import os
import pandas as pd
from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "sih_secret"

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TENDERS_FILE = os.path.join(BASE_DIR, "tenders.csv")
REPORTS_FILE = os.path.join(BASE_DIR, "reports.csv")
RATINGS_FILE = os.path.join(BASE_DIR, "ratings.csv")
CITIZENS_FILE = os.path.join(BASE_DIR, "citizens.csv")
CONTRACTORS_FILE = os.path.join(BASE_DIR, "contractors.csv")

# uploaded images inside static/uploads
STATIC_UPLOADS = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(STATIC_UPLOADS, exist_ok=True)

# ---------------- INIT FILES ----------------
def init_files():
    if not os.path.exists(TENDERS_FILE):
        df_sample = pd.DataFrame([
            {"id": "1", "road_name": "Main Street", "contractor_name": "ABC Constructions",
             "fund_allocated": "500000", "start_date": "2025-01-01", "end_date": "2025-06-01",
             "warranty_period": "5 years", "status": "In Progress"},
            {"id": "2", "road_name": "2nd Avenue", "contractor_name": "XYZ Builders",
             "fund_allocated": "750000", "start_date": "2025-02-01", "end_date": "2025-07-01",
             "warranty_period": "3 years", "status": "Completed"}
        ])
        df_sample.to_csv(TENDERS_FILE, index=False)
    if not os.path.exists(REPORTS_FILE):
        pd.DataFrame(columns=["report_id","username","tender_id","location","description","photo","status"]).to_csv(REPORTS_FILE, index=False)
    if not os.path.exists(RATINGS_FILE):
        pd.DataFrame(columns=["rating_id","username","tender_id","feedback"]).to_csv(RATINGS_FILE, index=False)
    if not os.path.exists(CITIZENS_FILE):
        pd.DataFrame(columns=["username","name","age","email","address","password"]).to_csv(CITIZENS_FILE, index=False)
    if not os.path.exists(CONTRACTORS_FILE):
        pd.DataFrame([
            {"username": "abc", "name": "ABC Constructions", "password": "password123"},
            {"username": "xyz", "name": "XYZ Builders", "password": "password456"}
        ]).to_csv(CONTRACTORS_FILE, index=False)

init_files()

# ---------------- HELPERS ----------------
def read_csv_safe(path):
    try:
        return pd.read_csv(path, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame()

def save_csv(df, path):
    df.to_csv(path, index=False)

# ---------------- ROUTES ----------------

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        age = (request.form.get("age") or "").strip()
        email = (request.form.get("email") or "").strip()
        address = (request.form.get("address") or "").strip()
        password = (request.form.get("password") or "").strip()

        if not (name and email and password):
            flash("Please fill name, email and password.")
            return redirect(url_for("register"))

        df_users = read_csv_safe(CITIZENS_FILE)
        base = name.split()[0].lower()
        domain = email.split("@")[0] if "@" in email else email
        username = f"{base}_{domain}"
        i = 1
        while username in df_users.get("username", "").tolist():
            username = f"{base}_{domain}{i}"
            i += 1

        new_user = {"username": username,"name": name,"age": age,"email": email,"address": address,"password": password}
        if df_users.empty:
            df_users = pd.DataFrame([new_user])
        else:
            df_users = pd.concat([df_users, pd.DataFrame([new_user])], ignore_index=True)
        save_csv(df_users, CITIZENS_FILE)
        flash(f"Registration successful! Your username is: {username}")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route('/contractor_register', methods=["GET", "POST"])
def contractor_register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        if not (name and username and password):
            flash("Please fill all fields.")
            return redirect(url_for("contractor_register"))

        df_contractors = read_csv_safe(CONTRACTORS_FILE)
        if username in df_contractors.get("username", "").tolist():
            flash("Username already exists. Please choose another.")
            return redirect(url_for("contractor_register"))

        new_contractor = {"username": username, "name": name, "password": password}
        if df_contractors.empty:
            df_contractors = pd.DataFrame([new_contractor])
        else:
            df_contractors = pd.concat([df_contractors, pd.DataFrame([new_contractor])], ignore_index=True)
        save_csv(df_contractors, CONTRACTORS_FILE)
        flash(f"Contractor registration successful! Your username is: {username}")
        return redirect(url_for("login"))
    
    return render_template("contractor_register.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        user_type = request.form.get("user_type")
        input_user = (request.form.get("username") or "").strip()
        input_pass = (request.form.get("password") or "").strip()

        if not input_user or not input_pass or not user_type:
            flash("Please enter all required fields.")
            return redirect(url_for("login"))

        if user_type == "citizen":
            df_users = read_csv_safe(CITIZENS_FILE)
            user_row = df_users[(df_users["username"] == input_user)]
            if user_row.empty:
                user_row = df_users[(df_users["email"] == input_user)]

        elif user_type == "contractor":
            df_users = read_csv_safe(CONTRACTORS_FILE)
            user_row = df_users[(df_users["username"] == input_user)]

        else:
            flash("Invalid user type.")
            return redirect(url_for("login"))

        if user_row.empty:
            flash("No user found with that username or email.")
            return redirect(url_for("login"))

        stored_password = user_row.iloc[0]["password"].strip()
        if stored_password == input_pass:
            session['username'] = user_row.iloc[0]["username"]
            session['user_type'] = user_type
            flash(f"Welcome {user_row.iloc[0]['name']}!")
            return redirect(url_for("dashboard"))
        else:
            flash("Incorrect password. Please try again.")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_type', None)
    flash("You have been logged out.")
    return redirect(url_for("login"))

# ----- DASHBOARD ROUTING -----
@app.route('/dashboard')
def dashboard():
    if "username" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))
    if session.get('user_type') == 'contractor':
        return redirect(url_for('contractor_dashboard'))
    
    # Citizen dashboard logic
    tenders_df = read_csv_safe(TENDERS_FILE)
    reports_df = read_csv_safe(REPORTS_FILE)
    ratings_df = read_csv_safe(RATINGS_FILE)

    if "username" not in reports_df.columns:
        reports_df["username"] = ""

    my_reports_count = len(reports_df[reports_df["username"] == session['username']])

    stats = {
        "tenders_count": len(tenders_df),
        "my_reports": my_reports_count,
        "ratings_count": len(ratings_df)
    }

    return render_template("dashboard.html", username=session['username'], stats=stats)


# ----- CONTRACTOR DASHBOARD -----
@app.route('/contractor_dashboard')
def contractor_dashboard():
    if session.get('user_type') != 'contractor':
        flash("Unauthorized access.")
        return redirect(url_for("dashboard"))

    tenders_df = read_csv_safe(TENDERS_FILE)
    reports_df = read_csv_safe(REPORTS_FILE)
    ratings_df = read_csv_safe(RATINGS_FILE)
    contractors_df = read_csv_safe(CONTRACTORS_FILE)

    # Correctly get the contractor's name from their username
    try:
        contractor_name = contractors_df[contractors_df['username'] == session['username']]['name'].iloc[0]
    except (KeyError, IndexError):
        flash("Contractor name not found. Please check your contractors.csv file.")
        return redirect(url_for("logout"))
    
    # Get tenders and reports for this contractor
    assigned_tenders = tenders_df[tenders_df['contractor_name'] == contractor_name].to_dict(orient="records")
    
    # Get the tender IDs to filter the reports
    assigned_tender_ids = [t['id'] for t in assigned_tenders]
    
    if "tender_id" not in reports_df.columns:
        reports_df["tender_id"] = ""

    assigned_reports = reports_df[reports_df["tender_id"].isin(assigned_tender_ids)].to_dict(orient="records")

    # Get feedbacks for this contractor's tenders
    if "tender_id" not in ratings_df.columns:
        ratings_df["tender_id"] = ""
    assigned_feedbacks = ratings_df[ratings_df["tender_id"].isin(assigned_tender_ids)].to_dict(orient="records")


    return render_template("contractor_dashboard.html", username=contractor_name, tenders=assigned_tenders, reports=assigned_reports, feedbacks=assigned_feedbacks)


# ----- UPDATE REPORT STATUS (CONTRACTOR FUNCTIONALITY) -----
@app.route('/update_report_status/<report_id>', methods=["POST"])
def update_report_status(report_id):
    if session.get('user_type') != 'contractor':
        flash("Unauthorized access.")
        return redirect(url_for("dashboard"))
    
    new_status = request.form.get("new_status")
    
    df_reports = read_csv_safe(REPORTS_FILE)
    if "report_id" in df_reports.columns:
        df_reports.loc[df_reports["report_id"] == report_id, "status"] = new_status
        save_csv(df_reports, REPORTS_FILE)
        flash(f"Report {report_id} status updated to {new_status}.")
    else:
        flash("Error: Report ID not found.")

    return redirect(url_for("contractor_dashboard"))

@app.route('/tenders', methods=["GET", "POST"])
def tenders():
    if "username" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))

    df = read_csv_safe(TENDERS_FILE)
    if request.method == "POST":
        filter_type = request.form.get("filter_type", "").strip()
        filter_value = (request.form.get("filter_value") or "").strip()
        if filter_type and filter_value:
            if filter_type == "status":
                df = df[df["status"].str.lower() == filter_value.lower()]
            elif filter_type == "road_name":
                df = df[df["road_name"].str.lower().str.contains(filter_value.lower(), na=False)]
            elif filter_type == "contractor":
                df = df[df["contractor_name"].str.lower().str.contains(filter_value.lower(), na=False)]
    tenders = df.to_dict(orient="records")
    return render_template("tenders.html", tenders=tenders)

@app.route('/report', methods=["GET", "POST"])
def report():
    if "username" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))
    if session.get('user_type') == 'contractor':
        flash("Unauthorized. Contractors cannot submit reports.")
        return redirect(url_for("contractor_dashboard"))

    df_reports = read_csv_safe(REPORTS_FILE)
    if request.method == "POST":
        tender_id = (request.form.get("tender_id") or "").strip()
        location = (request.form.get("location") or "").strip()
        description = (request.form.get("description") or "").strip()
        photo_file = request.files.get("photo")

        if not tender_id or not location or not description:
            flash("Please fill tender id, location and description.")
            return redirect(url_for("report"))

        if not photo_file or photo_file.filename == "":
            flash("Photo is mandatory.")
            return redirect(url_for("report"))

        filename = photo_file.filename
        save_path = os.path.join(STATIC_UPLOADS, filename)
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(save_path):
            filename = f"{base}_{counter}{ext}"
            save_path = os.path.join(STATIC_UPLOADS, filename)
            counter += 1
        photo_file.save(save_path)
        photo_rel = os.path.join("uploads", filename).replace("\\", "/")

        report_id = "R" + str(len(df_reports) + 1).zfill(4)
        new_report = {"report_id": report_id,"username": session['username'],"tender_id": tender_id,
                      "location": location,"description": description,"photo": photo_rel,"status": "Pending"}
        if df_reports.empty:
            df_reports = pd.DataFrame([new_report])
        else:
            df_reports = pd.concat([df_reports, pd.DataFrame([new_report])], ignore_index=True)
        save_csv(df_reports, REPORTS_FILE)
        flash("Report submitted successfully.")
        return redirect(url_for("report"))

    my_reports = df_reports[df_reports.get("username","") == session['username']].to_dict(orient="records")
    return render_template("report.html", reports=my_reports)


@app.route('/feedback', methods=["GET", "POST"])
def feedback():
    if "username" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))
    if session.get('user_type') == 'contractor':
        flash("Unauthorized. Contractors cannot give feedback.")
        return redirect(url_for("contractor_dashboard"))

    df_ratings = read_csv_safe(RATINGS_FILE)
    if request.method == "POST":
        tender_id = (request.form.get("tender_id") or "").strip()
        feedback_text = (request.form.get("feedback") or "").strip()
        if not tender_id or not feedback_text:
            flash("Please enter tender id and feedback.")
            return redirect(url_for("feedback"))

        rating_id = "F" + str(len(df_ratings) + 1).zfill(4)
        new_rating = {"rating_id": rating_id,"username": session['username'],"tender_id": tender_id,"feedback": feedback_text}
        if df_ratings.empty:
            df_ratings = pd.DataFrame([new_rating])
        else:
            df_ratings = pd.concat([df_ratings, pd.DataFrame([new_rating])], ignore_index=True)
        save_csv(df_ratings, RATINGS_FILE)
        flash("Feedback saved.")
        return redirect(url_for("feedback"))

    ratings = df_ratings.to_dict(orient="records")
    return render_template("feedback.html", ratings=ratings)


if __name__ == "__main__":
    app.run(debug=True)