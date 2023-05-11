import http.server
import http.cookies
import socketserver
import os
import cgi
import hashlib
import time
import json
PORT = 8000
UPLOAD_DIR = 'upload/'  # filefolder
USERS_FILE = 'users.json'  # users folder


class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
                <html>
                    <head>
                        <title>X-Disk</title>
                    </head>
                    <body>
                        <h1>Login form</h1>
                        <form method="post" action="/login">
                            <label for="username">Username:</label>
                            <input type="text" id="username" name="username" required><br>
                            <label for="password">Password:</label>
                            <input type="password" id="password" name="password" required><br>
                            <input type="submit" value="Enter">
                        </form>
                        <br>
                        <a href="/register">Registration form</a>
                    </body>
                </html>''')
        elif path == '/register':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
                <html>
                    <head>
                        <title>X-Disk</title>
                    </head>
                    <body>
                        <h1>Registration</h1>
                        <form method="post" action="/register">
                            <label for="username">Username:</label>
                            <input type="text" id="username" name="username" required><br>
                            <label for="password">Pas:</label>
                            <input type="password" id="password" name="password" required><br>
                            <label for="password_confirm">Confirm password:</label>
                            <input type="password" id="password_confirm" name="password_confirm" required><br>
                            <input type="submit" value="Registrate">
                        </form>
                        <br>
                        <a href="/">Enter</a>
                    </body>
                </html>
            ''')
        elif path == '/files':
            if not self.authorized():
                self.redirect('/')
                return
            files = os.listdir(UPLOAD_DIR)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
                <html>
                    <head>
                        <title>X-Disk</title>
                    </head>
                    <body>
                        <h1>List files:</h1>
                        <ul>
            ''')
            for file in files:
                self.wfile.write(b'<li><a href="/download?filename=' + bytes(file, 'utf-8') + b'">' + bytes(
                    file, 'utf-8') + b'</a> <a href="/delete?filename=' + bytes(file, 'utf-8') + b'">(delete)</a></li>')
            self.wfile.write(b'''
                        </ul>
                        <form method="post" enctype="multipart/form-data" action="/upload">
                            <label for="file">Choose file:</label>
                            <input type="file" id="file" name="file" required>
                            <br>
                            <input type="submit" value="Upload">
                        </form>
                        <br>
                        <a href="/">logout</a>
                    </body>
                </html>
            ''')
        elif path.startswith('/download'):
            if not self.authorized():
                self.redirect('/')
                return
            filename = self.get_filename(path)
            try:
                if not os.path.exists('uploads'):
                    os.mkdir('uploads')
                with open('uploads/' + filename, 'wb') as file:
                    self.send_response(200)
                    self.send_header(
                        'Content-type', 'application/octet-stream')
                    self.send_header('Content-disposition',
                                     'attachment; filename="' + filename + '"')
                    self.end_headers()
                    self.wfile.write(file.read())
            except FileNotFoundError:
                self.send_error(404, 'Р¤Р°Р№Р» РЅРµ РЅР°Р№РґРµРЅ')
        elif path.startswith('/delete'):
            if not self.authorized():
                self.redirect('/')
                return
            filename = self.get_filename(path)
            try:
                os.remove(UPLOAD_DIR + filename)
                self.send_response(302)
                self.send_header('Location', '/files')
                self.end_headers()
            except FileNotFoundError:
                self.send_error(404, 'Р¤Р°Р№Р» РЅРµ РЅР°Р№РґРµРЅ')
        else:
            self.send_error(404, 'РЎС‚СЂР°РЅРёС†Р° РЅРµ РЅР°Р№РґРµРЅР°')

    def do_POST(self):
        path = self.path
        if path == '/login':
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={
                                    'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
            username = form.getvalue('username')
            password = form.getvalue('password')
            if self.check_user(username, password):
                session_id = self.create_session()
                self.send_response(302)
                self.send_header('Set-Cookie', 'session_id=' + session_id)
                self.send_header('Location', '/files')
                self.end_headers()
            else:
                self.send_error(
                    401, 'РќРµРїСЂР°РІРёР»СЊРЅРѕРµ РёРјСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РёР»Рё РїР°СЂРѕР»СЊ')
        elif path == '/register':
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={
                                    'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
            username = form.getvalue('username')
            password = form.getvalue('password')
            password_confirm = form.getvalue('password_confirm')
            if password != password_confirm:
                self.send_error(
                    400, 'РќРµРїСЂР°РІРёР»СЊРЅРѕРµ РёРјСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РёР»Рё РїР°СЂРѕР»СЊ')
            else:
                if self.user_exists(username):
                    self.send_error(
                        400, 'РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ СЃ С‚Р°РєРёРј РёРјРµРЅРµРј СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚')
                else:
                    self.create_user(username, password)
                    self.send_response(302)
                    self.send_header('Location', '/')
                    self.end_headers()
        elif path == '/upload':
            if not self.authorized():
                self.redirect('/')
                return
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={
                                    'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
            fileitem = form['file']
            if fileitem.filename:
                filename = self.create_unique_filename(fileitem.filename)
                with open(UPLOAD_DIR + filename, 'wb') as file:
                    file.write(fileitem.file.read())
                self.send_response(302)
                self.send_header('Location', '/files')
                self.end_headers()
            else:
                self.send_error(400, 'Р¤Р°Р№Р» РЅРµ Р±С‹Р» Р·Р°РіСЂСѓР¶РµРЅ')

    def authorized(self):
        cookies = {}
        if 'Cookie' in self.headers:
            cookies = http.cookies.SimpleCookie(self.headers.get('Cookie', ''))
        if 'session_id' in cookies:
            session_id = cookies['session_id'].value
            if session_id in sessions:
                return True
        return False

    def create_session(self):
        session_id = hashlib.sha256(
            str(time.time()).encode('utf-8')).hexdigest()
        sessions[session_id] = True
        return session_id

    def check_user(self, username, password):
        with open(USERS_FILE, 'r') as file:
            users = json.load(file)
        if username in users and users[username] == hashlib.sha256(password.encode('utf-8')).hexdigest():
            return True
        else:
            return False

    def user_exists(self, username):
        with open(USERS_FILE, 'r') as file:
            users = json.load(file)
        if username in users:
            return True
        else:
            return False

    def create_user(self, username, password):
        with open(USERS_FILE, 'r') as file:
            users = json.load(file)
        users[username] = hashlib.sha256(password.encode('utf-8')).hexdigest()
        with open(USERS_FILE, 'w') as file:
            json.dump(users, file)

    def create_unique_filename(self, filename):
        extension = os.path.splitext(filename)[1]
        while True:
            filename = hashlib.sha256(str(time.time()).encode(
                'utf-8')).hexdigest() + extension
            if not os.path.exists(UPLOAD_DIR + filename):
                return filename

    def get_filename(self, path):
        query = path.split('?')[1]
        filename = query.split('=')[1]
        return filename
sessions = {}
with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
