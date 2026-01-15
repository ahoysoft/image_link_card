# Social Card Service - Project Specification

## Overview

A service that generates social media card preview links. Users upload images and specify redirect URLs, receiving a unique URL that:
- Serves rich meta tags (Twitter Card, OpenGraph) to social media crawlers
- Redirects regular users to the specified destination URL

---

## Core Features

### 1. Social Card Link Generation

**Input:**
- Image file (uploaded)
- Destination URL (where users get redirected)
- Card type: `summary` | `summary_large_image`
- Title (required)
- Description (optional)

**Output:**
- Unique URL (e.g., `https://service.com/c/abc123`)

**Behavior:**
- Bot user-agents → HTML page with meta tags + image reference
- Regular users → 302 redirect to destination URL

### 2. Image Processing

Uploaded images are automatically transformed to meet social card requirements:

| Card Type | Dimensions | Max Size |
|-----------|------------|----------|
| `summary` | 144x144 min, 1:1 ratio recommended | 5MB |
| `summary_large_image` | 1200x628 (2:1 ratio) | 5MB |

**Processing:**
- Resize/crop to target dimensions (preserve aspect ratio, pad if needed)
- Convert to PNG or JPG
- Optimize file size
- Store original + processed versions

### 3. API

**Authentication:** API Key (header: `X-API-Key`)

#### Endpoints

```
POST /api/v1/cards
  - Create a new social card link
  - Multipart form: image file + JSON metadata
  - Returns: card ID, generated URL

GET /api/v1/cards
  - List user's cards (paginated)

GET /api/v1/cards/:id
  - Get card details

PATCH /api/v1/cards/:id
  - Update card metadata (title, description, destination URL)
  - Cannot change image (create new card instead)

DELETE /api/v1/cards/:id
  - Delete card and associated images

GET /api/v1/keys
  - List user's API keys

POST /api/v1/keys
  - Create new API key
  - Returns: key (shown once)

DELETE /api/v1/keys/:id
  - Revoke API key
```

### 4. Developer Dashboard

#### Authentication
- Email/password with email verification
- Google OAuth

#### Tier System

| Tier | Monthly Card Limit | Notes |
|------|-------------------|-------|
| Free | 5 | Default for all new users |
| Core | 50 | Admin-assigned |
| Premium | 500 | Admin-assigned |

- All new users start on **Free** tier immediately (no approval needed)
- Monthly card count resets on the 1st of each month
- Admin can upgrade/downgrade any user's tier
- Admin role is separate from tier (admin can be on any tier)

#### Dashboard Pages

**Public:**
- Landing page with service description
- Login / Register

**Authenticated:**
- **Cards** - List, create, edit, delete social card links
- **Card Creator Form** - Upload image, set destination URL, title, description, card type
- **API Keys** - Create, list, revoke API keys
- **Usage Stats** - View count per card, monthly usage
- Account settings (profile, change password)

**Admin:**
- **User Management** - List users, upgrade/downgrade tiers, toggle admin status
- **All Cards** - View/manage all cards in system
- **System Stats** - Total users, cards, views

---

## Technical Architecture

### Stack

**Backend:**
- Python + Flask (application factory pattern)
- SQLAlchemy ORM
- PostgreSQL (Render managed)
- Flask-Login for session management

**Frontend:**
- Server-side rendered (Jinja2 templates)
- Minimal JavaScript for interactivity (no SPA framework)

**Image Processing:**
- Pillow (Python Imaging Library)

**Utilities:**
- nanoid (for generating card slugs)

**File Storage:**
- Cloudflare R2 (S3-compatible) for production
- Local filesystem for development

**Email:**
- Resend (transactional emails for verification, notifications)

**Authentication:**
- Flask-Login + Flask-Dance (Google OAuth)
- Werkzeug password hashing

**Deployment:**
- Render (web service + PostgreSQL)

### Database Schema

```
users
  - id (UUID)
  - email (unique)
  - password_hash (nullable for OAuth-only users)
  - tier: free | core | premium (default: free)
  - is_admin: boolean
  - email_verified: boolean
  - monthly_card_count: integer
  - card_count_reset_at: datetime
  - created_at
  - updated_at

oauth_accounts
  - id
  - user_id (FK)
  - provider: google
  - provider_user_id
  - created_at

api_keys
  - id (UUID)
  - user_id (FK)
  - key_hash
  - key_prefix (for lookup)
  - name (user-provided label)
  - last_used_at
  - created_at
  - revoked_at (nullable)

cards
  - id (UUID)
  - user_id (FK)
  - slug (unique, nanoid - e.g., "V1StGXR8_Z5jdHi6B-myT")
  - title
  - description
  - destination_url
  - card_type: summary | summary_large_image
  - image_original_key
  - image_processed_key
  - view_count
  - created_at
  - updated_at
```

### URL Structure

- Landing: `https://service.com/`
- Auth: `https://service.com/login`, `/register`, `/logout`
- Dashboard: `https://service.com/dashboard/*`
- API: `https://service.com/api/v1/*`
- Admin: `https://service.com/admin/*`
- Card links: `https://service.com/c/:slug`
- Card images: `https://service.com/i/:slug.png`

---

## Security Considerations

- API keys stored as hashes (like passwords)
- API key shown only once on creation
- CSRF protection on dashboard forms
- Input validation on all user inputs
- Sanitize/validate destination URLs (prevent open redirect abuse)
- Image upload validation (file type, size limits)

---

## Implementation Status: COMPLETE

| Phase | Status |
|-------|--------|
| Project Structure & Foundation | Done |
| Database Models | Done |
| Storage & Image Processing | Done |
| Authentication | Done |
| REST API | Done |
| Dashboard UI | Done |
| Public Card Serving | Done |
| Admin Functionality | Done |

---

## Decisions Made

| Decision | Choice |
|----------|--------|
| Frontend | Server-rendered templates (Jinja2) |
| Deployment | Render (web service + PostgreSQL) |
| Email provider | Resend |
| Image storage | Cloudflare R2 |
| Admin bootstrap | One-time manual creation directly in database |
| Card slug format | Nanoid (URL-safe, collision-resistant) |
| OAuth providers | Google only |
| User access model | Tier-based (Free/Core/Premium) with monthly limits |
| Domain | Custom domain (configure later) |

---

## Environment Variables

```
SECRET_KEY          - Flask secret key
DATABASE_URL        - PostgreSQL connection string
BASE_URL            - Public URL of the service

# R2 Storage
R2_ACCOUNT_ID
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY
R2_BUCKET_NAME
R2_PUBLIC_URL

# Email
RESEND_API_KEY
MAIL_FROM

# Google OAuth
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
```

---

## Out of Scope (Future)

- Payment/billing integration
- Custom domains for card links
- Team/organization accounts
- Webhook notifications
- Card expiration/TTL
- A/B testing multiple images per card
- Rate limiting

---

## Deployment Steps

1. Create Render PostgreSQL database
2. Set up Cloudflare R2 bucket with public access
3. Create Resend account and verify domain
4. Create Google OAuth credentials
5. Configure environment variables in Render
6. Deploy via render.yaml or manual setup
7. Run database migrations: `flask db upgrade`
8. Create first admin user directly in database:
   ```sql
   UPDATE users SET is_admin = true WHERE email = 'admin@example.com';
   ```
