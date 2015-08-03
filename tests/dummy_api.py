import logging

from flask import Flask, request
from flask.json import jsonify

import threading

app = Flask(__name__)

@app.route('/api', methods=['GET'])
def request_status():
    channels = request.args.get('channel').split(',')
    streams = []
    for channel in channels:
        streams.append({"channel":{"name":channel}})

    return jsonify(streams=streams)


if __name__=='__main__':

    app.run(host='0.0.0.0')
