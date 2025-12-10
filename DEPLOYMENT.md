# SupportFlow - Deployment Guide

This guide covers deploying SupportFlow to production with CI/CD.

## Table of Contents
- [Quick Deploy (Render.com)](#quick-deploy-rendercom)
- [AWS Deployment](#aws-deployment)
- [Docker Deployment](#docker-deployment)
- [CI/CD Setup](#cicd-setup)
- [Environment Variables](#environment-variables)

---

## Quick Deploy (Render.com) ⭐ RECOMMENDED

**Time:** 10-15 minutes
**Cost:** Free tier available (with limitations) or $7/month

### Prerequisites
- GitHub account
- Render.com account (free signup)
- OpenAI API key

### Steps

#### 1. Push to GitHub
```bash
cd C:\Users\amann\Documents\repos\SupportFlow
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR-USERNAME/SupportFlow.git
git push -u origin main
```

#### 2. Deploy to Render

1. **Go to [render.com](https://render.com)** and sign up/login
2. Click **"New"** → **"Blueprint"**
3. **Connect GitHub repository**: Select your SupportFlow repo
4. Render will automatically detect `render.yaml`
5. **Configure environment variables**:
   - Click on the backend service
   - Go to "Environment" tab
   - Add: `OPENAI_API_KEY` = your OpenAI key
   - (Optional) Add: `TAVILY_API_KEY` if you have one
6. Click **"Apply"**
7. Wait 5-10 minutes for deployment

#### 3. Access Your App

- **API**: `https://supportflow-api.onrender.com`
- **Frontend**: `https://supportflow-frontend.onrender.com`
- **Docs**: `https://supportflow-api.onrender.com/docs`

### Render Configuration Details

Your `render.yaml` includes:

```yaml
services:
  # Backend API
  - type: web
    name: supportflow-api
    env: python
    buildCommand: "cd backend && pip install -r requirements.txt"
    startCommand: "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT"

  # Frontend (static site)
  - type: web
    name: supportflow-frontend
    env: static
    buildCommand: "cd frontend && npm install && npm run build"
    staticPublishPath: frontend/dist

databases:
  # PostgreSQL database
  - name: supportflow-db
    plan: starter  # Free tier
```

### Free Tier Limitations

- Apps sleep after 15 minutes of inactivity
- 750 hours/month free (enough for 1 service)
- Database: 90 days retention, then deleted

### Upgrade to Paid ($7/month)

- No sleeping
- Unlimited hours
- Persistent database
- Custom domains

---

## AWS Deployment

**Time:** 2-3 hours
**Cost:** ~$30-50/month
**Complexity:** High

### Architecture

```
┌─────────────────────────────────────────┐
│         Application Load Balancer        │
│              (Port 443 HTTPS)            │
└───────────────┬─────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
┌───────▼──────┐  ┌──────▼──────┐
│  ECS Fargate │  │ S3 + CF     │
│   (Backend)  │  │ (Frontend)  │
└──────┬───────┘  └─────────────┘
       │
┌──────▼───────┐
│ RDS Postgres │
└──────────────┘
```

### Prerequisites

- AWS Account
- AWS CLI installed and configured
- Docker installed locally
- Domain name (optional)

### Step 1: Create ECR Repository

```bash
# Login to AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Create repository
aws ecr create-repository --repository-name supportflow

# Build and push image
docker build -t supportflow .
docker tag supportflow:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/supportflow:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/supportflow:latest
```

### Step 2: Create RDS Database

```bash
aws rds create-db-instance \
  --db-instance-identifier supportflow-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username supportflow \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 20
```

### Step 3: Create ECS Cluster

```bash
# Create cluster
aws ecs create-cluster --cluster-name supportflow

# Create task definition (see task-definition.json)
aws ecs register-task-definition --cli-input-json file://aws/task-definition.json

# Create service
aws ecs create-service \
  --cluster supportflow \
  --service-name supportflow-service \
  --task-definition supportflow \
  --desired-count 1 \
  --launch-type FARGATE
```

### Step 4: Deploy Frontend to S3

```bash
# Build frontend
cd frontend
npm run build

# Upload to S3
aws s3 sync dist/ s3://supportflow-frontend/

# Create CloudFront distribution
aws cloudfront create-distribution --origin-domain-name supportflow-frontend.s3.amazonaws.com
```

### Step 5: Configure Environment Variables

In ECS Task Definition, add:
```json
{
  "environment": [
    {"name": "OPENAI_API_KEY", "value": "your-key"},
    {"name": "DATABASE_URL", "value": "postgresql://..."},
    {"name": "ENVIRONMENT", "value": "production"}
  ]
}
```

### Estimated AWS Costs

- **ECS Fargate**: ~$15/month (1 task, 0.5 vCPU, 1GB RAM)
- **RDS t3.micro**: ~$15/month
- **S3 + CloudFront**: ~$1-5/month
- **ALB**: ~$16/month
- **Data transfer**: ~$1-5/month
- **Total**: ~$48-56/month

---

## Docker Deployment (Self-Hosted)

**Time:** 30-60 minutes
**Cost:** $5-12/month (VPS hosting)
**Complexity:** Medium

### Option A: DigitalOcean Droplet

1. **Create Droplet** ($6/month):
   - OS: Ubuntu 22.04
   - Size: Basic, 1GB RAM
   - Enable monitoring

2. **SSH into droplet**:
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

3. **Install Docker**:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   apt install docker-compose
   ```

4. **Clone and deploy**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/SupportFlow.git
   cd SupportFlow

   # Create .env file
   nano .env
   # Add OPENAI_API_KEY, etc.

   # Start services
   docker-compose up -d
   ```

5. **Configure Nginx reverse proxy** (optional):
   ```bash
   apt install nginx
   # Configure nginx to proxy to localhost:8000
   ```

6. **Set up SSL with Let's Encrypt**:
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d yourdomain.com
   ```

### Option B: Railway.app

1. Go to [railway.app](https://railway.app)
2. Connect GitHub
3. Deploy from repo
4. Add environment variables
5. Get public URL

**Cost:** ~$5/month

---

## CI/CD Setup

Your project includes a GitHub Actions workflow (`.github/workflows/ci-cd.yml`).

### What It Does

On every push to `main`:
1. ✅ **Test Backend**: Linting, type checking
2. ✅ **Test Frontend**: Linting, build
3. ✅ **Docker Build**: Verify container builds
4. ✅ **Auto-Deploy**: Triggers deployment (if configured)

### Enable GitHub Actions

1. Push `.github/workflows/ci-cd.yml` to your repo
2. Go to GitHub repo → **Actions** tab
3. Workflows will run automatically on push

### Add Deployment Secrets

For AWS deployment, add these secrets in GitHub:

1. Go to repo → **Settings** → **Secrets and variables** → **Actions**
2. Add secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `OPENAI_API_KEY`
   - `RENDER_DEPLOY_HOOK` (if using Render)

### Customize Workflow

Edit `.github/workflows/ci-cd.yml` to:
- Add actual tests (currently uses `continue-on-error: true`)
- Enable AWS deployment (uncomment the `deploy-aws` job)
- Add notifications (Slack, Discord, email)

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `DATABASE_URL` | Database connection | `postgresql://user:pass@host/db` |
| `SECRET_KEY` | App secret key | Random 32+ char string |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `TAVILY_API_KEY` | Tavily search API | None |
| `ENVIRONMENT` | Environment name | `production` |
| `DEBUG` | Debug mode | `false` |
| `CONFIDENCE_THRESHOLD` | AI confidence threshold | `0.7` |

### Setting Environment Variables

**Render:**
- Dashboard → Service → Environment tab

**AWS ECS:**
- Task Definition → Container → Environment variables

**Docker:**
- `.env` file in project root

**Heroku:**
```bash
heroku config:set OPENAI_API_KEY=sk-...
```

---

## Post-Deployment Checklist

- [ ] API accessible at public URL
- [ ] Frontend loads correctly
- [ ] Can submit test ticket
- [ ] Database persists data
- [ ] Agent workflow completes
- [ ] Environment variables set
- [ ] SSL/HTTPS enabled (production)
- [ ] Monitoring set up (optional)
- [ ] Custom domain configured (optional)
- [ ] CI/CD pipeline running

---

## Monitoring & Maintenance

### Application Monitoring

**Render:**
- Built-in logs and metrics
- View in Render dashboard

**AWS:**
- CloudWatch logs and metrics
- Set up alarms for errors

**Self-hosted:**
```bash
# View Docker logs
docker-compose logs -f backend

# Check resource usage
docker stats
```

### Database Backups

**Render:**
- Automatic daily backups (paid plans)
- Manual: `pg_dump` from Render shell

**AWS RDS:**
- Automatic daily snapshots
- Point-in-time recovery

**Self-hosted:**
```bash
# Backup PostgreSQL
docker-compose exec db pg_dump -U supportflow supportflow > backup.sql

# Restore
cat backup.sql | docker-compose exec -T db psql -U supportflow supportflow
```

---

## Troubleshooting

### Common Issues

**Issue: "Module not found" errors**
- Solution: Ensure all dependencies in `requirements.txt`
- Check Python version is 3.11+

**Issue: Database connection fails**
- Solution: Verify `DATABASE_URL` format
- Check database is running and accessible

**Issue: CORS errors in frontend**
- Solution: Add frontend URL to `CORS_ORIGINS` in backend config

**Issue: 502 Bad Gateway**
- Solution: Check backend is running
- Verify port configuration

**Issue: Out of memory**
- Solution: Increase instance size
- Reduce `MAX_AGENT_ITERATIONS` in config

---

## Cost Summary

| Platform | Monthly Cost | Setup Time | Complexity |
|----------|-------------|------------|------------|
| **Render (Free)** | $0 | 10 min | Low |
| **Render (Paid)** | $7 | 10 min | Low |
| **Railway** | $5 | 15 min | Low |
| **DigitalOcean** | $6 | 1 hour | Medium |
| **AWS** | $30-50 | 2-3 hours | High |
| **Heroku** | $7-25 | 20 min | Low |

---

## Next Steps

1. ✅ **Deploy to Render** (recommended first step)
2. 📊 **Set up monitoring** (Sentry for errors)
3. 🔒 **Add authentication** (JWT for admin routes)
4. 📝 **Add tests** (pytest for backend)
5. 🚀 **Add custom domain**
6. 📈 **Set up analytics**

---

**Questions?** Check the main [README.md](README.md) or open an issue on GitHub.
