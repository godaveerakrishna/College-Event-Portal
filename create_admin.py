from flask import Flask
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash
import MySQLdb.cursors
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
mysql = MySQL(app)

def create_admin_user():
    # Admin credentials
    admin_username = 'admin'
    admin_password = 'admin123'
    admin_email = 'admin@example.com'
    
    # Generate password hash
    password_hash = generate_password_hash(admin_password)
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if admin already exists
        cursor.execute('SELECT * FROM users WHERE username = %s', (admin_username,))
        admin = cursor.fetchone()
        
        if admin:
            # Update existing admin
            cursor.execute('''
                UPDATE users 
                SET password_hash = %s, email = %s, role = 'admin'
                WHERE username = %s
            ''', (password_hash, admin_email, admin_username))
            print("Admin user updated successfully!")
        else:
            # Create new admin
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (%s, %s, %s, 'admin')
            ''', (admin_username, admin_email, password_hash))
            print("Admin user created successfully!")
        
        mysql.connection.commit()
        cursor.close()
        
    except Exception as e:
        print(f"Error creating admin user: {e}")

if __name__ == '__main__':
    with app.app_context():
        create_admin_user() 