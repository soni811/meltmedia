#!/usr/bin/env python3
import argparse
import copy
import hippo
import json
import logging
import os
from hippo import util
from logging import config

ROOT = os.path.abspath(os.path.dirname(__file__))

LOG_CONFIG = '{0}/etc/logging.json'.format(ROOT)
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s %(message)s'
LOG_DATE = '%Y-%m-%d %I:%M:%S %p'
ENV_VARS = [util.GRAYLOG_FACILITY, util.GRAYLOG_LEVEL, util.HIPPO_S3_BUCKET, util.RHINO_HOST, util.HIPPO_ENVIRONMENT,
            util.HIPPO_PORT, util.GITHUB_REPO, util.GITHUB_TOKEN, util.GITHUB_DIRECTORY, util.ALLOW_BASE_CAPTURE,
            util.MANDRILL_KEY, util.HIPPO_AEM_USERNAME, util.HIPPO_AEM_PASSWORD, util.PFIZER_USERNAME,
            util.PFIZER_PASSWORD, util.GITHUB_BRANCH, util.AWS_KEY, util.AWS_SECRET,
            util.WATERING_HOLE_CLIENT, util.SAUCE_LABS_USERNAME, util.SAUCE_LABS_ACCESS_KEY]

logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.CRITICAL)

def get_args():
    """Setup argparser and return args"""
    parser = argparse.ArgumentParser(description="Let's take some screenshots!")

    parser.add_argument(
        "-e", "--hippo-environment", help="Environment: ['local', 'develop', 'prod']",
        choices=["local", "develop", "prod"])

    parser.add_argument(
        "-b", "--hippo-s3-bucket", help="S3 Bucket Name")

    parser.add_argument(
        "-r", "--hippo-rhino-host", help="Rhino Host to use for output")

    parser.add_argument(
        "-p", "--hippo-port", help="The port number that Hippo runs on")

    parser.add_argument(
        '-au', '--hippo-aem-username', help='AEM Prod Author username')

    parser.add_argument(
        '-ap', '--hippo-aem-password', help='AEM Prod Author password')

    parser.add_argument(
        "-m", "--hippo-mandrill-key", help="The mandrill key that Hippo will use to send results emails")

    parser.add_argument(
        "-gl", "--graylog-level", help="The level of logging sent to Graylogs",
        choices=["INFO", "WARN", "ERROR", "CRITICAL"])

    parser.add_argument(
        "-gr", "--github-repo", help="The Github repo in which the Hippo configs live")

    parser.add_argument(
        "-gb", "--github-branch", help="The branch under which to search for configurations on github")

    parser.add_argument(
        "-gt", "--github-token", help="The Github repo in which the Hippo configs live")

    parser.add_argument(
        "-gd", "--github-directory", help="The absolute path to the local hippo-sites github directory")

    parser.add_argument(
        "-c", "--watering-hole-client", help="The name of the Watering Hole client this this Hippo instance is running for")

    parser.add_argument(
        "-bc", "--allow-base-capture", action="store_true", default=None,
        help="If set, then Hippo will continue with base captures if there is no "
             "configuration file for the given project")

    parser.add_argument("-su", "--sauce-username", help="The username used to connect to Sauce Labs.")

    parser.add_argument("-sa", "--sauce-access-key", help="The access key used to connect to Sauce Labs.")

    return parser.parse_args()


def setup_logging(config):
    """Initialize logger with graylog config or default, use env vars if they exist"""
    if all(x in config for x in [util.GRAYLOG_FACILITY, util.GRAYLOG_LEVEL]):
        log_config = util.read_json_from_path(LOG_CONFIG)
        log_config["handlers"]["graylog"]["facility"] = os.environ[util.GRAYLOG_FACILITY]
        log_config["handlers"]["graylog"]["level"] = os.environ[util.GRAYLOG_LEVEL]
        logging.config.dictConfig(log_config)
    else:
        logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATE, level="INFO")


def setup_config(args):
    """
    Merge Hippo's default config with environment variables and argparse args, return config.
    Args override env vars which override default config.
    """
    merged_config = copy.deepcopy(util.DEFAULT_APP_CONFIG)

    # Merge in environment vars first
    for var in ENV_VARS:
        if var in os.environ and os.environ[var] != '':
            merged_config[var] = os.environ[var]

    # Finally, merge in arg vars
    arg_dict = vars(args)
    for key, value in arg_dict.items():
        if value:
            merged_config[key.upper()] = value

    # remove empty string values
    merged_config = {k: v for k, v in merged_config.items() if v != ''}

    # Make sure port is an integer. Command line arguments come through
    # as strings.
    if util.HIPPO_PORT in merged_config:
        merged_config[util.HIPPO_PORT] = int(merged_config[util.HIPPO_PORT])

    # TODO: Check the configuration against a schema?
    return merged_config


def main():
    """Set config, initialize logger and run the app"""
    import hippo
    args = get_args()
    hippo_config = setup_config(args)
    logger.info("Starting Hippo Service using the following configuration:\n"
                "ENV: {}\n"
                "REPO: {}\n"
                "BRANCH: {}\n"
                "CLIENT: {}\n"
                "BUCKET: {}\n".format(hippo_config[util.HIPPO_ENVIRONMENT], hippo_config[util.GITHUB_REPO],
                                      hippo_config[util.GITHUB_BRANCH], hippo_config[util.WATERING_HOLE_CLIENT],
                                      hippo_config[util.HIPPO_S3_BUCKET]))
    setup_logging(hippo_config)
    hippo.run(hippo_config)


if __name__ == "__main__":
    main()
