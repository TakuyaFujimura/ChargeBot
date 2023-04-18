#!/bin/bash
export SLACK_WEBHOOK_URL_FURO=""
cd ${HOME}/gitrepo/chargebot
source ./venv/bin/activate
python ./alert.py
