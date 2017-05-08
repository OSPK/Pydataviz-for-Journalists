from gevent.wsgi import WSGIServer
from app.init_app import app, init_app, manager

if __name__ == "__main__":
    init_app(app)
    app.run(host='0.0.0.0', port=8080)