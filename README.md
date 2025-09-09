# blockchain-client-testing
[![Blockchain JSON-RPC Tests](https://github.com/dmitriy-b/blockchain-client-testing/actions/workflows/test-kurtosis.yml/badge.svg)](https://github.com/dmitriy-b/blockchain-client-testing/actions/workflows/test-kurtosis.yml)
# Blockchain JSON-RPC Tests

This project (PoC) includes a set of JSON-RPC tests for a etherium blockchain using Nethermind client. The tests are run with pytest and Locust for performance testing. The GitHub Actions pipeline automates the setup, execution, and reporting of these tests.

## Features
- The framework supports both integration and performance tests.
- Configuration with a single file (pytest.ini).
- Every configuration property can be overridden using environment variables.
- Rich logging and reporting.
- Fully automated CI pipeline, including caching jobs to speed up execution.


## Functional Tests
This repository includes functional tests to verify the correct operation of the client's JSON-RPC methods. The tests are created using Pytest as a test runner.

Location: tests/test_json_rpc.py

## Performance Tests
This repository includes performance tests and have been created using Locust framework. They use the `getBlockByNumber` endpoint for a selected block and simulate high load by multiple users on public JSON-RPC API. These tests check the response status, validate the average response time, and count the number of errors.

Location: tests/performance_test.py

### Using locust as library
Typically, performance tests with the Locust framework are run using the `locust` command. However, to facilitate easy switching between functional and performance scenarios, I decided to use Locust as a library and run the tests from within Pytest.

This approach has its own advantages and disadvantages.

Pros:
- Easy to manage tests using Pytest.
- Allows the use of Pytest fixtures to manipulate configuration and data.
Cons:
- Difficult to generate reports.
- Cannot pass arguments from the command line.
- Not all features of Locust may be available.

To generate HTML report within Pytest, we need to use the Web UI and download the report from it. While the Web UI is useful locally, it is less practical for CI. However, we still need to start the Web UI in CI because the report cannot be generated without it.

To address the issue of conflicting arguments between Pytest and Locust, I implemented a workaround:

```python
    # Backup sys.argv
    original_argv = sys.argv
    sys.argv = sys.argv[:1]  # Reset sys.argv to prevent locust from parsing pytest arguments
    try:
        # your locust test here 
    finally:
        # Restore original sys.argv
        sys.argv = original_argv
```
This solution ensures that Locust does not attempt to parse arguments intended for Pytest, allowing the tests to run smoothly with additional pytest arguments like
```
pytest -k "test_performance_1"
```

## Prerequisites

Before you start, ensure you have the following installed:

- Docker
- Docker Compose
- Python 3.8 or higher

## Installation and Setup

Follow these steps to set up your environment locally (in my case Ubuntu) and run the tests:

### 1. Clone the Repository

```bash
git clone https://github.com/your-repository/blockchain-json-rpc-tests.git
cd blockchain-json-rpc-tests
```

### 2. Set Up Python Environment
Create a virtual environment and install the required Python dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Install Docker and Docker Compose

#### Docker

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce
sudo usermod -aG docker $USER
```

#### Docker Compose
```bash
sudo curl -SL https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-linux-x86_64 --output docker-compose
sudo chmod +x docker-compose
sudo mv docker-compose /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
which docker-compose
docker-compose --version
```

### 4. Install Sedge
Download and install Sedge:

``` bash
curl -L https://github.com/NethermindEth/sedge/releases/download/v1.3.2/sedge-v1.3.2-linux-amd64 --output sedge
chmod +x sedge
sudo mv sedge /usr/local/bin/sedge
sudo ln -s /usr/local/bin/sedge /usr/bin/sedge
which sedge  # Verify the location of sedge
sedge version  # Check if sedge is executable
```

### 5. Set Up the Sedge Environment
Generate the necessary environment for the Nethermind client:

``` bash
sedge deps install
sedge generate --logging none -p $HOME full-node \
--map-all --no-mev-boost --no-validator \
--network chiado -c lighthouse:sigp/lighthouse:latest \
-e nethermind:nethermindeth/nethermind:master \
--el-extra-flag Sync.NonValidatorNode=true \
--el-extra-flag Sync.DownloadBodiesInFastSync=false \
--el-extra-flag Sync.DownloadReceiptsInFastSync=false \
--el-extra-flag JsonRpc.EnabledModules=[Eth,TxPool,Web3,Net,Health,Rpc,Debug] \
--cl-extra-flag checkpoint-sync-url=YOUR_ENDPOINT
```

### 6. Check Sedge Dependencies

``` bash
cp /home/runner/.env .
cp /home/runner/docker-compose.yml .
sedge deps check
```

### 7. Run Sedge
Start the Nethermind client:

``` bash
sedge run -p .
```

### 8. Wait for Synchronization
It needs some time to synchronize the network. We can use following script to check the state

``` bash
echo "Waiting for Nethermind to synchronize..."
while true; do
  if curl -s localhost:8545 > /dev/null; then
    break
  fi
  sleep 10
done
echo "Nethermind is up. Checking sync status..."
echo "Sending eth_syncing request..."
response=$(curl localhost:8545 -X POST -H "Content-Type: application/json" --data '{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "eth_syncing",
  "params": []
}')
echo "Response: $response"
while true; do
  response=$(curl -s localhost:8545 -X POST -H "Content-Type: application/json" --data '{
    "jsonrpc": "2.0",
    "id": 0,
    "method": "debug_getSyncStage",
    "params": []
  }')
  echo "Response: $response"
  if echo "$response" | grep -q '"currentStage":"WaitingForBlock"' || echo "$response" | grep -q '"currentStage":"Full"' || echo "$response" | grep -q '"currentStage":"StateNodes"'; then
    echo "Synchronization completed."
    break
  fi
  du -sh execution-data/
  sleep 20
done
```

### 9. Run Tests
Run the verification and performance tests:

Verification Scenario 1
``` bash
pytest tests/test_json_rpc.py
``` 

Performance Scenario 1
``` bash
LOG_STDOUT_LEVEL=ERROR pytest -k "test_performance_1"
```
For this scenario, we generate 1,000 users and execute the test for 60 seconds, resulting in approximately 200 RPS (requests per second). If we need to achieve a higher number of requests, we can adjust the `scenario_1_users` and `scenario_1_duration` variables in the `pytest.ini` file.


Performance Scenario 2
``` bash
LOG_STDOUT_LEVEL=ERROR pytest -k "test_performance_2"
```

For this scenario we generate 10,000 users, executes the test during 300 seconds and reached about 800 RPS on CI. As above, we can change `scenario_2_users` /  `scenario_2_duration` variable in `pytest.ini` to increase the number of requests.

Note. We can override any variable from `pytest.ini` by using environment variables. For example, `LOG_STDOUT_LEVEL` links to `log_stdout_level` from `[general]` section.
It is also possible to specify the section by starting pytest with `--env`, e.g. `--env=general`. 

### 10. Stop Sedge
Stop the Sedge environment:

``` bash
sedge -p $PWD down
```


## Test Reports
Functional and performance test reports can be downloaded from Github artifacts. (See example [here](https://github.com/dmitriy-b/blockchain-client-testing/actions/runs/9288030336/artifacts/1548747708)).

