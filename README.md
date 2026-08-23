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

```bash
# Scrape all sources
python manage.py scrape_yarns

# Scrape one source only
python manage.py scrape_yarns --source ice_yarns
```

Scraping uses Selenium + Chromedriver (`lib/chromedriver-linux64/chromedriver`). It can take a while depending on how many pages the site has.

### Normalizing yarn types

Yarn type/weight data from scrapers is automatically normalized to standard categories (lace, fingering, sport, dk, worsted, aran, bulky, super bulky, jumbo) so the filter works reliably.

To normalize existing yarn types that were scraped before this feature:

```bash
python manage.py normalize_yarn_types
```

### Refreshing a brand

To delete and re-scrape all entries from a brand in one command:

```bash
python manage.py refresh_brand --source hobbii
```

### Deleting yarn entries

To remove all yarn entries from a specific source:

```bash
# Delete with confirmation prompt
python manage.py delete_yarns --source hobbii

# Skip confirmation (for scripts/automation)
python manage.py delete_yarns --source hobbii --confirm
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
