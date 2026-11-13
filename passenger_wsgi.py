import sys
import os

# Menambahkan direktori aplikasi ke sys.path
sys.path.insert(0, os.path.dirname(__file__))

from server import app

# cPanel Phusion Passenger menggunakan antarmuka WSGI standard (variable: application)
# Menggunakan ASGIMiddleware dari a2wsgi untuk konversi FastAPI (ASGI) ke WSGI Passenger cPanel
try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(app)
except ImportError:
    # Fallback jika a2wsgi belum terinstal
    import asyncio
    
    def application(environ, start_response):
        status = '500 Internal Server Error'
        output = b'Harap install module a2wsgi di cPanel: pip install a2wsgi'
        response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(output)))]
        start_response(status, response_headers)
        return [output]
