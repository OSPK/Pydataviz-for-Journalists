from gevent.wsgi import WSGIServer
from app.init_app import app

http_server = WSGIServer(('0.0.0.0', 8080), app)
http_server.serve_forever()