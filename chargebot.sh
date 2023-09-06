#!/bin/bash
#export SLACK_WEBHOOK_URL_FURO=""
cd ${HOME}/gitrepo/chargebot
source ./venv/bin/activate
python ./alert.py --balance 50000 --daily_announce --balance_log --userwise_log
