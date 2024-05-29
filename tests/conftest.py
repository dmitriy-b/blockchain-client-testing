from loguru import logger
import os, sys
from dotenv import load_dotenv
from utils.json_rpc_client import JsonRpcClient

import configparser

import pytest

def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="general",
        help="Environment to run tests against")


@pytest.fixture(scope="session")
def configuration(request):
    env = request.config.getoption("--env")
    cfg = configparser.ConfigParser()
    cfg.read("pytest.ini")
    if env not in cfg:
        # workaround for running tests inside docker
        cfg.read("../pytest.ini")
        if env not in cfg:
            raise ValueError(f"Invalid environment: {env}")
    for k, v in cfg["general"].items():
        cfg[env][k] = v
    # read from .env file
    load_dotenv()
    for k, v in os.environ.items():     
        for key in cfg[env].keys():
            # to store variables like GENERAL_BASE_URL
            if str(k).lower().startswith(f"{env}_"):
                cfg[env][str(k).lower().replace(f"{env}_", "")] = v
            if str(k).lower() == str(key).lower():
                cfg[env][str(k).lower()] = v
    # manky patching to pass config to teardown step    
    request.config.configuration = cfg[env]
    request.config.env_name = env
    cfg[env]["env_name"] = env
    cfg[env].context = {}
    logger.remove()
    logger.add(sys.stdout, level=cfg[env]['log_stdout_level'])
    logger.add(f"reports/{cfg[env]['log_file_name']}.log", level=cfg[env]['log_file_level'])
    logger.debug("Updated configuration ...")
    return cfg[env]

@pytest.fixture(scope="session")
def client(configuration):
    return JsonRpcClient(configuration["base_url"])