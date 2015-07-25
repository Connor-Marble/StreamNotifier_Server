import logging

from flask import Flask, request

import threading

from models import *
from dispatcher import Dispatcher

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S",
                    filename='SN.log')


app = Flask(__name__)

dispatcher = Dispatcher(app)

@app.route('/', methods=['POST'])
def recieve_update():
    dispatcher.post_data_queue.put(request.data.decode('utf-8'))
    
    return ''


if __name__=='__main__':
    
    dispatch_thread = threading.Thread(target=dispatcher.run, args=[])
    dispatch_thread.start()
    app.run(host='0.0.0.0')    
    
