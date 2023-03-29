import argparse
import csv
import datetime
import os
import subprocess

import pandas as pd
from slack_sdk import WebClient

SLACK_TOKEN_FURO = os.environ["SLACK_TOKEN_FURO"]
BALANCE_LOG_PATH = "data/balance_log.csv"
USERWISE_DIR = "data/userwise"


def get_name_point(text):
    return [text.split()[0], int(text.split()[-2].replace(",", ""))]


def update_balance_log(balance, today, n_latest=8):
    df = pd.read_csv(BALANCE_LOG_PATH)
    df = df.iloc[-(n_latest - 1) :]
    new_row = {
        "Date": today,
        "Balance": balance,
    }
    breakpoint()
    new_df = pd.concat([df, pd.DataFrame([new_row])])
    new_df.to_csv(BALANCE_LOG_PATH, index=False)


def update_userwise_log(charge_info, today):
    user_list = []
    point_list = []
    user_point_dict = {"User": [], "Point": []}
    for i in range(5, len(charge_info) - 1):
        name, point = get_name_point(charge_info[i])
        user_point_dict["User"].append(name)
        user_point_dict["Point"].append(point)
    df = pd.DataFrame(user_point_dict)
    df.to_csv(f"{USERWISE_DIR}/{today}.csv", index=False)


if __name__ == "__main__":
    today = datetime.date.today()

    parser = argparse.ArgumentParser()
    parser.add_argument("--balance", type=int, default=1000)
    args = parser.parse_args()

    # exec charge2 and obtain stdout
    cmd = ["ssh", "furo", "/center/local/bin/charge2"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    charge_info = result.stdout.splitlines()

    # get balance
    balance = get_name_point(charge_info[2])[-1]
    # Alert by Slack
    if balance < args.balance:
        client = WebClient(SLACK_TOKEN_FURO)
        res = client.conversations_open(users="U038N91UQ2K")
        dm_id = res["channel"]["id"]
        client.chat_postMessage(
            channel=dm_id, text=f"There are few points left.\nBalance: {balance}"
        )
    update_balance_log(balance, today)
    update_userwise_log(charge_info, today)
