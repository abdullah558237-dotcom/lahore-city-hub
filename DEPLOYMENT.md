# Lahore City Hub (LCH) — Production Deployment Manual

This guide outlines the production deployment architecture, security hardening, environment configuration, database setup, and operational runbooks for **Lahore City Hub**.

---

## 1. Development vs. Production Settings Comparison

| Setting | Development (`config.settings.local`) | Production (`config.settings.production`) | Rationale / Security Impact |
| :--- | :--- | :--- | :--- |
| **`DEBUG`** | `True` | **`False`** | Prevents exposure of stack traces, database schema, and secret credentials to users. |
| **`ALLOWED_HOSTS`** | `127.0.0.1, localhost` | **Strict list of domains** (`lahorecityhub.pk`, etc.) | Prevents HTTP Host Header poisoning and cache poisoning attacks. |
| **Database** | SQLite (`db.sqlite3`) | **Managed PostgreSQL** | Concurrent connection pooling (`CONN_MAX_AGE=600`), ACID safety, and high-concurrency throughput. |
| **Static Files** | Django Dev Server static handler | **WhiteNoise with Gzip & Brotli compression** | Cache-busting manifest hashes, zero external S3 cost for CSS/JS, 12-factor compliance. |
| **Media Files** | Local filesystem (`media/`) | **S3 / Cloudflare R2 OR Persistent Cloud Volume** | Ephemeral cloud containers erase uploaded files on restart; persistent storage is required. |
| **`SECURE_SSL_REDIRECT`** | `False` | **`True`** | Automatically upgrades all insecure HTTP traffic to HTTPS. |
| **`SESSION_COOKIE_SECURE`** | `False` | **`True`** | Browser sends session cookies strictly over encrypted TLS connections. |
| **`CSRF_COOKIE_SECURE`** | `False` | **`True`** | Browser sends CSRF anti-forgery tokens strictly over encrypted TLS connections. |
| **HTTP Strict Transport Security (HSTS)** | Disabled | **Active (`31536000` seconds / 1 Year)** | Instructs browsers to reject all non-HTTPS connections and enforce TLS preloading. |
| **Reverse Proxy SSL Header** | None | **`('HTTP_X_FORWARDED_PROTO', 'https')`** | Informs Django that SSL is terminated at Nginx/Cloudflare/Load Balancer to prevent redirect loops. |
| **`CSRF_TRUSTED_ORIGINS`** | None | **Strict HTTPS origin list** | Required by Django 4.0+ for cross-origin POST requests over HTTPS. |
| **Email Backend** | Console (`django.core.mail.backends.console`) | **SMTP (SendGrid / AWS SES / Mailgun)** | Asynchronous transactional user notifications and password resets. |

---

## 2. Production Architecture

```
                    Internet
                       │
                       ▼
          [Cloudflare / DNS & Edge CDN]
                       │ (HTTPS / TLS 1.3)
                       ▼
         [Reverse Proxy / PaaS Router] (Render / Railway / Nginx)
                       │ (Terminates SSL, injects X-Forwarded-Proto)
                       ▼
          [Gunicorn WSGI Application Server] (3 Workers, 2 Threads)
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
[Managed PostgreSQL]           [Storage Layer]
(Port 5432 / SSL)              - Static: WhiteNoise (Local RAM/Disk)
                               - Media: AWS S3 / Cloudflare R2 / Persistent Volume
```

---

## 3. Environment Variables Specification

Copy `.env.example` to `.env` in production. **Never commit `.env` into version control.**

```bash
# Core Django
DJANGO_SECRET_KEY="<generate-random-50-char-key>"
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS="lahorecityhub.pk,www.lahorecityhub.pk"
DJANGO_SETTINGS_MODULE="config.settings.production"

# Database
DATABASE_URL="postgresql://<user>:<password>@<host>:5432/<dbname>"
DB_CONN_MAX_AGE=600

# Security & Reverse Proxy
SECURE_SSL_REDIRECT=True
CSRF_TRUSTED_ORIGINS="https://lahorecityhub.pk,https://www.lahorecityhub.pk"

# Media Storage
MEDIA_STORAGE_BACKEND="local" # Or 's3' for Cloudflare R2 / AWS S3

# S3 Storage (Required only if MEDIA_STORAGE_BACKEND=s3)
# AWS_ACCESS_KEY_ID="your-key-id"
# AWS_SECRET_ACCESS_KEY="your-secret-key"
# AWS_STORAGE_BUCKET_NAME="lch-media-bucket"
# AWS_S3_REGION_NAME="ap-south-1"
# AWS_S3_CUSTOM_DOMAIN="media.lahorecityhub.pk"
# AWS_S3_ENDPOINT_URL="https://<account_id>.r2.cloudflarestorage.com"

# Logging
DJANGO_LOG_LEVEL=INFO
```

---

## 4. Hosting Platform Option A: Managed PaaS (Render / Railway)

*Recommended for fast, low-maintenance deployment with automated SSL, managed database, and zero server maintenance.*

### Step 1: Create a Managed PostgreSQL Database
1. In the **Render Dashboard**, click **New +** -> **PostgreSQL**.
2. Set Name: `lahore-city-hub-db`, Region: `Singapore` or `Frankfurt` (closest to Pakistan latency).
3. Copy the **Internal Database URL** (e.g. `postgresql://lahore_user:password@dpg-xxxx-a.render.com/lahore_city_hub`).

### Step 2: Create a Web Service
1. Click **New +** -> **Web Service**.
2. Connect your Git repository (`lahore_city_hub`).
3. Set the following fields:
   * **Environment:** `Python 3`
   * **Build Command:** `./build.sh` (or `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`)
   * **Start Command:** `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --threads 2 --timeout 120`

### Step 3: Configure Environment Variables
In the **Environment** tab, add:
* `DJANGO_SETTINGS_MODULE`: `config.settings.production`
* `DJANGO_DEBUG`: `False`
* `DJANGO_SECRET_KEY`: *(Generate using `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)*
* `DJANGO_ALLOWED_HOSTS`: `your-app-name.onrender.com,lahorecityhub.pk,www.lahorecityhub.pk`
* `DATABASE_URL`: *(Paste the Internal Database URL from Step 1)*
* `SECURE_SSL_REDIRECT`: `True`
* `CSRF_TRUSTED_ORIGINS`: `https://your-app-name.onrender.com,https://lahorecityhub.pk,https://www.lahorecityhub.pk`
* `MEDIA_STORAGE_BACKEND`: `local` *(if attaching a persistent disk)* or `s3` *(if using Cloudflare R2)*.

### Step 4: Persistent Media Disk (If using local media)
1. In your Web Service settings, go to **Disks** -> **Add Disk**.
2. Name: `lch-media`, Mount Path: `/app/media`, Size: `10 GB`.

### Step 5: Initial Superuser Creation
Once deployed, open the Render **Shell** tab and run:
```bash
python manage.py createsuperuser
```
Follow prompts to set email, username, and secure password.

---

## 5. Hosting Platform Option B: VPS (Ubuntu 22.04 LTS + Nginx + Gunicorn)

### Step 1: System Packages & Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv postgresql postgresql-contrib nginx certbot python3-certbot-nginx git -y
```

### Step 2: Setup PostgreSQL Database
```bash
sudo -u postgres psql
CREATE DATABASE lahore_city_hub;
CREATE USER lahore_admin WITH PASSWORD 'YourVerySecurePassword123!';
ALTER ROLE lahore_admin SET client_encoding TO 'utf8';
ALTER ROLE lahore_admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE lahore_admin SET timezone TO 'Asia/Karachi';
GRANT ALL PRIVILEGES ON DATABASE lahore_city_hub TO lahore_admin;
\q
```

### Step 3: Clone Code & Configure Virtual Environment
```bash
sudo mkdir -p /var/www/lahore_city_hub
sudo chown -R $USER:$USER /var/www/lahore_city_hub
cd /var/www/lahore_city_hub
git clone <repo_url> .

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env
cp .env.example .env
nano .env # Configure secrets and DB credentials
```

### Step 4: Database Migrations & Static Collection
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### Step 5: Systemd Gunicorn Service (`/etc/systemd/system/gunicorn.service`)
```ini
[Unit]
Description=Gunicorn daemon for Lahore City Hub
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/lahore_city_hub
ExecStart=/var/www/lahore_city_hub/venv/bin/gunicorn \
          --access-logfile /var/log/gunicorn/access.log \
          --error-logfile /var/log/gunicorn/error.log \
          --workers 3 \
          --threads 2 \
          --bind unix:/run/gunicorn.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```
Enable and start Gunicorn:
```bash
sudo mkdir -p /var/log/gunicorn
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

### Step 6: Nginx Reverse Proxy Configuration (`/etc/nginx/sites-available/lahorecityhub`)
```nginx
server {
    server_name lahorecityhub.pk www.lahorecityhub.pk;

    client_max_body_size 15M;

    # Static Assets (WhiteNoise handles caching, or Nginx serves directly)
    location /static/ {
        alias /var/www/lahore_city_hub/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
    }

    # Uploaded Media Assets
    location /media/ {
        alias /var/www/lahore_city_hub/media/;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # Application Proxy
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Enable site and acquire SSL certificate:
```bash
sudo ln -s /etc/nginx/sites-available/lahorecityhub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d lahorecityhub.pk -d www.lahorecityhub.pk
```

---

## 6. Media Storage Strategy (Cloudflare R2 / AWS S3)

To ensure uploaded images are never lost when cloud application containers restart:
1. Create a **Cloudflare R2 Bucket** (Zero egress fees) named `lahore-city-hub-media`.
2. Generate an S3 API Token with Read/Write access.
3. Install `django-storages[boto3]>=1.14.0` in `requirements.txt`.
4. In `.env`, set:
   ```bash
   MEDIA_STORAGE_BACKEND=s3
   AWS_ACCESS_KEY_ID=<r2_token_id>
   AWS_SECRET_ACCESS_KEY=<r2_secret_key>
   AWS_STORAGE_BUCKET_NAME=lahore-city-hub-media
   AWS_S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
   AWS_S3_CUSTOM_DOMAIN=media.lahorecityhub.pk
   ```
5. All future uploads via the Business Onboarding Form or Admin Desk will upload directly to R2 and stream across Cloudflare's global edge network.

---

## 7. Backup and Disaster Recovery Runbook

### Automated Daily Database Backup Script (`/usr/local/bin/backup_lch_db.sh`)
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/lahore_city_hub"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/lch_db_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

# Run compressed pg_dump
pg_dump -U lahore_admin -h localhost lahore_city_hub | gzip > "$BACKUP_FILE"

# Rotate: remove backups older than 14 days
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +14 -delete
```
Add to crontab (`crontab -e`):
```cron
# Run daily at 02:00 AM PKT
0 2 * * * /usr/local/bin/backup_lch_db.sh > /dev/null 2>&1
```

### Disaster Recovery / Database Restoration
To restore a backup into a fresh PostgreSQL instance:
```bash
gunzip < /var/backups/lahore_city_hub/lch_db_20261108.sql.gz | psql -U lahore_admin -d lahore_city_hub
```

---

## 8. Post-Deployment Verification Checklist

Once deployed to staging or production, execute this verification runbook:
- [ ] Run `python manage.py check --deploy --settings=config.settings.production` (Must output 0 issues).
- [ ] Check HTTPS redirection: `curl -I http://yourdomain.com` (Must return `HTTP 301 Moved Permanently` to `https://`).
- [ ] Verify SSL certificate valid in browser (TLS 1.2 or 1.3).
- [ ] Test admin panel access at `/admin/` and log in with created superuser.
- [ ] Test CSRF protection: Submit a new business at `/businesses/submit/` (Must succeed without 403 CSRF verification failure).
- [ ] Test static files: Inspect `/static/css/theme.css` (Must return HTTP 200 with `gzip` or `br` content encoding).
- [ ] Test dynamic sitemap at `/sitemap.xml` and robots at `/robots.txt`.
- [ ] Confirm `DEBUG = False` by requesting a non-existent path `/fake-404-check/` (Must render custom branded `404.html`, not Django debug trace).
