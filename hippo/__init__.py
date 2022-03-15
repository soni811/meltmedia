#!/usr/bin/env python3
from flask import Flask
import hippo.util as c
import logging
import werkzeug.serving

from hippo.request_thread import Request

log = c.create_logger(__name__)

app = Flask(__name__)
hippo_config = None

REQUEST_THREAD_MAX = 2


def run(config):
    """
    Update app.config, register endpoints, and start server
    :param
        - config: Dict of the hippo environment configuration
    """
    from hippo import api
    app.config.update(**config)

    # - Make the requests library stay quiet
    logging.getLogger("requests").setLevel(logging.WARNING)

    log.info("Registering Endpoints")
    api.register(app)

    environment = config.get(c.HIPPO_ENVIRONMENT)

    for i in range(REQUEST_THREAD_MAX):
        request_thread = Request(config)
        request_thread.setDaemon(True)
        request_thread.start()

    log.info("Starting Server")
    if environment == "local":
        werkzeug.serving.run_simple(
            '0.0.0.0', app.config[c.HIPPO_PORT], app,
            threaded=True, use_reloader=True, use_debugger=True, use_evalex=True)
    else:
        app.run('0.0.0.0', app.config[c.HIPPO_PORT], threaded=True)
