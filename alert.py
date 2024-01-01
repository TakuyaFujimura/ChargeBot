import argparse
import datetime
import json
import os
import subprocess
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import relativedelta
from slack_sdk import WebhookClient

SLACK_WEBHOOK_URL_FURO = os.environ["SLACK_WEBHOOK_URL_FURO"]
BALANCE_LOG_PATH = "data/balance_log"
USERWISE_DIR = "data/userwise"


def get_name_point(text):
    return [text.split()[0], int(text.split()[-2].replace(",", ""))]


def to_dict(df):
    return dict(zip(df["User"], df["Point"]))


def update_balance_log(balance, today, filepath):
    df = pd.read_csv(filepath)
    new_row = {
        "Date": today,
        "Balance": balance,
    }
    new_df = pd.concat([df, pd.DataFrame([new_row])])
    new_df.to_csv(filepath, index=False)


def update_userwise_log(charge_info, filepath):
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
    df.to_csv(filepath, index=False)


def get_user_diff(today, months, days, prefix=""):
    ### Get info
    user_diff_dict = {}
    with open("data/userdict.json", "r") as f:
        userdict = json.load(f)
    lastday = today - relativedelta(months=months, days=days)
    dict_new = to_dict(pd.read_csv(f"{USERWISE_DIR}/{today}{prefix}.csv"))
    dict_old = to_dict(pd.read_csv(f"{USERWISE_DIR}/{lastday}{prefix}.csv"))
    total_usage = 0
    for user_id, user_pt in dict_new.items():
        if user_pt == 0:
            continue
        # point
        if user_id in dict_old:
            diff_pt = user_pt - dict_old[user_id]
        else:
            diff_pt = user_pt  # new member
        total_usage += diff_pt
        if diff_pt == 0:
            continue
        # user name
        if user_id in userdict:
            user = userdict[user_id]
        else:
            user = user_id
        # store into dict
        user_diff_dict[user] = diff_pt
    return total_usage, user_diff_dict, lastday


def alert_user(user_diff_dict, user_threshold):
    is_big_difference = False
    message = (
        "Big difference:\n"  # <!subteam^{SERVERADMIN_ID}> Please contact the user.\n"
    )
    userwise_message = "```"
    for user, diff_pt in user_diff_dict.items():
        if diff_pt > user_threshold:
            is_big_difference = True
            userwise_message += f"{user}: {diff_pt:,} p, "
    userwise_message += "```"
    message += userwise_message

    if is_big_difference:
        return message
    else:
        return ""


def message_balance(balance, balance_threshold):
    if balance < balance_threshold:
        message = "<!channel>\n"
        message += ":warning: *There are few points left.*\n"
        message += f"Balance: {balance:18,} p\n"
    else:
        message = f"Balance: {balance:18,} p\n"
    return message


def message_user(user_diff_dict):
    userwise_message = "```"  # code block
    for user, diff_pt in user_diff_dict.items():
        userwise_message += f"{user}: {diff_pt:,} pt\n"
    userwise_message += "```"  # code block
    return userwise_message


def main(args):
    today = datetime.date.today()

    # Get info ###############################################
    ## Exec charge2 and obtain stdout
    cmd = ["ssh", "furo", "/center/local/bin/charge2"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    charge_info = result.stdout.splitlines()
    ## Get the balance
    balance = get_name_point(charge_info[2])[-1]
    ## Log data
    if args.balance_log:
        update_balance_log(balance, today, BALANCE_LOG_PATH + args.prefix + ".csv")
    if args.userwise_log:
        update_userwise_log(charge_info, f"{USERWISE_DIR}/{today}{args.prefix}.csv")
    ## Get user_diff_dict
    if args.announce_type == "daily":
        total_usage, user_diff_dict, lastday = get_user_diff(today, months=0, days=1)
    elif args.announce_type == "monthly":
        total_usage, user_diff_dict, lastday = get_user_diff(
            today, months=1, days=0, prefix=args.prefix
        )

    # Announce via slack ###############################################
    client = WebhookClient(SLACK_WEBHOOK_URL_FURO)
    if args.announce_type == "daily":
        message = message_balance(balance, args.threshold)
        message += "\n"
        message += alert_user(user_diff_dict, args.user_threshold)
    elif args.announce_type == "monthly":
        message = f":owl:*Monthly Usage ({lastday} to {today})*\n"
        message += f"*Total usage: {total_usage:18,} p*\n"
        message += f"*Userwise usage:*\n"
        message += "<https://docs.google.com/spreadsheets/d/1_wLEEGqrHAu2SMJfbTG5mmiXAe8P9kBwfxMQ2eWnYIo/edit?resourcekey#gid=32992617|Please report your usage.>\n"
        message += message_user(user_diff_dict)

    response = client.send(text=message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=int, default=10000)
    parser.add_argument("--user_threshold", type=int, default=10000)
    parser.add_argument("--announce_type", type=str)
    parser.add_argument("--balance_log", action="store_true")
    parser.add_argument("--userwise_log", action="store_true")
    parser.add_argument("--prefix", type=str, default="")
    args = parser.parse_args()
    main(args)
