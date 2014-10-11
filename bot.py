""" agelessmojo bot implementation """

import time, json, requests, os
from bottle import get, post, request, run, response

RELAY_SPEED_URL = \
        'http://carrera-relay.beta.swisscloud.io/relay/ws/rest/relay/speed'
TEAM_ID = 'agelessmojo'
PORT = os.getenv('VCAP_APP_PORT', '5000')
ACCESS_CODE = 'yoyoyo'

@get('/ping')
def ping():
    """ Check for bot health. Returns success in text/plain. """

    response.headers['Content-Type'] = 'text/plain'
    return "success"

@post('/start')
def start():
    """ Signals start of the round. Returns a speedcontrol json object. """

    return {'teamId':TEAM_ID, 'accessCode':ACCESS_CODE, \
            'power':50, 'timestamp': int(round(time.time() * 1000))}

@post('/sensor')
def sensor():
    """ Sensor event from the server. Returns a speedcontrol json object. """

    data = request.json
    if data['type'] == "CAR_SENSOR_DATA":
        if data["acc"][1] > 40:
            payload = {'teamId':TEAM_ID, 'accessCode':ACCESS_CODE, \
                    'power':45, 'timestamp': int(round(time.time()))}
            requests.post(RELAY_SPEED_URL, data=json.dumps(payload))
            #return {'teamId':TEAM_ID, 'accessCode':ACCESS_CODE, \
                    #'power':45, 'timestamp': int(round(time.time() * 1000))}
        else:
            payload = {'teamId':TEAM_ID, 'accessCode':ACCESS_CODE, \
                    'power':85, 'timestamp': int(round(time.time()))}
            requests.post(RELAY_SPEED_URL, data=json.dumps(payload))
            #return {'teamId':TEAM_ID, 'accessCode':ACCESS_CODE, \
                    #'power':85, 'timestamp': int(round(time.time() * 1000))}
    # end of round
    # need to do something here

if __name__ == '__main__':
    # TODO write a command line switch for debug and prod
    run(host='localhost', port=PORT)
    #run(host='localhost', port=8080, debug=True)
