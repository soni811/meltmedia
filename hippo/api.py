import datetime
import copy
import flask
import json
import logging
import os
import time
import uuid

from flask_cors import CORS, cross_origin
from hippo.action_field_configuration import actions
from hippo.schemas.validate_schemas import validate_hippo_request, RequestValidationError
from hippo.util import GITHUB_DIRECTORY, get_config_list, get_configuration_from_github, remove_basic_auth, get_all_github_branches, URL, RECIPIENTS, GITHUB_REPO, \
    GITHUB_TOKEN, HIPPO_ENVIRONMENT,GITHUB_BRANCH, START_DATE, START_TIME, HIPPO_PORT, RHINO_HOST, PROJECT, BRANCH, \
    WATERING_HOLE_CLIENT,HIPPO_SITES_PATH
from hippo.request_thread import request_queue

logger = logging.getLogger("Hippo API")

start_date = datetime.datetime.now()
start_time = time.time()

@cross_origin()
def status():
    """Returns 200, {"status": "Running", <METADATA>}"""
    data = {
        "status": "Running",
        "client": flask.current_app.config[WATERING_HOLE_CLIENT],
        "environment": flask.current_app.config[HIPPO_ENVIRONMENT],
        "branch": flask.current_app.config[GITHUB_BRANCH],
        "port": flask.current_app.config[HIPPO_PORT],
        "started": f"{start_date}",
        "run_time": f"{datetime.timedelta(seconds=time.time() - start_time)}",
        "queue_size": f"{request_queue.qsize()}",
        "version": "2.0.1"
    }
    return flask.json.dumps(data), 200

@cross_origin()
def start_capture():

    try:
        # Grab the data from the request
        data = flask.request.json
        logger.info(f"Starting Screenshot request from {flask.request.host}. Headers: {flask.request.headers}")

        # Verify that the request data is properly formatted by checking it against the request schema
        validate_hippo_request(data)

        # Parse out build_id or create one if not part of the request
        if data.get("build_id"):
            build_id = data.get("build_id")
        else:
            build_id = uuid.uuid4().urn.split("-")[4].upper() # JB
            data["build_id"] = build_id

        data[START_DATE] = time.strftime("At %H:%M on %A the %-d of %B %Y", time.localtime())
        data[START_TIME] = time.time()

        # Add the request data to the queue
        request_queue.put(data)

        # Clean up the request data before logging it out
        clean_data = copy.deepcopy(data)
        clean_data[URL] = remove_basic_auth(clean_data[URL])
        if clean_data.get(RECIPIENTS):
            clean_data[RECIPIENTS] = "* redacted *"
        logger.info(f"Adding request to Queue: {clean_data}. Queue Size: {request_queue.qsize()}")

        rhino_url = f"http://{flask.current_app.config[RHINO_HOST]}/#/brand/{data[PROJECT]}/branch/{data[BRANCH]}/build/{build_id}"
        # Return the successful response!
        response = {"success": True, "build_id": build_id, "rhino_url": rhino_url}
        return str(flask.json.dumps(response)), 200

    except RequestValidationError as request_exception:
        # TODO: Look into the error output here. Should not need to pass the error type around as a code
        msg = f"Unable to process incorrectly formatted request. " \
              "Error: {request_exception.message}"
        logger.warn(f"[{request_exception.code}] {msg} | " f"{request_exception.to_dict()}")
        return flask.json.dumps({"errors": msg}), 400
    except ValueError as e:
        return flask.json.dumps({"errors": "Expected valid JSON body. Error: " + e.message}), 400

@cross_origin()
def get_configs():
    """
    Checks remote repo for list of configs
    """
    try:
        projects = []
        github_branch = flask.request.args.get('branch')

        if not github_branch:
            github_branch = "develop" if flask.current_app.config[HIPPO_ENVIRONMENT] not in ["prod"] else "production"

        headers = {"Authorization": f"token {flask.current_app.config[GITHUB_TOKEN]}"}
        config_files = get_config_list(flask.current_app.config[GITHUB_REPO], github_branch, "sites", headers, flask.current_app.config.get(GITHUB_DIRECTORY))

        logger.info(f"Config files {config_files}")
        # - Iterate through the returned files and format them into a {'project': <project>, 'branch': <branch>} format
        for config_file in config_files:
            # Only add json files to the projects list
            if ".json" in config_file:
                # Parse out the the project (before the underscore)
                project = config_file.split("_")[0]
                project = project.split(".json")[0]
                # format and append the config data to the projects list
                projects.append(project)

        return json.dumps(projects), 200

    except Exception as e:
        message = f"Unexpected Error occurred while gathering Hippo configuration data: {e}"
        return flask.json.dumps({"errors": message}), 500

@cross_origin()
def get_branches():
    try:
        import pdb; pdb.set_trace()
        all_branches = get_all_github_branches(flask.current_app.config[GITHUB_TOKEN], HIPPO_SITES_PATH)
        # Removing the develop branch from the list so the front end doesn't display it.
        all_branches.remove("develop")
        return json.dumps(all_branches), 200

    except Exception as e:
        message = f"Unexpected Error occurred while attempting to get list of branches from remote: {e}"
        return flask.json.dumps({"errors": message}), 500


@cross_origin()
def get_single_config(project, branch):
    try:
        env = flask.current_app.config[HIPPO_ENVIRONMENT]
        token = flask.current_app.config[GITHUB_TOKEN]
        git_repo = flask.current_app.config[GITHUB_REPO]

        config = get_configuration_from_github(project, branch, env, token, git_repo)

        return json.dumps(config), 200

    except Exception as e:
        message = f"Unexpected Error occurred while getting the Hippo configuration data for {project} - {branch}: {e}"
        return flask.json.dumps({"message": message, "error": str(e)}), 500

@cross_origin()
def get_actions():
    try:
        return json.dumps(actions), 200
    except Exception as e:
        message = f"Unexpected Error occurred while cathering the Action Configuration data | {e}"
        return flask.json.dumps({"message": message, "error": str(e)}), 500


def register(app):
    """Add endpoints"""
    """
    Trying to set the allowed origin to localhost and 0.0.0.0 but it's not working so now it's set to *
    http://flask-cors.corydolphin.com/en/latest/api.html#extension
    """
    CORS(app, resources={r"*": {"origins": "*"}})
    app.add_url_rule("/status", "status_no_slash", status, methods=["GET"])
    app.add_url_rule("/status/", "status", status, methods=["GET"])
    app.add_url_rule("/capture", "start_capture_no_slash", start_capture, methods=["POST"])
    app.add_url_rule("/capture/", "start_capture", start_capture, methods=["POST"])
    app.add_url_rule("/configs", "get_configs_no_slash", get_configs, methods=["GET"])
    app.add_url_rule("/configs/", "get_configs", get_configs, methods=["GET"])
    app.add_url_rule("/config/<project>/<branch>", "get_a_single_config_no_slash", get_single_config, methods=["GET"])
    app.add_url_rule("/config<project>/<branch>/", "get_a_single_config", get_single_config, methods=["GET"])
    app.add_url_rule("/tactics","get_branches",get_branches, methods=["GET"])
    app.add_url_rule("/actions", "get_actions_no_slash", get_actions, methods=["GET"])
    app.add_url_rule("/actions/", "get_actions", get_actions, methods=["GET"])