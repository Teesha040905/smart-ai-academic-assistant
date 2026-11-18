# Deploying on AWS (EC2 + Docker)

This runs the whole app on **one AWS EC2 server** with Docker. It is a second deployment next to
Vercel + Render, and both use the **same MongoDB Atlas database**.

```
Browser ──HTTPS──► EC2 server (Ubuntu)
                   ├─ Caddy        ports 80/443, free HTTPS certificate (Let's Encrypt)
                   │   ├─ /api/*  ──► backend container  (FastAPI)
                   │   └─ /*      ──► frontend container (Next.js)
                   └─────────────────► MongoDB Atlas (internet)
```

| AWS concept | What it is | Used for |
|---|---|---|
| **EC2 instance** | a virtual server (Linux computer in the cloud) | runs the 3 containers |
| **Security group** | the server's firewall | allows HTTPS (443), HTTP (80), SSH (22) |
| **Elastic IP** | a fixed public IP address | website address stays the same after a restart |
| **Key pair** | SSH login key | logging in to the server |
| **AWS Budgets** | spending alerts | email if anything starts costing money |

Website address: `https://<your-ip-with-dashes>.sslip.io` (e.g. `https://13-233-10-5.sslip.io`).
[sslip.io](https://sslip.io) is a free service that turns any IP into a hostname, so HTTPS works
without buying a domain.

---

## Step 0 — Safety first: billing alert (2 min)

1. AWS Console → search **Budgets** → **Create budget**.
2. Choose **Use a template** → **Zero spend budget** → enter your email → **Create budget**.

You now get an email the moment anything costs money.

## Step 1 — Choose region

Top-right of the console → select **Asia Pacific (Mumbai) ap-south-1**. Use the same region for every step.

## Step 2 — Launch the EC2 server (5 min)

EC2 → **Launch instance**:

| Setting | Value |
|---|---|
| Name | `smart-academic` |
| OS image | **Ubuntu Server 24.04 LTS** (shows "Free tier eligible") |
| Instance type | **t3.micro** (or **t2.micro** — pick the one marked *Free tier eligible*) |
| Key pair | **Create new key pair** → name `smart-academic-key`, type RSA, format **.pem** → it downloads; keep it safe |
| Network settings → Firewall | **Create security group**, tick: ✅ Allow SSH traffic from **My IP**, ✅ Allow HTTPS traffic from the internet, ✅ Allow HTTP traffic from the internet |
| Storage | **20 GiB** gp3 (free tier allows up to 30 GiB) |

Click **Launch instance**.

## Step 3 — Give it a fixed IP (Elastic IP) (2 min)

1. EC2 → left menu **Elastic IPs** → **Allocate Elastic IP address** → **Allocate**.
2. Select the new IP → **Actions → Associate Elastic IP address** → Instance: `smart-academic` → **Associate**.
3. Note the IP, e.g. `13.233.10.5`.

## Step 4 — Connect to the server (1 min)

EC2 → **Instances** → select `smart-academic` → **Connect** → tab **EC2 Instance Connect** → **Connect**.
A black terminal opens in your browser — you are now on the server.

(Alternative from Windows: `ssh -i smart-academic-key.pem ubuntu@13.233.10.5`)

## Step 5 — Run the setup script (5 min)

Paste into the server terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/Teesha040905/smart-ai-academic-assistant/main/deploy/aws/setup-ec2.sh | bash
```

It adds swap memory, installs Docker, downloads the code, and creates `~/app/deploy/aws/.env`
(with your website address and a random JWT secret already filled in). At the end it prints your
website address.

## Step 6 — Add your secrets (2 min)

```bash
nano ~/app/deploy/aws/.env
```

Fill in (same values as on Render):

- `MONGODB_URL=` your Atlas connection string
- `AI_API_KEYS=` your Gemini key

Save: **Ctrl+O**, **Enter**, then **Ctrl+X**.

## Step 7 — Start the app (10–15 min first time)

```bash
cd ~/app/deploy/aws
sudo docker compose up -d --build
```

The first build is slow on a small server. Check progress / status:

```bash
sudo docker compose ps              # all 3 should be "running"
sudo docker compose logs -f api     # backend logs (Ctrl+C to exit)
sudo docker compose logs caddy      # HTTPS certificate messages
```

## Step 8 — Open the website

`https://<your-ip-with-dashes>.sslip.io` — register, log in, try the features.
Health check: `https://<your-ip-with-dashes>.sslip.io/health` → `"db_status":"ok"`.

---

## Updating to the latest code

After pushing changes to GitHub `main`:

```bash
bash ~/app/deploy/aws/update.sh
```

## Stopping to save free-tier hours / credits

- **Stop** (keeps everything): EC2 → Instances → select → **Instance state → Stop**. Start it again later; the Elastic IP keeps the same address. Containers start automatically.
- **Delete everything** when finished learning: **Terminate** the instance, then **Elastic IPs → Release** the IP (an unused Elastic IP is charged), and delete the security group / key pair if you like.

## Troubleshooting

| Problem | Fix |
|---|---|
| Site doesn't load | Security group must allow 80 and 443 from `0.0.0.0/0`; `sudo docker compose ps` shows all running |
| Certificate error | Wait 1–2 min after first start; `sudo docker compose logs caddy` |
| `db_status: unreachable` / `bad auth` | Check `MONGODB_URL` in `.env`, then `sudo docker compose up -d` |
| Build killed / very slow | Swap is missing: `free -h` should show 2 GB swap; re-run the setup script |
| Changed `.env` | `cd ~/app/deploy/aws && sudo docker compose up -d` |

## Cost notes

The **t3.micro / t2.micro** instance, 20–30 GB storage and normal traffic are covered by the AWS
free tier / free credits for new accounts. AWS also charges a small amount for public IPv4
addresses (about $0.005/hour); depending on your account type this is covered by free-tier hours or
credits. The **zero-spend budget** from Step 0 emails you if anything starts costing money. Stop
or terminate the server when you don't need it.
