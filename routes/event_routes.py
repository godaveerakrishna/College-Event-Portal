from flask import render_template, Blueprint
from flask_mysqldb import MySQLdb
from datetime import datetime, timedelta, date

event_bp = Blueprint('event', __name__)

@event_bp.route('/')
def events():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get published events with fixed dates
    cursor.execute('''
        SELECT e.*, 
            COUNT(er.id) as registered_count,
            e.date as event_date,
            e.time as event_time
        FROM events e 
        LEFT JOIN event_registrations er ON e.id = er.event_id 
        WHERE e.status = 'published' 
        GROUP BY e.id 
        ORDER BY e.date ASC, e.time ASC
    ''')
    events = cursor.fetchall()
    
    # Process dates and times
    for event in events:
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
    return render_template('events/list.html', events=events) 