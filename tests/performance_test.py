import os, sys
from utils.json_rpc_client import JsonRpcClient
from loguru import logger

from locust import task, HttpUser, constant_pacing

from locust.exception import StopUser

import gevent
from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import StatsCSVFileWriter, StatsCSV, stats_history, stats_printer
from locust.log import setup_logging
import gevent
import requests
import pytest

class BlockChainUser(HttpUser):
    wait_time = None
    block = None
    jrpc_client = None

    def on_start(self):
        if self.block is None:
            self.block = self.jrpc_client.call("eth_blockNumber")['result']

    @task
    def get_block_by_number(self):
        block_number = int(self.block, 16)
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [block_number, True],
            "id": 1
        }

        with self.client.post(f'{self.host}', json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure("Failed to get block by number: " + block_number)

def run_locust(configuration, client, number_of_users=100, spawn_rate=10, test_duration=60, scenario_name="locust"):
    # Backup sys.argv
    original_argv = sys.argv
    sys.argv = sys.argv[:1]
    
    wait_start = float(configuration['wait_start'])
    wait_end = float(configuration['wait_end'])

    # Set wait_time dynamically based on config
    BlockChainUser.wait_time = between(wait_start, wait_end)
    BlockChainUser.jrpc_client = client
    BlockChainUser.host = configuration['base_url']

    # Create a Locust environment
    env = Environment(user_classes=[BlockChainUser])
    env.create_local_runner()

    # Start a Web UI for monitoring
    env.create_web_ui(configuration['web_ui_host'], int(configuration['web_ui_port']))

    # generate CSV report
    stats_path =  "reports/" + scenario_name
    csv_writer = StatsCSVFileWriter(
        environment=env,
        base_filepath=stats_path,
        full_history=True,
        percentiles_to_report=[90.0, 95.0]
    )
    gevent.spawn(csv_writer.stats_writer)

    # start a greenlet that periodically outputs the current stats
    gevent.spawn(stats_printer(env.stats))

    # start a greenlet that saves current stats to history
    gevent.spawn(stats_history, env.runner)

    # Start the test
    env.runner.start(number_of_users, spawn_rate=spawn_rate)

    # Stop the test after 1 minute
    gevent.spawn_later(test_duration, lambda: env.runner.quit())

    # Wait for the greenlets
    env.runner.greenlet.join()

    # Download the HTML report
    report_url = f"http://{configuration['web_ui_host']}:{configuration['web_ui_port']}/stats/report?theme=dark"
    report_path = f"reports/{scenario_name}_report.html"
    response = requests.get(report_url)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'wb') as f:
        f.write(response.content)

    env.web_ui.stop()
    return env


@pytest.mark.performance
def test_performance_1(client, configuration):
    # Backup sys.argv
    original_argv = sys.argv
    sys.argv = sys.argv[:1]  # Reset sys.argv to prevent locust from parsing pytest arguments

    try:
        env = run_locust(configuration, client, 
                        number_of_users=int(configuration["scenario_1_users"]), 
                        spawn_rate=int(configuration["spawn_rate"]), 
                        test_duration=int(configuration["scenario_1_duration"]), 
                        scenario_name="scenario1")
        logger.info(env.stats.total)
        assert env.stats.total.avg_response_time < 60
        assert env.stats.total.num_failures == 0
        assert env.stats.total.get_response_time_percentile(0.95) < 100
    finally:
        # Restore original sys.argv
        sys.argv = original_argv


@pytest.mark.performance
def test_performance_2(client, configuration):
    # Backup sys.argv
    original_argv = sys.argv
    sys.argv = sys.argv[:1]  # Reset sys.argv to prevent locust from parsing pytest arguments
    try:
        env = run_locust(configuration, client, 
                        number_of_users=int(configuration["scenario_2_users"]), 
                        spawn_rate=int(configuration["spawn_rate"]), 
                        test_duration=int(configuration["scenario_2_duration"]), 
                        scenario_name="scenario2")
        logger.info(env.stats.total)
        assert env.stats.total.avg_response_time < 600
        assert env.stats.total.num_failures == 0
        assert env.stats.total.get_response_time_percentile(0.95) < 100
    finally:
        # Restore original sys.argv
        sys.argv = original_argv