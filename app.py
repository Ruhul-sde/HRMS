from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import uuid
from datetime import datetime, timedelta
import calendar
import config
from models.database import initialize_db, get_db, save_db
from utils.distance import calculate_distance
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from io import BytesIO

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

@app.route('/')
def login():
    db = get_db()
    departments = db.get('settings', {}).get('departments', ['IT', 'HR', 'Finance', 'Marketing', 'Operations'])
    job_roles = db.get('settings', {}).get('job_roles', [])
    return render_template('login.html', departments=departments, job_roles=job_roles)

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    db = get_db()
    if username in db['users'] and db['users'][username]['password'] == password:
        if db['users'][username]['role'] == 'pending':
            return render_template('login.html', error='Your account is pending approval from admin')

        session['username'] = username
        session['role'] = db['users'][username]['role']
        session['name'] = db['users'][username]['name']
        session['employee_id'] = db['users'][username]['employee_id']

        # Get user's assigned location from their profile
        if 'latitude' in db['users'][username] and 'longitude' in db['users'][username]:
            session['latitude'] = db['users'][username]['latitude']
            session['longitude'] = db['users'][username]['longitude']
        else:
            # Set default location if none is assigned yet
            session['latitude'] = 0
            session['longitude'] = 0

        # Redirect admin to admin dashboard, regular users to regular dashboard
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))

    return render_template('login.html', error='Invalid credentials')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    fullname = request.form.get('fullname')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    # Basic validation
    if not username or not password or not confirm_password or not fullname:
        return render_template('login.html', error='All fields are required')

    if password != confirm_password:
        return render_template('login.html', error='Passwords do not match')

    db = get_db()

    # Check if username already exists
    if username in db['users']:
        return render_template('login.html', error='Username already exists')

    # Generate a new employee ID
    employee_count = sum(1 for user in db['users'].values() if user['role'] == 'employee')
    new_emp_id = f"EMP{str(employee_count + 1).zfill(3)}"

    # Add the new user with pending status
    db['users'][username] = {
        'password': password,
        'name': fullname,
        'mobile': request.form.get('mobile'),
        'department': request.form.get('department'),
        'job_role': request.form.get('job_role'),
        'email': username,  # Company email
        'role': 'pending',  # Mark as pending instead of employee
        'employee_id': new_emp_id,
        'manager': 'admin',   # Default manager is admin
        'latitude': float(latitude) if latitude else 0,
        'longitude': float(longitude) if longitude else 0,
        'location_name': 'Custom Location',  # Default location name
        'join_date': datetime.now().strftime('%Y-%m-%d')
    }

    save_db(db)

    return render_template('login.html', success='Account created successfully! You can now login.')

@app.route('/reset_password', methods=['POST'])
def reset_password():
    username = request.form.get('username')
    employee_id = request.form.get('employee_id')
    dob = request.form.get('dob')

    if not all([username, employee_id, dob]):
        return render_template('login.html', error='All fields are required')

    db = get_db()

    if username not in db['users']:
        return render_template('login.html', error='Email not found')

    user = db['users'][username]
    if user['employee_id'] != employee_id or user['dob'] != dob:
        return render_template('login.html', error='Invalid credentials')

    # Generate a simple random password
    import random
    import string
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    # In a real application, you would send this password via email
    # For this demo, we'll just display it
    db['users'][username]['password'] = new_password
    save_db(db)

    return render_template('login.html', success=f'New password has been sent to your email: {username}')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    if session['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))

    db = get_db()
    user_data = db['users'][session['username']]

    # Get today's attendance
    today = datetime.now().strftime('%Y-%m-%d')
    attendance_today = None
    if 'attendance' in db and session['employee_id'] in db['attendance']:
        if today in db['attendance'][session['employee_id']]:
            attendance_today = db['attendance'][session['employee_id']][today]

    # Get pending leaves
    pending_leaves = []
    if 'leaves' in db and session['employee_id'] in db['leaves']:
        for leave_id, leave in db['leaves'][session['employee_id']].items():
            if leave['status'] == 'pending':
                pending_leaves.append(leave)

    # Calculate real attendance stats
    stats = {'present_days': 0, 'absent_days': 0, 'leave_days': 0}

    if 'attendance' in db and session['employee_id'] in db['attendance']:
        current_month = datetime.now().strftime('%Y-%m')
        stats['present_days'] = sum(1 for date, record in db['attendance'][session['employee_id']].items() 
                                  if date.startswith(current_month) and record['status'] == 'Present')

    # Calculate leave days
    if 'leaves' in db and session['employee_id'] in db['leaves']:
        current_month = datetime.now().strftime('%Y-%m')
        for leave in db['leaves'][session['employee_id']].values():
            if leave['status'] == 'approved' and leave['start_date'].startswith(current_month):
                start = datetime.strptime(leave['start_date'], '%Y-%m-%d')
                end = datetime.strptime(leave['end_date'], '%Y-%m-%d')
                stats['leave_days'] += (end - start).days + 1

    # Calculate working days in current month
    now = datetime.now()
    total_days = calendar.monthrange(now.year, now.month)[1]
    working_days = sum(1 for day in range(1, total_days + 1)
                      if datetime(now.year, now.month, day).weekday() < 5)  # Monday to Friday

    stats['absent_days'] = working_days - stats['present_days'] - stats['leave_days']
    stats['attendance_percentage'] = round((stats['present_days'] / working_days) * 100 if working_days > 0 else 0, 1)

    # Calculate weekly hours
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    weekly_hours = 0
    if 'attendance' in db and session['employee_id'] in db['attendance']:
        for date, record in db['attendance'][session['employee_id']].items():
            attendance_date = datetime.strptime(date, '%Y-%m-%d')
            if start_of_week <= attendance_date <= today and 'working_hours' in record:
                weekly_hours += record['working_hours']
    stats['weekly_hours'] = round(weekly_hours, 2)

    return render_template('dashboard.html', 
                          user=user_data, 
                          attendance_today=attendance_today,
                          pending_leaves=pending_leaves,
                          locations=db['locations'],
                          stats=stats)

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    try:
        if 'username' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'})

        data = request.json
        user_lat = float(data.get('latitude'))
        user_lon = float(data.get('longitude'))
        is_checkout = data.get('is_checkout', False)

        db = get_db()
        user_data = db['users'][session['username']]
        today = datetime.now().strftime('%Y-%m-%d')

        # Initialize attendance structure if needed
        if 'attendance' not in db:
            db['attendance'] = {}
        if session['employee_id'] not in db['attendance']:
            db['attendance'][session['employee_id']] = {}

        current_attendance = db['attendance'][session['employee_id']].get(today, {})

        # Check if user has assigned location
        if 'latitude' not in user_data or 'longitude' not in user_data:
            return jsonify({'success': False, 'message': 'No assigned location found'})

        # Calculate distance from assigned location
        try:
            distance = calculate_distance(
                user_lat, 
                user_lon, 
                user_data['latitude'], 
                user_data['longitude']
            )
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error calculating distance: {str(e)}'})

        # Use a more lenient radius of 500 meters for testing
        if distance > 500:  # 500 meters radius
            return jsonify({
                'success': False, 
                'message': f'You are {int(distance)}m away from your assigned location (max allowed: 500m)'
            })

        # Check if already marked for today
        today = datetime.now().strftime('%Y-%m-%d')
        if not is_checkout:  # Only check for duplicate check-in
            if ('attendance' in db and 
                session['employee_id'] in db['attendance'] and 
                today in db['attendance'][session['employee_id']] and
                'check_in' in db['attendance'][session['employee_id']][today]):
                return jsonify({
                    'success': False, 
                    'message': 'Already checked in for today'
                })

        # Mark attendance with Indian time
        indian_time = (datetime.now() + timedelta(hours=5, minutes=30)).strftime('%I:%M %p')

        if 'attendance' not in db:
            db['attendance'] = {}

        if session['employee_id'] not in db['attendance']:
            db['attendance'][session['employee_id']] = {}

        # Handle checkout
        if is_checkout:
            if not current_attendance or 'check_in' not in current_attendance:
                return jsonify({
                    'success': False,
                    'message': 'Please check-in first before checking out'
                })

            if current_attendance.get('check_out'):
                return jsonify({
                    'success': False,
                    'message': 'Already checked out for today'
                })

            current_attendance['check_out'] = indian_time
            current_attendance['check_out_latitude'] = user_lat
            current_attendance['check_out_longitude'] = user_lon
            current_attendance['check_out_location'] = user_data.get('location_name', 'Assigned Location')

            # Calculate working hours
            check_in_time = datetime.strptime(current_attendance['check_in'], '%I:%M %p')
            check_out_time = datetime.strptime(indian_time, '%I:%M %p')
            working_hours = (check_out_time - check_in_time).total_seconds() / 3600
            current_attendance['working_hours'] = round(working_hours, 2)

            db['attendance'][session['employee_id']][today] = current_attendance
            save_db(db)

            return jsonify({
                'success': True,
                'message': 'Check-out marked successfully',
                'check_out_time': indian_time,
                'check_in_time': current_attendance['check_in'],
                'location': user_data.get('location_name', 'Assigned Location')
            })

        # Store attendance with location details
        # Initialize check-in and check-out records if they don't exist
        if 'check_ins' not in db:
            db['check_ins'] = {}
        if 'check_outs' not in db:
            db['check_outs'] = {}

        if session['employee_id'] not in db['check_ins']:
            db['check_ins'][session['employee_id']] = {}
        if session['employee_id'] not in db['check_outs']:
            db['check_outs'][session['employee_id']] = {}

        if is_checkout:
            # Handle check-out
            if not current_attendance or 'check_in' not in current_attendance:
                return jsonify({
                    'success': False,
                    'message': 'Please check-in first before checking out'
                })

            if 'check_out' in current_attendance:
                return jsonify({
                    'success': False,
                    'message': 'Already checked out for today'
                })

            # Record check-out
            current_attendance['check_out'] = indian_time
            current_attendance['check_out_location'] = user_data.get('location_name', 'Assigned Location')
            current_attendance['status'] = 'Present'

            # Calculate working hours
            check_in_time = datetime.strptime(current_attendance['check_in'], '%I:%M %p')
            check_out_time = datetime.strptime(indian_time, '%I:%M %p')
            working_hours = (check_out_time - check_in_time).total_seconds() / 3600
            current_attendance['working_hours'] = round(working_hours, 2)

            db['attendance'][session['employee_id']][today] = current_attendance
            message = 'Check-out marked successfully'
        else:
            # Handle check-in
            if current_attendance and 'check_in' in current_attendance:
                return jsonify({
                    'success': False,
                    'message': 'Already checked in for today'
                })

            # Record check-in
            db['attendance'][session['employee_id']][today] = {
                'check_in': indian_time,
                'location': user_data.get('location_name', 'Assigned Location'),
                'status': 'Present',
                'latitude': user_lat,
                'longitude': user_lon
            }
            message = 'Check-in marked successfully'


        save_db(db)
        return jsonify({
            'success': True,
            'message': message,
            'location': user_data.get('location_name', 'Assigned Location')
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'})

@app.route('/apply_leave', methods=['GET', 'POST'])
def apply_leave():
    if 'username' not in session or session['role'] == 'admin':
        return redirect(url_for('home'))

    db = get_db()

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        reason = request.form.get('reason')
        leave_type = request.form.get('leave_type')

        db = get_db()

        if 'leaves' not in db:
            db['leaves'] = {}

        if session['employee_id'] not in db['leaves']:
            db['leaves'][session['employee_id']] = {}

        leave_id = str(uuid.uuid4())

        # Find manager
        manager_id = db['users'][session['username']].get('manager')

        db['leaves'][session['employee_id']][leave_id] = {
            'start_date': start_date,
            'end_date': end_date,
            'reason': reason,
            'type': leave_type,
            'status': 'pending',
            'manager': manager_id,
            'applied_on': datetime.now().strftime('%Y-%m-%d')
        }

        save_db(db)

        return redirect(url_for('leave_status')) 

    # Define leave types
    leave_types = ['PL', 'CL', 'ML', 'Other']

    # Calculate leave balances
    leave_balances = {
        'PL': {'total': 12, 'used': 0, 'remaining': 12},
        'CL': {'total': 6, 'used': 0, 'remaining': 6},
        'ML': {'total': 7, 'used': 0, 'remaining': 7},
        'Other': {'total': 5, 'used': 0, 'remaining': 5}
    }

    if 'leaves' in db and session['employee_id'] in db['leaves']:
        for leave in db['leaves'][session['employee_id']].values():
            if leave['status'] == 'approved':
                leave_type = leave['type']
                if leave_type in leave_balances:
                    start = datetime.strptime(leave['start_date'], '%Y-%m-%d')
                    end = datetime.strptime(leave['end_date'], '%Y-%m-%d')
                    days = (end - start).days + 1
                    leave_balances[leave_type]['used'] += days
                    leave_balances[leave_type]['remaining'] = max(0, leave_balances[leave_type]['total'] - leave_balances[leave_type]['used'])


    return render_template('apply_leave.html', leave_types=leave_types, leave_balances=leave_balances)

@app.route('/leave_status')
def leave_status():
    if 'username' not in session or session['role'] == 'admin':
        return redirect(url_for('home'))

    db = get_db()
    user_leaves = {}

    if 'leaves' in db and session['employee_id'] in db['leaves']:
        user_leaves = db['leaves'][session['employee_id']]

    return render_template('leave_status.html', leaves=user_leaves)

@app.route('/admin/pending_leaves')
def admin_pending_leaves():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))

    db = get_db()
    pending_leaves = {}
    pending_users = {username: user for username, user in db['users'].items() if user['role'] == 'pending'}

    if 'leaves' in db:
        for emp_id, leaves in db['leaves'].items():
            for leave_id, leave in leaves.items():
                if leave['status'] == 'pending':
                    if emp_id not in pending_leaves:
                        pending_leaves[emp_id] = {}
                    pending_leaves[emp_id][leave_id] = leave.copy()
                    # Add employee name
                    for username, user_data in db['users'].items():
                        if user_data['employee_id'] == emp_id:
                            pending_leaves[emp_id][leave_id]['employee_name'] = user_data['name']
                            break

    return render_template('admin_leaves.html', pending_leaves=pending_leaves, pending_users=pending_users)

@app.route('/admin/update_leave', methods=['POST'])
def admin_update_leave():
    if 'username' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    data = request.json
    emp_id = data.get('employee_id')
    leave_id = data.get('leave_id')
    status = data.get('status')  # 'approved' or 'rejected'

    db = get_db()

    if 'leaves' in db and emp_id in db['leaves'] and leave_id in db['leaves'][emp_id]:
        comment = data.get('comment', '')
        db['leaves'][emp_id][leave_id]['status'] = status
        db['leaves'][emp_id][leave_id]['comment'] = comment
        save_db(db)
        msg = 'approved' if status == 'approved' else 'rejected'
        return jsonify({'success': True, 'message': f'Leave {msg} successfully'})

    return jsonify({'success': False, 'message': 'Leave not found'})

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    try:
        data = request.json
        db = get_db()

        # Update user data
        db['users'][session['username']].update({
            'name': data.get('name'),
            'mobile': data.get('mobile'),
            'department': data.get('department'),
            'job_role': data.get('job_role')
        })

        save_db(db)
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/profile')
def profile():
    if 'username' not in session or session['role'] == 'admin':
        return redirect(url_for('home'))

    db = get_db()
    user_data = db['users'][session['username']]
    employee_id = user_data['employee_id']

    # Calculate real attendance stats
    stats = {'present_days': 0, 'absent_days': 0, 'leave_days': 0}

    # Calculate present days
    if 'attendance' in db and employee_id in db['attendance']:
        current_month = datetime.now().strftime('%Y-%m')
        stats['present_days'] = sum(1 for date, record in db['attendance'][employee_id].items() 
                                  if date.startswith(current_month) and record['status'] == 'Present')

    # Calculate leave days
    if 'leaves' in db and employee_id in db['leaves']:
        for leave in db['leaves'][employee_id].values():
            if leave['status'] == 'approved':
                start = datetime.strptime(leave['start_date'], '%Y-%m-%d')
                end = datetime.strptime(leave['end_date'], '%Y-%m-%d')
                stats['leave_days'] += (end - start).days + 1

    # Calculate working days in current month
    now = datetime.now()
    total_days = calendar.monthrange(now.year, now.month)[1]
    working_days = sum(1 for day in range(1, total_days + 1)
                      if datetime(now.year, now.month, day).weekday() < 5)

    stats['absent_days'] = working_days - stats['present_days'] - stats['leave_days']
    stats['attendance_percentage'] = round((stats['present_days'] / working_days) * 100 if working_days > 0 else 0, 1)

    # Get employment details
    employment_details = {
        'position': user_data.get('job_role', 'Not Set'),
        'join_date': user_data.get('join_date', 'Not Set'),
        'manager': user_data.get('manager', 'Not Assigned'),
        'department': user_data.get('department', 'Not Set'),
        'location': user_data.get('location_name', 'Not Set')
    }

    # Calculate leave balances
    leaves = {
        'pl_remaining': 12,
        'cl_remaining': 6,
        'ml_remaining': 7
    }

    if 'leaves' in db and employee_id in db['leaves']:
        for leave in db['leaves'][employee_id].values():
            if leave['status'] == 'approved':
                leave_type = leave['type'].lower()
                days = (datetime.strptime(leave['end_date'], '%Y-%m-%d') - 
                       datetime.strptime(leave['start_date'], '%Y-%m-%d')).days + 1
                if leave_type == 'pl':
                    leaves['pl_remaining'] -= days
                elif leave_type == 'cl':
                    leaves['cl_remaining'] -= days
                elif leave_type == 'ml':
                    leaves['ml_remaining'] -= days

    # Get employment details with extended information
    employment_details = {
        'position': user_data.get('job_role', 'Not Set'),
        'join_date': user_data.get('join_date', 'Not Set'),
        'manager': user_data.get('manager', 'Not Assigned'),
        'department': user_data.get('department', 'Not Set'),
        'location': user_data.get('location_name', 'Not Set'),
        'email': session['username'],
        'mobile': user_data.get('mobile', 'Not Set')
    }

    # Add coordinates and location info to user data
    user_data['latitude'] = user_data.get('latitude', 0.0)
    user_data['longitude'] = user_data.get('longitude', 0.0)
    user_data['email'] = session['username']

    return render_template('profile.html', user=user_data, stats=stats, leaves=leaves, employment_details=employment_details)

@app.route('/attendance_report')
def attendance_report():
    if 'username' not in session or session['role'] == 'admin':
        return redirect(url_for('home'))

    # Get selected month or default to current month
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    year, month_num = map(int, month.split('-'))

    db = get_db()
    attendance_data = {}
    leaves_data = {}

    # Initialize and calculate stats
    stats = {
        'present_days': 0,
        'absent_days': 0,
        'leave_days': 0,
        'attendance_percentage': 0
    }

    # Calculate present days
    if 'attendance' in db and session['employee_id'] in db['attendance']:
        stats['present_days'] = sum(1 for date, record in db['attendance'][session['employee_id']].items() 
                                  if date.startswith(month) and record['status'] == 'Present')

    # Calculate total working days in the month
    total_days = calendar.monthrange(year, month_num)[1]
    working_days = sum(1 for day in range(1, total_days + 1)
                      if datetime(year, month_num, day).weekday() < 5)  # Monday to Friday

    # Calculate leave days
    if 'leaves' in db and session['employee_id'] in db['leaves']:
        for leave in db['leaves'][session['employee_id']].values():
            if leave['status'] == 'approved' and leave['start_date'].startswith(month):
                start = datetime.strptime(leave['start_date'], '%Y-%m-%d')
                end = datetime.strptime(leave['end_date'], '%Y-%m-%d')
                stats['leave_days'] += (end - start).days + 1

    # Calculate absent days and attendance percentage
    stats['absent_days'] = working_days - stats['present_days'] - stats['leave_days']
    stats['attendance_percentage'] = round((stats['present_days'] / working_days) * 100 if working_days > 0 else 0, 1)

    # Get days in the selected month
    days_in_month = calendar.monthrange(year, month_num)[1]
    month_dates = [f"{month}-{str(day).zfill(2)}" for day in range(1, days_in_month + 1)]

    # Get attendance for the month
    if 'attendance' in db and session['employee_id'] in db['attendance']:
        employee_attendance = db['attendance'][session['employee_id']]
        for date in month_dates:
            if date in employee_attendance:
                attendance_data[date] = employee_attendance[date]

    # Get leaves for the month
    leave_counts = {'PL': 0, 'CL': 0, 'ML': 0, 'Other': 0}
    leave_details = []

    if 'leaves' in db and session['employee_id'] in db['leaves']:
        for leave_id, leave in db['leaves'][session['employee_id']].items():
            start = datetime.strptime(leave['start_date'], '%Y-%m-%d')
            end = datetime.strptime(leave['end_date'], '%Y-%m-%d')

            # Check if leave falls in selected month
            if start.year == year and start.month == month_num:
                leave_type = leave['type']
                days = (end - start).days + 1

                if leave_type in leave_counts:
                    leave_counts[leave_type] += days
                else:
                    leave_counts['Other'] += days

                leave_details.append(leave)

    # Get all months with attendance or leave data
    all_months = set()
    # Add current selected month
    all_months.add(month)

    # Add months with attendance data
    if 'attendance' in db and session['employee_id'] in db['attendance']:
        for date in db['attendance'][session['employee_id']]:
            all_months.add(date[:7])  # YYYY-MM format

    # Add months with leave data
    if 'leaves' in db and session['employee_id'] in db['leaves']:
        for leave_id, leave in db['leaves'][session['employee_id']].items():
            all_months.add(leave['start_date'][:7])

    # Ensure all months of current year are available for selection
    current_year = datetime.now().year
    for m in range(1, 13):
        all_months.add(f"{current_year}-{str(m).zfill(2)}")

    # Also add all months of the selected year
    for m in range(1, 13):
        all_months.add(f"{year}-{str(m).zfill(2)}")

    all_months = sorted(list(all_months), reverse=True)

    return render_template('attendance_report.html', 
                          attendance_data=attendance_data,
                          leaves_data=leave_counts,
                          leave_details=leave_details,
                          month=month,
                          all_months=all_months,
                          month_dates=month_dates,
                          stats=stats)

@app.route('/admin/attendance_report')
def admin_attendance_report():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))

    emp_id = request.args.get('employee_id')
    department = request.args.get('department', 'all')
    job_role = request.args.get('job_role', 'all')
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))

    db = get_db()

    # Get unique departments and job roles
    departments = set()
    job_roles = set()
    employees = {}

    for username, user in db['users'].items():
        if user['role'] != 'admin':
            if department == 'all' or user.get('department') == department:
                if job_role == 'all' or user.get('job_role') == job_role:
                    employees[user['employee_id']] = user['name']
                    if user.get('department'):
                        departments.add(user.get('department'))
                    if user.get('job_role'):
                        job_roles.add(user.get('job_role'))

    if not emp_id and employees:
        emp_id = list(employees.keys())[0]

    attendance_data = {}
    leaves_data = {}
    leave_counts = {'PL': 0, 'CL': 0, 'ML': 0, 'Other': 0}
    leave_details = []

    # Calculate stats
    stats = {
        'present_days': 0,
        'leave_days': 0,
        'weekly_hours': 0
    }

    if emp_id:
        year, month_num = map(int, month.split('-'))

        ```python
        # Get days in the selected month
        days_in_month = calendar.monthrange(year, month_num)[1]
        month_dates = [f"{month}-{str(day).zfill(2)}" for day in range(1, days_in_month + 1)]

        # Calculate present days
        if 'attendance' in db and emp_id in db['attendance']:
            stats['present_days'] = sum(1 for date, record in db['attendance'][emp_id].items() 
                                    if date.startswith(month) and record['status'] == 'Present')

        # Calculate leave days
        if 'leaves' in db and emp_id in db['leaves']:
            for leave in db['leaves'][emp_id].values():
                if leave['status'] == 'approved':
                    start = datetime.strptime(leave['start_date'], '%Y-%m-%d')
                    end = datetime.strptime(leave['end_date'], '%Y-%m-%d')
                    if start.strftime('%Y-%m') == month:
                        stats['leave_days'] += (end - start).days + 1

        # Calculate weekly hours
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        if 'attendance' in db and emp_id in db['attendance']:
            for date, record in db['attendance'][emp_id].items():
                attendance_date = datetime.strptime(date, '%Y-%m-%d')
                if start_of_week <= attendance_date <= today and 'working_hours' in record:
                    stats['weekly_hours'] += record['working_hours']
        stats['weekly_hours'] = round(stats['weekly_hours'], 2)

    # Get all months with attendance or leave data
    all_months = set()
    if 'attendance' in db:
        for employee_id in db['attendance']:
            for date in db['attendance'][employee_id]:
                all_months.add(date[:7])  # YYYY-MM format

    if 'leaves' in db:
        for employee_id in db['leaves']:
            for leave_id, leave in db['leaves'][employee_id].items():
                all_months.add(leave['start_date'][:7])

    all_months = sorted(list(all_months), reverse=True)

    return render_template('admin_attendance_report.html', 
                          employees=employees,
                          departments=sorted(list(departments)),
                          job_roles=sorted(list(job_roles)),
                          selected_employee=emp_id,
                          selected_department=department,
                          selected_job_role=job_role,
                          attendance_data=attendance_data,
                          leaves_data=leave_counts,
                          leave_details=leave_details,
                          month=month,
                          all_months=all_months,
                          month_dates=month_dates,
                          stats=stats)

@app.route('/admin/locations', methods=['GET', 'POST'])
def admin_locations():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))

    db = get_db()

    if request.method == 'POST':
        name = request.form.get('name')
        latitude = float(request.form.get('latitude'))
        longitude = float(request.form.get('longitude'))
        radius = float(request.form.get('radius'))

        location_id = str(uuid.uuid4())

        if 'locations' not in db:
            db['locations'] = {}

        db['locations'][location_id] = {
            'name': name,
            'latitude': latitude,
            'longitude': longitude,
            'radius': radius
        }

        save_db(db)

        return redirect(url_for('admin_locations'))

    return render_template('admin_locations.html', locations=db['locations'])


@app.route('/admin/approve_user/<username>', methods=['POST'])
def approve_user(username):
    if 'username' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    db = get_db()
    if username in db['users'] and db['users'][username]['role'] == 'pending':
        db['users'][username]['role'] = 'employee'
        save_db(db)
        return jsonify({'success': True, 'message': 'User approved successfully'})

    return jsonify({'success': False, 'message': 'User not found'})

@app.route('/admin/reject_user/<username>', methods=['POST'])
def reject_user(username):
    if 'username' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    db = get_db()
    if username in db['users'] and db['users'][username]['role'] == 'pending':
        del db['users'][username]
        save_db(db)
        return jsonify({'success': True, 'message': 'User rejected and removed'})

    return jsonify({'success': False, 'message': 'User not found'})

@app.route('/api/admin/settings/leave-balance', methods=['POST'])
def update_leave_balance():
    if 'username' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    data = request.json
    db = get_db()

    if 'settings' not in db:
        db['settings'] = {}

    db['settings']['leave_balance'] = {
        'pl': data['pl'],
        'cl': data['cl'],
        'ml': data['ml']
    }

    save_db(db)
    return jsonify({'success': True})

@app.route('/api/admin/settings/department', methods=['POST'])
def update_department():
    if 'username' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    data = request.json
    db = get_db()

    if 'settings' not in db:
        db['settings'] = {}
    if 'departments' not in db['settings']:
        db['settings']['departments'] = []

    if data['id']:  # Edit
        idx = db['settings']['departments'].index(data['id'])
        db['settings']['departments'][idx] = data['name']
    else:  # Add
        db['settings']['departments'].append(data['name'])

    save_db(db)
    return jsonify({'success': True})

@app.route('/api/admin/settings/department/<name>', methods=['DELETE'])
def delete_department(name):
    if 'username' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    db = get_db()
    db['settings']['departments'].remove(name)
    save_db(db)
    return jsonify({'success': True})

@app.route('/api/admin/settings/job-role', methods=['POST'])
def update_job_role():
    if 'username' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    data = request.json
    db = get_db()

    if 'settings' not in db:
        db['settings'] = {}
    if 'job_roles' not in db['settings']:
        db['settings']['job_roles'] = []

    if data['id']:  # Edit
        idx = db['settings']['job_roles'].index(data['id'])
        db['settings']['job_roles'][idx] = data['name']
    else:  # Add
        db['settings']['job_roles'].append(data['name'])

    save_db(db)
    return jsonify({'success': True})

@app.route('/api/admin/settings/job-role/<name>', methods=['DELETE'])
def delete_job_role(name):
    if 'username' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    db = get_db()
    db['settings']['job_roles'].remove(name)
    save_db(db)
    return jsonify({'success': True})

@app.route('/admin/settings')
def admin_settings():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))

    db = get_db()
    settings = db.get('settings', {})

    leave_settings = settings.get('leave_balance', {'pl': 12, 'cl': 6, 'ml': 7})
    departments = settings.get('departments', [])
    job_roles = settings.get('job_roles', [])

    return render_template('admin_settings.html', 
                         leave_settings=leave_settings,
                         departments=departments,
                         job_roles=job_roles)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))

    db = get_db()

    # Count total employees, present today, absent today, and pending leaves
    total_employees = sum(1 for user in db['users'].values() if user['role'] == 'employee')

    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')

    # Get today's attendance with employee details
    today_attendance = []
    if 'attendance' in db:
        for emp_id, dates in db['attendance'].items():
            if today in dates:
                # Find employee name
                emp_name = ''
                for username, user_data in db['users'].items():
                    if user_data['employee_id'] == emp_id:
                        emp_name = user_data['name']
                        break

                today_attendance.append({
                    'name': emp_name,
                    'check_in': dates[today]['check_in'],
                    'location': dates[today]['location'],
                    'status': dates[today]['status']
                })

    # Count present employees today
    present_today = len(today_attendance)

    # Count pending leaves
    pending_leaves = 0
    if 'leaves' in db:
        for emp_id, leaves in db['leaves'].items():
            for leave_id, leave in leaves.items():
                if leave['status'] == 'pending':
                    pending_leaves += 1

    # Calculate absent employees (total - present)
    absent_today = total_employees - present_today

    # Prepare stats for the admin dashboard
    stats = {
        'total_employees': total_employees,
        'present_today': present_today,
        'absent_today': absent_today,
        'pending_leaves': pending_leaves
    }

    return render_template('admin_dashboard.html', stats=stats)

@app.route('/admin/notices', methods=['GET', 'POST'])
def admin_notices():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))

    db = get_db()
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        target_type = request.form.get('target_type')
        target_value = request.form.get('target_value', '')

        notice_id = str(uuid.uuid4())

        if 'notices' not in db:
            db['notices'] = {}

        db['notices'][notice_id] = {
            'title': title,
            'content': content,
            'posted_by': session['username'],
            'posted_on': datetime.now().strftime('%Y-%m-%d'),
            'target': {
                'type': target_type,
                'value': target_value
            }
        }
        save_db(db)
        return redirect(url_for('admin_notices'))

    notices = db.get('notices', {})
    return render_template('admin_notices.html', notices=notices)

@app.route('/notices')
def view_notices():
    if 'username' not in session:
        return redirect(url_for('home'))

    db = get_db()
    user_data = db['users'][session['username']]
    all_notices = db.get('notices', {})

    # Filter notices based on target
    visible_notices = {}
    for notice_id, notice in all_notices.items():
        target = notice['target']
        if (target['type'] == 'all' or
            (target['type'] == 'department' and target['value'] == user_data.get('department')) or
            (target['type'] == 'job_role' and target['value'] == user_data.get('job_role')) or
            (target['type'] == 'employee' and target['value'] == user_data['employee_id'])):
            visible_notices[notice_id] = notice

    return render_template('notices.html', notices=visible_notices)

@app.route('/employee_directory')
def employee_directory():
    if 'username' not in session:
        return redirect(url_for('home'))

    db = get_db()

    # Get all employees with complete information
    employees = []
    departments = set()
    job_roles = set()

    for username, user in db['users'].items():
        if user['role'] == 'employee':
            employee_data = user.copy()
            employee_data['email'] = username
            employee_data['phone'] = user.get('mobile', 'Not provided')
            employee_data['department'] = user.get('department', 'General')
            employee_data['job_role'] = user.get('job_role', 'Employee')
            employee_data['join_date'] = user.get('join_date', 'Not available')
            employee_data['avatar'] = None

            if employee_data['department']:
                departments.add(employee_data['department'])
            if employee_data['job_role']:
                job_roles.add(employee_data['job_role'])

            employees.append(employee_data)

    return render_template('employee_directory.html', 
                         employees=employees,
                         departments=sorted(list(departments)),
                         job_roles=sorted(list(job_roles)))

@app.route('/api/employee/<employee_id>')
def get_employee(employee_id):
    if 'username' not in session or session['role'] != 'admin':
        returnjsonify({'success': False, 'message': 'Unauthorized'}), 401

    db = get_db()
    for username, user in db['users'].items():
        if user.get('employee_id') == employee_id:
            user_data = user.copy()
            user_data['email'] = username
            return jsonify(user_data)

    return jsonify({'success': False, 'message': 'Employee not found'}), 404

@app.route('/api/update_employee', methods=['POST'])
def update_employee():
    if 'username' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.json
    employee_id = data.get('employee_id')

    db = get_db()
    for username, user in db['users'].items():
        if user.get('employee_id') == employee_id:
            # Update user data
            db['users'][username].update({
                'name': data.get('name'),
                'department': data.get('department'),
                'job_role': data.get('job_role'),
                'mobile': data.get('mobile')
            })

            # If email changed, need to update the key in the users dictionary
            new_email = data.get('email')
            if new_email != username:
                user_data = db['users'].pop(username)
                db['users'][new_email] = user_data

            save_db(db)
            return jsonify({'success': True, 'message': 'Profile updated successfully'})

    return jsonify({'success': False, 'message': 'Employee not found'}), 404

@app.route('/profile/<employee_id>')
def view_employee_profile(employee_id):
    if 'username' not in session:
        return redirect(url_for('home'))

    db = get_db()
    for username, user in db['users'].items():
        if user.get('employee_id') == employee_id:
            return render_template('profile.html', user=user)

    return redirect(url_for('employee_directory'))

@app.route('/admin/employee_locations', methods=['GET', 'POST'])
def admin_employee_locations():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))

    db = get_db()

    # Get all employees
    employees = {}
    for username, user in db['users'].items():
        if user['role'] == 'employee':
            employees[username] = user

    if request.method == 'POST':
        username = request.form.get('username')
        location_id = request.form.get('location_id')
        custom_lat = request.form.get('custom_latitude')
        custom_lng = request.form.get('custom_longitude')

        if username in db['users']:
            if location_id == 'custom' and custom_lat and custom_lng:
                # Set custom location
                db['users'][username]['latitude'] = float(custom_lat)
                db['users'][username]['longitude'] = float(custom_lng)
                db['users'][username]['location_name'] = 'Custom Location'
            elif location_id in db['locations']:
                # Set to predefined location
                db['users'][username]['latitude'] = db['locations'][location_id]['latitude']
                db['users'][username]['longitude'] = db['locations'][location_id]['longitude']
                db['users'][username]['location_name'] = db['locations'][location_id]['name']

            save_db(db)
            return redirect(url_for('admin_employee_locations', success='Employee location updated'))

    # Get success message if any
    success = request.args.get('success')

    return render_template('admin_employee_locations.html', 
                          employees=employees, 
                          locations=db['locations'],
                          success=success)

if __name__ == '__main__':
    initialize_db()
    app.run(host='0.0.0.0', port=5000)