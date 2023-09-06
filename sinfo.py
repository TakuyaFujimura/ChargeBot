import datetime
import os
import subprocess

from slack_sdk import WebhookClient

SLACK_WEBHOOK_URL_SLURM = os.environ["SLACK_WEBHOOK_URL_SLURM"]
SERVERADMIN_ID = os.environ["SERVERADMIN_ID"]


def main():
    cmd = ["ssh", "lab-mrcompute01", "sinfo -R"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if len(result.stdout.splitlines()) > 1:
        client = WebhookClient(SLACK_WEBHOOK_URL_SLURM)
        message = f":warning: <!subteam^{SERVERADMIN_ID}> Slurm is not normal. Please follow <https://www.notion.so/todalab/0c6b0040a41844408fea8b4b89c7b3e8?v=86497d48b35d43e2ac97849c49963c26&pvs=4|this instructions.>\n"
        message += str(datetime.datetime.now()) + "\n"
        message += "Result of sinfo -R\n"
        message += "```"
        message += result.stdout
        message += "```"
        response = client.send(text=message)


if __name__ == "__main__":
    main()