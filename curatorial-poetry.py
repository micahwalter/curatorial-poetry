import os
from flask import Flask, url_for, request
from flaskext.mysql import MySQL
import simplejson as json
from flask.ext.script import Manager
import pycurl
import oauth2 as oauth
import cStringIO
import urlparse
import urllib

app = Flask(__name__)
mysql = MySQL()

app.config['MYSQL_DATABASE_USER'] = os.environ['MYSQL_USER']
app.config['MYSQL_DATABASE_PASSWORD'] = os.environ['MYSQL_PASSWORD']
app.config['MYSQL_DATABASE_HOST'] = os.environ['MYSQL_HOST']
app.config['MYSQL_DATABASE_DB'] = os.environ['MYSQL_DB']
app.config['HOSTNAME'] = os.environ['HOSTNAME']

app.config['CONSUMER_KEY'] = os.environ['CONSUMER_KEY']
app.config['CONSUMER_SECRET'] = os.environ['CONSUMER_SECRET']
app.config['OAUTH_KEY'] = os.environ['OAUTH_KEY']
app.config['OAUTH_SECRET'] = os.environ['OAUTH_SECRET']

app.config['TUMBLR_BLOG'] = os.environ['TUMBLR_BLOG']

request_token_url = 'http://www.tumblr.com/oauth/request_token'
access_token_url = 'http://www.tumblr.com/oauth/access_token'
authorize_url = 'http://www.tumblr.com/oauth/authorize'

mysql.init_app(app)
manager = Manager(app)

@app.route('/')
def hello():
	
	r = getRandom()
	
	html = '<h1>' + str(r['id']) + '</h1>'
	html = html + "<p>" + r['description'] + "</p>"
	html = html + '<a href="' + r['url'] + '">' + r['url'] + '</a>'
		
	return html

@app.route('/json')
def jsonstuff():
	r = getRandom()
	rsp = json.dumps(r)
		
	return rsp
	
def getRandom():
	randomObject = {}
	
	cursor = mysql.get_db().cursor()
	
	cursor.execute("SELECT * FROM objects WHERE description IS NOT NULL AND published IS NULL ORDER BY RAND() LIMIT 1")
	
	row = cursor.fetchall()
	
	for f in row:
		object_id = f[0]
		description = f[1]
		url = encode(object_id)
		url = "http://cprhw.tt/o/" + url
	
	cursor.execute("UPDATE objects SET published = 1 WHERE id=" + str(object_id))
	
	randomObject['id'] = object_id
	randomObject['description'] = description
	randomObject['url'] = url
	
	return randomObject

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

@manager.command
def newPost():
	buf = cStringIO.StringIO()
	
	c = pycurl.Curl()
	curlurl = app.config['HOSTNAME'] + '/json'
	c.setopt(c.URL, curlurl)
	c.setopt(c.WRITEFUNCTION, buf.write)
	c.perform()
	
	data = json.loads(buf.getvalue())

	buf.reset()
	buf.truncate()
	
	# post to tumblr blog

	consumer = oauth.Consumer(app.config['CONSUMER_KEY'], app.config['CONSUMER_SECRET'])
	client = oauth.Client(consumer)

	resp, content = client.request(request_token_url, "GET")
	if resp['status'] != '200':
		raise Exception("Invalid response %s." % resp['status'])

	request_token = dict(urlparse.parse_qsl(content))

	token = oauth.Token(app.config['OAUTH_KEY'], app.config['OAUTH_SECRET'])
	client = oauth.Client(consumer, token)
	
	the_body = data['description'] + "\n" + "\n" + data['url']
	params = {
		'type': 'text',
		'title': data['id'],
		'body': the_body,
	}

	requestUrl = "http://api.tumblr.com/v2/blog/" + app.config['TUMBLR_BLOG'] + "/post"
	print client.request(requestUrl, method="POST", body=urllib.urlencode(params))

	print "done"

if __name__ == "__main__":
	manager.run()
