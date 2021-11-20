import requests
import time

HOSTNAME = "bko7deq544.execute-api.us-east-2.amazonaws.com/dev"
AUTHORIZATION_TOKEN = "allow"
PANEL_WIDTH = 35
NUM_TIMELINE_POINTS = 60

end_time = time.time()
length = NUM_TIMELINE_POINTS
start_time = end_time - (length * 60 * 60)
endpoint = (f"https://{HOSTNAME}/sensors/devices/test"
            f"?start={start_time}&end={end_time}")
headers = {'authorization-token': AUTHORIZATION_TOKEN}
response = requests.get(endpoint, headers=headers)
data = response.json()
print(data)
