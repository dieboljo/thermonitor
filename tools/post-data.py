import time

import json
import math
import random
import requests

URL = "https://bko7deq544.execute-api.us-east-2.amazonaws.com/dev/sensors"
headers = {'authorization-token': 'allow'}
def main():
    while True:
        payload = {
            "EpochTime": math.floor(time.time()),
            "LocationId": "45203",
            "DeviceId": "test",
            "Temperature": random.randrange(-10, 121, 1),
            "Humidity": random.randrange(0, 101, 1),
        }
        body = json.dumps(payload)
        r = requests.post(URL, headers=headers, data=body)
        print(r.text)
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
