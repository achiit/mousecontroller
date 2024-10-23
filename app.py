# server.py
from flask import Flask, jsonify, request
import pyautogui
import qrcode
import socket
import netifaces
import base64
from io import BytesIO
from flask_cors import CORS
import logging
import threading

app = Flask(__name__)
CORS(app)
pyautogui.FAILSAFE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

active_connections = set()

def get_local_ip():
    try:
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    if (ip.startswith('192.168.') or 
                        ip.startswith('10.') or 
                        ip.startswith('172.')):
                        return ip
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
        finally:
            s.close()
    except Exception as e:
        logger.error(f"Error getting IP: {e}")
        return None

def generate_qr():
    server_ip = get_local_ip()
    if not server_ip:
        return None, "Could not determine server IP"
    
    server_url = f"http://{server_ip}:8000"
    logger.info(f"Generated server URL: {server_url}")
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(server_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str, server_url

@app.route('/')
def home():
    qr_code, server_url = generate_qr()
    if not qr_code:
        return "Error: Could not determine server IP", 500
    
    return f'''
    <html>
        <head>
            <style>
                body {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    flex-direction: column;
                    font-family: Arial, sans-serif;
                    background-color: #f0f0f0;
                }}
                .container {{
                    text-align: center;
                    padding: 20px;
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                .url {{
                    margin: 20px 0;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    font-family: monospace;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Mouse Controller Server</h1>
                <p>Scan this QR code with the mobile app</p>
                <img src="data:image/png;base64,{qr_code}"/>
                <div class="url">
                    Server URL: {server_url}
                </div>
                <p>Make sure your phone is connected to the same WiFi network as this computer</p>
            </div>
        </body>
    </html>
    '''

@app.route('/connect', methods=['POST'])
def connect():
    client_id = request.remote_addr
    active_connections.add(client_id)
    logger.info(f"New client connected: {client_id}")
    return jsonify({"status": "connected", "message": "Successfully connected to server"})

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "active"})

@app.route('/mouse/move', methods=['POST'])
def move_mouse():
    try:
        client_id = request.remote_addr
        if client_id not in active_connections:
            logger.warning(f"Unauthorized client attempt: {client_id}")
            return jsonify({"status": "error", "message": "Not connected"}), 401

        data = request.json
        dx = data.get('dx', 0)
        dy = data.get('dy', 0)
        
        current_x, current_y = pyautogui.position()
        pyautogui.moveTo(current_x + dx, current_y + dy)
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error in move_mouse: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/mouse/click', methods=['POST'])
def mouse_click():
    try:
        client_id = request.remote_addr
        if client_id not in active_connections:
            return jsonify({"status": "error", "message": "Not connected"}), 401

        data = request.json
        button = data.get('button', 'left')
        
        pyautogui.click(button=button)
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error in mouse_click: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/mouse/scroll', methods=['POST'])
def scroll_mouse():
    try:
        client_id = request.remote_addr
        if client_id not in active_connections:
            return jsonify({"status": "error", "message": "Not connected"}), 401

        data = request.json
        dx = data.get('dx', 0)
        dy = data.get('dy', 0)
        
        scroll_factor = 0.5
        pyautogui.scroll(int(-dy * scroll_factor))
        pyautogui.hscroll(int(dx * scroll_factor))
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error in scroll_mouse: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def check_server_accessibility():
    local_ip = get_local_ip()
    if not local_ip:
        logger.error("Could not determine local IP address")
        return
    
    logger.info(f"""
    =====================================
    Mouse Controller Server is running!
    =====================================
    
    Server IP: {local_ip}
    Server URL: http://{local_ip}:8000
    
    To connect your mobile device:
    1. Make sure your phone is connected to the same WiFi network as this computer
    2. Open a browser on your phone and visit: http://{local_ip}:8000
    3. Or scan the QR code shown in your computer's browser
    
    To test the connection:
    - Visit http://{local_ip}:8000/test-connection
    
    Press Ctrl+C to stop the server
    =====================================
    """)

if __name__ == '__main__':
    threading.Thread(target=check_server_accessibility, daemon=True).start()
    try:
        app.run(host='0.0.0.0', port=8000, debug=False)
    except Exception as e:
        logger.error(f"Server error: {e}")