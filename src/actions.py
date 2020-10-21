import api

def connect(ip):
    api.enter_cmd("{/}connect " + api.escape(ip))
