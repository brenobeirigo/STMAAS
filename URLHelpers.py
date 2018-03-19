from urllib.request import Request as RequestURL, urlopen
from urllib.error import  URLError
from time import sleep
from URLHelpers import *

class URLHelpers:

    @staticmethod
    def read_url(url, trials, timeout):
        response = None
        for x in range(0, trials):  # try 4 times
            req = RequestURL(url)
            try:
                # msg.send()
                # put your logic here
                response = urlopen(req)
                return response.read()
            except:
                pass
            if response is None:
                print("Waiting %d seconds..." % timeout)
                sleep(timeout)  # wait for 2 seconds before trying to fetch the data again
            else:
                break