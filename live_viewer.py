"""
Live Viewer for SVG rendering.

Runs a simple, local HTTP server in a background thread to serve an
HTML page that auto-refreshes, displaying an SVG file as it's updated.
"""

import os
import http.server
import socketserver
import threading
import webbrowser
from functools import partial


class LiveViewer:
    """Manages a background web server for live SVG viewing."""

    def __init__(self, port: int, directory: str, svg_filename: str):
        self.port = port
        self.directory = directory
        self.svg_filename = svg_filename
        self.server_thread: Optional[threading.Thread] = None
        self.httpd: Optional[socketserver.TCPServer] = None

    def start(self) -> None:
        """
        Start the server in a background thread and open the browser.
        Creates an index.html file to display the SVG.
        """
        os.makedirs(self.directory, exist_ok=True)

        # Create an index.html that auto-refreshes
        html_path = os.path.join(self.directory, "index.html")
        with open(html_path, "w") as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Live Drawing</title>
                <meta http-equiv="refresh" content="1">
            </head>
            <body style="margin: 0; background-color: #f0f0f0; display: flex; justify-content: center; align-items: center; height: 100vh;">
                <img src="{self.svg_filename}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
            </body>
            </html>
            """)

        # Create a request handler that serves files from the specified directory
        handler_with_dir = partial(http.server.SimpleHTTPRequestHandler, directory=self.directory)
        
        # Allow the port to be reused quickly
        socketserver.TCPServer.allow_reuse_address = True
        self.httpd = socketserver.TCPServer(("", self.port), handler_with_dir)

        # Start the server in a daemon thread
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

        url = f"http://localhost:{self.port}"
        print(f"  [Viewer] Live preview running at: {url}")
        webbrowser.open_new_tab(url)

    def stop(self) -> None:
        """Stop the HTTP server."""
        if self.httpd:
            print("  [Viewer] Shutting down server...")
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
            self.server_thread = None

