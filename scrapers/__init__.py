from .hobbii import HobbiiScraper
from .ice_yarns import IceYarnsScraper
from .icewear import IcewearScraper
from .lovecrafts import LoveCraftsScraper

SCRAPERS: dict[str, type] = {
    IceYarnsScraper.source_id: IceYarnsScraper,
    LoveCraftsScraper.source_id: LoveCraftsScraper,
    HobbiiScraper.source_id: HobbiiScraper,
    IcewearScraper.source_id: IcewearScraper,
}
