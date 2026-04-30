# Deployment Guide — AWS Lightsail

This guide walks through deploying the Company Address Scraper to AWS Lightsail ($10/month).

## Prerequisites

- AWS account (with Lightsail available)
- Git credentials set up
- Domain name (optional, for Cloudflare + custom domain)

## Step 1: Create Lightsail Instance

1. Go to [AWS Lightsail console](https://lightsail.aws.amazon.com/)
2. Click "Create instance"
3. Select:
   - **Location**: Your preferred region
   - **OS only**: Ubuntu 22.04
   - **Instance plan**: $10/month (2GB RAM, 1 vCPU, 60GB SSD)
4. **Instance name**: `company-scraper`
5. Click "Create instance"
6. Wait 2-3 minutes for the instance to start

## Step 2: Connect via SSH

1. In the Lightsail console, click on your instance
2. Click "SSH browser terminal" OR copy the SSH key and use:
   ```bash
   ssh -i LightsailDefaultPrivateKey-us-east-1.pem ubuntu@<instance-ip>
   ```

## Step 3: Install Docker & Docker Compose

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

## Step 4: Clone Repository

```bash
cd /home/ubuntu
git clone https://github.com/YOUR_GITHUB/company-address-scraping.git
cd company-address-scraping
```

## Step 5: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys
nano .env
```

Fill in:
- `SERPAPI_KEY` — from https://serpapi.com/dashboard
- `FIRECRAWL_API_KEY` — from Firecrawl dashboard
- `AWS_ACCESS_KEY_ID` — from AWS IAM
- `AWS_SECRET_ACCESS_KEY` — from AWS IAM
- `NEXT_PUBLIC_ADSENSE_ID` — (optional) your Google AdSense publisher ID

**Save and exit** (Ctrl+X, then Y, then Enter in nano)

## Step 6: Build and Start

```bash
# Build Docker images (this may take 5-10 minutes)
sudo docker-compose build

# Start services in background
sudo docker-compose up -d

# Check status
sudo docker-compose ps

# View logs
sudo docker-compose logs -f backend
```

Wait 1-2 minutes for services to fully start.

## Step 7: Verify It's Working

From your local machine:

```bash
# Replace <lightsail-ip> with the instance public IP from Lightsail console
curl http://<lightsail-ip>:8000/health
# Should return: {"status":"ok"}

curl http://<lightsail-ip>:3000
# Should return HTML (the home page)
```

Or open in browser: `http://<lightsail-ip>:3000`

## Step 8: (Optional) Set Up Cloudflare

For a custom domain with rate limiting:

1. Go to [Cloudflare](https://dash.cloudflare.com/)
2. Add your domain
3. Update your domain's nameservers to Cloudflare's
4. Create a DNS A record pointing to your Lightsail instance IP
5. Set up rate limiting rules:
   - Ratelimit: 10 requests per 1 minute from same IP to `/api/jobs/upload`

## Step 9: Enable HTTPS (Optional)

Add this to `docker-compose.yml` to use Let's Encrypt with Caddy reverse proxy:

```yaml
  caddy:
    image: caddy:latest
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - frontend

volumes:
  caddy_data:
  caddy_config:
```

Create `Caddyfile`:
```
your-domain.com {
  reverse_proxy /api/* http://backend:8000
  reverse_proxy * http://frontend:3000
}
```

Then:
```bash
sudo docker-compose up -d --build
```

## Step 10: Monitor Logs

```bash
# Watch backend logs
sudo docker-compose logs -f backend

# Watch frontend logs
sudo docker-compose logs -f frontend

# All logs
sudo docker-compose logs -f
```

## Troubleshooting

### Port already in use
```bash
sudo docker-compose down
sudo docker-compose up -d
```

### Out of memory
Lightsail 2GB is tight with Playwright. If jobs fail:
- Increase to 4GB instance ($20/month)
- Or reduce `MAX_CONCURRENT_PLAYWRIGHT` to 1 in `.env`

### Backend 502 errors
```bash
# Check backend health
sudo docker-compose exec backend curl http://localhost:8000/health

# Restart backend
sudo docker-compose restart backend
```

### Files not persisting
The `./data` volume is mounted on the instance. Check permissions:
```bash
ls -la /home/ubuntu/company-address-scraping/data
```

## Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| Lightsail 2GB | $10/month | Covers all compute |
| SerpAPI | ~$1-5/month | Depends on usage (100 searches free tier) |
| Firecrawl | ~$5-10/month | Depends on usage (3000 credits free tier) |
| AWS Bedrock | ~$0.10-1/month | Nova Micro is cheap |
| **Total** | ~$16-26/month | All-in for 50+ concurrent users |

## Updating Code

When you push code to GitHub:

```bash
cd /home/ubuntu/company-address-scraping
git pull origin main
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

## Backup Data

To backup your Excel results:

```bash
# On Lightsail instance
tar -czf company-scraper-backup-$(date +%Y%m%d).tar.gz data/

# Download to your machine
scp -i ~/.ssh/LightsailDefaultPrivateKey-us-east-1.pem \
  ubuntu@<instance-ip>:~/company-address-scraping/company-scraper-backup-*.tar.gz \
  ./backups/
```

---

## Next Steps

1. ✅ Instance running
2. ✅ App deployed
3. Share the public IP with users to start using
4. Monitor logs and costs
5. Scale if needed (more concurrent Playwright, higher instance tier)
