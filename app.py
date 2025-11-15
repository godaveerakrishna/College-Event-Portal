from flask import Flask, render_template
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin
from config import Config
import MySQLdb.cursors

# Initialize extensions
mysql = MySQL()
login_manager = LoginManager()

# User class definition
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.role = user_data['role']

    def get_id(self):
        return str(self.id)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Flask extensions
    mysql.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Optional: If you don't want redirection on unauthorized views
    login_manager.login_view_unauthorized_handler = lambda: None

    # User loader function
    @login_manager.user_loader
    def load_user(user_id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        
        if user_data:
            return User(user_data)
        return None

    # Import and register blueprints
    from routes.auth_routes import auth_bp
    from routes.main_routes import main_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return """
        <h1>404 - Page Not Found</h1>
        <p>The requested page could not be found.</p>
        <a href="/">Return to Home</a>
        """, 404

    @app.errorhandler(500)
    def internal_error(error):
        mysql.connection.rollback()
        return """
        <h1>500 - Internal Server Error</h1>
        <p>An unexpected error has occurred.</p>
        <a href="/">Return to Home</a>
        """, 500

    return app

if __name__ == '__main__':
    app = create_app()
    
    # ✅ IMPORTANT: host='0.0.0.0' allows access from other devices
    # ✅ You can change the port if needed, e.g., 8080 or 8000
    app.run(host='0.0.0.0', port=5000, debug=True)
