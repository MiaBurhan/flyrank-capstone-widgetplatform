# Embeddable Widget & Lead-Capture Platform

Creates a widget, paste **one line** on any website, and collect leads that are validated,
spam-filtered, enriched and visible on a dashboard.

A platform that lets customers create embeddable widgets, signup forms, contact forms,
call-to-action popovers and install them on any website with a single <script> tag.
When a visitor interacts with the widget, the submission travels back to your backend, where it is validated, protected against abuse, enriched with location data, stored, and shown to the widget's owner in a dashboard.

## Run it
```bash
docker compose up --build
```
- API docs: http://localhost:8000/docs
- Dashboard: http://localhost:8000/dashboard (paste `ADMIN_API_KEY` from `.env`)

## Set the $ADMIN_API_KEY for the terminal
```
cd /home/green/Documents/Flyrank/widgetplatform
export ADMIN_API_KEY=$(grep '^ADMIN_API_KEY=' .env | cut -d= -f2)
echo $ADMIN_API_KEY
```
> replace the path with your Project directory  

## Try it 

```bash
# 1. create a widget (admin)
curl -X POST localhost:8000/admin/widgets \
  -H "X-Admin-Key: $ADMIN_API_KEY" -H "Content-Type: application/json" \
  -d '{"name":"My shop","allowed_origins":["http://localhost:5500"],"fields":["name","email","message"]}'
# -> response contains "embed_snippet": paste it into any page served from an allowed origin

# 2. submit a lead like a browser would
curl -X POST localhost:8000/public/widgets/WGT_ID/leads \
  -H "Origin: http://localhost:5500" -H "Content-Type: application/json" \
  -d '{"email":"jane@acme.com","name":"Jane","message":"Hello","elapsed_ms":9000}'
```

## Layers (each only calls the one below it)
```
api/        HTTP routes (public, admin, pages)        <- thin: parse request, call a service
services/   business logic (lead pipeline, spam, enrichment, widgets)
storage.py  all database queries (repositories)
models.py / database.py   tables and connection
schemas.py  validation of everything coming in from the internet
security.py admin key, rate limiter, origin allow-list
errors.py   domain errors -> HTTP codes in main.py
static/     embed.js (the widget) and dashboard.html
```

## Lead pipeline (`services/lead_service.py`)
guard (widget exists, origin allowed, rate limit) -> validate (pydantic) -> sanitize ->
enrich -> spam score (honeypot, speed, links, keywords, disposable email, duplicates, bot UA) ->
store as `accepted` or `spam`. Bots always get the same `201` answer.

## Tests
`pip install -r requirements.txt && python -m pytest`

## Known limits (good "next steps")
- Rate limiter is in-memory (use Redis with several workers).
- `elapsed_ms` comes from the browser, so it can be faked; sign a timestamp token to harden it.
- Tables are created on startup; add Alembic migrations when the schema starts changing.

## Turn off the server 

```bash
docker compose down
```
