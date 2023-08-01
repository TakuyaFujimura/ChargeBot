import argparse
import datetime
import os
import subprocess
from pathlib import Path

import pandas as pd
from slack_sdk import WebhookClient

SLACK_WEBHOOK_URL_FURO = os.environ["SLACK_WEBHOOK_URL_FURO"]
BALANCE_LOG_PATH = "data/balance_log.csv"
USERWISE_DIR = "data/userwise"


def get_name_point(text):
    return [text.split()[0], int(text.split()[-2].replace(",", ""))]


def update_balance_log(balance, today):
    df = pd.read_csv(BALANCE_LOG_PATH)
    new_row = {
        "Date": today,
        "Balance": balance,
    }
    new_df = pd.concat([df, pd.DataFrame([new_row])])
    new_df.to_csv(BALANCE_LOG_PATH, index=False)


def update_userwise_log(charge_info, today):
    user_point_dict = {"User": [], "Point": []}
    for i in range(5, len(charge_info) - 1):
        name, point = get_name_point(charge_info[i])
        user_point_dict["User"].append(name)
        user_point_dict["Point"].append(point)
    df = pd.DataFrame(user_point_dict)
    """
    for old_data in sorted(Path(USERWISE_DIR).glob("*.csv"))[:-n_latest]:
        old_data.unlink()
    """
    df.to_csv(f"{USERWISE_DIR}/{today}.csv", index=False)


if __name__ == "__main__":
    today = datetime.date.today()

    parser = argparse.ArgumentParser()
    parser.add_argument("--balance", type=int, default=5000)
    args = parser.parse_args()

    # exec charge2 and obtain stdout
    cmd = ["ssh", "furo", "/center/local/bin/charge2"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    charge_info = result.stdout.splitlines()

    # get balance
    balance = get_name_point(charge_info[2])[-1]
    # Alert by Slack
    client = WebhookClient(SLACK_WEBHOOK_URL_FURO)
    if balance < args.balance:
        # alert
        message = "<!channel>\n"
        message += ":warning: *There are few points left.*\n"
        message += f"Balance: {balance:18} p"
    else:
        # daily log
        client = WebhookClient(SLACK_WEBHOOK_URL_FURO)
        message = f"Balance: {balance:18} p"
    response = client.send(text=message)

    update_balance_log(balance, today)
    update_userwise_log(charge_info, today)
