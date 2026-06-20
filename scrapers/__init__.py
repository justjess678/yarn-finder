from .ice_yarns import IceYarnsScraper
from .lovecrafts import LoveCraftsScraper

SCRAPERS: dict[str, type] = {
    IceYarnsScraper.source_id: IceYarnsScraper,
    LoveCraftsScraper.source_id: LoveCraftsScraper,
}
