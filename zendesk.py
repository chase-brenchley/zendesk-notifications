import json
import time
import pdb
import requests
import argparse
from requests.auth import HTTPBasicAuth

parse = argparse.ArgumentParser(description='Sends zendesk notifications to your phone.')
parse.add_argument('--silent', '-s', help='stops phone TTS', action='store_true')
parse.add_argument('--verbose', '-v', help='prints helpful messages', action='store_true')
parse.add_argument('--own', '-o', help='only notifies when my own or new tickets come in', action='store_true')
args = parse.parse_args()

with open('apitoken.txt') as f:
	token, email, url = f.read().splitlines()

with open('pushbullet.txt') as f:
	pushbullet, phone = f.read().splitlines()

payload = {'type':'note', 'title':'Queue Change', 'body':'A change in the queue has been detected'}
if args.silent: payload['title'] = 'Silent Queue Change'

header = {'Access-token':pushbullet, 'Content-Type':'application/json'}

current_state = set()

while True:
	r = requests.get(url+'search.json?query=type:ticket priority>low group_id:20349363 brand_id:3275876 status<=open', auth=HTTPBasicAuth(email,token))

	try:
		results = set([ticket['id'] for ticket in r.json()['results']])
	except KeyError as e:
		raise e
	
	if (current_state != results and not results.issubset(current_state)) and r.json()['count'] != 0:
		if args.verbose:
			print("Change in queue has been detected")
			print(f"Previously there were {len(current_state)} tickets with {current_state} ids")
			print(f"Now there are {len(results)} tickets with {results} ids")

		new = [ticket['subject'] if ticket['id'] in results-current_state else None for ticket in r.json()['results']]
		payload['body'] = "Queue update! There are {} tickets requiring attention!\n".format(len(results))

		for subject in new:
			if subject:
				payload['body'] += 'Ticket Subject: {}\n'.format(subject)

		requests.post('https://api.pushbullet.com/v2/pushes', data=json.dumps(payload), headers=header)

	current_state = results
	time.sleep(10)
