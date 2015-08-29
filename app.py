import logging

from flask import Flask, request
from flask.json import jsonify

import threading

from models import *
from dispatcher import Dispatcher
import config

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S",
                    filename='SN.log')

app = Flask(__name__)
dispatcher = Dispatcher(app)
dispatch_thread = threading.Thread(target=dispatcher.run, args=[])
dispatch_thread.start()

@app.route('/', methods=['POST'])
def recieve_update():
    dispatcher.post_data_queue.put(request.data.decode('utf-8'))
    
    return ''


@app.route('/api', methods=['GET'])
def request_status():

    if not config.TESTING:
        return ''
    
    channels = request.args.get('channel').split(',')
    streams = []
    with open("./tests/online_dummy_streams") as file:
        online = file.readlines()
        for channel in channels:
            if channel in online:
                streams.append({"channel":{"name":channel}})

    return jsonify(streams=streams)


    
