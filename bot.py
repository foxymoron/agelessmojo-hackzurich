""" agelessmojo bot implementation """
from __future__ import division # for floating point division
import time, json, requests, os
from bottle import get, post, request, run, response

RELAY_SPEED_URL = \
        'http://carrera-relay.beta.swisscloud.io/relay/ws/rest/relay/speed'
TEAM_ID = 'agelessmojo'
PORT = os.getenv('VCAP_APP_PORT')
HOST = os.getenv('VCAP_APP_HOST')
ACCESS_CODE = 'yoyoyo'

WINDOW_SIZE = 11

MAX_NORMAL = 255
MIN_NORMAL = -255


LAP_DATA = {}
LAP_DATA_SMOOTHED = {}
LAP_COUNT = 0
LAP_ITERATOR = 0

@get('/ping')
def ping():
    """ Check for bot health. Returns success in text/plain. """

    response.headers['Content-Type'] = 'text/plain'
    return "success"

def send_power_control(power):
    """ Send power control to the relay. """
    payload = {'teamId':TEAM_ID,
               'accessCode': ACCESS_CODE,
               'power': power,
               'timeStamp': int(round(time.time() * 1000))}
    #requests.post(RELAY_SPEED_URL, data=json.dumps(payload))
    return payload

def round_reset():
    """ Bookkeeping and preparing for the next round """
    global LAP_COUNT, LAP_ITERATOR
    LAP_COUNT += 1
    LAP_ITERATOR = 0


def smoothing():
    """ Carry out smoothing over a moving window """
    global LAP_ITERATOR

    if not LAP_DATA_SMOOTHED[LAP_COUNT]:
        acc0 = [LAP_DATA[LAP_COUNT][0][0][LAP_ITERATOR]]
        acc1 = [LAP_DATA[LAP_COUNT][0][1][LAP_ITERATOR]]
        acc2 = [LAP_DATA[LAP_COUNT][0][2][LAP_ITERATOR]]
        gyr0 = [LAP_DATA[LAP_COUNT][1][0][LAP_ITERATOR]]
        gyr1 = [LAP_DATA[LAP_COUNT][1][1][LAP_ITERATOR]]
        gyr2 = [LAP_DATA[LAP_COUNT][1][2][LAP_ITERATOR]]

        acc = [acc0]
        acc.append(acc1)
        acc.append(acc2)

        gyr = [gyr0]
        gyr.append(gyr1)
        gyr.append(gyr2)

        LAP_DATA_SMOOTHED[LAP_COUNT].append(acc)
        LAP_DATA_SMOOTHED[LAP_COUNT].append(gyr)

        LAP_ITERATOR += 1
    elif len(LAP_DATA[LAP_COUNT][0][0]) <= WINDOW_SIZE:
        acc0 = (LAP_DATA[LAP_COUNT][0][0][LAP_ITERATOR] + \
                ((LAP_DATA_SMOOTHED[LAP_COUNT][0][0][LAP_ITERATOR- 1]) * \
                LAP_ITERATOR)) / LAP_ITERATOR + 1
        acc1 = (LAP_DATA[LAP_COUNT][0][1][LAP_ITERATOR] + \
                ((LAP_DATA_SMOOTHED[LAP_COUNT][0][1][LAP_ITERATOR - 1]) * \
                LAP_ITERATOR)) / LAP_ITERATOR + 1
        acc2 = (LAP_DATA[LAP_COUNT][0][2][LAP_ITERATOR] + \
                ((LAP_DATA_SMOOTHED[LAP_COUNT][0][2][LAP_ITERATOR - 1]) * \
                LAP_ITERATOR)) / LAP_ITERATOR + 1
        gyr0 = (LAP_DATA[LAP_COUNT][1][0][LAP_ITERATOR] + \
                ((LAP_DATA_SMOOTHED[LAP_COUNT][1][0][LAP_ITERATOR - 1]) * \
                LAP_ITERATOR)) / LAP_ITERATOR + 1
        gyr1 = (LAP_DATA[LAP_COUNT][1][1][LAP_ITERATOR] + \
                ((LAP_DATA_SMOOTHED[LAP_COUNT][1][1][LAP_ITERATOR - 1]) * \
                LAP_ITERATOR)) / LAP_ITERATOR + 1
        gyr2 = (LAP_DATA[LAP_COUNT][1][2][LAP_ITERATOR] + \
                ((LAP_DATA_SMOOTHED[LAP_COUNT][1][2][LAP_ITERATOR - 1]) * \
                LAP_ITERATOR)) / LAP_ITERATOR + 1

        LAP_DATA_SMOOTHED[LAP_COUNT][0][0].append(acc0)
        LAP_DATA_SMOOTHED[LAP_COUNT][0][1].append(acc1)
        LAP_DATA_SMOOTHED[LAP_COUNT][0][2].append(acc2)
        LAP_DATA_SMOOTHED[LAP_COUNT][1][0].append(gyr0)
        LAP_DATA_SMOOTHED[LAP_COUNT][1][1].append(gyr1)
        LAP_DATA_SMOOTHED[LAP_COUNT][1][2].append(gyr2)

        LAP_ITERATOR += 1
    else:
        acc0 = LAP_DATA_SMOOTHED[LAP_COUNT][0][0][LAP_ITERATOR - 1] + \
                (LAP_DATA[LAP_COUNT][0][0][LAP_ITERATOR] / WINDOW_SIZE) - \
                (LAP_DATA[LAP_COUNT][0][0][LAP_ITERATOR - WINDOW_SIZE] / \
                WINDOW_SIZE)
        acc1 = LAP_DATA_SMOOTHED[LAP_COUNT][0][1][LAP_ITERATOR - 1] + \
                (LAP_DATA[LAP_COUNT][0][1][LAP_ITERATOR] / WINDOW_SIZE) - \
                (LAP_DATA[LAP_COUNT][0][1][LAP_ITERATOR - WINDOW_SIZE] / \
                WINDOW_SIZE)
        acc2 = LAP_DATA_SMOOTHED[LAP_COUNT][0][2][LAP_ITERATOR - 1] + \
                (LAP_DATA[LAP_COUNT][0][2][LAP_ITERATOR] / WINDOW_SIZE) - \
                (LAP_DATA[LAP_COUNT][0][2][LAP_ITERATOR - WINDOW_SIZE] / \
                WINDOW_SIZE)
        gyr0 = LAP_DATA_SMOOTHED[LAP_COUNT][1][0][LAP_ITERATOR - 1] + \
                (LAP_DATA[LAP_COUNT][1][0][LAP_ITERATOR] / WINDOW_SIZE) - \
                (LAP_DATA[LAP_COUNT][1][0][LAP_ITERATOR - WINDOW_SIZE] / \
                WINDOW_SIZE)
        gyr1 = LAP_DATA_SMOOTHED[LAP_COUNT][1][1][LAP_ITERATOR - 1] + \
                (LAP_DATA[LAP_COUNT][1][1][LAP_ITERATOR] / WINDOW_SIZE) - \
                (LAP_DATA[LAP_COUNT][1][1][LAP_ITERATOR - WINDOW_SIZE] / \
                WINDOW_SIZE)
        gyr2 = LAP_DATA_SMOOTHED[LAP_COUNT][1][2][LAP_ITERATOR - 1] + \
                (LAP_DATA[LAP_COUNT][1][2][LAP_ITERATOR] / WINDOW_SIZE) - \
                (LAP_DATA[LAP_COUNT][1][2][LAP_ITERATOR - WINDOW_SIZE] / \
                WINDOW_SIZE)

        LAP_ITERATOR += 1

@post('/start')
def start():
    """ Signals start of the round. Returns a speedcontrol json object. """
    LAP_DATA[LAP_COUNT] = []
    LAP_DATA_SMOOTHED[LAP_COUNT] = []
    return send_power_control(120) # sending 120 to begin with


@get('/status')
def status():
    """
    Current status
    """
    return {'numSensorEvents': len(LAP_DATA[LAP_COUNT][0][0]),
            'lapData': json.dumps(LAP_DATA),
            'lapDataSmoothed': json.dumps(LAP_DATA_SMOOTHED)}

@post('/sensor')
def sensor():
    """ Sensor event from the server. Returns a speedcontrol json object. """

    data = request.json
    if data['type'] == 'CAR_SENSOR_DATA':
        # append to the data dictionary
        if not LAP_DATA[LAP_COUNT]:
            acc0 = [(data['acc'][0] - MIN_NORMAL) / (MAX_NORMAL - MIN_NORMAL)]
            acc1 = [(data['acc'][1] - MIN_NORMAL) / (MAX_NORMAL - MIN_NORMAL)]
            acc2 = [(data['acc'][2] - MIN_NORMAL) / (MAX_NORMAL - MIN_NORMAL)]
            gyr0 = [(data['gyr'][0] - MIN_NORMAL) / (MAX_NORMAL - MIN_NORMAL)]
            gyr1 = [(data['gyr'][1] - MIN_NORMAL) / (MAX_NORMAL - MIN_NORMAL)]
            gyr2 = [(data['gyr'][2] - MIN_NORMAL) / (MAX_NORMAL - MIN_NORMAL)]

            acc = [acc0]
            acc.append(acc1)
            acc.append(acc2)

            gyr = [gyr0]
            gyr.append(gyr1)
            gyr.append(gyr2)

            LAP_DATA[LAP_COUNT].append(acc)
            LAP_DATA[LAP_COUNT].append(gyr)
        else:
            acc0 = (data['acc'][0] - MIN_NORMAL) / (MAX_NORMAL - MIN_NORMAL)
            acc1 = (data['acc'][1] - MIN_NORMAL) / (MAX_NORMAL - MIN_NORMAL)
            acc2 = (data['acc'][2] - MIN_NORMAL) / (MAX_NORMAL - MIN_NORMAL)
            gyr0 = (data['gyr'][0] - MIN_NORMAL) / (MAX_NORMAL - MIN_NORMAL)
            gyr1 = (data['gyr'][1] - MIN_NORMAL) / (MAX_NORMAL - MIN_NORMAL)
            gyr2 = (data['gyr'][2] - MIN_NORMAL) / (MAX_NORMAL - MIN_NORMAL)

            LAP_DATA[LAP_COUNT][0][0].append(acc0)
            LAP_DATA[LAP_COUNT][0][1].append(acc1)
            LAP_DATA[LAP_COUNT][0][2].append(acc2)
            LAP_DATA[LAP_COUNT][1][0].append(gyr0)
            LAP_DATA[LAP_COUNT][1][1].append(gyr1)
            LAP_DATA[LAP_COUNT][1][2].append(gyr2)

        smoothing()
        # fancy prediction algorithm
        return send_power_control(120)
    else:
        round_reset()

@post('/reset')
def reset():
    """ Reset values. """
    # TODO write this
    pass

if __name__ == '__main__':
    # TODO write a command line switch for debug and prod
    run(host=HOST, port=PORT, debug=False)
    #run(host='localhost', port=8080, debug=True)
