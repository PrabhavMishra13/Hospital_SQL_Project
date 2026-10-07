# MediCore Hospital Management Web App

This project is generated from the uploaded Hospital Management System MySQL schema. The schema defines modules for patients, doctors/staff, appointments, billing/payments, pharmacy, and wards/rooms. See the source schema: hospital_schema(1).sql

## Stack
- Frontend: HTML5 + CSS3 + vanilla JavaScript
- Backend: Python + Flask
- Demo database: SQLite, initialized automatically from the schema's structure and sample data
- The original SQL remains the source of the data model; this demo uses SQLite so it can run without a MySQL server.

## Run
1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Run: `pip install -r requirements.txt`
4. Run: `python app.py`
5. Open: http://127.0.0.1:5000

## Main pages
- Dashboard
- Patients (search + register)
- Appointments (schedule)
- Doctors & Staff
- Wards & Rooms
- Pharmacy
- Billing & Payments

## Production note
For a production deployment, replace the SQLite connection layer with MySQL Connector/Python or SQLAlchemy and configure authentication, password hashing, CSRF protection, role-based authorization, validation, audit logging, and environment-based secrets.
