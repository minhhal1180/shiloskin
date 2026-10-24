#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
[[ "$(id -un)" == student && "$project_dir" == /home/student/shiloskin ]] || { echo 'Run as student from /home/student/shiloskin'; exit 1; }
cd "$project_dir"
python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check -r requirements-server.txt
install -d -m 700 instance
.venv/bin/python -m flask --app 'app:create_app()' init-db --demo
chmod 600 instance/secret.key
backup_stamp="$(date -u +%Y%m%dT%H%M%SZ)"
install -d -m 700 /home/student/shiloskin-backups
if sudo test -e /etc/nginx/sites-available/cse3045; then
    sudo cp -a /etc/nginx/sites-available/cse3045 "/home/student/shiloskin-backups/cse3045.conf.$backup_stamp"
fi
# Preserve the previous Hòa Lạc Food vhost for rollback, without deleting its app/data.
if sudo test -L /etc/nginx/sites-enabled/cse3045; then
    sudo mv /etc/nginx/sites-enabled/cse3045 "/home/student/shiloskin-backups/cse3045.enabled.$backup_stamp"
fi
for config in /etc/systemd/system/shiloskin.service /etc/nginx/sites-available/shiloskin; do
    if sudo test -e "$config"; then sudo cp -a "$config" "$config.bak.$backup_stamp"; fi
done
if ! sudo test -e /etc/shiloskin.env; then sudo install -m 640 -o root -g student deploy/shiloskin.env /etc/shiloskin.env; fi
sudo install -m 644 deploy/shiloskin.service /etc/systemd/system/shiloskin.service
sudo install -m 644 deploy/nginx.conf /etc/nginx/sites-available/shiloskin
sudo ln -sfn /etc/nginx/sites-available/shiloskin /etc/nginx/sites-enabled/shiloskin
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable shiloskin
sudo systemctl restart shiloskin
sudo systemctl reload nginx
for attempt in {1..20}; do
    if curl --fail --silent -H 'Host: sv21.bcse-vju.com' http://127.0.0.1/ >/dev/null; then echo 'Ready: https://sv21.bcse-vju.com'; exit 0; fi
    sleep 1
done
sudo journalctl -u shiloskin -n 30 --no-pager
exit 1
