from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timezone
import pytz
from werkzeug.security import generate_password_hash, check_password_hash
import os
from typing import Optional
from random import choices
import string
import json

app = Flask(__name__)
app.secret_key = 'school_monitoring_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_monitoring.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Helper function to convert UTC time to local time
def utc_to_local(utc_dt):
    """Convert UTC datetime to local timezone"""
    try:
        # Use IST (Indian Standard Time) as default
        local_tz = pytz.timezone('Asia/Kolkata')
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        return utc_dt.astimezone(local_tz)
    except Exception:
        # Fallback to UTC if timezone conversion fails
        return utc_dt
 # Template filter for timezone conversion
@app.template_filter('localtime')
def localtime_filter(timestamp):
    """Convert UTC timestamp to local time for templates"""
    if timestamp:
        local_time = utc_to_local(timestamp)
        return local_time.strftime('%H:%M')
    return ''
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    plain_password = db.Column(db.String(120), nullable=True)  # Store plain password for admin
    role = db.Column(db.String(20), nullable=False)  # 'parent', 'teacher', or 'admin'
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    students_as_parent = db.relationship('Student', foreign_keys='Student.parent_id', backref='parent')
    students_as_teacher = db.relationship('Student', foreign_keys='Student.teacher_id', backref='teacher')
    leave_requests_as_parent = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.parent_id', backref='parent_user')
    leave_requests_as_teacher = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.teacher_id', backref='teacher_user')

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(10), nullable=False)
    section = db.Column(db.String(10), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    hour_1 = db.Column(db.Boolean, default=False)
    hour_2 = db.Column(db.Boolean, default=False)
    hour_3 = db.Column(db.Boolean, default=False)
    hour_4 = db.Column(db.Boolean, default=False)
    hour_5 = db.Column(db.Boolean, default=False)
    hour_6 = db.Column(db.Boolean, default=False)
    hour_7 = db.Column(db.Boolean, default=False)
    hour_8 = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(10), nullable=False)
    marks = db.Column(db.Integer)
    semester = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Fee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    fee_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # 'sick', 'personal', 'other'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    teacher_comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    
    if not username or not password or not role:
        flash('All fields are required!', 'error')
        return redirect(url_for('index'))
    
    user = User.query.filter_by(username=username, role=role).first()
    
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    else:
        flash('Invalid credentials!', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    role = session['role']
    
    if role == 'parent':
        students = Student.query.filter_by(parent_id=user_id).all()
        if not students:
            flash('No student found for this parent account!', 'error')
            return redirect(url_for('index'))
        # Determine selected student
        selected_student_id = request.args.get('student_id')
        if not selected_student_id and students:
            selected_student_id = str(students[0].id)
        selected_student = next((s for s in students if str(s.id) == str(selected_student_id)), students[0])
        # Fetch data for selected student
        today_attendance = Attendance.query.filter_by(
            student_id=selected_student.id,
            date=date.today()
        ).first()
        recent_grades = Grade.query.filter_by(student_id=selected_student.id).order_by(Grade.created_at.desc()).limit(5).all()
        pending_fees = Fee.query.filter_by(student_id=selected_student.id, paid=False).all()
        leave_requests = LeaveRequest.query.filter_by(student_id=selected_student.id).order_by(LeaveRequest.created_at.desc()).all()
        return render_template('parent_dashboard.html', students=students, selected_student=selected_student, attendance=today_attendance, grades=recent_grades, fees=pending_fees, leave_requests=leave_requests)
    
    elif role == 'teacher':
        # Get students assigned to teacher
        students = Student.query.filter_by(teacher_id=user_id).all()
        
        # Get pending leave requests
        pending_leaves = LeaveRequest.query.filter_by(
            teacher_id=user_id, 
            status='pending'
        ).order_by(LeaveRequest.created_at.desc()).all()
        
        # Get recent messages (last 5 messages sent to teacher)
        student_ids = [s.id for s in students]
        recent_messages = []
        if student_ids:
            try:
                messages = Message.query.filter(
                    Message.student_id.in_(student_ids),
                    Message.receiver_id == user_id
                ).order_by(Message.timestamp.desc()).limit(5).all()
                
                for msg in messages:
                    student = Student.query.get(msg.student_id)
                    parent = User.query.get(msg.sender_id)
                    recent_messages.append({
                        'id': msg.id,
                        'content': msg.content,
                        'timestamp': msg.timestamp,
                        'parent_name': parent.username if parent else 'Unknown',
                        'student_name': student.name if student else 'Unknown'
                    })
            except Exception as e:
                # If there's any error with messages, just continue with empty list
                recent_messages = []
        
        return render_template('teacher_dashboard.html', 
                             students=students,
                             pending_leaves=pending_leaves,
                             recent_messages=recent_messages)
    
    return redirect(url_for('index'))

@app.route('/attendance')
def attendance():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    role = session['role']
    
    if role == 'parent':
        students = Student.query.filter_by(parent_id=user_id).all()
        if not students:
            return redirect(url_for('index'))
        selected_student_id = request.args.get('student_id')
        if not selected_student_id:
            selected_student_id = str(students[0].id)
        selected_student = next((s for s in students if str(s.id) == str(selected_student_id)), students[0])
        current_month = date.today().replace(day=1)
        attendance_records = Attendance.query.filter(
            Attendance.student_id == selected_student.id,
            Attendance.date >= current_month
        ).order_by(Attendance.date.desc()).all()
        return render_template('attendance.html', students=students, selected_student=selected_student, attendance_records=attendance_records)
    
    elif role == 'teacher':
        students = Student.query.filter_by(teacher_id=user_id).all()
        selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
        
        # Get attendance for all students on selected date
        attendance_data = {}
        for student in students:
            attendance = Attendance.query.filter_by(
                student_id=student.id, 
                date=datetime.strptime(selected_date, '%Y-%m-%d').date()
            ).first()
            attendance_data[student.id] = attendance
        
        return render_template('teacher_attendance.html', 
                             students=students, 
                             attendance_data=attendance_data,
                             selected_date=selected_date)
    
    return redirect(url_for('index'))

@app.route('/update_attendance', methods=['POST'])
def update_attendance():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    student_id = request.form.get('student_id')
    date_str = request.form.get('date')
    hour = request.form.get('hour')
    present = request.form.get('present') == 'true'
    
    if not student_id or not date_str or not hour:
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        attendance = Attendance.query.filter_by(
            student_id=int(student_id), 
            date=attendance_date
        ).first()
        
        if not attendance:
            attendance = Attendance(
                student_id=int(student_id),
                date=attendance_date
            )
            db.session.add(attendance)
        
        # Update the specific hour
        setattr(attendance, f'hour_{hour}', present)
        
        db.session.commit()
        return jsonify({'success': True})
    except (ValueError, TypeError) as e:
        return jsonify({'error': 'Invalid data provided'}), 400

@app.route('/grades')
def grades():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    role = session['role']
    
    if role == 'parent':
        students = Student.query.filter_by(parent_id=user_id).all()
        if not students:
            return redirect(url_for('index'))
        selected_student_id = request.args.get('student_id')
        if not selected_student_id:
            selected_student_id = str(students[0].id)
        selected_student = next((s for s in students if str(s.id) == str(selected_student_id)), students[0])
        grades = Grade.query.filter_by(student_id=selected_student.id).order_by(Grade.created_at.desc()).all()
        return render_template('grades.html', students=students, selected_student=selected_student, grades=grades)
    
    elif role == 'teacher':
        students = Student.query.filter_by(teacher_id=user_id).all()
        return render_template('teacher_grades.html', students=students)
    
    return redirect(url_for('index'))

@app.route('/add_grade', methods=['POST'])
def add_grade():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    student_id = request.form.get('student_id')
    subject = request.form.get('subject')
    grade = request.form.get('status')
    marks = request.form.get('marks')
    semester = request.form.get('semester')
    
    if not all([student_id, subject, grade, semester]):
        flash('All fields are required!', 'error')
        return redirect(url_for('grades'))
    
    try:
        marks_value = int(marks) if marks and str(marks).strip() else None
        
        new_grade = Grade(
            student_id=int(student_id),
            subject=subject,
            grade=grade,
            marks=marks_value,
            semester=semester
        )
        
        db.session.add(new_grade)
        db.session.commit()
        
        flash('Grade added successfully!', 'success')
    except (ValueError, TypeError) as e:
        flash('Invalid data provided!', 'error')
        db.session.rollback()
    
    return redirect(url_for('grades'))

@app.route('/fees')
def fees():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    role = session['role']
    
    if role == 'parent':
        students = Student.query.filter_by(parent_id=user_id).all()
        if not students:
            return redirect(url_for('index'))
        selected_student_id = request.args.get('student_id')
        if not selected_student_id:
            selected_student_id = str(students[0].id)
        selected_student = next((s for s in students if str(s.id) == str(selected_student_id)), students[0])
        fees = Fee.query.filter_by(student_id=selected_student.id).order_by(Fee.due_date.desc()).all()
        return render_template('fees.html', students=students, selected_student=selected_student, fees=fees)
    
    elif role == 'teacher':
        students = Student.query.filter_by(teacher_id=user_id).all()
        return render_template('teacher_fees.html', students=students)
    
    return redirect(url_for('index'))

@app.route('/add_fee', methods=['POST'])
def add_fee():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    student_id = request.form.get('student_id')
    fee_type = request.form.get('fee_type')
    amount = request.form.get('amount')
    due_date = request.form.get('due_date')
    if not all([student_id, fee_type, amount, due_date]):
        flash('All fields are required!', 'error')
        return redirect(url_for('fees'))
    try:
        new_fee = Fee(
            student_id=student_id,
            fee_type=fee_type,
            amount=float(amount),
            due_date=datetime.strptime(due_date, '%Y-%m-%d').date()
        )
        db.session.add(new_fee)
        db.session.commit()
        flash('Fee added successfully!', 'success')
    except Exception as e:
        flash('Error adding fee!', 'error')
        db.session.rollback()
    return redirect(url_for('fees'))

@app.route('/leave_requests')
def leave_requests():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    role = session['role']
    
    if role == 'parent':
        students = Student.query.filter_by(parent_id=user_id).all()
        if not students:
            return redirect(url_for('index'))
        selected_student_id = request.args.get('student_id')
        if not selected_student_id:
            selected_student_id = str(students[0].id)
        selected_student = next((s for s in students if str(s.id) == str(selected_student_id)), students[0])
        leave_requests = LeaveRequest.query.filter_by(student_id=selected_student.id).order_by(LeaveRequest.created_at.desc()).all()
        return render_template('leave_requests.html', students=students, selected_student=selected_student, leave_requests=leave_requests)
    
    elif role == 'teacher':
        leave_requests = LeaveRequest.query.filter_by(teacher_id=user_id).order_by(LeaveRequest.created_at.desc()).all()
        return render_template('teacher_leave_requests.html', leave_requests=leave_requests)
    
    return redirect(url_for('index'))

@app.route('/submit_leave_request', methods=['POST'])
def submit_leave_request():
    if 'user_id' not in session or session['role'] != 'parent':
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = Student.query.filter_by(parent_id=session['user_id']).first()
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    leave_type = request.form.get('leave_type')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    reason = request.form.get('reason')
    
    if not all([leave_type, start_date, end_date, reason]):
        flash('All fields are required!', 'error')
        return redirect(url_for('leave_requests'))
    
    new_leave = LeaveRequest(
        student_id=student.id,
        parent_id=session['user_id'],
        teacher_id=student.teacher_id,
        leave_type=leave_type,
        start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
        end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
        reason=reason
    )
    
    db.session.add(new_leave)
    db.session.commit()
    
    flash('Leave request submitted successfully!', 'success')
    return redirect(url_for('leave_requests'))

@app.route('/update_leave_status', methods=['POST'])
def update_leave_status():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    leave_id = request.form.get('leave_id')
    status = request.form.get('status')
    comment = request.form.get('comment', '')
    
    if not leave_id or not status:
        flash('Missing required fields!', 'error')
        return redirect(url_for('leave_requests'))
    
    leave_request = LeaveRequest.query.get(leave_id)
    if leave_request and leave_request.teacher_id == session['user_id']:
        leave_request.status = status
        leave_request.teacher_comment = comment
        db.session.commit()
        
        flash('Leave request status updated!', 'success')
    else:
        flash('Leave request not found or unauthorized!', 'error')
    
    return redirect(url_for('leave_requests'))

# Admin Routes
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    
    # Get statistics
    total_students = Student.query.count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_parents = User.query.filter_by(role='parent').count()
    total_attendance_records = Attendance.query.count()
    
    return render_template('admin_dashboard.html',
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_parents=total_parents,
                         total_attendance_records=total_attendance_records)

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/students')
def admin_students():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    
    students = Student.query.all()
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('admin_students.html', students=students, teachers=teachers)

@app.route('/admin/add_user', methods=['POST'])
def admin_add_user():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    email = request.form.get('email')
    
    if not all([username, password, role, email]):
        flash('All fields are required!', 'error')
        return redirect(url_for('admin_users'))
    
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        flash('Username already exists!', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            plain_password=password,  # Store plain password
            role=role,
            email=email
        )
        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully!', 'success')
    except Exception as e:
        flash('Error adding user!', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/add_student', methods=['POST'])
def admin_add_student():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    student_id = request.form.get('student_id')
    name = request.form.get('name')
    grade = request.form.get('grade')
    section = request.form.get('section')
    parent_username = request.form.get('parent_username')
    teacher_id = request.form.get('teacher_id')
    
    if not all([student_id, name, grade, section, parent_username, teacher_id]):
        flash('All fields are required!', 'error')
        return redirect(url_for('admin_students'))
    
    # Check if student ID already exists
    if Student.query.filter_by(student_id=student_id).first():
        flash('Student ID already exists!', 'error')
        return redirect(url_for('admin_students'))
    
    # Get parent user
    parent = User.query.filter_by(username=parent_username, role='parent').first()
    if not parent:
        flash('Parent username not found!', 'error')
        return redirect(url_for('admin_students'))
    
    try:
        new_student = Student(
            student_id=student_id,
            name=name,
            grade=grade,
            section=section,
            parent_id=parent.id,
            teacher_id=int(teacher_id)
        )
        db.session.add(new_student)
        db.session.commit()
        session['last_added_student'] = {
            'student_id': student_id,
            'student_name': name,
            'parent_username': parent_username,
            'parent_password': parent.password_hash
        }
        flash('Student added successfully!', 'success')
    except Exception as e:
        flash('Error adding student!', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin_credentials'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('admin_users'))
    
    if user.role == 'admin':
        flash('Admin user cannot be deleted!', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        # Delete related records first
        if user.role == 'parent':
            # Delete students associated with this parent
            students = Student.query.filter_by(parent_id=user.id).all()
            for student in students:
                # Delete related records
                Attendance.query.filter_by(student_id=student.id).delete()
                Grade.query.filter_by(student_id=student.id).delete()
                Fee.query.filter_by(student_id=student.id).delete()
                LeaveRequest.query.filter_by(student_id=student.id).delete()
            Student.query.filter_by(parent_id=user.id).delete()
        
        elif user.role == 'teacher':
            # Reassign students to another teacher or delete them
            students = Student.query.filter_by(teacher_id=user.id).all()
            for student in students:
                student.teacher_id = 1  # Assign to first teacher or handle differently
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting user!', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/delete_student/<int:student_id>', methods=['POST'])
def admin_delete_student(student_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = Student.query.get(student_id)
    if not student:
        flash('Student not found!', 'error')
        return redirect(url_for('admin_students'))
    
    try:
        # Delete related records
        Attendance.query.filter_by(student_id=student.id).delete()
        Grade.query.filter_by(student_id=student.id).delete()
        Fee.query.filter_by(student_id=student.id).delete()
        LeaveRequest.query.filter_by(student_id=student.id).delete()
        parent_id = student.parent_id
        # Delete the student
        db.session.delete(student)
        db.session.commit()
        # After deleting the student, check if parent has any more students
        remaining_students = Student.query.filter_by(parent_id=parent_id).count()
        if remaining_students == 0:
            parent_user = User.query.get(parent_id)
            if parent_user:
                db.session.delete(parent_user)
                db.session.commit()
        flash('Student (and parent if no more students) deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting student!', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin_students'))

@app.route('/admin/credentials')
def admin_credentials():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    
    users = User.query.all()
    students = Student.query.all()
    last_added_student = session.pop('last_added_student', None)
    return render_template('admin_credentials.html', users=users, students=students, last_added_student=last_added_student)

@app.route('/admin/delete_all_users', methods=['POST'])
def admin_delete_all_users():
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        User.query.filter(User.role != 'admin').delete(synchronize_session=False)
        db.session.commit()
        flash('All users except admin have been deleted!', 'success')
    except Exception as e:
        flash('Error deleting users!', 'error')
        db.session.rollback()
    return redirect(url_for('admin_credentials'))

# Route for parent to contact teacher
@app.route('/contact_teacher', methods=['GET', 'POST'])
def contact_teacher():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('index'))
    parent_id = session['user_id']
    students = Student.query.filter_by(parent_id=parent_id).all()
    if not students:
        flash('Student not found!', 'error')
        return redirect(url_for('parent_dashboard'))
    # Get selected student_id from query or form
    if request.method == 'POST':
        selected_student_id = request.form.get('student_id')
    else:
        selected_student_id = request.args.get('student_id')
    if not selected_student_id:
        selected_student_id = str(students[0].id)
    selected_student = next((s for s in students if str(s.id) == str(selected_student_id)), students[0])
    teacher = User.query.get(selected_student.teacher_id)
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash('Message cannot be empty!', 'error')
            return redirect(url_for('contact_teacher', student_id=selected_student.id))
        message = Message(
            sender_id=parent_id,
            receiver_id=teacher.id,
            student_id=selected_student.id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent to teacher!', 'success')
        return redirect(url_for('contact_teacher', student_id=selected_student.id))
    # Show message history
    messages = Message.query.filter_by(student_id=selected_student.id).order_by(Message.timestamp.asc()).all()
    return render_template('contact_teacher.html', teacher=teacher, student=selected_student, students=students, messages=messages)

# Route for teacher to view and reply to messages
@app.route('/messages', methods=['GET', 'POST'])
def teacher_messages():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('index'))
    teacher_id = session['user_id']
    # Get all students assigned to this teacher
    students = Student.query.filter_by(teacher_id=teacher_id).all()
    student_ids = [s.id for s in students]
    
    # Get selected parent from query parameter
    selected_parent_id = request.args.get('parent_id')
    
    # Build parent chats list
    parent_chats = []
    try:
        # Get ALL parents associated with this teacher's students
        parent_ids = set()
        for student in students:
            parent_ids.add(student.parent_id)
        
        for parent_id in parent_ids:
            parent = User.query.get(parent_id)
            if parent:
                # Get the student for this parent
                student = Student.query.filter_by(parent_id=parent_id, teacher_id=teacher_id).first()
                
                # Get messages between this parent and teacher
                parent_messages = Message.query.filter(
                    Message.student_id.in_(student_ids),
                    ((Message.sender_id == parent_id) & (Message.receiver_id == teacher_id)) |
                    ((Message.sender_id == teacher_id) & (Message.receiver_id == parent_id))
                ).order_by(Message.timestamp.desc()).all()
                
                # Count unread messages (messages from parent to teacher that are unread)
                unread_count = Message.query.filter(
                    Message.sender_id == parent_id,
                    Message.receiver_id == teacher_id,
                    Message.is_read == False
                ).count()
                
                # Determine last message and time
                if parent_messages:
                    last_message = parent_messages[0]
                    last_message_text = last_message.content
                    # Convert UTC to local time
                    local_time = utc_to_local(last_message.timestamp)
                    last_message_time = local_time.strftime('%H:%M')
                    has_messages = True
                else:
                    last_message_text = "No messages yet"
                    last_message_time = ""
                    has_messages = False
                
                # Check if the last message is from parent (unreplied) or teacher (replied)
                is_unreplied = False
                if parent_messages:
                    last_message = parent_messages[0]
                    is_unreplied = (last_message.sender_id == parent_id and last_message.receiver_id == teacher_id)
                
                parent_chats.append({
                    'parent_id': parent_id,
                    'parent_name': parent.username,
                    'student_name': student.name if student else 'Unknown',
                    'student_id': student.id if student else None,
                    'last_message': last_message_text,
                    'last_time': last_message_time,
                    'unread_count': unread_count,
                    'has_messages': has_messages,
                    'is_unreplied': is_unreplied,
                    'messages': parent_messages[::-1] if parent_messages else []  # Reverse to show in chronological order
                })
        
        # Sort parent chats: unreplied messages first, then by last message time
        parent_chats.sort(key=lambda x: (not x['is_unreplied'], x['last_time'] if x['last_time'] else ''), reverse=True)
        
    except Exception as e:
        # If there's any error, just continue with empty list
        parent_chats = []
    
    # Get selected parent data
    selected_parent = None
    if selected_parent_id:
        for chat in parent_chats:
            if str(chat['parent_id']) == str(selected_parent_id):
                selected_parent = chat
                # Mark messages as read when teacher views the chat
                try:
                    Message.query.filter(
                        Message.sender_id == int(selected_parent_id),
                        Message.receiver_id == teacher_id,
                        Message.is_read == False
                    ).update({'is_read': True})
                    db.session.commit()
                except Exception as e:
                    # If there's an error, just continue
                    pass
                break
    
    if request.method == 'POST':
        reply_content = request.form.get('reply_content')
        parent_id = request.form.get('parent_id')
        student_id = request.form.get('student_id')
        
        if reply_content and parent_id and student_id:
            try:
                reply = Message(
                    sender_id=teacher_id,
                    receiver_id=int(parent_id),
                    student_id=int(student_id),
                    content=reply_content
                )
                db.session.add(reply)
                db.session.commit()
                flash('Message sent!', 'success')
                return redirect(url_for('teacher_messages', parent_id=parent_id))
            except Exception as e:
                flash('Error sending message!', 'error')
        else:
            flash('Missing required information!', 'error')
        
        return redirect(url_for('teacher_messages', parent_id=selected_parent_id))
    
    return render_template('teacher_messages.html', 
                         parent_chats=parent_chats, 
                         selected_parent=selected_parent,
                         students=students)

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create sample data if database is empty
        if not User.query.first():
            # Create admin user
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                plain_password='admin123',
                role='admin',
                email='admin@school.com'
            )
            db.session.add(admin)
            db.session.commit()
            
            # Create sample teacher
            teacher = User(
                username='teacher1',
                password_hash=generate_password_hash('teacher123'),
                plain_password='teacher123',
                role='teacher',
                email='teacher1@school.com'
            )
            db.session.add(teacher)
            db.session.commit()
            
            # Create sample parent
            parent = User(
                username='parent1',
                password_hash=generate_password_hash('parent123'),
                plain_password='parent123',
                role='parent',
                email='parent1@email.com'
            )
            db.session.add(parent)
            db.session.commit()
            
            # Create sample student
            student = Student(
                student_id='STU001',
                name='John Doe',
                grade='10',
                section='A',
                parent_id=parent.id,
                teacher_id=teacher.id
            )
            db.session.add(student)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
