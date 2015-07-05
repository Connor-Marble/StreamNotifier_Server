import logging

from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy

import threading

from models import *
from dispatcher import Dispatcher

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://connor:postgresytrewq@localhost/Stream_Notifier"

dispatcher = Dispatcher(SQLAlchemy(app), app)

@app.route('/', methods=['POST'])
def recieve_update():
    dispatcher.post_data_queue.put(request.data.decode('utf-8'))
    
    return ''


if __name__=='__main__':
    
    dispatch_thread = threading.Thread(target=dispatcher.run, args=[])
    dispatch_thread.start()
    app.run(host='0.0.0.0')    
    
