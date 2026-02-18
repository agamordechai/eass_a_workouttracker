# Deployment Guide

## Overview

Deploy GrindLogger to an AWS EC2 free-tier instance (t2.micro — 1 vCPU, 1 GB RAM, 30 GB storage).
Free for 12 months. A 4 GB swap file is added to comfortably run all services on 1 GB RAM.

---

## Step 1: Create an AWS Account

1. Go to https://aws.amazon.com → **Create an AWS Account**
2. Verify email, set password, choose **Personal** account type
3. Enter a credit card (free-tier usage won't be charged)
4. Verify phone, select **Basic Support — Free**, complete sign-up
5. Wait for the activation email

---

## Step 2: Generate an SSH Key Pair

On your local machine:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/aws-grindlogger -N ""
cat ~/.ssh/aws-grindlogger.pub | pbcopy   # macOS — copies public key to clipboard
```

---

## Step 3: Launch an EC2 Instance

1. Log in to https://console.aws.amazon.com → search **EC2** → **Launch Instance**
2. Configure:
   - **Name:** `grindlogger`
   - **OS:** Ubuntu Server 24.04 LTS, 64-bit x86
   - **Instance type:** `t2.micro` (Free tier eligible)
   - **Key pair:** Import key pair → paste your `~/.ssh/aws-grindlogger.pub`
   - **Network settings → Edit:**
     - Auto-assign public IP: **Enable**
     - Add inbound rule: **HTTP** (port 80) from `0.0.0.0/0`
   - **Storage:** 30 GB gp3
3. **Launch Instance** → wait for **2/2 status checks passed**
4. Copy the **Public IPv4 address**

---

## Step 4: SSH into the Server

```bash
ssh -i ~/.ssh/aws-vm ubuntu@<YOUR-PUBLIC-IP>
```

---

## Step 5: Add Swap Space

On the server (1 GB RAM needs swap to build Docker images):

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Verify: `free -h` should show 4 GB swap.

---

## Step 6: Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
newgrp docker
```

---

## Step 7: Clone and Configure

```bash
git clone https://github.com/<your-username>/GrindLogger.git
cd GrindLogger

cp .env.example .env
nano .env
```

Fill in the following in `.env`:

| Variable | How to get it |
|---|---|
| `JWT_SECRET_KEY` | `openssl rand -hex 32` |
| `ANTHROPIC_API_KEY` | From https://console.anthropic.com |
| `GOOGLE_CLIENT_ID` | From Google Cloud Console (Step 9) |
| `POSTGRES_PASSWORD` | `openssl rand -hex 16` |

---

## Step 8: Deploy

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

First build takes 5–10 minutes on t2.micro. Monitor with:

```bash
docker compose ps
docker compose logs -f
```

Verify the app:

```bash
curl http://<YOUR-PUBLIC-IP>/api/health
# then open http://<YOUR-PUBLIC-IP> in a browser
```

---

## Step 9: Set Up Google OAuth

1. Go to https://console.cloud.google.com → **APIs & Services** → **Credentials**
2. Click your **OAuth 2.0 Client ID** (create one if needed)
3. Under **Authorized JavaScript origins**, add: `http://<YOUR-PUBLIC-IP>`
4. Under **Authorized redirect URIs**, add: `http://<YOUR-PUBLIC-IP>`
5. Copy the **Client ID** into your `.env` as `GOOGLE_CLIENT_ID`
6. Redeploy: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

---

## Step 10: Add HTTPS via Cloudflare (Optional)

### 10a: Get a Domain

Buy from any registrar (Cloudflare Registrar, Namecheap, etc.).

### 10b: Add Domain to Cloudflare

1. https://dash.cloudflare.com → **Add a site** → enter your domain → **Free plan**
2. Copy the two Cloudflare nameservers and set them at your registrar
3. Wait for the activation email

### 10c: Point DNS at Your EC2

In Cloudflare → **DNS** → **Records**, add two A records:

| Type | Name | Value | Proxy |
|---|---|---|---|
| A | `@` | your EC2 IP | Proxied (orange) |
| A | `www` | your EC2 IP | Proxied (orange) |

### 10d: Set SSL Mode

Cloudflare → **SSL/TLS** → **Overview** → set to **Full (Strict)**

### 10e: Create an Origin Certificate

1. Cloudflare → **SSL/TLS** → **Origin Server** → **Create Certificate**
2. Keep defaults (RSA, 15 years, root + wildcard hostnames) → **Create**
3. Save the two blocks locally:

```bash
nano nginx/certs/cert.pem   # paste Origin Certificate
nano nginx/certs/key.pem    # paste Private Key
```

> **Important:** Copy the private key now — Cloudflare won't show it again.

### 10f: Copy Certs to the Server

```bash
scp -i ~/.ssh/aws-vm nginx/certs/cert.pem nginx/certs/key.pem \
  ubuntu@<YOUR-EC2-IP>:~/GrindLogger/nginx/certs/
```

### 10g: Open Port 443

In AWS → **EC2** → your instance → **Security** tab → **Security group** → **Edit inbound rules** → add **HTTPS** (port 443) from `0.0.0.0/0`.

### 10h: Set Domain in .env and Redeploy

```bash
# On the server
cd ~/GrindLogger
echo "DOMAIN_NAME=yourdomain.com" >> .env
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 10i: Update Google OAuth for HTTPS

In Google Cloud Console → your OAuth 2.0 Client ID:
- Add `https://yourdomain.com` to **Authorized JavaScript origins**
- Add `https://yourdomain.com` to **Authorized redirect URIs**

### 10j: Verify

```bash
curl -I http://yourdomain.com        # should redirect to https
curl https://yourdomain.com/api/health
```

---

## Architecture

**HTTP only:**
```
Internet → :80 (nginx)
               → /          → static React files
               → /api/      → api:8000
               → /ai-coach/ → ai-coach:8001
```

**With HTTPS (Cloudflare):**
```
Client → Cloudflare (edge TLS) → EC2:443 (Origin Cert) → nginx
                                                              → /          → React
                                                              → /api/      → api:8000
                                                              → /ai-coach/ → ai-coach:8001
```

---

## Maintenance Commands

```bash
# View all logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# View specific service
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f api

# Pull latest code and redeploy
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Restart all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart

# Check resource usage
free -h
docker stats --no-stream

# Full reset (destroys all data)
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v
```

---

## Cost Reference

| Resource | Free tier | After 12 months |
|---|---|---|
| t2.micro | 750 hrs/month (1 instance 24/7) | ~$8.50/month |
| EBS storage | 30 GB | ~$2.40/month |
| Data transfer out | 100 GB/month | $0.09/GB |

Set up a **zero-spend budget** in AWS Billing → Budgets to get alerted if anything is charged.
