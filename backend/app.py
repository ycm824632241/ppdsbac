from flask import Flask
from flask_cors import CORS
from api import register_blueprints

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
register_blueprints(app)

if __name__ == "__main__":
    print("=" * 55)
    print("  PPDSBAC Demo Server  —  http://localhost:5000")
    print("  IEEE TDSC 2025 · Han, Chen, Susilo")
    print("=" * 55)
    # host="0.0.0.0" 同时监听 IPv4(127.0.0.1) 和 IPv6(::1)
    # 解决 Node 18+ 将 localhost 解析为 ::1 导致的 ECONNREFUSED
    app.run(debug=True, host="0.0.0.0", port=5000)
