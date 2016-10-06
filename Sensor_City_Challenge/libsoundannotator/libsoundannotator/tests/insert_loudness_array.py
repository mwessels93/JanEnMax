# Stream loudness to the API
import requests, json, pprint, time, random, sys, datetime, pytz, oauthlib.oauth1

# Insert the frequency of the STS chunks in seconds. this is used for metadata
freq = 600 #every 10 minutes

# in this simulation: the maximum allowed length of a data point (for instance if you want to have max 24 hours in one data point)
maxlen = 144

now_time = datetime.datetime.now(pytz.utc)
# starting time of the simulated data
start_time = now_time - datetime.timedelta(days=1)

# maximum range of the values that can be inserted
valmax = 100

agitation_max = 6

# API base URL
api = 'http://localhost:1337'
# name of the desired Dataset: see http://test.sndrc.nl:1337/dataset for possible datasets
name = "Node1"

# the API public key of the consumer we want to use
key = "a12ead32-a4f3-4462-9188-e362e95c8748"
# The API secret key
secret = "80940fbc-1de5-4893-8440-4cb988ad7ebd"

# The UID of the 'system' user we use to POST data to the API
uid = "55e5d253e3cf102c250a4ff0"

# construct an OAuth client to sign our requests
client = oauthlib.oauth1.Client(key, client_secret=secret)


"""
	Convert all python dictionary values to unicode strings. Needed to sign a POST request
"""
def body_to_unicode(body):
	if body == None:
		return body
	uni = {}
	for key in body:
		uni[key] = unicode(str(body[key]))
	return uni


"""
	Generate an OAuth1.0a signature for an HTTP request to the API.
	Possible parameters are 'method' and 'body'
"""
def signed_request(url, method="GET", body=None):
	headers = {}
	if method == "POST":
		headers = {
			"Content-Type":"application/x-www-form-urlencoded"
		}
		body['uid'] = uid

	uri, headers, body = client.sign(url, method, body_to_unicode(body), headers=headers)
	headers['uid'] = uid
	if method == "GET":
		return requests.get(url, headers=headers)
	elif method == "POST" and body == None:
		raise Exception("POST request most have body")
	elif method == "POST" and body != None:
		return requests.post(url, data=body, headers=headers)


"""
	Get the dataset from the API
"""

def get_dataset():
	dset_url = '{0}/dataset?name={1}'.format(api,name)
	print dset_url
	req = signed_request(dset_url)
	resp = req.json()[0]
	dset_id = resp['id']
	print "Dataset ID: {0}".format(dset_id)
	return dset_id

"""
	Add a loudness value to an existing datapoint or to a new data point
"""
def add_loudness_data(dset_id, value, createdAt, d_id):
	data_url = '{0}/data/{1}/stream/audio_loudness'.format(api, d_id)
	opts = {
		"loudness": value,
		"datetime": createdAt
	}

	print data_url
	#print "Fake request: {0}".format(opts)
	req = signed_request(data_url, "POST", opts)
	#print "Response: {0}".format(req.json())
	return req.json()

def add_agitation_data(dset_id, value, createdAt, d_id):
	data_url = '{0}/data/{1}/stream/audio_agitation'.format(api, d_id)
	opts = {
		"agitation": value,
		"datetime": createdAt
	}

	print data_url
	#print "Fake request: {0}".format(opts)
	req = signed_request(data_url, "POST", opts)
	#print "Response: {0}".format(req.json())
	return req.json()

def add_loudness_data_new(dset_id, value, createdAt, metadata=None):
	data_url = '{0}/data/stream/audio_loudness'.format(api)
	opts = {
		"loudness": value,
		"dataset": dset_id,
		"datetime": createdAt,
		"info": metadata if metadata is not None else {}
	}
	print data_url
	req = signed_request(data_url, "POST", opts)
	return req.json()


"""
MAIN
"""

# try to get the dataset ID
try:
	dset_id = get_dataset()
except Exception as e:
	sys.exit("Exception: " + str(e))

count = 0
cur_time = start_time
d_id = None


# initial metadata object
metadata = json.dumps({
	"frequency":freq
})

#insert as many points as desired
while cur_time  < now_time:
	cur_time = cur_time + datetime.timedelta(seconds=freq)
	createdAt = "{0}Z".format(cur_time.isoformat()[:-9])
	loudness = int(random.random() * valmax)
	agitation = int(random.random() * agitation_max)
		#sometimes, a discontinuity occurs
	if random.random() < 0.05 or count % maxlen == 0:
		print "\n\nSimulating discontinuity"
		print "New data point"
		representation = add_loudness_data_new(dset_id, loudness, createdAt, metadata)
		print representation
		d_id = representation['data']['id']

		#add agitation data
		add_agitation_data(dset_id, agitation, createdAt, d_id)
	else:
		print "Existing data point"
		add_loudness_data(dset_id, loudness, createdAt, d_id)
		add_agitation_data(dset_id, agitation, createdAt, d_id)

	count += 1
