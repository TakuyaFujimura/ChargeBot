import datetime
import sys
import os
import subprocess
import argparse

from slack_sdk import WebhookClient

SLACK_WEBHOOK_URL_SLURM = os.environ["SLACK_WEBHOOK_URL_SLURM"]
SERVERADMIN_ID = os.environ["SERVERADMIN_ID"]


def main(args):
    now = datetime.datetime.now()
    if args.suspended_until is not None:
        if now < datetime.datetime.strptime(args.suspended_until, "%Y-%m-%d %H:%M:%S"):
            sys.exit(0)

    cmd = ["ssh", "lab-mrcompute01", "sinfo -R"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if len(result.stdout.splitlines()) > 1:
        if any(["STOP" not in x for x in result.stdout.splitlines()[1:]]):
            client = WebhookClient(SLACK_WEBHOOK_URL_SLURM)
            message = f":warning: <!subteam^{SERVERADMIN_ID}> Slurm is not normal. Please follow <https://www.notion.so/todalab/0c6b0040a41844408fea8b4b89c7b3e8?v=86497d48b35d43e2ac97849c49963c26&pvs=4|this instructions.>\n"
            message += str(now) + "\n"
            message += "Result of sinfo -R\n"
            message += "```"
            message += result.stdout
            message += "```"
            response = client.send(text=message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--suspended_until", type=str)
    args = parser.parse_args()
    main(args)
