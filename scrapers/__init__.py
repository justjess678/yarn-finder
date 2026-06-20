from .ice_yarns import IceYarnsScraper

SCRAPERS: dict[str, type] = {
    IceYarnsScraper.source_id: IceYarnsScraper,
}
