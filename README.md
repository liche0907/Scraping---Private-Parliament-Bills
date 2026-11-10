# Scraping Private Members' Bills — Belgian Chamber of Representatives

A small, polite scraper that collects every bill a given Member of Parliament authored in one legislature, from the Belgian Chamber's website (dekamer.be), and saves one row per bill. Built as a feasibility test for a comparative study of private members' bills.

## Structure

| Path | Contents |
|---|---|
| `scraper/belgian_pmb_sample.py` | the scraper: replays the MP page's background search request, then follows each bill's dossier page |
| `data/bergers_bills_leg56.csv` | sample output: one MP, legislature 56 (since June 2024) — dossier, type, title, lead author, co-authors, status, Eurovoc topic, link |
| `docs/belgian_pmb_feasibility.pdf` | feasibility note: how the site works and what a full collection would take |

## Run

```
pip install requests beautifulsoup4
python scraper/belgian_pmb_sample.py
```

Change `MEMBER_KEY` and `LEGISLATURE` at the top of the script for another MP or legislature. The script waits 5 seconds between requests, as the site's robots.txt asks.
