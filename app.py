from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "hospital.db"

app = Flask(__name__)
app.secret_key = "hospital-demo-secret-key"


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS departments (
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dept_name TEXT NOT NULL,
        location TEXT,
        phone TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS staff (
        staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        role TEXT NOT NULL,
        dept_id INTEGER,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        gender TEXT,
        dob TEXT,
        hire_date TEXT NOT NULL,
        salary REAL,
        status TEXT DEFAULT 'Active',
        FOREIGN KEY(dept_id) REFERENCES departments(dept_id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS doctors (
        doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id INTEGER NOT NULL UNIQUE,
        specialization TEXT NOT NULL,
        qualification TEXT,
        license_number TEXT UNIQUE NOT NULL,
        consultation_fee REAL DEFAULT 0,
        available_days TEXT,
        FOREIGN KEY(staff_id) REFERENCES staff(staff_id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS wards (
        ward_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ward_name TEXT NOT NULL,
        ward_type TEXT NOT NULL,
        dept_id INTEGER,
        total_beds INTEGER NOT NULL DEFAULT 0,
        available_beds INTEGER NOT NULL DEFAULT 0,
        floor_no INTEGER,
        FOREIGN KEY(dept_id) REFERENCES departments(dept_id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS rooms (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT NOT NULL UNIQUE,
        ward_id INTEGER NOT NULL,
        room_type TEXT NOT NULL,
        status TEXT DEFAULT 'Available',
        daily_rate REAL NOT NULL DEFAULT 0,
        FOREIGN KEY(ward_id) REFERENCES wards(ward_id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS patients (
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        dob TEXT NOT NULL,
        gender TEXT NOT NULL,
        blood_group TEXT,
        phone TEXT NOT NULL,
        email TEXT,
        address TEXT,
        emergency_contact_name TEXT,
        emergency_contact_phone TEXT,
        medical_history TEXT,
        allergies TEXT,
        registered_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS patient_admissions (
        admission_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        room_id INTEGER,
        admitted_by INTEGER,
        admission_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        discharge_date TEXT,
        diagnosis TEXT,
        status TEXT DEFAULT 'Admitted',
        notes TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
        FOREIGN KEY(room_id) REFERENCES rooms(room_id) ON DELETE SET NULL,
        FOREIGN KEY(admitted_by) REFERENCES doctors(doctor_id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS appointments (
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        reason TEXT,
        status TEXT DEFAULT 'Scheduled',
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
        FOREIGN KEY(doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS medicines (
        medicine_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        generic_name TEXT,
        category TEXT,
        manufacturer TEXT,
        unit TEXT DEFAULT 'Tablet',
        unit_price REAL NOT NULL DEFAULT 0,
        stock_qty INTEGER NOT NULL DEFAULT 0,
        reorder_level INTEGER NOT NULL DEFAULT 10,
        expiry_date TEXT,
        requires_prescription INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS bills (
        bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        admission_id INTEGER,
        appointment_id INTEGER,
        bill_date TEXT DEFAULT CURRENT_TIMESTAMP,
        due_date TEXT,
        subtotal REAL NOT NULL DEFAULT 0,
        discount REAL DEFAULT 0,
        tax REAL DEFAULT 0,
        total_amount REAL NOT NULL DEFAULT 0,
        paid_amount REAL DEFAULT 0,
        status TEXT DEFAULT 'Pending',
        notes TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_date TEXT DEFAULT CURRENT_TIMESTAMP,
        payment_method TEXT NOT NULL,
        transaction_ref TEXT,
        received_by INTEGER,
        FOREIGN KEY(bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE
    );
    """)
    seed(conn)
    conn.commit()
    conn.close()


def seed(conn):
    if conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0]:
        return
    departments = [
        ("Cardiology","Block A, Floor 2","0512-300-101"),
        ("Neurology","Block B, Floor 1","0512-300-102"),
        ("Orthopedics","Block C, Floor 3","0512-300-103"),
        ("Pediatrics","Block A, Floor 1","0512-300-104"),
        ("General Medicine","Block D, Floor 1","0512-300-105"),
        ("Pharmacy","Ground Floor","0512-300-200"),
    ]
    conn.executemany("INSERT INTO departments(dept_name,location,phone) VALUES (?,?,?)", departments)
    wards = [
        ("Cardiac Ward","ICU",1,10,4,2),("Neuro Ward","General",2,20,12,1),
        ("Ortho Ward","General",3,15,9,3),("Pediatric Ward","Pediatric",4,18,10,1),
        ("General Ward","General",5,30,18,1),("Emergency","ICU",5,8,3,0)
    ]
    conn.executemany("INSERT INTO wards(ward_name,ward_type,dept_id,total_beds,available_beds,floor_no) VALUES (?,?,?,?,?,?)", wards)
    rooms = [
        ("A-101",1,"ICU","Available",5000),("A-102",1,"ICU","Occupied",5000),
        ("B-201",2,"Single","Available",2500),("B-202",2,"Double","Available",1800),
        ("C-301",3,"Single","Occupied",2200),("D-101",4,"Single","Available",2000),
        ("E-101",5,"Double","Available",900),("E-102",5,"Suite","Available",4500),
        ("ER-01",6,"Emergency","Occupied",3500)
    ]
    conn.executemany("INSERT INTO rooms(room_number,ward_id,room_type,status,daily_rate) VALUES (?,?,?,?,?)", rooms)
    staff = [
        ("Arun","Sharma","Doctor",1,"arun.sharma@hospital.com","9876543210","Male","1978-05-12","2010-06-01",150000),
        ("Priya","Mehta","Doctor",2,"priya.mehta@hospital.com","9876543211","Female","1982-08-22","2012-03-15",140000),
        ("Rakesh","Verma","Doctor",3,"rakesh.verma@hospital.com","9876543212","Male","1975-11-30","2008-01-10",160000),
        ("Sunita","Singh","Nurse",1,"sunita.singh@hospital.com","9876543213","Female","1990-04-18","2015-07-01",45000),
        ("Mohit","Jain","Pharmacist",6,"mohit.jain@hospital.com","9876543214","Male","1988-02-14","2016-09-01",50000),
        ("Kavita","Rao","Receptionist",5,"kavita.rao@hospital.com","9876543215","Female","1993-07-25","2019-01-15",35000),
        ("Deepak","Gupta","Doctor",4,"deepak.gupta@hospital.com","9876543216","Male","1980-09-07","2011-04-01",145000),
        ("Prabhav","Shankar Mishra","Admin",5,"neha.agarwal@hospital.com","9876543217","Female","1985-12-03","2013-08-01",60000),
    ]
    conn.executemany("""INSERT INTO staff(first_name,last_name,role,dept_id,email,phone,gender,dob,hire_date,salary)
                        VALUES (?,?,?,?,?,?,?,?,?,?)""", staff)
    doctors = [
        (1,"Cardiology","MD, DM Cardiology","MCI-CARD-001",800,"Mon,Tue,Wed,Thu,Fri"),
        (2,"Neurology","MD, DM Neurology","MCI-NEUR-002",900,"Mon,Wed,Fri"),
        (3,"Orthopedics","MS Orthopedics","MCI-ORTH-003",700,"Tue,Thu,Sat"),
        (7,"Pediatrics","MD Pediatrics, MRCP","MCI-PEDI-004",600,"Mon,Tue,Wed,Thu,Fri"),
    ]
    conn.executemany("""INSERT INTO doctors(staff_id,specialization,qualification,license_number,consultation_fee,available_days)
                        VALUES (?,?,?,?,?,?)""", doctors)
    patients = [
        ("Ramesh","Kumar","1965-03-10","Male","B+","9811111111","ramesh.k@email.com","Civil Lines, Kanpur"),
        ("Anita","Patel","1990-07-22","Female","A+","9822222222","anita.p@email.com","Swaroop Nagar, Kanpur"),
        ("Vikas","Tiwari","1978-11-05","Male","O-","9833333333","vikas.t@email.com","Kidwai Nagar, Kanpur"),
        ("Shalini","Mishra","2001-01-15","Female","AB+","9844444444","shalini.m@email.com","Kakadeo, Kanpur"),
        ("Amit","Srivastava","1955-06-28","Male","A-","9855555555","amit.s@email.com","Armapur, Kanpur"),
    ]
    conn.executemany("""INSERT INTO patients(first_name,last_name,dob,gender,blood_group,phone,email,address)
                        VALUES (?,?,?,?,?,?,?,?)""", patients)
    admissions = [
        (1,2,1,"2026-03-20 10:30:00","Acute Myocardial Infarction","Admitted"),
        (3,5,3,"2026-03-21 14:00:00","Fractured Femur","Admitted"),
        (5,9,1,"2026-03-23 08:15:00","Chest Pain - Under Observation","Admitted"),
    ]
    conn.executemany("""INSERT INTO patient_admissions(patient_id,room_id,admitted_by,admission_date,diagnosis,status)
                        VALUES (?,?,?,?,?,?)""", admissions)
    appointments = [
        (2,1,"2026-03-25","10:00","Routine cardiac checkup","Scheduled"),
        (4,2,"2026-03-25","11:30","Recurring headaches","Scheduled"),
        (2,3,"2026-03-26","09:00","Knee pain follow-up","Scheduled"),
        (1,1,"2026-03-15","10:00","Initial consultation","Completed"),
        (3,3,"2026-03-18","09:30","Pre-surgery assessment","Completed"),
    ]
    conn.executemany("""INSERT INTO appointments(patient_id,doctor_id,appointment_date,appointment_time,reason,status)
                        VALUES (?,?,?,?,?,?)""", appointments)
    medicines = [
        ("Aspirin 75mg","Aspirin","Antiplatelet","Sun Pharma","Tablet",2.5,500,50,"2027-12-31"),
        ("Atorvastatin 20mg","Atorvastatin","Statin","Cipla","Tablet",8,300,30,"2027-06-30"),
        ("Metformin 500mg","Metformin HCl","Antidiabetic","Dr. Reddys","Tablet",3.5,200,25,"2026-09-30"),
        ("Paracetamol 500mg","Paracetamol","Analgesic","GSK India","Tablet",1.5,800,100,"2027-03-31"),
        ("Amoxicillin 500mg","Amoxicillin","Antibiotic","Mankind Pharma","Capsule",12,15,20,"2026-12-31"),
        ("Normal Saline 500ml","Sodium Chloride","IV Fluid","Baxter","Bottle",120,60,15,"2026-08-31"),
        ("Omeprazole 20mg","Omeprazole","PPI","Torrent Pharma","Capsule",5,400,40,"2027-01-31"),
        ("Ceftriaxone 1g","Ceftriaxone","Antibiotic","Sun Pharma","Vial",180,8,10,"2026-10-31"),
    ]
    conn.executemany("""INSERT INTO medicines(name,generic_name,category,manufacturer,unit,unit_price,stock_qty,reorder_level,expiry_date)
                        VALUES (?,?,?,?,?,?,?,?,?)""", medicines)
    bills = [(1,1,"2026-03-20","2026-04-20",25000,10000,"Partial"),
             (3,2,"2026-03-21","2026-04-21",18000,18000,"Paid"),
             (5,3,"2026-03-23","2026-04-23",12000,0,"Pending")]
    for p,a,bd,due,total,paid,status in bills:
        conn.execute("""INSERT INTO bills(patient_id,admission_id,bill_date,due_date,subtotal,total_amount,paid_amount,status)
                        VALUES (?,?,?,?,?,?,?,?)""",(p,a,bd,due,total,total,paid,status))
    conn.executemany("""INSERT INTO payments(bill_id,amount,payment_method,transaction_ref,received_by)
                        VALUES (?,?,?,?,?)""", [(1,10000,"UPI","UPI20260320ABC",6),(2,18000,"Card","CARD20260322XYZ",6)])


def count(table):
    return get_db().execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


@app.route("/")
def dashboard():
    db = get_db()
    stats = {
        "patients": db.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
        "doctors": db.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
        "appointments": db.execute("SELECT COUNT(*) FROM appointments WHERE status='Scheduled'").fetchone()[0],
        "revenue": db.execute("SELECT COALESCE(SUM(paid_amount),0) FROM bills").fetchone()[0],
        "beds": db.execute("SELECT COALESCE(SUM(total_beds),0), COALESCE(SUM(available_beds),0) FROM wards").fetchone(),
        "low_stock": db.execute("SELECT COUNT(*) FROM medicines WHERE stock_qty <= reorder_level").fetchone()[0],
    }
    appointments = db.execute("""SELECT a.*, p.first_name||' '||p.last_name patient_name,
                                  s.first_name||' '||s.last_name doctor_name
                                  FROM appointments a
                                  JOIN patients p ON p.patient_id=a.patient_id
                                  JOIN doctors d ON d.doctor_id=a.doctor_id
                                  JOIN staff s ON s.staff_id=d.staff_id
                                  ORDER BY a.appointment_date, a.appointment_time LIMIT 6""").fetchall()
    low_stock = db.execute("SELECT * FROM medicines WHERE stock_qty <= reorder_level ORDER BY stock_qty").fetchall()
    db.close()
    return render_template("dashboard.html", stats=stats, appointments=appointments, low_stock=low_stock)


@app.route("/patients", methods=["GET","POST"])
def patients():
    db = get_db()
    if request.method == "POST":
        f = request.form
        db.execute("""INSERT INTO patients(first_name,last_name,dob,gender,blood_group,phone,email,address)
                      VALUES (?,?,?,?,?,?,?,?)""",
                   (f["first_name"],f["last_name"],f["dob"],f["gender"],f["blood_group"],
                    f["phone"],f.get("email"),f.get("address")))
        db.commit()
        flash("Patient registered successfully.")
        return redirect(url_for("patients"))
    q = request.args.get("q","").strip()
    if q:
        rows = db.execute("""SELECT * FROM patients WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ?
                             ORDER BY patient_id DESC""",(f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
    else:
        rows = db.execute("SELECT * FROM patients ORDER BY patient_id DESC").fetchall()
    db.close()
    return render_template("patients.html", patients=rows, q=q)


@app.route("/appointments", methods=["GET","POST"])
def appointments():
    db = get_db()
    if request.method == "POST":
        f=request.form
        db.execute("""INSERT INTO appointments(patient_id,doctor_id,appointment_date,appointment_time,reason,status)
                      VALUES (?,?,?,?,?,'Scheduled')""",
                   (f["patient_id"],f["doctor_id"],f["appointment_date"],f["appointment_time"],f.get("reason")))
        db.commit()
        flash("Appointment scheduled.")
        return redirect(url_for("appointments"))
    rows=db.execute("""SELECT a.*, p.first_name||' '||p.last_name patient_name,
                       s.first_name||' '||s.last_name doctor_name
                       FROM appointments a JOIN patients p ON p.patient_id=a.patient_id
                       JOIN doctors d ON d.doctor_id=a.doctor_id JOIN staff s ON s.staff_id=d.staff_id
                       ORDER BY a.appointment_date,a.appointment_time""").fetchall()
    patients_list=db.execute("SELECT patient_id,first_name,last_name FROM patients ORDER BY first_name").fetchall()
    doctors_list=db.execute("""SELECT d.doctor_id,s.first_name||' '||s.last_name name,d.specialization
                               FROM doctors d JOIN staff s ON s.staff_id=d.staff_id ORDER BY s.first_name""").fetchall()
    db.close()
    return render_template("appointments.html", appointments=rows, patients=patients_list, doctors=doctors_list)


@app.route("/doctors")
def doctors():
    db=get_db()
    rows=db.execute("""SELECT d.*,s.first_name||' '||s.last_name name,s.email,s.phone,dep.dept_name
                       FROM doctors d JOIN staff s ON s.staff_id=d.staff_id
                       LEFT JOIN departments dep ON dep.dept_id=s.dept_id
                       ORDER BY name""").fetchall()
    db.close()
    return render_template("doctors.html", doctors=rows)


@app.route("/pharmacy")
def pharmacy():
    db=get_db()
    rows=db.execute("SELECT * FROM medicines ORDER BY name").fetchall()
    db.close()
    return render_template("pharmacy.html", medicines=rows)


@app.route("/billing")
def billing():
    db=get_db()
    rows=db.execute("""SELECT b.*,p.first_name||' '||p.last_name patient_name
                       FROM bills b JOIN patients p ON p.patient_id=b.patient_id ORDER BY b.bill_id DESC""").fetchall()
    db.close()
    return render_template("billing.html", bills=rows)


@app.route("/wards")
def wards():
    db=get_db()
    rows=db.execute("""SELECT w.*,d.dept_name FROM wards w LEFT JOIN departments d ON d.dept_id=w.dept_id
                       ORDER BY w.ward_id""").fetchall()
    rooms=db.execute("""SELECT r.*,w.ward_name FROM rooms r JOIN wards w ON w.ward_id=r.ward_id
                        ORDER BY r.room_number""").fetchall()
    db.close()
    return render_template("wards.html", wards=rows, rooms=rooms)


@app.route("/api/stats")
def api_stats():
    db=get_db()
    data={
        "patients": db.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
        "doctors": db.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
        "scheduled": db.execute("SELECT COUNT(*) FROM appointments WHERE status='Scheduled'").fetchone()[0],
        "low_stock": db.execute("SELECT COUNT(*) FROM medicines WHERE stock_qty <= reorder_level").fetchone()[0],
    }
    db.close()
    return jsonify(data)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
