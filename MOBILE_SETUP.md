# Carnal 2.0 Mobile Access Guide

## Quick Start (Home WiFi)

### Step 1: Install Flask
```bash
.venv\Scripts\pip install flask
```

### Step 2: Find Your Computer's IP Address
Open Command Prompt and run:
```bash
ipconfig
```
Look for the **IPv4 Address** (usually looks like `192.168.1.xxx` or `10.0.0.xxx`)

### Step 3: Start the Web Server
```bash
.venv\Scripts\python web_app.py
```

You should see:
```
Running on http://0.0.0.0:5000
```

### Step 4: Access from iPhone
On your iPhone, open Safari and go to:
```
http://YOUR_COMPUTER_IP:5000
```

For example: `http://192.168.1.50:5000`

---

## Features

✅ **Chat** - Talk to Carnal in real-time  
✅ **Mobile-friendly** - Works perfectly on iPhone Safari  
✅ **No app needed** - Just a web browser  
✅ **Same local AI** - Uses your desktop LLM setup  

---

## Troubleshooting

**"Can't connect"**
- Make sure both devices are on the same WiFi network
- Check the IP address is correct (try pinging it first)
- Firewall: You may need to allow Python through Windows Firewall

**"Server won't start"**
- Make sure Flask is installed: `.venv\Scripts\pip install flask`
- Check if port 5000 is already in use

**"Slow responses"**
- Normal if using local LLM or cloud API with high latency
- Check your internet/LAN speed

---

## Advanced: Remote Access (Deploy Online)

If you want to access from anywhere (not just home WiFi):
1. Use ngrok: `ngrok http 5000`
2. Or deploy to Heroku/Replit (requires setup)

For now, home WiFi access should work great!
