#channels checked per twitch call
REQUEST_LENGTH = 20

#Seconds to wait between twitch requests
REQUEST_DELAY=0

#Minimum time in seconds it takes the server to update
#databse with new client requests and twitch status
CYCLE_TIME=60

#GCM API Key
API_KEY='xxxxxxxxxxxxxxxxxxxxxxxx_xxxxxxxx_xxxxxx'

#Time in seconds between database cleans
CLEAN_PERIOD=600

#Base for querying channel status from twitch api
API_CALL='https://api.twitch.tv/kraken/streams?channel='

#Base for querying channel from test server designed to mimick twitch api
TESTING_CALL='http://0.0.0.0:5000/api?channel='

#will get information from test server when true
TESTING  =False
