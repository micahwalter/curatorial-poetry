#!/usr/bin/env python

import sys
import os
import os.path
import sqlite3 as lite
import urlparse
import oauth2 as oauth
import urllib

consumer_key = 'your-consumer-key'
consumer_secret = 'your-consumer-secret'
oauth_key = 'your-oauth-key'
oauth_secret = 'your-oauth-secret'

request_token_url = 'http://www.tumblr.com/oauth/request_token'
access_token_url = 'http://www.tumblr.com/oauth/access_token'
authorize_url = 'http://www.tumblr.com/oauth/authorize'

import logging
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':

	whoami = os.path.abspath(sys.argv[0])
	bindir = os.path.dirname(whoami)
	rootdir = os.path.dirname(bindir)

	datadir = os.path.join(rootdir, 'data')

	datafile = os.path.join(datadir, 'objects.sqlite3')
	
	logging.info("file %s" % datafile)
	
	# grab top row where it has a description and has NOT been published
	con = None

	con = lite.connect(datafile)

	with con:
		cur = con.cursor()
		cur.execute("SELECT * FROM objects WHERE description IS NOT NULL AND published IS NULL ORDER BY RANDOM() LIMIT 1")
		
	
		row = cur.fetchall()
		
		for f in row:
			object_id = f[0]
			description = f[1]
			url = f[2]
			published = f[3]
			the_body = description + "\n" + "\n" + url
			print the_body
			
	# post to tumblr blog
	
	consumer = oauth.Consumer(consumer_key, consumer_secret)
	client = oauth.Client(consumer)

	resp, content = client.request(request_token_url, "GET")
	if resp['status'] != '200':
	        raise Exception("Invalid response %s." % resp['status'])

	request_token = dict(urlparse.parse_qsl(content))

	token = oauth.Token(oauth_key, oauth_secret)
	client = oauth.Client(consumer, token)
	
	params = {
	       'type': 'text',
	       'title': object_id,
	       'body': the_body,
	}
	
	print client.request("http://api.tumblr.com/v2/blog/{your-tumblr-blog}.tumblr.com/post", method="POST", body=urllib.urlencode(params))
	
	with con:
		con = con.cursor()
		sql = "UPDATE objects SET published = 1 WHERE id=" + str(object_id)
		cur.execute(sql)

		data = cur.fetchone()

		print data
	
	
	