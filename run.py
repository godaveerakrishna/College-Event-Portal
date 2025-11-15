from app import create_app
import socket

def get_local_ip():
    try:
        # Get the local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    app = create_app()
    local_ip = get_local_ip()
    print(f"\nYour application is accessible at:")
    print(f"Local:            http://127.0.0.1:5000")
    print(f"On Your Network:  http://{local_ip}:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=True) 