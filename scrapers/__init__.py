from .hobbii import HobbiiScraper
from .ice_yarns import IceYarnsScraper
from .icewear import IcewearScraper
from .istex import IstexScraper
from .king_cole import KingColeScraper
from .lovecrafts import LoveCraftsScraper
from .yarnspirations import YarnspirationsScraper

SCRAPERS: dict[str, type] = {
    IceYarnsScraper.source_id: IceYarnsScraper,
    LoveCraftsScraper.source_id: LoveCraftsScraper,
    HobbiiScraper.source_id: HobbiiScraper,
    IcewearScraper.source_id: IcewearScraper,
    IstexScraper.source_id: IstexScraper,
    YarnspirationsScraper.source_id: YarnspirationsScraper,
    KingColeScraper.source_id: KingColeScraper,
}
