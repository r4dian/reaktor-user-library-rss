#!/usr/bin/env sh

# Apparently only metarpa members should be able to use cron
# it was an error that I could before.
# Running this in a detached tmux session should keep the feed updating,
# unless that session is killed.
#
# The script is standard-library only now, so no virtualenv is required.
#
# https://stackoverflow.com/questions/42801100/how-to-run-scheduled-scripts-on-linux-without-using-cron

echo 'Running the Reaktor lib RSS update process.'

while true; do
    python3 main.py "$HOME/html/reaktor_library_rss.php"
    # sleep 6 hours
    sleep $((6 * 60 * 60))
done
