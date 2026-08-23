# Yarnpalette

A Django web app that finds yarn colours matching a reference image or colour you pick.

## Setup

```bash
pip install -r requirements.txt
python manage.py migrate
```

Copy `.env.example` to `.env` and set a real `SECRET_KEY` before running anywhere other than your local machine.

## Running the dev server

```bash
python manage.py runserver
```

Then open http://127.0.0.1:8000.

## Populating the database

Yarn data is scraped separately and stored in the database. The web search runs against whatever is already in the DB, so scrape first.

Scraping uses Selenium + Chromedriver (`lib/chromedriver-linux64/chromedriver`). It can take a while depending on how many pages the site has.

### Quick start: Refresh a brand

To delete old data and re-scrape a brand in one command (recommended):

```bash
python manage.py refresh_brand --source hobbii
```

This deletes all existing entries for that brand and re-scrapes everything fresh. Yarn types are automatically normalized to standard categories in the process.

### Alternative: Scrape without deleting

To add or update yarn data without removing existing entries:

```bash
# Scrape all sources
python manage.py scrape_yarns

# Scrape one source only
python manage.py scrape_yarns --source ice_yarns
```

### Syncing data between local and production

To copy yarn data from your local database to production, replacing all existing entries for that brand:

#### Step 1: Export from local

On your local machine, export the brand data to a JSON file:

```bash
python manage.py export_brand --source hobbii --output hobbii.json
```

This creates a `hobbii.json` file containing all hobbii yarns with their colors, fiber info, and yarn types.

#### Step 2: Transfer to production

You can transfer the JSON file in a few ways:

**Option A: Via git (recommended)**
```bash
git add hobbii.json
git commit -m "Add hobbii data export"
git push origin webapp
```

Then redeploy on Render, and the file will be available.

**Option B: Via Render shell upload**
Use the Render dashboard's file upload feature or copy/paste the JSON content.

**Option C: Email/messaging**
Copy the file content and paste it into the Render shell.

#### Step 3: Import on production

In the Render shell, run:

```bash
python manage.py import_brand --source hobbii --file hobbii.json
```

This will:
1. Delete all existing hobbii entries in production
2. Import all entries from the JSON file
3. Report how many yarns were imported

The import includes all data: URLs, images, colors, fiber content, and yarn types.

#### Example workflow

```bash
# Local: Export hobbii data
python manage.py export_brand --source hobbii

# Commit and push
git add hobbii.json
git commit -m "Export hobbii data for sync"
git push origin webapp

# On Render: Pull and import
git pull origin webapp
python manage.py import_brand --source hobbii --file hobbii.json
```

### Advanced: Delete entries (without re-scraping)

To remove all yarn entries from a specific source without re-scraping:

```bash
# Delete with confirmation prompt
python manage.py delete_yarns --source hobbii

# Skip confirmation (for scripts/automation)
python manage.py delete_yarns --source hobbii --confirm
```

### Normalizing yarn types

Yarn type/weight data is automatically normalized to standard categories (lace, fingering, sport, dk, worsted, aran, bulky, super bulky, jumbo) during scraping.

To normalize existing yarn types that were scraped before this feature:

```bash
python manage.py normalize_yarn_types
```

### Seeding test data (dev only)

If you can't run the real scraper (e.g. the site has changed), seed 22 placeholder yarns spanning the colour spectrum:

```bash
python manage.py seed_test_yarns
```

## How to add a new yarn brand

1. Create `scrapers/<brand_name>.py` and write a class that extends `BaseScraper`:

```python
from .base import BaseScraper

class MyBrandScraper(BaseScraper):
    source_id    = "my_brand"       # used in the DB and as the --source flag
    display_name = "My Brand"       # shown in the rolling gallery on the homepage
    site_url     = "https://mybrand.com"

    def scrape(self) -> list[dict]:
        # Return a list of dicts. Required keys:
        #   name (str), url (str), image_url (str)
        # Optional keys (stored if present, blank otherwise):
        #   fiber (str)  e.g. "100% Merino Wool"
        #   yarn_type (str)  one of: lace, fingering, sport, dk, worsted, aran, bulky, super_bulky, jumbo
        #   skein_weight_grams (int)
        return [...]
```

2. Register it in `scrapers/__init__.py`:

```python
from .my_brand import MyBrandScraper

SCRAPERS = {
    ...,
    MyBrandScraper.source_id: MyBrandScraper,
}
```

That's it. The management command, admin, and homepage gallery all pick it up automatically.

## How searching works

1. Upload a reference image or pick a colour with the colour picker.
2. The app extracts the dominant non-white colour from the image (or uses the picked hex directly).
3. That colour is compared against every yarn in the database using Euclidean distance in RGB space.
4. Results are ranked closest-first and shown in a paginated grid. Clicking a yarn goes to its product page.

Optionally filter by fiber content, yarn type, or skein weight before searching.

## Admin

Django admin is at `/admin/`. From there you can:
- Browse and edit yarn records (including manually filling in fiber/type/weight).
- Trigger a re-scrape for selected yarns via the action dropdown.

Create a superuser if you haven't already:

```bash
python manage.py createsuperuser
```

## Project structure

```
yarn_finder/      Django project settings
yarns/            Main app - Yarn model, views, URLs, admin
  management/
    commands/
      scrape_yarns.py           Populate DB from scrapers
      refresh_brand.py          Delete and re-scrape a brand
      export_brand.py           Export brand data to JSON
      import_brand.py           Import brand data from JSON (replaces existing)
      delete_yarns.py           Delete entries by source
      normalize_yarn_types.py   Normalize yarn weights to standard categories
      seed_test_yarns.py        Dev seed data
scrapers/         One file per yarn brand
  base.py         BaseScraper ABC
  ice_yarns.py    Ice Yarns implementation
color/            Colour extraction and comparison logic
templates/        HTML templates
static/           CSS
lib/              Chromedriver binary
```
