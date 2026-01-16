import http.server
import socketserver
import threading
import os
import time

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress logging to keep CLI clean
        pass

def start_server(port=8080, directory="."):
    os.chdir(directory)
    handler = QuietHandler
    # Allow address reuse to avoid "Address already in use" errors on restart
    socketserver.TCPServer.allow_reuse_address = True
    
    # Try binding to the requested port, or increment until free
    while True:
        try:
            # We must assign to a variable to keep the socket open (in serve_forever)
            # But here we are just starting the server logic.
            # The issue with threading is returning the port *before* serving.
            # So we create the server object first.
            httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
            return httpd, port
        except OSError as e:
            if e.errno == 98: # Address already in use
                port += 1
            else:
                raise e

def run_server_logic(httpd):
    httpd.serve_forever()

def run_server_in_background(port=8080):
    httpd, actual_port = start_server(port)
    thread = threading.Thread(target=run_server_logic, args=(httpd,), daemon=True)
    thread.start()
    return actual_port
