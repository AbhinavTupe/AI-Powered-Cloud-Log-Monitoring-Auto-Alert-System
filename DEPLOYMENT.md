# AWS EC2 Deployment Guide

This guide deploys the monitoring API on a single Ubuntu EC2 instance using Docker Compose. It is intentionally simple and resume-friendly: one VM, one containerized Flask service, persistent SQLite storage, and a health-checked deployment.

## What You Will Deploy

```text
Internet
   |
   v
EC2 Security Group
   |  inbound: 22 from your IP, 80 from allowed users
   v
Ubuntu EC2 Instance
   |
   v
Docker Compose
   |
   v
Flask + Gunicorn container on host port 80
   |
   v
SQLite volume for logs and alerts
```

## Prerequisites

- AWS account
- EC2 key pair
- GitHub repository pushed to `main`
- Local terminal with SSH

AWS notes:

- EC2 security groups act like stateful firewalls for instances.
- EC2 user data can run a shell script during instance launch.

## 1. Launch EC2

Recommended beginner-friendly instance:

- AMI: Ubuntu Server LTS
- Instance type: `t2.micro` or `t3.micro`
- Storage: 8-16 GB
- Key pair: create or select an existing `.pem`

Security group inbound rules:

| Type | Port | Source |
| --- | --- | --- |
| SSH | 22 | Your IP only |
| HTTP | 80 | `0.0.0.0/0` for demo, or your IP for private testing |

Avoid opening SSH to the whole internet for a resume demo.

## 2. Add User Data

In the EC2 launch wizard, open **Advanced details** and paste this user data:

```bash
#!/usr/bin/env bash
export REPO_URL="https://github.com/AbhinavTupe/AI-Powered-Cloud-Log-Monitoring-Auto-Alert-System.git"
export BRANCH="main"
curl -fsSL https://raw.githubusercontent.com/AbhinavTupe/AI-Powered-Cloud-Log-Monitoring-Auto-Alert-System/main/scripts/ec2/bootstrap_ubuntu.sh | bash
```

This installs Docker, clones the repo into `/opt/cloud-log-monitoring`, creates `.env`, and runs:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## 3. Validate Deployment

After the instance status checks pass, open:

```text
http://<EC2_PUBLIC_IP>/health
http://<EC2_PUBLIC_IP>/dashboard
```

Or from your terminal:

```bash
curl http://<EC2_PUBLIC_IP>/health
curl http://<EC2_PUBLIC_IP>/dashboard
```

## 4. Generate Demo Logs On EC2

SSH into the instance:

```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

Generate logs from inside the running project:

```bash
cd /opt/cloud-log-monitoring
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_logs.py --api-url http://localhost/logs --count 30 --mode mixed
```

Then check:

```bash
curl http://localhost/dashboard
curl http://localhost/alerts
```

## 5. Deploy Updates

After pushing changes to GitHub, SSH into EC2 and run:

```bash
cd /opt/cloud-log-monitoring
bash scripts/ec2/deploy.sh
```

This pulls the latest `main`, rebuilds the Docker image, restarts the service, and checks `/health`.

## 6. Configure Slack Alerts

On EC2:

```bash
cd /opt/cloud-log-monitoring
nano .env
```

Set:

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

Restart:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## Useful Operations Commands

View containers:

```bash
docker compose -f docker-compose.prod.yml ps
```

View logs:

```bash
docker compose -f docker-compose.prod.yml logs -f monitoring-api
```

Restart:

```bash
docker compose -f docker-compose.prod.yml restart
```

Stop:

```bash
docker compose -f docker-compose.prod.yml down
```

Check user data logs:

```bash
sudo tail -n 100 /var/log/cloud-log-monitoring-bootstrap.log
sudo tail -n 100 /var/log/cloud-init-output.log
```

## Troubleshooting

If the browser cannot connect:

- Confirm the EC2 security group allows inbound HTTP port `80`.
- Confirm the instance public IP did not change after restart.
- SSH into EC2 and run `docker compose -f docker-compose.prod.yml ps`.
- Check container logs with `docker compose -f docker-compose.prod.yml logs -f monitoring-api`.

If `/health` fails:

- Check whether Docker is running: `sudo systemctl status docker`.
- Rebuild manually: `docker compose -f docker-compose.prod.yml up -d --build`.
- Review bootstrap logs: `sudo tail -n 100 /var/log/cloud-log-monitoring-bootstrap.log`.

## Interview Explanation

This deployment demonstrates a practical cloud workflow:

- GitHub stores source code and triggers CI.
- Docker creates a consistent runtime artifact.
- EC2 provides a simple cloud compute target.
- Docker Compose keeps deployment understandable for a student project.
- Health checks validate that the container is actually serving traffic.
- Environment variables keep alert settings outside source code.

## References

- AWS EC2 security groups: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html
- AWS EC2 user data: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html
- Docker Engine on Ubuntu: https://docs.docker.com/engine/install/ubuntu/
