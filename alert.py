import argparse
import datetime
import os
import subprocess
from pathlib import Path

import pandas as pd
from slack_sdk import WebhookClient

SLACK_WEBHOOK_URL_FURO = os.environ["SLACK_WEBHOOK_URL_FURO"]
BALANCE_LOG_PATH = "data/balance_log"
USERWISE_DIR = "data/userwise"


def get_name_point(text):
    return [text.split()[0], int(text.split()[-2].replace(",", ""))]


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

    # Announce via slack ###############################################
    ## Daily
    if args.daily_announce:
        client = WebhookClient(SLACK_WEBHOOK_URL_FURO)
        if balance < args.balance:
            message = "<!channel>\n"
            message += ":warning: *There are few points left.*\n"
            message += f"Balance: {balance:18,} p"
        else:
            client = WebhookClient(SLACK_WEBHOOK_URL_FURO)
            message = f"Balance: {balance:18,} p"
        response = client.send(text=message)
    ## Monthly
    if args.monthly_announce:
        client = WebhookClient(SLACK_WEBHOOK_URL_FURO)
        import json

        import pandas as pd
        from dateutil.relativedelta import relativedelta

        ### Get info
        lastmonth = today - relativedelta(months=1)
        df_new = pd.read_csv(f"{USERWISE_DIR}/{today}{args.prefix}.csv")
        df_old = pd.read_csv(f"{USERWISE_DIR}/{lastmonth}{args.prefix}.csv")
        df_diff = df_new.copy()
        df_diff["Point"] -= df_old["Point"]
        with open("data/userdict.json", "r") as f:
            userdict = json.load(f)
        ### Announce
        total_usage = df_diff["Point"].sum()
        message = f":owl:*Monthly Usage ({lastmonth} to {today})*\n"
        message += f"*Total usage: {total_usage:18,} p*\n"
        message += f"*Userwise usage:*\n"
        message += "<https://docs.google.com/spreadsheets/d/1_wLEEGqrHAu2SMJfbTG5mmiXAe8P9kBwfxMQ2eWnYIo/edit?resourcekey#gid=32992617|Please report your usage.>\n"
        message += "```"  # code block
        for row in df_diff.itertuples():
            if row.Point == 0:
                continue
            if row.User in userdict:
                user = userdict[row.User]
            else:
                user = row.User
            message += f"{user}: {row.Point:,} pt\n"
        message += "```"  # code block
        response = client.send(text=message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--balance", type=int, default=5000)
    parser.add_argument("--daily_announce", action="store_true")
    parser.add_argument("--monthly_announce", action="store_true")
    parser.add_argument("--balance_log", action="store_true")
    parser.add_argument("--userwise_log", action="store_true")
    parser.add_argument("--prefix", type=str, default="")
    args = parser.parse_args()
    main(args)
