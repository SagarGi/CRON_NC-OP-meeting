## Description

This Python script sends meeting details (agenda and meeting link) from an OpenProject project to a Matrix chat room.

## Set up locally

> **_NOTE_**: Ensure that `Python3` and `pip3` are already installed on your system.

### 1. Clone

```bash
git clone https://github.com/SagarGi/CRON_NC-OP-meeting.git
cd CRON_NC-OP-meeting
```

### 2. Install required modules

```bash
pip3 install -r requirements.txt
```

### 3. Install cron locally

```bash
apt-get install cron
```

### 4. Set environment variables

```bash
cp .env.example .env
# All ENV's needs to be set accordingly
```

### 4. Set cron job locally

```bash
# Open the crontab editor first
EDITOR=/usr/bin/nano crontab -e
# Set the cron time
# Here the belwo cron time runs the script every thursday at 13:30,13:38,13:42,13:46
# m h  dom mon dow   command
30,38,42,46 13 * * 4 XDG_RUNTIME_DIR=/run/user/$(id -u) python3  ${HOME}/<path-to-CRON_NC-OP-meeting>/meeting.py
```
