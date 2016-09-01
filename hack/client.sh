#!/bin/sh

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH=${CUR_DIR}/../third_party/cmdsignature
${CUR_DIR}/../client/client.py "$@"
