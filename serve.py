from gevent.wsgi import WSGIServer
from app.init_app import app, init_app, manager

http_server = WSGIServer(('127.0.0.1', 8080), app)
init_app(app)
http_server.serve_forever()

# if __name__ == "__main__":
#     init_app(app)
#     app.run()