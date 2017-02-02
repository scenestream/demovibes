import uwsgi
import bottle
#from bottle import route, default_app, request, post, get
import pickle
import random

import hashlib

try:
    import local_config
    allowed_ips = getattr(local_config, "allowed_ips", ["127.0.0.1"])
    debug = getattr(local_config, "debug", False)
    secret = getattr(local_config, "UWSGI_ID_SECRET", None)
except:
    print "EventHandler: Could not load local settings, using default!"
    debug = False
    secret = None
    allowed_ips = ["127.0.0.1"]

bottle.debug(debug)

event = []

@bottle.post('/demovibes/ajax/monitor/new/')
def http_event_receiver():
    ip = bottle.request.environ.get('REMOTE_ADDR')
    if ip not in allowed_ips:
        return ip
    data = bottle.request.forms.get('data')
    data = pickle.loads(data)
    event_receiver(data, 0)
    return "OK"

def event_receiver(obj, id):
    global event
    event = obj

uwsgi.message_manager_marshal = event_receiver

@bottle.get('/demovibes/ajax/monitor/:id#[0-9]+#/')
def handler(id):
    userid = bottle.request.GET.get('uid', None)
    if userid and secret:
        hash = hashlib.sha1("%s.%s" % (userid, secret)).hexdigest()
        sign = bottle.request.GET.get('sign', "NA")
        if hash != sign:
            userid = None
    id = int(id)
    
    if not event or event[1] <= id:
      yield ""
      return
    myevent = event
    eventid = myevent[1]
    levent = [x[1] for x in myevent[0] if x[0] > id and (x[2] == "N" or (userid and x[2] == int(userid)))]
    levent = set(levent)
    #yield "eval://Error no id : %s\n" % str(myevent) + "\n".join(levent) + "\n!%s" % eventid
    yield "\n" + "\n".join(levent) + "\n!%s" % eventid

application = bottle.default_app()
