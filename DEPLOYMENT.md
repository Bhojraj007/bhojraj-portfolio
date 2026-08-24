# Deployment Guide — Bhojraj Portfolio + Private Portal

## Pre-Deployment Checklist

- [ ] Create a `.env` file based on `.env.example` with real values
- [ ] Set `DEBUG=False` in production
- [ ] Set a strong, unique `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS` to your domain(s)
- [ ] Configure `DATABASE_URL` for PostgreSQL

## 1. Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser (first time only)
python manage.py createsuperuser
```

## 2. Environment Variables

Set these in your hosting provider's dashboard (Render, Railway, Heroku, etc.):

| Variable | Example | Description |
|---|---|---|
| `SECRET_KEY` | `your-50-char-random-string` | Django secret key |
| `DEBUG` | `False` | Must be False in production |
| `ALLOWED_HOSTS` | `yourdomain.com,www.yourdomain.com` | Comma-separated |
| `DATABASE_URL` | `postgres://user:pass@host:5432/dbname` | PostgreSQL connection |

## 3. Production Security

Security headers are **automatically** activated when `DEBUG=False` (configured in `settings.py`):
- HTTPS enforcement (SSL redirect)
- HSTS (1 year with preload)
- Secure cookies (session + CSRF)
- XSS and content-type sniff protection
- X-Frame-Options: DENY

## 4. Static & Media Files

- **Static files**: Served via WhiteNoise (bundled in middleware). Run `collectstatic` before deploying.
- **Media files**: User uploads (photos, videos, moments). Use a persistent storage solution:
  - **Render**: Use a persistent disk mounted at `/media`
  - **Railway**: Use a volume
  - **AWS/Cloud**: Use `django-storages` with S3

## 5. Run Command

```bash
# Procfile (Heroku/Render)
web: gunicorn portfolio_site.wsgi

# Or manually:
gunicorn portfolio_site.wsgi:application --bind 0.0.0.0:$PORT
```

## 6. Post-Deploy Verification

```bash
# Verify deployment checks pass
python manage.py check --deploy

# Verify migrations are up to date
python manage.py showmigrations
```

## 7. Admin Panel

Access the Django admin at `/admin/` to manage:
- Site Configuration (hero text, about section, footer)
- Photos, Videos, Posts, Blogs
- User accounts & permissions
- Cash Book transactions
- Contact messages

## File Structure (Production)

```
scratch/
├── accounts/           # Custom User model
├── portfolio_site/     # Django project settings
├── private_portal/     # Private dashboard app
├── public_portal/      # Public portfolio app
├── static/             # Source static files
├── templates/          # HTML templates
├── requirements.txt    # Python dependencies
├── Procfile           # Process file for deployment
├── .env.example       # Environment variable template
└── manage.py          # Django management
```

> **Note:** `db.sqlite3`, `venv/`, `__pycache__/`, and `media/` are excluded from version control via `.gitignore`.
