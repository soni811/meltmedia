import logging
import json
import requests


class PicardClient(object):

    def __init__(self):
        """
        Contains methods used to query Epsilon.
        """

    def send_to_picard(self, schema_url, form_data, headers=None, **kwargs):
        r = None

        if not headers:
            headers = self.create_headers()

        r = requests.post(schema_url, form_data, headers=headers, **kwargs)

        # Able to reach Picard, but request failed
        if r.status_code == 400:
            raise PicardClientException(r.text)
        # Unable to reach picard
        if r.status_code is not 200:
            raise PicardClientException("Unable to Post to Picard")

        # Received a valid response from Picard. Return the data received.
        return json.loads(r.text)

    def create_headers(self, referer="qa.picardclient.com"):
        return {"Referer": referer}


class PicardClientException(Exception):
    def __init__(self, arg):
        self.msg = arg