""" agelessmojo bot implementation """
from __future__ import division # for floating point division
import os, json
import numpy as np
from sklearn.hmm import GaussianHMM
from bottle import get, post, request, run, response

PORT = os.getenv('VCAP_APP_PORT')
HOST = os.getenv('VCAP_APP_HOST')

HMM = GaussianHMM(50, "diag")

# TODO Variables here

WINDOW_SIZE = 5

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
    response.headers['Content-Type'] = 'text/plain'
    return str(power)

def round_reset():
    """ Bookkeeping and preparing for the next round """
    global LAP_COUNT, LAP_ITERATOR
    LAP_COUNT += 1
    LAP_ITERATOR = 0


def smoothing():
    """ Carry out smoothing over a moving window """
    global LAP_ITERATOR

    if not LAP_DATA_SMOOTHED[LAP_COUNT]:
        LAP_DATA_SMOOTHED[LAP_COUNT] = LAP_DATA[LAP_COUNT]
        LAP_ITERATOR += 1
    elif len(LAP_DATA[LAP_COUNT][0][0]) <= WINDOW_SIZE:
        sacc0 = (LAP_DATA[LAP_COUNT][0][LAP_ITERATOR] + \
                ((LAP_DATA_SMOOTHED[LAP_COUNT][0][LAP_ITERATOR- 1]) * \
                LAP_ITERATOR)) / LAP_ITERATOR + 1
        sacc1 = (LAP_DATA[LAP_COUNT][1][LAP_ITERATOR] + \
                ((LAP_DATA_SMOOTHED[LAP_COUNT][1][LAP_ITERATOR - 1]) * \
                LAP_ITERATOR)) / LAP_ITERATOR + 1
        sgyr0 = (LAP_DATA[LAP_COUNT][2][LAP_ITERATOR] + \
                ((LAP_DATA_SMOOTHED[LAP_COUNT][2][LAP_ITERATOR - 1]) * \
                LAP_ITERATOR)) / LAP_ITERATOR + 1

        LAP_DATA_SMOOTHED[LAP_COUNT] = np.vstack( \
                [np.append(LAP_DATA[LAP_COUNT][0], sacc0),\
                np.append(LAP_DATA[LAP_COUNT][1], sacc1), \
                np.append(LAP_DATA[LAP_COUNT][2], sgyr0)])
        LAP_ITERATOR += 1
    else:
        sacc0 = LAP_DATA_SMOOTHED[LAP_COUNT][0][LAP_ITERATOR - 1] + \
                (LAP_DATA[LAP_COUNT][0][LAP_ITERATOR] / WINDOW_SIZE) - \
                (LAP_DATA[LAP_COUNT][0][LAP_ITERATOR - WINDOW_SIZE] / \
                WINDOW_SIZE)
        sacc1 = LAP_DATA_SMOOTHED[LAP_COUNT][1][LAP_ITERATOR - 1] + \
                (LAP_DATA[LAP_COUNT][1][LAP_ITERATOR] / WINDOW_SIZE) - \
                (LAP_DATA[LAP_COUNT][1][LAP_ITERATOR - WINDOW_SIZE] / \
                WINDOW_SIZE)
        sgyr0 = LAP_DATA_SMOOTHED[LAP_COUNT][2][LAP_ITERATOR - 1] + \
                (LAP_DATA[LAP_COUNT][2][LAP_ITERATOR] / WINDOW_SIZE) - \
                (LAP_DATA[LAP_COUNT][2][LAP_ITERATOR - WINDOW_SIZE] / \
                WINDOW_SIZE)

        LAP_DATA_SMOOTHED[LAP_COUNT] = np.vstack( \
        [np.append(LAP_DATA[LAP_COUNT][0], sacc0),\
        np.append(LAP_DATA[LAP_COUNT][1], sacc1), \
        np.append(LAP_DATA[LAP_COUNT][2], sgyr0)])

        LAP_ITERATOR += 1

@post('/start')
def start():
    """ Signals start of the round. Returns a speedcontrol json object. """
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
            nacc0 = np.array([(data['acc'][0] + 255) / 510])
            nacc1 = np.array([(data['acc'][1] + 255) / 510])
            ngyr0 = np.array([(data['gyr'][0] - 242) / 440])

            LAP_DATA[LAP_COUNT] = np.vstack([nacc0, nacc1, ngyr0])
        else:
            nacc0 = (data['acc'][0] + 255) / 510
            nacc1 = (data['acc'][1] + 255) / 510
            ngyr0 = (data['gyr'][0] - 242) / 440

            LAP_DATA[LAP_COUNT] = np.vstack( \
                    [np.append(LAP_DATA[LAP_COUNT][0], nacc0),\
                    np.append(LAP_DATA[LAP_COUNT][1], nacc1), \
                    np.append(LAP_DATA[LAP_COUNT][2], ngyr0)])
        smoothing()
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
