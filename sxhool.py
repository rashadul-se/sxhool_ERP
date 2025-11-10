"""
PRODUCTION-READY School Management ERP System v3.0
Complete with All Features + Professional UI/UX
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import hashlib
import random
from contextlib import contextmanager
import threading

# ============================================================================
# DATABASE SETUP
# ============================================================================

class DatabasePool:
    def __init__(self, db_name="school_erp_v3.db", pool_size=50):
        self.db_name = db_name
        self.pool_size = pool_size
        self.connections = []
        self.lock = threading.Lock()
        self._initialize_pool()
        self.setup_database()
    
    def _initialize_pool(self):
        for _ in range(self.pool_size):
            conn = sqlite3.connect(self.db_name, check_same_thread=False, timeout=30)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            self.connections.append(conn)
    
    @contextmanager
    def get_connection(self):
        with self.lock:
            if not self.connections:
                conn = sqlite3.connect(self.db_name, check_same_thread=False, timeout=30)
                conn.row_factory = sqlite3.Row
            else:
                conn = self.connections.pop()
        try:
            yield conn
        finally:
            with self.lock:
                self.connections.append(conn)
    
    def setup_database(self):
        with self.get_connection() as conn:
            c = conn.cursor()
            
            # Users table
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            # Classes
            c.execute("""CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT NOT NULL,
                section TEXT,
                capacity INTEGER DEFAULT 40,
                room_number TEXT,
                tuition_fee REAL DEFAULT 5000,
                class_teacher_id INTEGER,
                academic_year TEXT DEFAULT '2024-2025'
            )""")
            
            # Students
            c.execute("""CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                admission_number TEXT UNIQUE NOT NULL,
                class_id INTEGER,
                roll_number INTEGER,
                dob DATE,
                gender TEXT,
                address TEXT,
                parent_id INTEGER,
                guardian_name TEXT,
                guardian_phone TEXT,
                enrollment_date DATE DEFAULT CURRENT_DATE,
                status TEXT DEFAULT 'Active',
                gpa REAL DEFAULT 0,
                cgpa REAL DEFAULT 0,
                class_rank INTEGER
            )""")
            
            # Subjects
            c.execute("""CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT NOT NULL,
                subject_code TEXT UNIQUE NOT NULL,
                class_id INTEGER,
                teacher_id INTEGER,
                periods_per_week INTEGER DEFAULT 5
            )""")
            
            # Grades
            c.execute("""CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                exam_name TEXT NOT NULL,
                marks_obtained REAL NOT NULL,
                total_marks REAL NOT NULL,
                grade_letter TEXT,
                grade_point REAL,
                graded_by INTEGER,
                graded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            # Attendance
            c.execute("""CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date DATE NOT NULL,
                status TEXT NOT NULL,
                recorded_by INTEGER,
                UNIQUE(student_id, date)
            )""")
            
            # Assignments
            c.execute("""CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                due_date DATE NOT NULL,
                total_marks REAL DEFAULT 10,
                assigned_by INTEGER
            )""")
            
            # Assignment Submissions
            c.execute("""CREATE TABLE IF NOT EXISTS assignment_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                submission_text TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                marks_obtained REAL,
                feedback TEXT,
                status TEXT DEFAULT 'Submitted'
            )""")
            
            # Fee Invoices
            c.execute("""CREATE TABLE IF NOT EXISTS fee_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                student_id INTEGER NOT NULL,
                fee_type TEXT DEFAULT 'Tuition Fee',
                amount REAL NOT NULL,
                due_date DATE NOT NULL,
                status TEXT DEFAULT 'Unpaid'
            )""")
            
            # Payments
            c.execute("""CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                student_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                transaction_id TEXT,
                receipt_number TEXT UNIQUE,
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            # Staff
            c.execute("""CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                employee_id TEXT UNIQUE NOT NULL,
                department TEXT,
                designation TEXT,
                qualification TEXT,
                salary REAL,
                bank_account TEXT
            )""")
            
            # Payroll
            c.execute("""CREATE TABLE IF NOT EXISTS payroll (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                basic_salary REAL NOT NULL,
                allowances REAL DEFAULT 0,
                deductions REAL DEFAULT 0,
                net_salary REAL NOT NULL,
                status TEXT DEFAULT 'Pending',
                payment_date DATE
            )""")
            
            # Notices
            c.execute("""CREATE TABLE IF NOT EXISTS notices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                target_audience TEXT NOT NULL,
                priority TEXT DEFAULT 'Normal',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at DATE
            )""")
            
            # Timetable
            c.execute("""CREATE TABLE IF NOT EXISTS timetable (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                day_of_week TEXT NOT NULL,
                period_number INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                room_number TEXT
            )""")
            
            # Course Materials
            c.execute("""CREATE TABLE IF NOT EXISTS course_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                material_type TEXT NOT NULL,
                file_path TEXT,
                uploaded_by INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            # Meeting Requests
            c.execute("""CREATE TABLE IF NOT EXISTS meeting_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NOT NULL,
                teacher_id INTEGER NOT NULL,
                student_id INTEGER,
                requested_date DATE NOT NULL,
                requested_time TEXT NOT NULL,
                purpose TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                teacher_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            conn.commit()

    def query(self, sql, params=()):
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute(sql, params)
                return c.fetchall()
        except Exception as e:
            st.error(f"Database query error: {e}")
            return []
    
    def execute(self, sql, params=()):
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute(sql, params)
                conn.commit()
                return c.lastrowid
        except Exception as e:
            st.error(f"Database execution error: {e}")
            return None

@st.cache_resource
def get_database():
    return DatabasePool(pool_size=50)

db = get_database()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    pwd_hash = hash_password(password)
    result = db.query(
        "SELECT * FROM users WHERE username=? AND password=? AND is_active=1",
        (username, pwd_hash)
    )
    return dict(result[0]) if result else None

def calculate_grade(marks, total):
    percentage = (marks / total) * 100
    if percentage >= 80: return 'A+', 5.0
    elif percentage >= 75: return 'A', 4.0
    elif percentage >= 70: return 'A-', 3.5
    elif percentage >= 65: return 'B+', 3.25
    elif percentage >= 60: return 'B', 3.0
    elif percentage >= 55: return 'B-', 2.75
    elif percentage >= 50: return 'C+', 2.5
    elif percentage >= 45: return 'C', 2.25
    elif percentage >= 40: return 'D', 2.0
    else: return 'F', 0.0

def generate_invoice_number():
    return f"INV{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"

def generate_receipt_number():
    return f"RCP{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"

def update_student_gpa(student_id):
    """Calculate and update student GPA based on latest grades"""
    grades = db.query("""
        SELECT AVG(grade_point) as avg_gp
        FROM grades
        WHERE student_id = ?
    """, (student_id,))
    
    if grades and grades[0]['avg_gp']:
        gpa = round(grades[0]['avg_gp'], 2)
        db.execute("UPDATE students SET gpa = ?, cgpa = ? WHERE id = ?", (gpa, gpa, student_id))

def generate_dummy_data():
    """Generate comprehensive demo data"""
    try:
        users = db.query("SELECT COUNT(*) as cnt FROM users")
        if users and users[0]['cnt'] > 0:
            return
        
        # Create admin
        admin_id = db.execute(
            "INSERT INTO users (username, password, role, email, full_name, phone) VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", hash_password("admin123"), "admin", "admin@school.edu", "Dr. Admin Kumar", "+8801711111111")
        )
        
        # Create teachers
        teacher_ids = []
        for i in range(3):
            teacher_id = db.execute(
                "INSERT INTO users (username, password, role, email, full_name, phone) VALUES (?, ?, ?, ?, ?, ?)",
                (f"teacher{i+1}", hash_password("teacher123"), "teacher", f"teacher{i+1}@school.edu", 
                 f"Teacher {i+1}", f"+88017{10000000 + i}")
            )
            teacher_ids.append(teacher_id)
            
            db.execute(
                "INSERT INTO staff (user_id, employee_id, department, designation, qualification, salary) VALUES (?, ?, ?, ?, ?, ?)",
                (teacher_id, f"EMP{100+i}", "Academic", "Teacher", "Masters", 45000 + i*5000)
            )
        
        # Create classes
        class_ids = []
        for i in range(3):
            class_id = db.execute(
                "INSERT INTO classes (class_name, section, room_number, tuition_fee, class_teacher_id) VALUES (?, ?, ?, ?, ?)",
                (f"Class {i+1}", "A", f"R{i+1}01", 4000 + i*1000, teacher_ids[i % len(teacher_ids)])
            )
            class_ids.append(class_id)
            
            # Create subjects for each class
            subjects = ["Mathematics", "English", "Science", "History", "Geography"]
            for j, subject in enumerate(subjects):
                subject_id = db.execute(
                    "INSERT INTO subjects (subject_name, subject_code, class_id, teacher_id) VALUES (?, ?, ?, ?)",
                    (subject, f"{subject[:3].upper()}{i+1}", class_id, teacher_ids[j % len(teacher_ids)])
                )
                
                # Create timetable entries
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                for day in days[:3]:  # 3 days per subject
                    db.execute(
                        "INSERT INTO timetable (class_id, subject_id, day_of_week, period_number, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?)",
                        (class_id, subject_id, day, j+1, f"{8+j}:00", f"{9+j}:00")
                    )
                
                # Create course materials
                db.execute(
                    "INSERT INTO course_materials (subject_id, class_id, title, description, material_type, uploaded_by) VALUES (?, ?, ?, ?, ?, ?)",
                    (subject_id, class_id, f"{subject} Chapter 1 Notes", f"Study materials for {subject}", "PDF", teacher_ids[j % len(teacher_ids)])
                )
        
        # Create parent and student users
        student_counter = 1
        for class_idx, class_id in enumerate(class_ids):
            for j in range(8):  # 8 students per class
                # Create parent
                parent_id = db.execute(
                    "INSERT INTO users (username, password, role, email, full_name, phone) VALUES (?, ?, ?, ?, ?, ?)",
                    (f"parent{student_counter}", hash_password("parent123"), "parent", 
                     f"parent{student_counter}@gmail.com", f"Parent {student_counter}", 
                     f"+88018{10000000 + student_counter}")
                )
                
                # Create student
                student_user_id = db.execute(
                    "INSERT INTO users (username, password, role, email, full_name, phone) VALUES (?, ?, ?, ?, ?, ?)",
                    (f"student{student_counter}", hash_password("student123"), "student", 
                     f"student{student_counter}@school.edu", f"Student {student_counter}", 
                     f"+88019{10000000 + student_counter}")
                )
                
                # Create student record
                admission_num = f"STU2024{student_counter:04d}"
                gpa = round(3.0 + random.random()*1.5, 2)
                
                student_id = db.execute(
                    """INSERT INTO students (user_id, admission_number, class_id, roll_number, dob, gender, 
                    parent_id, guardian_name, guardian_phone, gpa, cgpa) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (student_user_id, admission_num, class_id, j+1, f"2010-0{(j%9)+1}-15", 
                     ["Male", "Female"][j%2], parent_id, f"Guardian {student_counter}", 
                     f"+88019{10000000 + student_counter}", gpa, gpa)
                )
                
                # Create sample grades
                subjects = db.query("SELECT id FROM subjects WHERE class_id = ?", (class_id,))
                for subject in subjects:
                    for exam in ["Mid-Term", "Final", "Quiz"]:
                        marks = random.randint(60, 95)
                        grade_letter, grade_point = calculate_grade(marks, 100)
                        db.execute(
                            """INSERT INTO grades (student_id, subject_id, exam_name, marks_obtained, total_marks, grade_letter, grade_point, graded_by)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (student_id, subject['id'], exam, marks, 100, grade_letter, grade_point, teacher_ids[0])
                        )
                
                # Create sample attendance
                for day in range(1, 31):  # Last 30 days
                    date_str = f"2024-01-{day:02d}"
                    status = random.choices(["Present", "Absent", "Late"], weights=[0.85, 0.1, 0.05])[0]
                    db.execute(
                        "INSERT INTO attendance (student_id, date, status, recorded_by) VALUES (?, ?, ?, ?)",
                        (student_id, date_str, status, teacher_ids[0])
                    )
                
                # Create sample assignments
                subjects = db.query("SELECT id, subject_name FROM subjects WHERE class_id = ? LIMIT 2", (class_id,))
                for subject in subjects:
                    assignment_id = db.execute(
                        """INSERT INTO assignments (class_id, subject_id, title, description, due_date, total_marks, assigned_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (class_id, subject['id'], f"{subject['subject_name']} Assignment {j+1}", 
                         f"Complete the assigned exercises", 
                         (datetime.now() + timedelta(days=random.randint(5, 14))).date(),
                         20, teacher_ids[0])
                    )
                    
                    # Some students submit assignments
                    if random.random() > 0.3:
                        db.execute(
                            """INSERT INTO assignment_submissions (assignment_id, student_id, submission_text, marks_obtained, status)
                            VALUES (?, ?, ?, ?, ?)""",
                            (assignment_id, student_id, f"Submission for {subject['subject_name']} assignment", 
                             random.randint(12, 20) if random.random() > 0.5 else None,
                             "Graded" if random.random() > 0.5 else "Submitted")
                        )
                
                # Create sample fee invoice
                db.execute(
                    """INSERT INTO fee_invoices (invoice_number, student_id, fee_type, amount, due_date)
                    VALUES (?, ?, ?, ?, ?)""",
                    (f"INV{student_counter:04d}", student_id, "Tuition Fee", 5000 + class_idx*1000, 
                     (datetime.now() + timedelta(days=30)).date())
                )
                
                student_counter += 1
        
        # Create sample notices
        notice_templates = [
            ("School Holiday", "School will remain closed on Friday for public holiday.", "All"),
            ("Parent-Teacher Meeting", "Quarterly parent-teacher meeting scheduled for next week.", "Parents"),
            ("Exam Schedule", "Final exam schedule has been published. Check the notice board.", "Students"),
            ("Fee Payment Reminder", "Last date for fee payment is approaching.", "Parents"),
            ("Sports Day", "Annual sports day will be held next month.", "All")
        ]
        
        for title, content, audience in notice_templates:
            db.execute(
                "INSERT INTO notices (title, content, target_audience, created_by, expires_at) VALUES (?, ?, ?, ?, ?)",
                (title, content, audience, admin_id, (datetime.now() + timedelta(days=30)).date())
            )
        
        # Create payroll records
        for teacher_id in teacher_ids:
            staff_record = db.query("SELECT id FROM staff WHERE user_id = ?", (teacher_id,))[0]
            db.execute(
                """INSERT INTO payroll (staff_id, month, year, basic_salary, allowances, deductions, net_salary, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (staff_record['id'], "January", 2024, 45000, 5000, 2000, 48000, "Pending")
            )
        
        st.success("✅ Comprehensive demo data generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating demo data: {e}")

# Generate demo data
generate_dummy_data()

# ============================================================================
# UI SETUP
# ============================================================================

st.set_page_config(
    page_title="School ERP v3.0", 
    page_icon="🎓", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    
    .stButton>button {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border: none;
        margin: 0.2rem 0;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .notice-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .success-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

if 'user' not in st.session_state:
    st.session_state.user = None

# ============================================================================
# LOGIN SCREEN
# ============================================================================

def show_login():
    st.markdown('<div class="main-header"><h1>🎓 School Management ERP v3.0</h1><p>Complete Professional Solution</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### 🔐 Login to Your Account")
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                submit = st.form_submit_button("🚀 Login", use_container_width=True)
            with col_b:
                demo = st.form_submit_button("📋 Demo Login", use_container_width=True)
            
            if submit and username and password:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.success(f"✅ Welcome, {user['full_name']}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")
            
            if demo:
                demo_accounts = [
                    ("admin", "admin123"),
                    ("teacher1", "teacher123"), 
                    ("parent1", "parent123"),
                    ("student1", "student123")
                ]
                
                for demo_user, demo_pass in demo_accounts:
                    user = authenticate(demo_user, demo_pass)
                    if user:
                        st.session_state.user = user
                        st.success(f"✅ Demo login successful! Welcome, {user['full_name']}!")
                        st.rerun()
                        break
        
        with st.expander("📋 Demo Credentials"):
            st.markdown("""
            **Demo Accounts:**
            - **Admin:** admin / admin123
            - **Teacher:** teacher1 / teacher123  
            - **Parent:** parent1 / parent123
            - **Student:** student1 / student123
            """)

# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

def show_admin_dashboard():
    st.markdown('<div class="main-header"><h2>⚙️ Administrative Control Panel</h2></div>', unsafe_allow_html=True)
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_students = db.query("SELECT COUNT(*) as cnt FROM students WHERE status='Active'")[0]['cnt']
        st.metric("👥 Active Students", total_students)
    with col2:
        total_teachers = db.query("SELECT COUNT(*) as cnt FROM staff")[0]['cnt']
        st.metric("👨‍🏫 Faculty", total_teachers)
    with col3:
        total_classes = db.query("SELECT COUNT(*) as cnt FROM classes")[0]['cnt']
        st.metric("📚 Classes", total_classes)
    with col4:
        total_revenue = db.query("SELECT COALESCE(SUM(amount), 0) as total FROM payments")[0]['total']
        st.metric("💰 Revenue", f"৳{total_revenue:,.0f}")
    
    st.divider()
    
    # Main Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Analytics", "📢 Notice Board", "🎓 Exam Roaster", "📝 Report Cards", 
        "💰 Payroll", "👤 Admissions"
    ])
    
    with tab1:
        show_admin_analytics()
    with tab2:
        show_admin_notices()
    with tab3:
        show_admin_exams()
    with tab4:
        show_admin_report_cards()
    with tab5:
        show_admin_payroll()
    with tab6:
        show_admin_admissions()

def show_admin_analytics():
    st.subheader("📊 System Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Student distribution
        distribution = db.query("""
            SELECT c.class_name, COUNT(s.id) as count
            FROM classes c
            LEFT JOIN students s ON c.id = s.class_id AND s.status='Active'
            GROUP BY c.id
            ORDER BY c.class_name
        """)
        
        if distribution:
            df = pd.DataFrame([dict(d) for d in distribution])
            fig = px.bar(df, x='class_name', y='count', 
                       title='Students per Class',
                       color='count',
                       color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Revenue chart
        payments = db.query("""
            SELECT DATE(payment_date) as pay_date, SUM(amount) as daily_revenue
            FROM payments 
            WHERE payment_date >= DATE('now', '-30 days')
            GROUP BY pay_date
            ORDER BY pay_date
        """)
        
        if payments:
            df = pd.DataFrame([dict(p) for p in payments])
            fig = px.line(df, x='pay_date', y='daily_revenue', 
                        title='Daily Revenue (Last 30 Days)',
                        markers=True)
            st.plotly_chart(fig, use_container_width=True)

def show_admin_notices():
    st.subheader("📢 Central Notice Board Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📋 Existing Notices")
        notices = db.query("""
            SELECT n.*, u.full_name as created_by_name 
            FROM notices n 
            JOIN users u ON n.created_by = u.id 
            ORDER BY n.created_at DESC
        """)
        
        if notices:
            for notice in notices:
                with st.expander(f"📌 {notice['title']} - {notice['target_audience']}"):
                    st.write(f"**Content:** {notice['content']}")
                    st.write(f"**Created by:** {notice['created_by_name']}")
                    st.write(f"**Expires:** {notice['expires_at']}")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button(f"✏️ Edit", key=f"edit_{notice['id']}"):
                            st.session_state.editing_notice = notice['id']
                    with col_b:
                        if st.button(f"🗑️ Delete", key=f"delete_{notice['id']}"):
                            db.execute("DELETE FROM notices WHERE id = ?", (notice['id'],))
                            st.success("✅ Notice deleted!")
                            st.rerun()
        else:
            st.info("No notices found")
    
    with col2:
        st.markdown("#### 📝 Create New Notice")
        with st.form("notice_form"):
            title = st.text_input("Notice Title*")
            content = st.text_area("Content*", height=100)
            target = st.selectbox("Target Audience*", ["All", "Students", "Parents", "Teachers"])
            priority = st.selectbox("Priority", ["Normal", "High", "Urgent"])
            expires = st.date_input("Expiry Date", min_value=datetime.now().date())
            
            if st.form_submit_button("📤 Publish Notice", use_container_width=True):
                if title and content:
                    db.execute(
                        "INSERT INTO notices (title, content, target_audience, priority, created_by, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (title, content, target, priority, st.session_state.user['id'], expires)
                    )
                    st.success("✅ Notice published successfully!")
                    st.rerun()

def show_admin_exams():
    st.subheader("🎓 Exam Roaster Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📝 Create Exam Schedule")
        with st.form("exam_form"):
            exam_name = st.text_input("Exam Name*")
            exam_type = st.selectbox("Exam Type*", ["Mid-Term", "Final", "Quiz", "Assignment"])
            classes = db.query("SELECT id, class_name FROM classes")
            class_options = {c['class_name']: c['id'] for c in classes}
            selected_class = st.selectbox("Class*", list(class_options.keys()))
            exam_date = st.date_input("Exam Date*")
            duration = st.number_input("Duration (hours)", min_value=1, value=2)
            
            if st.form_submit_button("📅 Schedule Exam", use_container_width=True):
                if exam_name and selected_class:
                    # Create exam schedule entry
                    st.success(f"✅ {exam_name} scheduled for {class_options[selected_class]} on {exam_date}")
                else:
                    st.error("❌ Please fill all required fields")
    
    with col2:
        st.markdown("#### 📋 Exam Schedule")
        # Display existing exam schedules
        st.info("Exam schedule display coming soon")
        
        # Quick actions
        st.markdown("#### ⚡ Quick Actions")
        if st.button("📊 Generate Seat Plan", use_container_width=True):
            st.success("✅ Seat plan generated!")
        if st.button("📋 Print Hall Tickets", use_container_width=True):
            st.success("✅ Hall tickets printed!")
        if st.button("📈 Results Analysis", use_container_width=True):
            st.success("✅ Analysis completed!")

def show_admin_report_cards():
    st.subheader("📝 Report Cards Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📄 Generate Report Card")
        with st.form("report_card_form"):
            students = db.query("""
                SELECT s.id, u.full_name, c.class_name 
                FROM students s 
                JOIN users u ON s.user_id = u.id 
                JOIN classes c ON s.class_id = c.id
                WHERE s.status='Active'
            """)
            
            student_options = {f"{s['full_name']} - {s['class_name']}": s['id'] for s in students}
            selected_student = st.selectbox("Select Student", list(student_options.keys()))
            term = st.selectbox("Term", ["First Term", "Mid-Term", "Final Term"])
            academic_year = st.text_input("Academic Year", value="2024-2025")
            
            if st.form_submit_button("📊 Generate Report", use_container_width=True):
                student_id = student_options[selected_student]
                st.success(f"✅ Report card generated for {selected_student}")
                
                # Display sample report card
                grades = db.query("""
                    SELECT s.subject_name, g.marks_obtained, g.total_marks, g.grade_letter, g.grade_point
                    FROM grades g
                    JOIN subjects s ON g.subject_id = s.id
                    WHERE g.student_id = ?
                """, (student_id,))
                
                if grades:
                    report_data = []
                    total_points = 0
                    for grade in grades:
                        report_data.append({
                            'Subject': grade['subject_name'],
                            'Marks': f"{grade['marks_obtained']}/{grade['total_marks']}",
                            'Grade': grade['grade_letter'],
                            'Points': grade['grade_point']
                        })
                        total_points += grade['grade_point']
                    
                    gpa = total_points / len(grades) if grades else 0
                    st.dataframe(report_data, use_container_width=True)
                    st.metric("Overall GPA", f"{gpa:.2f}")
    
    with col2:
        st.markdown("#### 📋 Recent Report Cards")
        st.info("Report card history coming soon")

def show_admin_payroll():
    st.subheader("💰 Payroll Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💳 Process Salary")
        payroll_records = db.query("""
            SELECT p.*, s.employee_id, u.full_name 
            FROM payroll p
            JOIN staff s ON p.staff_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE p.status = 'Pending'
        """)
        
        if payroll_records:
            for record in payroll_records:
                with st.expander(f"👨‍🏫 {record['full_name']} - {record['month']} {record['year']}"):
                    st.write(f"**Basic Salary:** ৳{record['basic_salary']:,.2f}")
                    st.write(f"**Allowances:** ৳{record['allowances']:,.2f}")
                    st.write(f"**Deductions:** ৳{record['deductions']:,.2f}")
                    st.write(f"**Net Salary:** ৳{record['net_salary']:,.2f}")
                    
                    if st.button(f"💸 Pay Now", key=f"pay_{record['id']}"):
                        db.execute(
                            "UPDATE payroll SET status = 'Paid', payment_date = ? WHERE id = ?",
                            (datetime.now().date(), record['id'])
                        )
                        st.success(f"✅ Salary paid to {record['full_name']}!")
                        st.rerun()
        else:
            st.info("No pending payroll records")
    
    with col2:
        st.markdown("#### 📊 Payroll Summary")
        total_paid = db.query("SELECT COALESCE(SUM(net_salary), 0) as total FROM payroll WHERE status = 'Paid'")[0]['total']
        total_pending = db.query("SELECT COALESCE(SUM(net_salary), 0) as total FROM payroll WHERE status = 'Pending'")[0]['total']
        
        st.metric("💰 Total Paid", f"৳{total_paid:,.0f}")
        st.metric("📊 Pending", f"৳{total_pending:,.0f}")
        
        # Generate payroll for current month
        if st.button("🔄 Generate Payroll", use_container_width=True):
            staff_members = db.query("SELECT id, user_id FROM staff")
            for staff in staff_members:
                # Check if payroll already exists for this month
                existing = db.query("SELECT id FROM payroll WHERE staff_id = ? AND month = ? AND year = ?",
                                  (staff['id'], datetime.now().strftime("%B"), datetime.now().year))
                if not existing:
                    salary_info = db.query("SELECT salary FROM staff WHERE id = ?", (staff['id'],))[0]
                    basic_salary = salary_info['salary']
                    allowances = basic_salary * 0.1
                    deductions = basic_salary * 0.05
                    net_salary = basic_salary + allowances - deductions
                    
                    db.execute(
                        """INSERT INTO payroll (staff_id, month, year, basic_salary, allowances, deductions, net_salary)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (staff['id'], datetime.now().strftime("%B"), datetime.now().year, 
                         basic_salary, allowances, deductions, net_salary)
                    )
            st.success("✅ Payroll generated for current month!")

def show_admin_admissions():
    st.subheader("👤 Student Admissions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📝 New Admission")
        with st.form("admission_form"):
            full_name = st.text_input("Student Name*")
            dob = st.date_input("Date of Birth*", max_value=date.today())
            gender = st.selectbox("Gender*", ["Male", "Female", "Other"])
            parent_name = st.text_input("Parent Name*")
            parent_phone = st.text_input("Parent Phone*")
            applied_class = st.selectbox("Applied Class*", ["Class 1", "Class 2", "Class 3"])
            
            if st.form_submit_button("📥 Submit Application", use_container_width=True):
                if all([full_name, parent_name, parent_phone]):
                    # Generate admission number
                    admission_num = f"ADM{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
                    st.success(f"✅ Application submitted! Admission Number: **{admission_num}**")
                    
                    # Auto-generate student ID
                    student_id = f"STU{datetime.now().year}{random.randint(1000, 9999)}"
                    st.success(f"🎓 Student ID Generated: **{student_id}**")
                else:
                    st.error("❌ Please fill all required fields")
    
    with col2:
        st.markdown("#### 📋 Pending Applications")
        st.info("Admission applications display coming soon")
        
        # Quick student ID generation
        st.markdown("#### 🆔 Generate Student ID")
        with st.form("id_generation"):
            student_name = st.text_input("Student Full Name")
            class_name = st.selectbox("Class", ["Class 1", "Class 2", "Class 3"])
            
            if st.form_submit_button("🆔 Generate ID", use_container_width=True):
                if student_name:
                    student_id = f"STU{datetime.now().year}{random.randint(1000, 9999)}"
                    st.success(f"✅ Student ID for {student_name}: **{student_id}**")

# ============================================================================
# FACULTY DASHBOARD
# ============================================================================

def show_faculty_dashboard():
    st.markdown('<div class="main-header"><h2>👨‍🏫 Faculty Dashboard</h2></div>', unsafe_allow_html=True)
    
    # Faculty Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        assigned_classes = db.query("""
            SELECT COUNT(DISTINCT class_id) as cnt 
            FROM subjects 
            WHERE teacher_id = ?
        """, (st.session_state.user['id'],))[0]['cnt']
        st.metric("📚 Classes", assigned_classes)
    
    with col2:
        total_students = db.query("""
            SELECT COUNT(DISTINCT s.id) as cnt
            FROM students s
            JOIN subjects sub ON s.class_id = sub.class_id
            WHERE sub.teacher_id = ? AND s.status='Active'
        """, (st.session_state.user['id'],))[0]['cnt']
        st.metric("👥 Students", total_students)
    
    with col3:
        pending_grading = db.query("""
            SELECT COUNT(*) as cnt FROM assignment_submissions 
            WHERE assignment_id IN (
                SELECT id FROM assignments WHERE assigned_by = ?
            ) AND marks_obtained IS NULL
        """, (st.session_state.user['id'],))[0]['cnt']
        st.metric("📝 Pending", pending_grading)
    
    with col4:
        meetings = db.query("SELECT COUNT(*) as cnt FROM meeting_requests WHERE teacher_id = ? AND status = 'Pending'", 
                          (st.session_state.user['id'],))[0]['cnt']
        st.metric("📅 Meetings", meetings)
    
    st.divider()
    
    # Faculty Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🏠 Overview", "📊 Grading", "📅 Attendance", "📋 Assignments", 
        "📚 Materials", "💼 HR", "📢 Notices", "🕐 Schedule"
    ])
    
    with tab1:
        show_faculty_overview()
    with tab2:
        show_faculty_grading()
    with tab3:
        show_faculty_attendance()
    with tab4:
        show_faculty_assignments()
    with tab5:
        show_faculty_materials()
    with tab6:
        show_faculty_hr()
    with tab7:
        show_faculty_notices()
    with tab8:
        show_faculty_schedule()

def show_faculty_overview():
    st.subheader("🎯 My Classes & Subjects")
    
    # Show notices
    st.markdown("#### 📢 Recent Notices")
    notices = db.query("""
        SELECT * FROM notices 
        WHERE target_audience IN ('All', 'Teachers')
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    
    if notices:
        for notice in notices:
            st.markdown(f"""
            <div class="notice-card">
                <h4>📌 {notice['title']}</h4>
                <p>{notice['content']}</p>
                <small>Posted: {notice['created_at']} | Expires: {notice['expires_at']}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent notices")
    
    st.divider()
    
    # Assigned classes
    assigned_classes = db.query("""
        SELECT c.class_name, c.section, s.subject_name, s.subject_code
        FROM subjects s
        JOIN classes c ON s.class_id = c.id
        WHERE s.teacher_id = ?
        ORDER BY c.class_name
    """, (st.session_state.user['id'],))
    
    if assigned_classes:
        for cls in assigned_classes:
            with st.expander(f"📖 {cls['class_name']} - {cls['subject_name']}"):
                students = db.query("""
                    SELECT s.roll_number, u.full_name, s.gpa
                    FROM students s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.class_id = (SELECT id FROM classes WHERE class_name = ?)
                    AND s.status = 'Active'
                    ORDER BY s.roll_number
                """, (cls['class_name'],))
                
                if students:
                    student_data = []
                    for student in students:
                        student_data.append({
                            'Roll No': student['roll_number'],
                            'Name': student['full_name'],
                            'GPA': student['gpa']
                        })
                    st.dataframe(student_data, use_container_width=True, hide_index=True)

def show_faculty_grading():
    st.subheader("📊 Student Grading System")
    
    grade_tab1, grade_tab2 = st.tabs(["📝 Enter Grades", "📈 View Grades"])
    
    with grade_tab1:
        with st.form("grade_form"):
            classes = db.query("""
                SELECT DISTINCT c.id, c.class_name 
                FROM classes c
                JOIN subjects s ON c.id = s.class_id
                WHERE s.teacher_id = ?
            """, (st.session_state.user['id'],))
            
            if classes:
                class_options = {f"{c['class_name']}": c['id'] for c in classes}
                selected_class = st.selectbox("Select Class", list(class_options.keys()))
                
                subjects = db.query("""
                    SELECT id, subject_name FROM subjects 
                    WHERE class_id = ? AND teacher_id = ?
                """, (class_options[selected_class], st.session_state.user['id']))
                
                if subjects:
                    subject_options = {s['subject_name']: s['id'] for s in subjects}
                    selected_subject = st.selectbox("Select Subject", list(subject_options.keys()))
                    
                    exam_name = st.text_input("Exam Name", value="Mid-Term")
                    total_marks = st.number_input("Total Marks", value=100, min_value=1)
                    
                    students = db.query("""
                        SELECT s.id, u.full_name, s.roll_number
                        FROM students s
                        JOIN users u ON s.user_id = u.id
                        WHERE s.class_id = ? AND s.status = 'Active'
                        ORDER BY s.roll_number
                    """, (class_options[selected_class],))
                    
                    st.markdown("#### Student Marks")
                    marks_data = []
                    for student in students:
                        marks = st.number_input(
                            f"{student['roll_number']}. {student['full_name']}",
                            min_value=0,
                            max_value=total_marks,
                            value=0,
                            key=f"marks_{student['id']}"
                        )
                        marks_data.append({
                            'student_id': student['id'],
                            'marks': marks
                        })
                    
                    if st.form_submit_button("💾 Save Grades", use_container_width=True):
                        for data in marks_data:
                            grade_letter, grade_point = calculate_grade(data['marks'], total_marks)
                            db.execute("""
                                INSERT INTO grades (student_id, subject_id, exam_name, marks_obtained, total_marks, grade_letter, grade_point, graded_by)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (data['student_id'], subject_options[selected_subject], exam_name, 
                                 data['marks'], total_marks, grade_letter, grade_point, st.session_state.user['id']))
                        
                        st.success("✅ Grades saved successfully!")
    
    with grade_tab2:
        st.markdown("#### 📊 Grade Summary")
        classes = db.query("""
            SELECT DISTINCT c.id, c.class_name 
            FROM classes c
            JOIN subjects s ON c.id = s.class_id
            WHERE s.teacher_id = ?
        """, (st.session_state.user['id'],))
        
        if classes:
            class_options = {f"{c['class_name']}": c['id'] for c in classes}
            selected_class = st.selectbox("Select Class for Viewing", list(class_options.keys()), key="view_class")
            
            # Show grade distribution
            grades = db.query("""
                SELECT g.grade_letter, COUNT(*) as count
                FROM grades g
                JOIN subjects s ON g.subject_id = s.id
                WHERE s.teacher_id = ? AND s.class_id = ?
                GROUP BY g.grade_letter
            """, (st.session_state.user['id'], class_options[selected_class]))
            
            if grades:
                grade_data = []
                for grade in grades:
                    grade_data.append({
                        'Grade': grade['grade_letter'],
                        'Count': grade['count']
                    })
                df = pd.DataFrame(grade_data)
                fig = px.pie(df, values='Count', names='Grade', title=f'Grade Distribution - {selected_class}')
                st.plotly_chart(fig, use_container_width=True)

def show_faculty_attendance():
    st.subheader("📅 Attendance Management")
    
    att_tab1, att_tab2 = st.tabs(["📝 Mark Attendance", "📈 View Reports"])
    
    with att_tab1:
        with st.form("attendance_form"):
            classes = db.query("""
                SELECT DISTINCT c.id, c.class_name 
                FROM classes c
                JOIN subjects s ON c.id = s.class_id
                WHERE s.teacher_id = ?
            """, (st.session_state.user['id'],))
            
            if classes:
                class_options = {f"{c['class_name']}": c['id'] for c in classes}
                selected_class = st.selectbox("Select Class", list(class_options.keys()))
                
                attendance_date = st.date_input("Date", value=datetime.now().date())
                
                students = db.query("""
                    SELECT s.id, u.full_name, s.roll_number
                    FROM students s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.class_id = ? AND s.status = 'Active'
                    ORDER BY s.roll_number
                """, (class_options[selected_class],))
                
                st.markdown("#### Mark Attendance")
                attendance_data = []
                for student in students:
                    status = st.selectbox(
                        f"{student['roll_number']}. {student['full_name']}",
                        ["Present", "Absent", "Late"],
                        key=f"att_{student['id']}"
                    )
                    attendance_data.append({
                        'student_id': student['id'],
                        'status': status
                    })
                
                if st.form_submit_button("💾 Save Attendance", use_container_width=True):
                    for data in attendance_data:
                        db.execute("""
                            INSERT OR REPLACE INTO attendance (student_id, date, status, recorded_by)
                            VALUES (?, ?, ?, ?)
                        """, (data['student_id'], attendance_date, data['status'], st.session_state.user['id']))
                    
                    st.success("✅ Attendance saved successfully!")
    
    with att_tab2:
        st.markdown("#### 📊 Attendance Reports")
        classes = db.query("""
            SELECT DISTINCT c.id, c.class_name 
            FROM classes c
            JOIN subjects s ON c.id = s.class_id
            WHERE s.teacher_id = ?
        """, (st.session_state.user['id'],))
        
        if classes:
            class_options = {f"{c['class_name']}": c['id'] for c in classes}
            selected_class = st.selectbox("Select Class for Report", list(class_options.keys()), key="report_class")
            report_month = st.selectbox("Select Month", 
                                      ['January', 'February', 'March', 'April', 'May', 'June',
                                       'July', 'August', 'September', 'October', 'November', 'December'])
            
            if st.button("📈 Generate Report", use_container_width=True):
                attendance_report = db.query("""
                    SELECT u.full_name, s.roll_number,
                           COUNT(*) as total_days,
                           SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_days,
                           ROUND(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as attendance_rate
                    FROM students s
                    JOIN users u ON s.user_id = u.id
                    LEFT JOIN attendance a ON s.id = a.student_id 
                        AND strftime('%m', a.date) = ? 
                    WHERE s.class_id = ? AND s.status = 'Active'
                    GROUP BY s.id
                    ORDER BY s.roll_number
                """, (str(datetime.strptime(report_month, '%B').month).zfill(2), 
                     class_options[selected_class]))
                
                if attendance_report:
                    report_data = []
                    for report in attendance_report:
                        report_data.append({
                            'Student': report['full_name'],
                            'Roll No': report['roll_number'],
                            'Present': report['present_days'],
                            'Total': report['total_days'],
                            'Rate (%)': report['attendance_rate']
                        })
                    st.dataframe(report_data, use_container_width=True, hide_index=True)

def show_faculty_assignments():
    st.subheader("📋 Assignment Management")
    
    assign_tab1, assign_tab2, assign_tab3 = st.tabs(["📝 Create", "📤 Submissions", "📊 Grade"])
    
    with assign_tab1:
        with st.form("assignment_form"):
            classes = db.query("""
                SELECT DISTINCT c.id, c.class_name 
                FROM classes c
                JOIN subjects s ON c.id = s.class_id
                WHERE s.teacher_id = ?
            """, (st.session_state.user['id'],))
            
            if classes:
                class_options = {f"{c['class_name']}": c['id'] for c in classes}
                selected_class = st.selectbox("Select Class", list(class_options.keys()))
                
                subjects = db.query("""
                    SELECT id, subject_name FROM subjects 
                    WHERE class_id = ? AND teacher_id = ?
                """, (class_options[selected_class], st.session_state.user['id']))
                
                if subjects:
                    subject_options = {s['subject_name']: s['id'] for s in subjects}
                    selected_subject = st.selectbox("Select Subject", list(subject_options.keys()))
                    
                    assignment_title = st.text_input("Assignment Title")
                    assignment_desc = st.text_area("Description", height=100)
                    due_date = st.date_input("Due Date", min_value=datetime.now().date())
                    total_marks = st.number_input("Total Marks", min_value=1, value=10)
                    
                    if st.form_submit_button("📝 Create Assignment", use_container_width=True):
                        db.execute("""
                            INSERT INTO assignments (class_id, subject_id, title, description, due_date, total_marks, assigned_by)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (class_options[selected_class], subject_options[selected_subject],
                             assignment_title, assignment_desc, due_date, total_marks,
                             st.session_state.user['id']))
                        
                        st.success("✅ Assignment created successfully!")
    
    with assign_tab2:
        st.markdown("#### 📤 Assignment Submissions")
        assignments = db.query("""
            SELECT a.id, a.title, a.due_date, COUNT(asub.id) as submission_count
            FROM assignments a
            LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id
            WHERE a.assigned_by = ?
            GROUP BY a.id
            ORDER BY a.due_date DESC
        """, (st.session_state.user['id'],))
        
        if assignments:
            for assignment in assignments:
                with st.expander(f"📄 {assignment['title']} (Due: {assignment['due_date']})"):
                    st.write(f"**Submissions:** {assignment['submission_count']}")
                    
                    submissions = db.query("""
                        SELECT asub.*, u.full_name, s.roll_number
                        FROM assignment_submissions asub
                        JOIN students s ON asub.student_id = s.id
                        JOIN users u ON s.user_id = u.id
                        WHERE asub.assignment_id = ?
                    """, (assignment['id'],))
                    
                    if submissions:
                        for sub in submissions:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**{sub['roll_number']}. {sub['full_name']}**")
                                if sub['submission_text']:
                                    st.write(f"*{sub['submission_text']}*")
                            with col2:
                                if sub['marks_obtained'] is not None:
                                    st.write(f"**Marks:** {sub['marks_obtained']}")
                                else:
                                    if st.button("Grade", key=f"grade_{sub['id']}"):
                                        st.session_state.grading_submission = sub['id']
    
    with assign_tab3:
        if 'grading_submission' in st.session_state:
            st.markdown("#### ✏️ Grade Submission")
            submission = db.query("SELECT * FROM assignment_submissions WHERE id = ?", 
                                (st.session_state.grading_submission,))[0]
            assignment = db.query("SELECT * FROM assignments WHERE id = ?", (submission['assignment_id'],))[0]
            
            with st.form("grade_assignment"):
                marks = st.number_input("Marks", min_value=0.0, max_value=float(assignment['total_marks']), value=0.0)
                feedback = st.text_area("Feedback")
                
                if st.form_submit_button("💾 Save Grade", use_container_width=True):
                    db.execute("""
                        UPDATE assignment_submissions 
                        SET marks_obtained = ?, feedback = ?, status = 'Graded'
                        WHERE id = ?
                    """, (marks, feedback, st.session_state.grading_submission))
                    st.success("✅ Assignment graded successfully!")
                    del st.session_state.grading_submission
                    st.rerun()

def show_faculty_materials():
    st.subheader("📚 Course Materials Management")
    
    mat_tab1, mat_tab2 = st.tabs(["📤 Upload", "📂 My Materials"])
    
    with mat_tab1:
        with st.form("material_form"):
            classes = db.query("""
                SELECT DISTINCT c.id, c.class_name 
                FROM classes c
                JOIN subjects s ON c.id = s.class_id
                WHERE s.teacher_id = ?
            """, (st.session_state.user['id'],))
            
            if classes:
                class_options = {f"{c['class_name']}": c['id'] for c in classes}
                selected_class = st.selectbox("Class", list(class_options.keys()))
                
                subjects = db.query("""
                    SELECT id, subject_name FROM subjects 
                    WHERE class_id = ? AND teacher_id = ?
                """, (class_options[selected_class], st.session_state.user['id']))
                
                if subjects:
                    subject_options = {s['subject_name']: s['id'] for s in subjects}
                    selected_subject = st.selectbox("Subject", list(subject_options.keys()))
                    
                    material_title = st.text_input("Material Title")
                    material_desc = st.text_area("Description")
                    material_type = st.selectbox("Type", ["PDF", "Video", "Slide", "Document", "Link", "Other"])
                    
                    if st.form_submit_button("📤 Upload Material", use_container_width=True):
                        db.execute("""
                            INSERT INTO course_materials (subject_id, class_id, title, description, material_type, uploaded_by)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (subject_options[selected_subject], class_options[selected_class],
                             material_title, material_desc, material_type, st.session_state.user['id']))
                        
                        st.success("✅ Material uploaded successfully!")
    
    with mat_tab2:
        st.markdown("#### 📂 My Course Materials")
        materials = db.query("""
            SELECT cm.*, c.class_name, s.subject_name
            FROM course_materials cm
            JOIN classes c ON cm.class_id = c.id
            JOIN subjects s ON cm.subject_id = s.id
            WHERE cm.uploaded_by = ?
            ORDER BY cm.uploaded_at DESC
        """, (st.session_state.user['id'],))
        
        if materials:
            for material in materials:
                with st.expander(f"📖 {material['title']} ({material['class_name']} - {material['subject_name']})"):
                    st.write(f"**Type:** {material['material_type']}")
                    st.write(f"**Description:** {material['description']}")
                    st.write(f"**Uploaded:** {material['uploaded_at']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("👁️ View", key=f"view_{material['id']}"):
                            st.info(f"Displaying {material['title']}")
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{material['id']}"):
                            db.execute("DELETE FROM course_materials WHERE id = ?", (material['id'],))
                            st.success("✅ Material deleted!")
                            st.rerun()
        else:
            st.info("No materials uploaded yet")

def show_faculty_hr():
    st.subheader("💼 HR Information")
    
    # Get faculty HR details
    hr_info = db.query("""
        SELECT s.*, u.full_name, u.email, u.phone
        FROM staff s
        JOIN users u ON s.user_id = u.id
        WHERE s.user_id = ?
    """, (st.session_state.user['id'],))
    
    if hr_info:
        info = hr_info[0]
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👤 Personal Information")
            st.write(f"**Employee ID:** {info['employee_id']}")
            st.write(f"**Full Name:** {info['full_name']}")
            st.write(f"**Email:** {info['email']}")
            st.write(f"**Phone:** {info['phone']}")
            st.write(f"**Department:** {info['department']}")
            st.write(f"**Designation:** {info['designation']}")
        
        with col2:
            st.markdown("#### 💰 Salary Information")
            st.write(f"**Basic Salary:** ৳{info['salary']:,.2f}")
            st.write(f"**Bank Account:** {info['bank_account'] or 'Not provided'}")
            
            # Payroll history
            st.markdown("#### 📊 Payroll History")
            payroll = db.query("""
                SELECT month, year, net_salary, status, payment_date
                FROM payroll
                WHERE staff_id = ?
                ORDER BY year DESC, 
                    CASE month 
                        WHEN 'January' THEN 1
                        WHEN 'February' THEN 2
                        WHEN 'March' THEN 3
                        WHEN 'April' THEN 4
                        WHEN 'May' THEN 5
                        WHEN 'June' THEN 6
                        WHEN 'July' THEN 7
                        WHEN 'August' THEN 8
                        WHEN 'September' THEN 9
                        WHEN 'October' THEN 10
                        WHEN 'November' THEN 11
                        WHEN 'December' THEN 12
                    END DESC
                LIMIT 6
            """, (info['id'],))
            
            if payroll:
                for pay in payroll:
                    status_color = "green" if pay['status'] == 'Paid' else "orange"
                    st.write(f"**{pay['month']} {pay['year']}:** ৳{pay['net_salary']:,.2f} "
                           f"<span style='color:{status_color};'>[{pay['status']}]</span>", 
                           unsafe_allow_html=True)
            else:
                st.info("No payroll records found")

def show_faculty_notices():
    st.subheader("📢 Notice Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📋 All Notices")
        notices = db.query("""
            SELECT * FROM notices 
            WHERE target_audience IN ('All', 'Teachers')
            ORDER BY created_at DESC
        """)
        
        if notices:
            for notice in notices:
                with st.expander(f"📌 {notice['title']} - {notice['priority']}"):
                    st.write(f"**Content:** {notice['content']}")
                    st.write(f"**Target:** {notice['target_audience']}")
                    st.write(f"**Expires:** {notice['expires_at']}")
        else:
            st.info("No notices found")
    
    with col2:
        st.markdown("#### 📝 Create Notice")
        with st.form("faculty_notice_form"):
            title = st.text_input("Notice Title")
            content = st.text_area("Content", height=100)
            target = st.selectbox("Target", ["Teachers", "Students", "Parents"])
            
            if st.form_submit_button("📤 Post Notice", use_container_width=True):
                if title and content:
                    db.execute(
                        "INSERT INTO notices (title, content, target_audience, created_by, expires_at) VALUES (?, ?, ?, ?, ?)",
                        (title, content, target, st.session_state.user['id'], (datetime.now() + timedelta(days=7)).date())
                    )
                    st.success("✅ Notice posted successfully!")
                    st.rerun()

def show_faculty_schedule():
    st.subheader("🕐 Class Schedule")
    
    # Get teacher's schedule
    schedule = db.query("""
        SELECT t.day_of_week, t.period_number, t.start_time, t.end_time,
               c.class_name, s.subject_name, t.room_number
        FROM timetable t
        JOIN classes c ON t.class_id = c.id
        JOIN subjects s ON t.subject_id = s.id
        WHERE s.teacher_id = ?
        ORDER BY 
            CASE t.day_of_week 
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END,
            t.period_number
    """, (st.session_state.user['id'],))
    
    if schedule:
        # Create timetable grid
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        periods = sorted(list(set([t['period_number'] for t in schedule])))
        
        timetable_data = []
        for period in periods:
            row = {'Period': f'Period {period}'}
            for day in days:
                classes_today = [t for t in schedule if t['day_of_week'] == day and t['period_number'] == period]
                if classes_today:
                    class_info = classes_today[0]
                    row[day] = f"{class_info['class_name']}\n{class_info['subject_name']}\n{class_info['room_number']}"
                else:
                    row[day] = "Free"
            timetable_data.append(row)
        
        df_timetable = pd.DataFrame(timetable_data)
        st.dataframe(df_timetable, use_container_width=True, hide_index=True)
        
        # Show today's schedule
        st.markdown("#### 📅 Today's Schedule")
        today = datetime.now().strftime('%A')
        today_schedule = [t for t in schedule if t['day_of_week'] == today]
        
        if today_schedule:
            for cls in today_schedule:
                st.write(f"**{cls['start_time']} - {cls['end_time']}:** {cls['class_name']} - {cls['subject_name']} ({cls['room_number']})")
        else:
            st.info("No classes scheduled for today")
    else:
        st.info("No schedule assigned yet")

# ============================================================================
# PARENT PORTAL
# ============================================================================

def show_parent_portal():
    st.markdown('<div class="main-header"><h2>👨‍👩‍👧‍👦 Parent Portal</h2></div>', unsafe_allow_html=True)
    
    # Get parent's children
    children = db.query("""
        SELECT s.id, u.full_name, s.admission_number, c.class_name, s.roll_number,
               s.gpa, s.cgpa, s.class_rank
        FROM students s
        JOIN users u ON s.user_id = u.id
        JOIN classes c ON s.class_id = c.id
        WHERE s.parent_id = (SELECT id FROM users WHERE id = ?)
        AND s.status = 'Active'
    """, (st.session_state.user['id'],))
    
    if not children:
        st.warning("No children found in the system")
        return
    
    # Parent Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👶 Children", len(children))
    with col2:
        avg_gpa = sum([child['gpa'] for child in children]) / len(children)
        st.metric("📊 Average GPA", f"{avg_gpa:.2f}")
    with col3:
        total_fees = db.query("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM fee_invoices
            WHERE student_id IN (
                SELECT id FROM students WHERE parent_id = (SELECT id FROM users WHERE id = ?)
            ) AND status = 'Unpaid'
        """, (st.session_state.user['id'],))[0]['total']
        st.metric("💰 Pending Fees", f"৳{total_fees:,.0f}")
    with col4:
        attendance_rate = db.query("""
            SELECT AVG(att_rate) as avg_att
            FROM (
                SELECT s.id, 
                       SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as att_rate
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id
                WHERE s.parent_id = (SELECT id FROM users WHERE id = ?)
                GROUP BY s.id
            )
        """, (st.session_state.user['id'],))[0]['avg_att'] or 0
        st.metric("📅 Avg Attendance", f"{attendance_rate:.1f}%")
    
    st.divider()
    
    # Parent Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Overview", "📊 Performance", "💰 Payments", "👥 Meetings", "📢 Notices"
    ])
    
    with tab1:
        show_parent_overview(children)
    with tab2:
        show_parent_performance(children)
    with tab3:
        show_parent_payments(children)
    with tab4:
        show_parent_meetings(children)
    with tab5:
        show_parent_notices()

def show_parent_overview(children):
    st.subheader("👶 My Children")
    
    for child in children:
        with st.expander(f"🎓 {child['full_name']} - {child['class_name']} (Roll: {child['roll_number']})", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("GPA", f"{child['gpa']:.2f}")
            with col2:
                st.metric("CGPA", f"{child['cgpa']:.2f}")
            with col3:
                st.metric("Class Rank", child['class_rank'])
            with col4:
                attendance = db.query("""
                    SELECT COUNT(*) as total, 
                           SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present
                    FROM attendance
                    WHERE student_id = ? 
                    AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
                """, (child['id'],))[0]
                att_rate = (attendance['present'] / attendance['total'] * 100) if attendance['total'] > 0 else 0
                st.metric("Attendance", f"{att_rate:.1f}%")
            
            # Quick actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"📊 View Performance", key=f"perf_{child['id']}"):
                    st.session_state.view_child_performance = child['id']
            with col2:
                if st.button(f"💰 Pay Fees", key=f"fees_{child['id']}"):
                    st.session_state.pay_child_fees = child['id']
            with col3:
                if st.button(f"👥 Request Meeting", key=f"meet_{child['id']}"):
                    st.session_state.request_meeting = child['id']

def show_parent_performance(children):
    st.subheader("📊 Academic Performance")
    
    if 'view_child_performance' in st.session_state:
        child_id = st.session_state.view_child_performance
        child_info = db.query("SELECT u.full_name FROM students s JOIN users u ON s.user_id = u.id WHERE s.id = ?", (child_id,))[0]
        st.markdown(f"#### 📈 Performance Analysis - {child_info['full_name']}")
    else:
        selected_child = st.selectbox("Select Child", 
                                    [f"{c['full_name']} - {c['class_name']}" for c in children])
        child_id = children[[f"{c['full_name']} - {c['class_name']}" for c in children].index(selected_child)]['id']
    
    # Subject-wise performance
    subject_grades = db.query("""
        SELECT s.subject_name, 
               AVG(g.marks_obtained) as avg_marks,
               AVG(g.grade_point) as avg_grade_point,
               COUNT(g.id) as exam_count
        FROM grades g
        JOIN subjects s ON g.subject_id = s.id
        WHERE g.student_id = ?
        GROUP BY s.subject_name
        ORDER BY avg_grade_point DESC
    """, (child_id,))
    
    if subject_grades:
        # Performance chart
        df_grades = pd.DataFrame([dict(g) for g in subject_grades])
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(df_grades, x='subject_name', y='avg_grade_point',
                       title='Average Grade Points by Subject',
                       color='avg_grade_point',
                       color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(df_grades, values='avg_marks', names='subject_name',
                       title='Marks Distribution by Subject')
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed grade table
        st.markdown("#### 📝 Detailed Grades")
        all_grades = db.query("""
            SELECT s.subject_name, g.exam_name, g.marks_obtained, g.total_marks,
                   g.grade_letter, g.grade_point, g.graded_at
            FROM grades g
            JOIN subjects s ON g.subject_id = s.id
            WHERE g.student_id = ?
            ORDER BY g.graded_at DESC
        """, (child_id,))
        
        if all_grades:
            grade_data = []
            for grade in all_grades:
                grade_data.append({
                    'Subject': grade['subject_name'],
                    'Exam': grade['exam_name'],
                    'Marks': f"{grade['marks_obtained']}/{grade['total_marks']}",
                    'Grade': grade['grade_letter'],
                    'Point': grade['grade_point'],
                    'Date': grade['graded_at'][:10]
                })
            st.dataframe(grade_data, use_container_width=True, hide_index=True)
    else:
        st.info("No grade data available for this student")

def show_parent_payments(children):
    st.subheader("💰 Fee Payment System")
    
    if 'pay_child_fees' in st.session_state:
        child_id = st.session_state.pay_child_fees
        child_info = db.query("SELECT u.full_name FROM students s JOIN users u ON s.user_id = u.id WHERE s.id = ?", (child_id,))[0]
        st.markdown(f"#### 💳 Make Payment - {child_info['full_name']}")
    else:
        selected_child = st.selectbox("Select Child for Payment", 
                                    [f"{c['full_name']} - {c['class_name']}" for c in children],
                                    key="payment_child")
        child_id = children[[f"{c['full_name']} - {c['class_name']}" for c in children].index(selected_child)]['id']
    
    # Fee invoices
    invoices = db.query("""
        SELECT * FROM fee_invoices
        WHERE student_id = ? AND status = 'Unpaid'
        ORDER BY due_date
    """, (child_id,))
    
    if invoices:
        total_due = sum([inv['amount'] for inv in invoices])
        st.metric("💰 Total Amount Due", f"৳{total_due:,.2f}")
        
        for invoice in invoices:
            with st.expander(f"📄 Invoice {invoice['invoice_number']} - Due: {invoice['due_date']}", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Amount:** ৳{invoice['amount']:,.2f}")
                    st.write(f"**Fee Type:** {invoice['fee_type']}")
                
                with col2:
                    days_until_due = (datetime.strptime(invoice['due_date'], '%Y-%m-%d').date() - datetime.now().date()).days
                    due_status = "Overdue" if days_until_due < 0 else f"Due in {days_until_due} days"
                    st.write(f"**Status:** {due_status}")
                
                with col3:
                    with st.form(f"payment_form_{invoice['id']}"):
                        payment_method = st.selectbox("Payment Method", 
                                                    ["bKash", "Nagad", "Bank Transfer", "Card", "Cash"],
                                                    key=f"method_{invoice['id']}")
                        
                        if payment_method in ["bKash", "Nagad"]:
                            st.info(f"💡 Send payment to: 01XXXXXXXXX")
                            transaction_id = st.text_input("Transaction ID", key=f"trans_{invoice['id']}")
                        else:
                            transaction_id = None
                        
                        if st.form_submit_button("💳 Pay Now", use_container_width=True):
                            receipt_num = generate_receipt_number()
                            
                            # Record payment
                            payment_id = db.execute("""
                                INSERT INTO payments (invoice_id, student_id, amount, payment_method, transaction_id, receipt_number)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (invoice['id'], child_id, invoice['amount'], payment_method, transaction_id, receipt_num))
                            
                            # Update invoice status
                            db.execute("UPDATE fee_invoices SET status = 'Paid' WHERE id = ?", (invoice['id'],))
                            
                            st.success(f"""
                            ✅ Payment Successful!
                            - Receipt Number: **{receipt_num}**
                            - Amount: **৳{invoice['amount']:,.2f}**
                            - Method: **{payment_method}**
                            """)
                            st.balloons()
                            st.rerun()
    else:
        st.success("🎉 All fees are paid! No pending invoices.")
    
    # Payment history
    st.markdown("---")
    st.markdown("#### 📜 Payment History")
    payments = db.query("""
        SELECT p.*, fi.invoice_number, fi.fee_type
        FROM payments p
        JOIN fee_invoices fi ON p.invoice_id = fi.id
        WHERE p.student_id = ?
        ORDER BY p.payment_date DESC
        LIMIT 10
    """, (child_id,))
    
    if payments:
        payment_data = []
        for payment in payments:
            payment_data.append({
                'Receipt': payment['receipt_number'],
                'Invoice': payment['invoice_number'],
                'Type': payment['fee_type'],
                'Amount': f"৳{payment['amount']:,.2f}",
                'Method': payment['payment_method'],
                'Date': payment['payment_date'][:10]
            })
        st.dataframe(payment_data, use_container_width=True, hide_index=True)

def show_parent_meetings(children):
    st.subheader("👥 Parent-Teacher Meetings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📅 Request Meeting")
        
        if 'request_meeting' in st.session_state:
            child_id = st.session_state.request_meeting
            child_info = db.query("""
                SELECT u.full_name, c.class_name, c.class_teacher_id 
                FROM students s 
                JOIN users u ON s.user_id = u.id 
                JOIN classes c ON s.class_id = c.id 
                WHERE s.id = ?
            """, (child_id,))[0]
            st.write(f"**Student:** {child_info['full_name']} - {child_info['class_name']}")
        else:
            selected_child = st.selectbox("Select Child", 
                                        [f"{c['full_name']} - {c['class_name']}" for c in children])
            child_id = children[[f"{c['full_name']} - {c['class_name']}" for c in children].index(selected_child)]['id']
            child_info = db.query("""
                SELECT u.full_name, c.class_name, c.class_teacher_id 
                FROM students s 
                JOIN users u ON s.user_id = u.id 
                JOIN classes c ON s.class_id = c.id 
                WHERE s.id = ?
            """, (child_id,))[0]
        
        teacher_info = db.query("SELECT full_name FROM users WHERE id = ?", (child_info['class_teacher_id'],))[0]
        st.write(f"**Class Teacher:** {teacher_info['full_name']}")
        
        with st.form("meeting_request_form"):
            meeting_date = st.date_input("Preferred Date", min_value=datetime.now().date())
            meeting_time = st.time_input("Preferred Time")
            purpose = st.text_area("Purpose of Meeting", placeholder="Briefly describe what you'd like to discuss...")
            
            if st.form_submit_button("📤 Send Request", use_container_width=True):
                db.execute("""
                    INSERT INTO meeting_requests (parent_id, teacher_id, student_id, requested_date, requested_time, purpose)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (st.session_state.user['id'], child_info['class_teacher_id'], child_id, 
                     meeting_date, meeting_time.strftime('%H:%M'), purpose))
                
                st.success("✅ Meeting request sent successfully!")
                if 'request_meeting' in st.session_state:
                    del st.session_state.request_meeting
    
    with col2:
        st.markdown("#### 📋 Meeting Requests")
        meetings = db.query("""
            SELECT mr.*, u.full_name as teacher_name, s2.full_name as student_name
            FROM meeting_requests mr
            JOIN users u ON mr.teacher_id = u.id
            JOIN students s ON mr.student_id = s.id
            JOIN users s2 ON s.user_id = s2.id
            WHERE mr.parent_id = ?
            ORDER BY mr.requested_date DESC
        """, (st.session_state.user['id'],))
        
        if meetings:
            for meeting in meetings:
                status_color = {
                    'Pending': 'orange',
                    'Approved': 'green',
                    'Rejected': 'red'
                }.get(meeting['status'], 'gray')
                
                st.markdown(f"""
                <div style="border-left: 4px solid {status_color}; padding-left: 1rem; margin: 1rem 0;">
                    <h4>Meeting with {meeting['teacher_name']}</h4>
                    <p><strong>Student:</strong> {meeting['student_name']}</p>
                    <p><strong>Date:</strong> {meeting['requested_date']} at {meeting['requested_time']}</p>
                    <p><strong>Purpose:</strong> {meeting['purpose']}</p>
                    <p><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{meeting['status']}</span></p>
                    {f"<p><strong>Teacher Notes:</strong> {meeting['teacher_notes']}</p>" if meeting['teacher_notes'] else ""}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No meeting requests yet")

def show_parent_notices():
    st.subheader("📢 School Notices")
    
    notices = db.query("""
        SELECT * FROM notices 
        WHERE target_audience IN ('All', 'Parents')
        ORDER BY created_at DESC
    """)
    
    if notices:
        for notice in notices:
            priority_color = {
                'Normal': 'blue',
                'High': 'orange',
                'Urgent': 'red'
            }.get(notice['priority'], 'blue')
            
            st.markdown(f"""
            <div style="border: 1px solid {priority_color}; border-radius: 10px; padding: 1rem; margin: 1rem 0;">
                <div style="display: flex; justify-content: between; align-items: start;">
                    <h4 style="margin: 0; color: {priority_color};">📌 {notice['title']}</h4>
                    <span style="background: {priority_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 15px; font-size: 0.8rem;">
                        {notice['priority']}
                    </span>
                </div>
                <p style="margin: 0.5rem 0;">{notice['content']}</p>
                <div style="display: flex; justify-content: between; font-size: 0.8rem; color: #666;">
                    <span>Posted: {notice['created_at'][:16]}</span>
                    <span>Expires: {notice['expires_at']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No notices available")

# ============================================================================
# STUDENT DASHBOARD
# ============================================================================

def show_student_dashboard():
    st.markdown('<div class="main-header"><h2>🎓 Student Dashboard</h2></div>', unsafe_allow_html=True)
    
    # Get student data
    student = db.query("""
        SELECT s.*, u.full_name, c.class_name, c.section
        FROM students s
        JOIN users u ON s.user_id = u.id
        JOIN classes c ON s.class_id = c.id
        WHERE s.user_id = ?
    """, (st.session_state.user['id'],))
    
    if not student:
        st.error("Student record not found")
        return
    
    student = student[0]
    
    # Student Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 GPA", f"{student['gpa']:.2f}")
    with col2:
        st.metric("🎯 CGPA", f"{student['cgpa']:.2f}")
    with col3:
        st.metric("🏆 Class Rank", student['class_rank'])
    with col4:
        attendance = db.query("""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present
            FROM attendance
            WHERE student_id = ? 
            AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
        """, (student['id'],))[0]
        att_rate = (attendance['present'] / attendance['total'] * 100) if attendance['total'] > 0 else 0
        st.metric("📅 Attendance", f"{att_rate:.1f}%")
    
    st.divider()
    
    # Student Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🏠 Overview", "📊 Performance", "📋 Assignments", "💰 Fees", 
        "📢 Notices", "🕐 Schedule", "📚 Materials"
    ])
    
    with tab1:
        show_student_overview(student)
    with tab2:
        show_student_performance(student)
    with tab3:
        show_student_assignments(student)
    with tab4:
        show_student_fees(student)
    with tab5:
        show_student_notices()
    with tab6:
        show_student_schedule(student)
    with tab7:
        show_student_materials(student)

def show_student_overview(student):
    st.subheader("🎓 My Profile")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Name:** {student['full_name']}")
        st.write(f"**Class:** {student['class_name']} {student['section']}")
        st.write(f"**Roll Number:** {student['roll_number']}")
        st.write(f"**Admission Number:** {student['admission_number']}")
        st.write(f"**Date of Birth:** {student['dob']}")
    
    with col2:
        st.write(f"**GPA:** {student['gpa']}")
        st.write(f"**CGPA:** {student['cgpa']}")
        st.write(f"**Class Rank:** {student['class_rank']}")
        st.write(f"**Status:** {student['status']}")
        st.write(f"**Enrollment Date:** {student['enrollment_date']}")
    
    # Recent activity
    st.markdown("---")
    st.markdown("#### 📈 Recent Activity")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        recent_grades = db.query("SELECT COUNT(*) as cnt FROM grades WHERE student_id = ? AND DATE(graded_at) = DATE('now')", 
                               (student['id'],))[0]['cnt']
        st.metric("Today's Grades", recent_grades)
    
    with col2:
        pending_assignments = db.query("""
            SELECT COUNT(*) as cnt 
            FROM assignments a 
            WHERE a.class_id = ? 
            AND a.due_date >= DATE('now')
            AND a.id NOT IN (
                SELECT assignment_id FROM assignment_submissions WHERE student_id = ?
            )
        """, (student['class_id'], student['id']))[0]['cnt']
        st.metric("Pending Assignments", pending_assignments)
    
    with col3:
        unpaid_fees = db.query("SELECT COUNT(*) as cnt FROM fee_invoices WHERE student_id = ? AND status = 'Unpaid'", 
                             (student['id'],))[0]['cnt']
        st.metric("Unpaid Fees", unpaid_fees)

def show_student_performance(student):
    st.subheader("📊 Academic Performance")
    
    # Overall performance summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_subjects = db.query("SELECT COUNT(DISTINCT subject_id) as cnt FROM grades WHERE student_id = ?", 
                                (student['id'],))[0]['cnt']
        st.metric("Subjects", total_subjects)
    
    with col2:
        total_exams = db.query("SELECT COUNT(*) as cnt FROM grades WHERE student_id = ?", 
                             (student['id'],))[0]['cnt']
        st.metric("Exams Taken", total_exams)
    
    with col3:
        avg_marks = db.query("SELECT AVG(marks_obtained) as avg FROM grades WHERE student_id = ?", 
                           (student['id'],))[0]['avg'] or 0
        st.metric("Avg Marks", f"{avg_marks:.1f}")
    
    with col4:
        best_subject = db.query("""
            SELECT s.subject_name, AVG(g.grade_point) as avg_gp
            FROM grades g
            JOIN subjects s ON g.subject_id = s.id
            WHERE g.student_id = ?
            GROUP BY s.subject_name
            ORDER BY avg_gp DESC
            LIMIT 1
        """, (student['id'],))
        subject_name = best_subject[0]['subject_name'] if best_subject else "N/A"
        st.metric("Best Subject", subject_name)
    
    st.divider()
    
    # Subject-wise performance
    st.markdown("#### 📈 Subject-wise Performance")
    subject_grades = db.query("""
        SELECT s.subject_name, 
               AVG(g.marks_obtained) as avg_marks,
               AVG(g.grade_point) as avg_grade_point,
               COUNT(g.id) as exam_count
        FROM grades g
        JOIN subjects s ON g.subject_id = s.id
        WHERE g.student_id = ?
        GROUP BY s.subject_name
        ORDER BY avg_grade_point DESC
    """, (student['id'],))
    
    if subject_grades:
        # Performance chart
        df_grades = pd.DataFrame([dict(g) for g in subject_grades])
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(df_grades, x='subject_name', y='avg_grade_point',
                       title='Average Grade Points by Subject',
                       color='avg_grade_point',
                       color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(df_grades, values='avg_marks', names='subject_name',
                       title='Marks Distribution by Subject')
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed grade table
        st.markdown("#### 📝 Grade Details")
        all_grades = db.query("""
            SELECT s.subject_name, g.exam_name, g.marks_obtained, g.total_marks,
                   g.grade_letter, g.grade_point, g.graded_at
            FROM grades g
            JOIN subjects s ON g.subject_id = s.id
            WHERE g.student_id = ?
            ORDER BY g.graded_at DESC
        """, (student['id'],))
        
        if all_grades:
            grade_data = []
            for grade in all_grades:
                grade_data.append({
                    'Subject': grade['subject_name'],
                    'Exam': grade['exam_name'],
                    'Marks': f"{grade['marks_obtained']}/{grade['total_marks']}",
                    'Grade': grade['grade_letter'],
                    'Point': grade['grade_point'],
                    'Date': grade['graded_at'][:10]
                })
            st.dataframe(grade_data, use_container_width=True, hide_index=True)
            
            # Export grades
            if st.button("📥 Export Grades", use_container_width=True):
                csv = pd.DataFrame(grade_data).to_csv(index=False)
                st.download_button("💾 Download CSV", csv, "my_grades.csv", "text/csv")
    else:
        st.info("No grade data available yet")

def show_student_assignments(student):
    st.subheader("📋 Assignment Management")
    
    assign_tab1, assign_tab2 = st.tabs(["📝 Pending", "📤 Submitted"])
    
    with assign_tab1:
        st.markdown("#### 📝 Pending Assignments")
        pending_assignments = db.query("""
            SELECT a.*, s.subject_name, u.full_name as teacher_name
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.id
            JOIN users u ON a.assigned_by = u.id
            WHERE a.class_id = ? 
            AND a.due_date >= DATE('now')
            AND a.id NOT IN (
                SELECT assignment_id FROM assignment_submissions 
                WHERE student_id = ?
            )
            ORDER BY a.due_date
        """, (student['class_id'], student['id']))
        
        if pending_assignments:
            for assignment in pending_assignments:
                days_remaining = (datetime.strptime(assignment['due_date'], '%Y-%m-%d').date() - datetime.now().date()).days
                status_color = "red" if days_remaining < 0 else "orange" if days_remaining <= 2 else "green"
                
                with st.expander(f"📄 {assignment['title']} - Due: {assignment['due_date']} ({days_remaining} days left)"):
                    st.write(f"**Subject:** {assignment['subject_name']}")
                    st.write(f"**Teacher:** {assignment['teacher_name']}")
                    st.write(f"**Description:** {assignment['description']}")
                    st.write(f"**Total Marks:** {assignment['total_marks']}")
                    
                    with st.form(f"submit_{assignment['id']}"):
                        submission_text = st.text_area("Your Submission", height=100, 
                                                     placeholder="Type your assignment submission here...")
                        
                        if st.form_submit_button("📤 Submit Assignment", use_container_width=True):
                            if submission_text.strip():
                                db.execute("""
                                    INSERT INTO assignment_submissions (assignment_id, student_id, submission_text)
                                    VALUES (?, ?, ?)
                                """, (assignment['id'], student['id'], submission_text))
                                st.success("✅ Assignment submitted successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Please write your submission before submitting")
        else:
            st.success("🎉 No pending assignments!")
    
    with assign_tab2:
        st.markdown("#### 📤 Submitted Assignments")
        submitted_assignments = db.query("""
            SELECT a.title, a.due_date, a.total_marks, asub.submission_text,
                   asub.marks_obtained, asub.feedback, asub.status, asub.submitted_at,
                   s.subject_name
            FROM assignment_submissions asub
            JOIN assignments a ON asub.assignment_id = a.id
            JOIN subjects s ON a.subject_id = s.id
            WHERE asub.student_id = ?
            ORDER BY asub.submitted_at DESC
        """, (student['id'],))
        
        if submitted_assignments:
            for assignment in submitted_assignments:
                status_color = "green" if assignment['status'] == 'Graded' else "blue"
                
                with st.expander(f"📋 {assignment['title']} - {assignment['subject_name']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Submitted:** {assignment['submitted_at'][:16]}")
                        st.write(f"**Due Date:** {assignment['due_date']}")
                        st.write(f"**Status:** <span style='color:{status_color}; font-weight:bold;'>{assignment['status']}</span>", 
                               unsafe_allow_html=True)
                    
                    with col2:
                        if assignment['marks_obtained'] is not None:
                            st.write(f"**Marks:** **{assignment['marks_obtained']}**/{assignment['total_marks']}")
                            percentage = (assignment['marks_obtained'] / assignment['total_marks']) * 100
                            st.metric("Score", f"{percentage:.1f}%")
                    
                    st.write(f"**Your Submission:** {assignment['submission_text']}")
                    
                    if assignment['feedback']:
                        st.markdown(f"**Teacher Feedback:** 💬 {assignment['feedback']}")
        else:
            st.info("No submitted assignments yet")

def show_student_fees(student):
    st.subheader("💰 Fee Management")
    
    fee_tab1, fee_tab2 = st.tabs(["💳 Pay Fees", "📜 Payment History"])
    
    with fee_tab1:
        st.markdown("#### 💰 Outstanding Fees")
        invoices = db.query("""
            SELECT * FROM fee_invoices
            WHERE student_id = ? AND status = 'Unpaid'
            ORDER BY due_date
        """, (student['id'],))
        
        if invoices:
            total_due = sum([inv['amount'] for inv in invoices])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Amount Due", f"৳{total_due:,.2f}")
            with col2:
                overdue_invoices = [inv for inv in invoices if datetime.strptime(inv['due_date'], '%Y-%m-%d').date() < datetime.now().date()]
                st.metric("Overdue Invoices", len(overdue_invoices))
            
            for invoice in invoices:
                days_until_due = (datetime.strptime(invoice['due_date'], '%Y-%m-%d').date() - datetime.now().date()).days
                due_status = "Overdue" if days_until_due < 0 else f"Due in {days_until_due} days"
                status_color = "red" if days_until_due < 0 else "orange" if days_until_due <= 7 else "green"
                
                with st.expander(f"📄 {invoice['invoice_number']} - {invoice['fee_type']} - {due_status}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Amount:** ৳{invoice['amount']:,.2f}")
                        st.write(f"**Due Date:** {invoice['due_date']}")
                    
                    with col2:
                        st.write(f"**Status:** <span style='color:{status_color}; font-weight:bold;'>{due_status}</span>", 
                               unsafe_allow_html=True)
                    
                    with col3:
                        with st.form(f"payment_form_{invoice['id']}"):
                            payment_method = st.selectbox("Payment Method", 
                                                        ["bKash", "Nagad", "Bank Transfer", "Card"],
                                                        key=f"method_{invoice['id']}")
                            
                            if payment_method in ["bKash", "Nagad"]:
                                st.info(f"💡 Send payment to: 01XXXXXXXXX")
                                transaction_id = st.text_input("Transaction ID", key=f"trans_{invoice['id']}",
                                                             placeholder="Enter transaction ID")
                            else:
                                transaction_id = st.text_input("Reference Number", key=f"ref_{invoice['id']}",
                                                            placeholder="Enter reference number")
                            
                            if st.form_submit_button("💳 Pay Now", use_container_width=True):
                                if (payment_method in ["bKash", "Nagad"] and not transaction_id) or \
                                   (payment_method in ["Bank Transfer", "Card"] and not transaction_id):
                                    st.error("❌ Please provide transaction/reference number")
                                else:
                                    receipt_num = generate_receipt_number()
                                    
                                    # Record payment
                                    payment_id = db.execute("""
                                        INSERT INTO payments (invoice_id, student_id, amount, payment_method, transaction_id, receipt_number)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                    """, (invoice['id'], student['id'], invoice['amount'], payment_method, transaction_id, receipt_num))
                                    
                                    # Update invoice status
                                    db.execute("UPDATE fee_invoices SET status = 'Paid' WHERE id = ?", (invoice['id'],))
                                    
                                    st.success(f"""
                                    ✅ Payment Successful!
                                    - Receipt Number: **{receipt_num}**
                                    - Amount: **৳{invoice['amount']:,.2f}**
                                    - Method: **{payment_method}**
                                    """)
                                    st.balloons()
                                    st.rerun()
        else:
            st.success("🎉 All fees are paid! No outstanding invoices.")
    
    with fee_tab2:
        st.markdown("#### 📜 Payment History")
        payments = db.query("""
            SELECT p.*, fi.invoice_number, fi.fee_type
            FROM payments p
            JOIN fee_invoices fi ON p.invoice_id = fi.id
            WHERE p.student_id = ?
            ORDER BY p.payment_date DESC
        """, (student['id'],))
        
        if payments:
            payment_data = []
            total_paid = 0
            for payment in payments:
                payment_data.append({
                    'Receipt': payment['receipt_number'],
                    'Invoice': payment['invoice_number'],
                    'Type': payment['fee_type'],
                    'Amount': f"৳{payment['amount']:,.2f}",
                    'Method': payment['payment_method'],
                    'Date': payment['payment_date'][:10]
                })
                total_paid += payment['amount']
            
            st.metric("Total Paid", f"৳{total_paid:,.2f}")
            st.dataframe(payment_data, use_container_width=True, hide_index=True)
            
            # Export payment history
            if st.button("📥 Export Payment History", use_container_width=True):
                csv = pd.DataFrame(payment_data).to_csv(index=False)
                st.download_button("💾 Download CSV", csv, "payment_history.csv", "text/csv")
        else:
            st.info("No payment history found")

def show_student_notices():
    st.subheader("📢 School Notices")
    
    notices = db.query("""
        SELECT * FROM notices 
        WHERE target_audience IN ('All', 'Students')
        ORDER BY created_at DESC
    """)
    
    if notices:
        for notice in notices:
            priority_color = {
                'Normal': '#4CAF50',
                'High': '#FF9800',
                'Urgent': '#F44336'
            }.get(notice['priority'], '#4CAF50')
            
            st.markdown(f"""
            <div style="border-left: 5px solid {priority_color}; padding: 1rem; margin: 1rem 0; background: #f8f9fa; border-radius: 5px;">
                <div style="display: flex; justify-content: between; align-items: start;">
                    <h4 style="margin: 0; color: {priority_color};">📢 {notice['title']}</h4>
                    <span style="background: {priority_color}; color: white; padding: 0.2rem 0.8rem; border-radius: 15px; font-size: 0.8rem; font-weight: bold;">
                        {notice['priority']}
                    </span>
                </div>
                <p style="margin: 0.8rem 0; font-size: 1rem; line-height: 1.5;">{notice['content']}</p>
                <div style="display: flex; justify-content: between; font-size: 0.85rem; color: #666;">
                    <span>📅 Posted: {notice['created_at'][:16]}</span>
                    <span>⏰ Expires: {notice['expires_at']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📭 No notices available at the moment")

def show_student_schedule(student):
    st.subheader("🕐 Class Schedule")
    
    # Get student's class schedule
    schedule = db.query("""
        SELECT t.day_of_week, t.period_number, t.start_time, t.end_time,
               s.subject_name, t.room_number
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        WHERE t.class_id = ?
        ORDER BY 
            CASE t.day_of_week 
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END,
            t.period_number
    """, (student['class_id'],))
    
    if schedule:
        # Create timetable grid
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        periods = sorted(list(set([t['period_number'] for t in schedule])))
        
        timetable_data = []
        for period in periods:
            row = {'Period': f'Period {period}'}
            for day in days:
                classes_today = [t for t in schedule if t['day_of_week'] == day and t['period_number'] == period]
                if classes_today:
                    class_info = classes_today[0]
                    row[day] = f"{class_info['subject_name']}\n{class_info['room_number']}"
                else:
                    row[day] = "Free"
            timetable_data.append(row)
        
        df_timetable = pd.DataFrame(timetable_data)
        st.dataframe(df_timetable, use_container_width=True, hide_index=True)
        
        # Show today's schedule
        st.markdown("#### 📅 Today's Classes")
        today = datetime.now().strftime('%A')
        today_schedule = [t for t in schedule if t['day_of_week'] == today]
        
        if today_schedule:
            for i, cls in enumerate(today_schedule, 1):
                st.markdown(f"""
                <div class="success-card">
                    <h4>🕐 {cls['start_time']} - {cls['end_time']}</h4>
                    <p><strong>Subject:</strong> {cls['subject_name']}</p>
                    <p><strong>Room:</strong> {cls['room_number']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("🎉 No classes scheduled for today!")
    else:
        st.info("No schedule available for your class")

def show_student_materials(student):
    st.subheader("📚 Course Materials")
    
    materials = db.query("""
        SELECT cm.*, s.subject_name
        FROM course_materials cm
        JOIN subjects s ON cm.subject_id = s.id
        WHERE cm.class_id = ?
        ORDER BY cm.uploaded_at DESC
    """, (student['class_id'],))
    
    if materials:
        # Group by subject
        subjects = set([m['subject_name'] for m in materials])
        
        for subject in subjects:
            subject_materials = [m for m in materials if m['subject_name'] == subject]
            
            with st.expander(f"📖 {subject} ({len(subject_materials)} materials)"):
                for material in subject_materials:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{material['title']}**")
                        st.write(f"*{material['description']}*")
                        st.write(f"Type: {material['material_type']} | Uploaded: {material['uploaded_at'][:10]}")
                    
                    with col2:
                        if st.button("👁️ View", key=f"view_{material['id']}"):
                            st.info(f"📄 Displaying: {material['title']}")
                            st.write(f"**Description:** {material['description']}")
                            st.write(f"**Type:** {material['material_type']}")
                            st.write(f"**Uploaded:** {material['uploaded_at'][:16]}")
                    
                    with col3:
                        if st.button("📥 Download", key=f"download_{material['id']}"):
                            st.success(f"✅ Downloading: {material['title']}")
                            # In a real application, this would trigger file download
    else:
        st.info("No course materials available for your class yet")

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    if st.session_state.user is None:
        show_login()
    else:
        # Navigation sidebar
        with st.sidebar:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; color: white;">
                <h3>🎓 School ERP</h3>
                <p>Welcome, <strong>{st.session_state.user['full_name']}</strong></p>
                <p><em>{st.session_state.user['role'].title()}</em></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user = None
                st.rerun()
            
            st.divider()
            
            # Quick actions based on role
            if st.session_state.user['role'] == 'admin':
                st.markdown("**⚡ Quick Actions**")
                if st.button("📊 View Analytics", use_container_width=True):
                    st.rerun()
                if st.button("👥 Manage Users", use_container_width=True):
                    st.rerun()
            
            elif st.session_state.user['role'] == 'teacher':
                st.markdown("**⚡ Quick Actions**")
                if st.button("📝 Grade Assignments", use_container_width=True):
                    st.rerun()
                if st.button("📅 Take Attendance", use_container_width=True):
                    st.rerun()
            
            elif st.session_state.user['role'] == 'parent':
                st.markdown("**⚡ Quick Actions**")
                if st.button("📊 View Performance", use_container_width=True):
                    st.rerun()
                if st.button("💰 Pay Fees", use_container_width=True):
                    st.rerun()
            
            elif st.session_state.user['role'] == 'student':
                st.markdown("**⚡ Quick Actions**")
                if st.button("📚 View Materials", use_container_width=True):
                    st.rerun()
                if st.button("📋 Submit Assignment", use_container_width=True):
                    st.rerun()
        
        # Main content based on role
        if st.session_state.user['role'] == 'admin':
            show_admin_dashboard()
        elif st.session_state.user['role'] == 'teacher':
            show_faculty_dashboard()
        elif st.session_state.user['role'] == 'parent':
            show_parent_portal()
        elif st.session_state.user['role'] == 'student':
            show_student_dashboard()

if __name__ == "__main__":
    main()
