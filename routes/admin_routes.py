from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from app import mysql
import MySQLdb.cursors
from datetime import datetime, timedelta, date

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You need to be an admin to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get event statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_events,
            COUNT(CASE WHEN date >= CURDATE() THEN 1 END) as upcoming_events,
            COUNT(CASE WHEN date < CURDATE() THEN 1 END) as past_events
        FROM events
        WHERE status = 'published'
    ''')
    event_stats = cursor.fetchone()
    
    # Get pending event requests count
    cursor.execute('SELECT COUNT(*) as pending_requests FROM event_requests WHERE status = "pending"')
    request_stats = cursor.fetchone()
    
    # Get upcoming events with fixed dates
    cursor.execute('''
        SELECT e.*, 
            COUNT(er.id) as registered_count,
            e.date as event_date,
            e.time as event_time
        FROM events e 
        LEFT JOIN event_registrations er ON e.id = er.event_id 
        WHERE e.status = 'published' 
        AND e.date >= CURDATE()
        GROUP BY e.id 
        ORDER BY e.date ASC, e.time ASC
        LIMIT 10
    ''')
    upcoming_events = cursor.fetchall()
    
    # Process dates and times
    for event in upcoming_events:
        try:
            # Handle date
            if isinstance(event['event_date'], str):
                event['date'] = datetime.strptime(event['event_date'], '%Y-%m-%d')
            else:
                event['date'] = event['event_date']
            
            # Handle time
            if isinstance(event['event_time'], timedelta):
                # Convert timedelta to time
                total_seconds = int(event['event_time'].total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                event['time'] = datetime.now().replace(hour=hours, minute=minutes, second=0, microsecond=0)
            elif isinstance(event['event_time'], str):
                event['time'] = datetime.strptime(event['event_time'], '%H:%M:%S')
            else:
                # If it's already a time object, convert to datetime for strftime
                event['time'] = datetime.combine(date.today(), event['event_time'])
        except (ValueError, TypeError) as e:
            print(f"Date/Time conversion error: {str(e)}")
            # Set default values if conversion fails
            event['date'] = datetime.now()
            event['time'] = datetime.now()
    
    cursor.close()
    return render_template('admin/dashboard.html', 
                         event_stats=event_stats, 
                         request_stats=request_stats,
                         upcoming_events=upcoming_events)

@admin_bp.route('/events')
@login_required
@admin_required
def manage_events():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT e.*, COUNT(er.id) as registered_count 
        FROM events e 
        LEFT JOIN event_registrations er ON e.id = er.event_id 
        GROUP BY e.id 
        ORDER BY e.date DESC
    ''')
    events = cursor.fetchall()
    cursor.close()
    return render_template('admin/events.html', events=events)

@admin_bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_event(event_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        date = request.form.get('date')
        time = request.form.get('time')
        location = request.form.get('location')
        capacity = request.form.get('capacity')
        status = request.form.get('status')
        
        cursor.execute('''
            UPDATE events 
            SET title = %s, description = %s, date = %s, time = %s, 
                location = %s, capacity = %s, status = %s
            WHERE id = %s
        ''', (title, description, date, time, location, capacity, status, event_id))
        mysql.connection.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin.manage_events'))
    
    cursor.execute('SELECT * FROM events WHERE id = %s', (event_id,))
    event = cursor.fetchone()
    cursor.close()
    
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('admin.manage_events'))
    
    return render_template('admin/edit_event.html', event=event)

@admin_bp.route('/events/<int:event_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_event(event_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    try:
        # First check if the event exists
        cursor.execute('SELECT * FROM events WHERE id = %s', (event_id,))
        event = cursor.fetchone()
        
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # First delete related registrations
        cursor.execute('DELETE FROM event_registrations WHERE event_id = %s', (event_id,))
        print(f"Deleted {cursor.rowcount} registrations for event {event_id}")
        
        # Then delete the event
        cursor.execute('DELETE FROM events WHERE id = %s', (event_id,))
        print(f"Deleted event {event_id}")
        
        if cursor.rowcount > 0:
            mysql.connection.commit()
            flash('Event has been deleted successfully.', 'success')
        else:
            mysql.connection.rollback()
            flash('Error: Event could not be deleted.', 'error')
            
    except Exception as e:
        print(f"Error deleting event {event_id}: {str(e)}")
        mysql.connection.rollback()
        flash('Error deleting event. Please try again.', 'error')
    finally:
        cursor.close()
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/requests')
@login_required
@admin_required
def event_requests():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT er.*, u.username as requester_name,
        DATE_FORMAT(er.proposed_date, '%%Y-%%m-%%d') as formatted_date,
        DATE_FORMAT(er.proposed_time, '%%H:%%i:%%s') as formatted_time,
        DATE_FORMAT(er.created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as formatted_created_at
        FROM event_requests er 
        JOIN users u ON er.requested_by = u.id 
        ORDER BY er.created_at DESC
    ''')
    requests = cursor.fetchall()
    
    # Convert string dates to datetime objects
    for request in requests:
        try:
            request['proposed_date'] = datetime.strptime(request['formatted_date'], '%Y-%m-%d')
            request['proposed_time'] = datetime.strptime(request['formatted_time'], '%H:%M:%S')
            request['created_at'] = datetime.strptime(request['formatted_created_at'], '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            request['proposed_date'] = datetime.now()
            request['proposed_time'] = datetime.now()
            request['created_at'] = datetime.now()
            
    cursor.close()
    return render_template('admin/requests.html', requests=requests)

@admin_bp.route('/requests/<int:request_id>/review', methods=['POST'])
@login_required
@admin_required
def review_request(request_id):
    action = request.form.get('action')
    remarks = request.form.get('remarks', '')
    
    if action not in ['approve', 'reject']:
        flash('Invalid action', 'error')
        return redirect(url_for('admin.event_requests'))
    
    status = 'approved' if action == 'approve' else 'rejected'
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Update request status
    cursor.execute('''
        UPDATE event_requests 
        SET status = %s, admin_remarks = %s 
        WHERE id = %s
    ''', (status, remarks, request_id))
    
    # If approved, create the event
    if action == 'approve':
        cursor.execute('''
            SELECT * FROM event_requests WHERE id = %s
        ''', (request_id,))
        event_request = cursor.fetchone()
        
        if event_request:
            cursor.execute('''
                INSERT INTO events 
                (title, description, date, time, location, capacity, created_by, status, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'published', %s)
            ''', (
                event_request['title'],
                event_request['description'],
                event_request['proposed_date'],
                event_request['proposed_time'],
                event_request['location'],
                event_request['capacity'],
                event_request['requested_by'],
                event_request['image_url']
            ))
    
    mysql.connection.commit()
    cursor.close()
    
    flash(f'Request has been {status}', 'success')
    return redirect(url_for('admin.event_requests'))

@admin_bp.route('/events/<int:event_id>/registrations')
@login_required
@admin_required
def event_registrations(event_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get event details
    cursor.execute('SELECT * FROM events WHERE id = %s', (event_id,))
    event = cursor.fetchone()
    
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('admin.manage_events'))
    
    # Get registrations
    cursor.execute('''
        SELECT er.*, u.username, u.email 
        FROM event_registrations er 
        JOIN users u ON er.user_id = u.id 
        WHERE er.event_id = %s 
        ORDER BY er.registration_date DESC
    ''', (event_id,))
    registrations = cursor.fetchall()
    
    cursor.close()
    return render_template('admin/registrations.html', 
                         event=event, 
                         registrations=registrations) 