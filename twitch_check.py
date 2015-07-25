import logging
import sys

import urllib.request
import json
from time import sleep

import config

def rate_limit_check(channel_names):

    start_index = 0

    twitch_data = {}
    for i in range(config.REQUEST_LENGTH, len(channel_names), config.REQUEST_LENGTH):
        twitch_data.update(check_live(channel_names[start_index:i]))
        start_index = i

        sleep(config.REQUEST_DELAY)

    twitch_data.update(check_live(channel_names[start_index:]))

    sleep(config.REQUEST_DELAY)
    return twitch_data

def check_live(channel_names):
    baseurl = 'https://api.twitch.tv/kraken/streams?channel='
    url = baseurl + ','.join(channel_names)

    try:
        response = urllib.request.urlopen(url)

        response_json = json.loads(response.read().decode('utf-8'))
        streams = response_json['streams']

        result = {name.lower():0 for name in channel_names}
        for stream in streams:
            result[stream['channel']['name'].lower()] = 1

            
        logging.info(result)
        return result

    except:
        logging.error('unexpected error encountered: '+sys.exc_info()[0])



if __name__ == '__main__':
    result = check_live(sys.argv[1:])
    print("Name".ljust(25), "status".ljust(8))
    for key in result:
        print('-'*37)
        print('|',key.ljust(25), (str)(result[key]).ljust(8),'|')
