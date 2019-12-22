import urllib.request
import base64, uuid, json, time
import socket

BRAVIA_IP = "192.168.0.XXX"
BRAVIA_MAC = "AC:9B:0A:XX:XX:XX"
NICKNAME = 'Script'
CLIENTID = str(uuid.uuid4())

# auth header
AUTH_HEADER = json.dumps(
{
	"method":"actRegister",
	"params":[
	{
		"clientid":CLIENTID,
		"nickname":NICKNAME,
		"level":"private"},[
		{
			"value":"yes",
			"function":"WOL"}
		]
	],
	"id":1,
	"version":"1.0"}
).encode("utf-8")


def wakeonlan(mac_address):
	addr_str = mac_address.replace(':','')
	msg = bytearray.fromhex(('FF' * 6) + (addr_str * 16))
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	s.sendto(msg, ('<broadcast>', 9))
	s.close()



def bravia_req_ircc( ip, port, url, code, cookie ):
	params = str("<?xml version=\"2.0\"?><s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><s:Body><u:X_SendIRCC xmlns:u=\"urn:schemas-sony-com:service:IRCC:1\"><IRCCCode>"+code+"</IRCCCode></u:X_SendIRCC></s:Body></s:Envelope>").encode("utf-8")

	req = urllib.request.Request('http://'+ip+':'+port+'/'+url, params)
	req.add_header('SOAPACTION', 'urn:schemas-sony-com:service:IRCC:1#X_SendIRCC')
	req.add_header('Cookie', cookie)

	try:
		response = urllib.request.urlopen(req)
	except urllib.error.HTTPError as e:
		print("[W] HTTPError: ",str(e.code))

	except urllib.error.URLError as e:
		print("[W] URLError: ",str(e.reason))

	else:
		tree = response.read()
		return tree


def remote_code(cookie):
	resp = bravia_req(BRAVIA_IP, "80", "sony/system", jdata_build("getRemoteControllerInfo", ""), cookie);
	data = resp['result'][1]
	commands = {}
	for item in data:
		print(item['value'],item['name'])
		commands[item['name']] = item['value']
	return commands

def jdata_build(method, params):
	if params:
		ret =  json.dumps({"method":method,"params":[params],"id":1,"version":"1.0"})
	else:
		ret =  json.dumps({"method":method,"params":[],"id":1,"version":"1.0"})
	return ret

def bravia_req( ip, port, url, params, cookie ):
	req = urllib.request.Request('http://'+ip+':'+port+'/'+url, params.encode("utf-8"))
	req.add_header('Cookie', cookie)

	if url == "DIAL/sony/applist":
		req.get_method = lambda: 'GET'
	try:
		response = urllib.request.urlopen(req)
	except urllib.error.HTTPError as e:
		print("[W] HTTPError: ",str(e.code))

	except urllib.error.URLError as e:
		print("[W] URLError: ",str(e.reason))

	else:
		if url == "DIAL/sony/applist":
			return response.read()
		else:
			html = json.load(response)
			return html

def bravia_auth ( ip, port, url, params, pin ):
	req = urllib.request.Request('http://'+ip+':'+port+'/'+url, params)
	cookie = None
	response = None
	
	if pin:
		username = ''
		base64string = base64.encodestring(('%s:%s' % (username, pin)).encode()).decode().replace('\n', '')
		req.add_header("Authorization", "Basic %s" % base64string)
		req.add_header("Connection", "keep-alive")
		
	try:
		response = urllib.request.urlopen(req)
		
	except urllib.error.HTTPError as e:
		print("[W] HTTPError: ",str(e.code))
		pin = str(input("Please Enter PIN Number: "))
		return bravia_auth(BRAVIA_IP, "80", "sony/accessControl", AUTH_HEADER, pin );
		
	except urllib.error.URLError as e:
		print("[W] URLError: ",str(e.reason))
		return None
		
	else: 
		for h in response.headers:
			if h.find("Set-Cookie") > -1:
				cookie=h			
		if cookie:
			cookie = response.headers['Set-Cookie']
			return cookie
		return None

def test_send(code,count):
	for i in range(count):
		rsp = bravia_req_ircc(BRAVIA_IP, "80", "sony/IRCC", code, cookie)
		time.sleep(0.1)
	return rsp


wakeonlan(BRAVIA_MAC)
time.sleep(30)
cookie = bravia_auth(BRAVIA_IP, "80", "sony/accessControl", AUTH_HEADER, None );
#cookie = "auth=XXXXXXXXXXXXXXXXXX; path=/sony/; max-age=1209600; expires=Sat, 18-Aug-2018 04:10:41 GMT;"
print(cookie)

#print(bravia_req(BRAVIA_IP, "80", "sony/system", jdata_build("requestToNotifyDeviceStatus", ""), cookie))
#print(bravia_req(BRAVIA_IP, "80", "DIAL/sony/applist", "", cookie))
commands = remote_code(cookie)

#while(True):
#	test_send(commands[input(">")],1)

test_send(commands['OneTouchView'],1)
time.sleep(3)
test_send(commands['Options'],1)
test_send(commands['Up'],2)
test_send(commands['Confirm'],1)
test_send(commands['Up'],1)
test_send(commands['Confirm'],1)
time.sleep(3)
for i in range(60):
	test_send(commands['Green'],1)
	test_send(commands['Left'],1)
	test_send(commands['Confirm'],1)
	time.sleep(3)
	test_send(commands['Return'],1)

test_send(commands['Digital'],1)
time.sleep(3)
test_send(commands['PowerOff'],1)
