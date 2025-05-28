#!/bin/bash

# Default Enclave Name
ENCLAVE_NAME="local-eth-dev"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ETH_PACKAGE_DIR="${SCRIPT_DIR}/../ethereum-package"
ETH_PACKAGE_REPO="https://github.com/dmitriy-b/ethereum-package.git"
ETH_PACKAGE_BRANCH="feat/el-proxy"

# Function to display usage
usage() {
    echo "Usage: $0 {start|stop|update-submodule}"
    exit 1
}

# Check if at least one argument is provided
if [ "$#" -ne 1 ]; then
    usage
fi

COMMAND=$1

# Ensure Kurtosis is installed
if ! command -v kurtosis &> /dev/null
then
    echo "Kurtosis CLI could not be found. Please install it first."
    echo "Follow instructions at https://docs.kurtosis.com/install"
    exit 1
fi

# Ensure git is installed
if ! command -v git &> /dev/null
then
    echo "git could not be found. Please install it first."
    exit 1
fi


start_enclave() {
    echo ">>> Starting Kurtosis enclave: ${ENCLAVE_NAME}"

    # Check if ethereum-package directory exists and is a git submodule
    if [ -d "${ETH_PACKAGE_DIR}/.git" ] && git -C "${SCRIPT_DIR}/.." submodule status "${ETH_PACKAGE_DIR}" | grep -q "^[+-]"; then
        echo ">>> Ethereum-package submodule found. Updating..."
        git -C "${SCRIPT_DIR}/.." submodule update --init --recursive "${ETH_PACKAGE_DIR}"
        # Ensure correct branch
        (cd "${ETH_PACKAGE_DIR}" && git checkout "${ETH_PACKAGE_BRANCH}" && git pull origin "${ETH_PACKAGE_BRANCH}")
    elif [ -d "${ETH_PACKAGE_DIR}" ] && [ ! -d "${ETH_PACKAGE_DIR}/.git" ]; then
        echo ">>> Warning: ${ETH_PACKAGE_DIR} exists but is not a git submodule."
        echo ">>> Please remove it or initialize it as a submodule manually."
        # Optionally, you could offer to remove it and re-clone as submodule here.
    else
        echo ">>> Ethereum-package submodule not found. Cloning..."
        git -C "${SCRIPT_DIR}/.." submodule add -b "${ETH_PACKAGE_BRANCH}" --name ethereum-package "${ETH_PACKAGE_REPO}" "ethereum-package"
        git -C "${SCRIPT_DIR}/.." submodule update --init --recursive "${ETH_PACKAGE_DIR}"
    fi

    echo ">>> Attempting to remove existing enclave (if any)..."
    kurtosis enclave rm "${ENCLAVE_NAME}" -f 2>/dev/null || echo ">>> Couldn't delete, perhaps it's the first run or already removed."

    echo ">>> Running Kurtosis package..."
    # Ensure we are in the root of the main project for Kurtosis to resolve paths correctly
    cd "${SCRIPT_DIR}/.."
    kurtosis run "${ETH_PACKAGE_DIR##*/}" --args-file "${ETH_PACKAGE_DIR##*/}/minimal.yaml" --enclave "${ENCLAVE_NAME}"
    echo ">>> Kurtosis package started in enclave: ${ENCLAVE_NAME}"
}

stop_enclave() {
    echo ">>> Stopping Kurtosis enclave: ${ENCLAVE_NAME}"
    kurtosis enclave rm "${ENCLAVE_NAME}" -f
    echo ">>> Kurtosis enclave ${ENCLAVE_NAME} stopped."
}

update_submodule_only() {
    echo ">>> Updating ethereum-package submodule..."
    if [ -d "${ETH_PACKAGE_DIR}/.git" ] && git -C "${SCRIPT_DIR}/.." submodule status "${ETH_PACKAGE_DIR}" | grep -q "^[+-]"; then
        git -C "${SCRIPT_DIR}/.." submodule update --remote --merge "${ETH_PACKAGE_DIR}"
        (cd "${ETH_PACKAGE_DIR}" && git checkout "${ETH_PACKAGE_BRANCH}" && git pull origin "${ETH_PACKAGE_BRANCH}")
        echo ">>> Submodule updated and checked out to ${ETH_PACKAGE_BRANCH}."
    elif [ ! -d "${ETH_PACKAGE_DIR}" ]; then
        echo ">>> Ethereum-package submodule not found. Cloning..."
        git -C "${SCRIPT_DIR}/.." submodule add -b "${ETH_PACKAGE_BRANCH}" --name ethereum-package "${ETH_PACKAGE_REPO}" "ethereum-package"
        git -C "${SCRIPT_DIR}/.." submodule update --init --recursive "${ETH_PACKAGE_DIR}"
    else
        echo ">>> ${ETH_PACKAGE_DIR} exists but does not seem to be a correctly initialized submodule."
        echo ">>> Try 'git submodule init' and 'git submodule update', or remove the directory and run this command again."
    fi
}


case "$COMMAND" in
    start)
        start_enclave
        ;;
    stop)
        stop_enclave
        ;;
    update-submodule)
        update_submodule_only
        ;;
    *)
        usage
        ;;
esac

exit 0 