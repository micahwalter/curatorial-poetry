#!/usr/bin/python
import logging, os
import MySQLdb
import simplejson as json
import oauth2 as oauth
import cStringIO
import urlparse
import urllib
from apscheduler.scheduler import Scheduler

request_token_url = 'http://www.tumblr.com/oauth/request_token'
access_token_url = 'http://www.tumblr.com/oauth/access_token'
authorize_url = 'http://www.tumblr.com/oauth/authorize'

logging.basicConfig()
sched = Scheduler()

def create_post():
	cur = db.cursor() 	
	buf = cStringIO.StringIO()
	
	cur.execute("SELECT * FROM objects WHERE description IS NOT NULL AND published IS NULL ORDER BY RAND() LIMIT 1")
	
	row = cur.fetchall()
	
	for f in row:
		object_id = f[0]
		description = f[1]
		url = encode(object_id)
		url = "http://cprhw.tt/o/" + url
	
	# post to tumblr blog

	consumer = oauth.Consumer(os.environ['CONSUMER_KEY'], os.environ['CONSUMER_SECRET'])
	client = oauth.Client(consumer)

	resp, content = client.request(request_token_url, "GET")
	if resp['status'] != '200':
		raise Exception("Invalid response %s." % resp['status'])

	request_token = dict(urlparse.parse_qsl(content))

	token = oauth.Token(os.environ['OAUTH_KEY'], os.environ['OAUTH_SECRET'])
	client = oauth.Client(consumer, token)
	
	the_body = description + "\n" + "\n" + url
	params = {
		'type': 'text',
		'title': object_id,
		'body': the_body,
	}

	requestUrl = "http://api.tumblr.com/v2/blog/" + os.environ['TUMBLR_BLOG'] + "/post"
	print client.request(requestUrl, method="POST", body=urllib.urlencode(params))
	
	cur.execute("UPDATE objects SET published = 1 WHERE id=" + str(object_id))

def encode(num):
	alphabet = '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
	base_count = len(alphabet)
	encode = ''

	if (num < 0):
		return ''

	while (num >= base_count):	
		mod = num % base_count
		encode = alphabet[mod] + encode
		num = num / base_count

	if (num):
		encode = alphabet[num] + encode

	return encode

@sched.cron_schedule(hour='*/2')
def scheduled_job():
	create_post()

def run_clock():
	sched.start()

	while True:
		pass

if __name__ == "__main__":
	
	import sys
	
	db = MySQLdb.connect(host=os.environ['MYSQL_HOST'], user=os.environ['MYSQL_USER'], passwd=os.environ['MYSQL_PASSWORD'], db=os.environ['MYSQL_DB'])
	
	if len(sys.argv) > 1:
		if (sys.argv[1] == "timed"):
			run_clock()
	
	create_post()
