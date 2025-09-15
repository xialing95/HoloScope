from flask import Flask
from app import create_app

if __name__ == '__main__':
    # This line runs the application.
    # host='0.0.0.0' tells the server to listen on all available network interf>
    # making it accessible from other computers on the same network.
    # debug=True allows for automatic reloading and provides a debugger.
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=True)
