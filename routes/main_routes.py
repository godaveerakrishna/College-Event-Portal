from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import mysql
import MySQLdb.cursors
from datetime import datetime
import os
from werkzeug.utils import secure_filename

main_bp = Blueprint('main', __name__)

# Add these configurations at the top of the file
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/')
def index():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT e.*, COUNT(er.id) as registered_count,
        DATE_FORMAT(e.date, '%%Y-%%m-%%d') as formatted_date,
        DATE_FORMAT(e.time, '%%H:%%i:%%s') as formatted_time
        FROM events e 
        LEFT JOIN event_registrations er ON e.id = er.event_id 
        WHERE e.status = 'published' AND e.date >= CURDATE()
        GROUP BY e.id 
        ORDER BY e.date ASC
    ''')
    events = cursor.fetchall()
    
    # Convert string dates and times to datetime objects
    for event in events:
        try:
            event['date'] = datetime.strptime(event['formatted_date'], '%Y-%m-%d')
            event['time'] = datetime.strptime(event['formatted_time'], '%H:%M:%S')
        except (ValueError, TypeError):
            # Handle any conversion errors
            event['date'] = datetime.now()
            event['time'] = datetime.now()
            
    cursor.close()
    return render_template('main/index.html', events=events)

@main_bp.route('/event/<int:event_id>')
def event_details(event_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT e.*, COUNT(er.id) as registered_count,
        DATE_FORMAT(e.date, '%%Y-%%m-%%d') as formatted_date,
        DATE_FORMAT(e.time, '%%H:%%i:%%s') as formatted_time
        FROM events e 
        LEFT JOIN event_registrations er ON e.id = er.event_id 
        WHERE e.id = %s
        GROUP BY e.id
    ''', (event_id,))
    event = cursor.fetchone()
    
    if event:
        # Convert string dates to datetime objects
        try:
            event['date'] = datetime.strptime(event['formatted_date'], '%Y-%m-%d')
            event['time'] = datetime.strptime(event['formatted_time'], '%H:%M:%S')
        except (ValueError, TypeError):
            event['date'] = datetime.now()
            event['time'] = datetime.now()
    
    is_registered = False
    if current_user.is_authenticated:
        cursor.execute('''
            SELECT * FROM event_registrations 
            WHERE event_id = %s AND user_id = %s
        ''', (event_id, current_user.id))
        is_registered = cursor.fetchone() is not None
    
    cursor.close()
    return render_template('main/event_details.html', event=event, is_registered=is_registered)

@main_bp.route('/event/<int:event_id>/register', methods=['POST'])
@login_required
def register_event(event_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Check if event exists and has capacity
    cursor.execute('''
        SELECT e.*, COUNT(er.id) as registered_count 
        FROM events e 
        LEFT JOIN event_registrations er ON e.id = er.event_id 
        WHERE e.id = %s
        GROUP BY e.id
    ''', (event_id,))
    event = cursor.fetchone()
    
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('main.index'))
    
    if event['registered_count'] >= event['capacity']:
        flash('Event is full', 'error')
        return redirect(url_for('main.event_details', event_id=event_id))
    
    try:
        cursor.execute('''
            INSERT INTO event_registrations (event_id, user_id)
            VALUES (%s, %s)
        ''', (event_id, current_user.id))
        mysql.connection.commit()
        flash('Successfully registered for the event!', 'success')
    except MySQLdb.IntegrityError:
        flash('You are already registered for this event', 'error')
    
    cursor.close()
    return redirect(url_for('main.event_details', event_id=event_id))

@main_bp.route('/request-event', methods=['GET', 'POST'])
@login_required
def request_event():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        date = request.form.get('date')
        time = request.form.get('time')
        location = request.form.get('location')
        capacity = request.form.get('capacity')
        
        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                # Create unique filename
                filename = secure_filename(image.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_filename = f"{timestamp}_{filename}"
                image.save(os.path.join(UPLOAD_FOLDER, image_filename))
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            INSERT INTO event_requests 
            (title, description, proposed_date, proposed_time, location, capacity, requested_by, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (title, description, date, time, location, capacity, current_user.id, image_filename))
        mysql.connection.commit()
        cursor.close()
        
        flash('Event request submitted successfully!', 'success')
        return redirect(url_for('main.my_requests'))
    
    return render_template('main/request_event.html')

@main_bp.route('/my-requests')
@login_required
def my_requests():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT *, 
        DATE_FORMAT(proposed_date, '%%Y-%%m-%%d') as formatted_date,
        DATE_FORMAT(proposed_time, '%%H:%%i:%%s') as formatted_time,
        DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as formatted_created_at
        FROM event_requests 
        WHERE requested_by = %s 
        ORDER BY created_at DESC
    ''', (current_user.id,))
    requests = cursor.fetchall()
    
    # Convert string dates to datetime objects
    for request in requests:
        try:
            request['proposed_date'] = datetime.strptime(request['formatted_date'], '%Y-%m-%d')
            request['proposed_time'] = datetime.strptime(request['formatted_time'], '%H:%M:%S')
            request['created_at'] = datetime.strptime(request['formatted_created_at'], '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            # Handle any conversion errors
            request['proposed_date'] = datetime.now()
            request['proposed_time'] = datetime.now()
            request['created_at'] = datetime.now()
            
    cursor.close()
    return render_template('main/my_requests.html', requests=requests)

@main_bp.route('/my-registrations')
@login_required
def my_registrations():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT e.*, er.registration_date,
        DATE_FORMAT(e.date, '%%Y-%%m-%%d') as formatted_date,
        DATE_FORMAT(e.time, '%%H:%%i:%%s') as formatted_time,
        DATE_FORMAT(er.registration_date, '%%Y-%%m-%%d %%H:%%i:%%s') as formatted_registration_date
        FROM events e 
        JOIN event_registrations er ON e.id = er.event_id 
        WHERE er.user_id = %s 
        ORDER BY e.date ASC
    ''', (current_user.id,))
    registrations = cursor.fetchall()
    
    # Convert string dates to datetime objects
    for registration in registrations:
        try:
            registration['date'] = datetime.strptime(registration['formatted_date'], '%Y-%m-%d')
            registration['time'] = datetime.strptime(registration['formatted_time'], '%H:%M:%S')
            registration['registration_date'] = datetime.strptime(registration['formatted_registration_date'], '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            registration['date'] = datetime.now()
            registration['time'] = datetime.now()
            registration['registration_date'] = datetime.now()
    
    cursor.close()
    return render_template('main/my_registrations.html', registrations=registrations)

@main_bp.route('/event/<int:event_id>/cancel', methods=['POST'])
@login_required
def cancel_registration(event_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Check if user is registered
        cursor.execute('''
            SELECT * FROM event_registrations 
            WHERE event_id = %s AND user_id = %s
        ''', (event_id, current_user.id))
        
        if cursor.fetchone():
            # Delete registration
            cursor.execute('''
                DELETE FROM event_registrations 
                WHERE event_id = %s AND user_id = %s
            ''', (event_id, current_user.id))
            mysql.connection.commit()
            flash('Your registration has been cancelled successfully.', 'success')
        else:
            flash('You are not registered for this event.', 'error')
            
    except Exception as e:
        mysql.connection.rollback()
        flash('An error occurred while cancelling your registration.', 'error')
    finally:
        cursor.close()
    
    return redirect(url_for('main.my_registrations')) 