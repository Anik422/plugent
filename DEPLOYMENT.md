# Plugent Deployment Guide

## Quick Start with Docker

```bash
# Clone and setup
git clone https://github.com/plugent/plugent.git
cd plugent

# Configure environment
cp .env.example .env
nano .env  # Add your API keys

# Run with Docker Compose
docker-compose up -d

# Check status
docker-compose ps
curl http://localhost:8000/health
```

---

## Local Docker Deployment

### Prerequisites
- Docker
- Docker Compose

### Steps

1. **Create `.env` file:**
```env
DATABASE_URL=sqlite:///./plugent.db
LITELLM_MODEL=openai
LITELLM_API_KEY=sk-your-key
PLUGENT_API_KEY=your-secure-password
```

2. **Build and run:**
```bash
docker build -t plugent .
docker run -d -p 8000:8000 --env-file .env plugent
```

3. **Verify:**
```bash
curl http://localhost:8000/health
```

---

## VPS with Nginx

### Prerequisites
- Ubuntu server with Docker
- Domain name pointed to server
- Nginx installed

### Steps

1. **Deploy with Docker:**
```bash
docker-compose up -d
```

2. **Install Nginx:**
```bash
sudo apt update
sudo apt install nginx
```

3. **Configure Nginx:**
```bash
sudo cp nginx.conf /etc/nginx/sites-available/plugent
sudo ln -s /etc/nginx/sites-available/plugent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

4. **Setup SSL (Let's Encrypt):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Railway Deployment

### Prerequisites
- Railway account
- GitHub repository

### Steps

1. **Connect to Railway:**
   - Go to [railway.app](https://railway.app)
   - "New Project" → "Deploy from GitHub"
   - Select your plugent fork

2. **Configure Environment:**
   - Add variables in Railway dashboard:
     ```
     DATABASE_URL=sqlite:///./plugent.db
     LITELLM_API_KEY=sk-...
     PORT=8000
     ```

3. **Deploy:**
   - Railway auto-deploys on push
   - Get URL from Railway dashboard

4. **Custom Domain (optional):**
   - Settings → Domains → Add domain

---

## Render Deployment (Free Tier)

### Prerequisites
- Render account
- GitHub repository

### Steps

1. **Create Web Service:**
   - Go to [render.com](https://render.com)
   - "New" → "Web Service"
   - Connect GitHub repo

2. **Configure:**
   - Build Command: `pip install -e .`
   - Start Command: `plugent serve`

3. **Environment Variables:**
   - Add in Render dashboard:
     ```
     DATABASE_URL=sqlite:///./plugent.db
     LITELLM_API_KEY=sk-...
     ```

4. **Deploy:**
   - Auto-deploys on push
   - Free tier: sleep after 15 min inactivity

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Database connection string |
| `LITELLM_MODEL` | No | LLM provider (default: openai) |
| `LITELLM_API_KEY` | Yes* | API key for LLM |
| `PLUGENT_API_KEY` | No | Bearer token for API auth |
| `REDIS_URL` | No | Redis for sessions |
| `CHROMA_DIR` | No | ChromaDB persistence dir |
| `COMPANY_NAME` | No | Your company name |
| `COMPANY_DOMAIN` | No | Business domain |

---

## Database Options

### SQLite (Default, No Setup)
```env
DATABASE_URL=sqlite:///./plugent.db
```

### PostgreSQL
```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### MySQL
```env
DATABASE_URL=mysql://user:password@host:3306/dbname
```

---

## LLM Provider Setup

### OpenAI
```env
LITELLM_MODEL=openai
LITELLM_API_KEY=sk-...
```

### Anthropic (Claude)
```env
LITELLM_MODEL=anthropic
LITELLM_API_KEY=sk-ant-...
```

### Groq (Free Tier)
```env
LITELLM_MODEL=groq
LITELLM_API_KEY=gsk_...
```

### Ollama (Local)
```env
LITELLM_MODEL=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs plugent

# Common issues
# - Missing API key
# - Database URL incorrect
# - Port already in use
```

### Health check fails
```bash
# Check if app is running inside container
docker exec -it plugent curl localhost:8000/health

# Check environment
docker exec -it plugent env
```

### Out of memory
- Reduce ChromaDB batch size
- Use smaller LLM model
- Add swap space

---

## Production Checklist

- [ ] Set `PLUGENT_API_KEY` for auth
- [ ] Use PostgreSQL for production
- [ ] Configure backup for database
- [ ] Set up monitoring (optional)
- [ ] Enable HTTPS with SSL
- [ ] Set up log rotation
- [ ] Configure resource limits

---

## Support

- Issues: https://github.com/plugent/plugent/issues
- Documentation: https://plugent.dev
- Discord: https://discord.gg/plugent