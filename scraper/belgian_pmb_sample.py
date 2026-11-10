"""
Belgian Chamber of Representatives: sample scrape of one MP's bills.

Downloads the "Auteur (doc. principal)" list for one MP in one legislature
and saves one row per document to a CSV.

How the site works (found by reading the page source):
  * The MP page loads its bill list with a background request to
    /site/wwwcfm/search/search_new_submit.cfm, passing a search query in the
    Chamber's own query language (db=FLWB is the legislative file database).
  * The server only answers that request if it looks like it came from the MP
    page (same session, Referer and X-Requested-With headers).
  * Each bill links to a dossier page whose address is predictable:
    flwbn.cfm?dossierID=<number>&legislat=<legislature>&inst=K

Etiquette: robots.txt asks for a 5-second crawl delay, so we wait 5 s between requests.

Run:  pip install requests beautifulsoup4
      python belgian_pmb_sample.py
"""
import csv
import time

import requests
from bs4 import BeautifulSoup

MEMBER_KEY = "08000"      # Jeroen Bergers (from the MP page address: key=08000)
LEGISLATURE = 56          # current legislature (since June 2024)
DELAY = 5                 # seconds between requests (robots.txt crawl-delay)
OUT = "bergers_bills_leg56.csv"

SITE = "https://www.dekamer.be"
MP_PAGE = (f"{SITE}/kvvcr/showpage.cfm?section=/depute&language=fr"
           f"&cfm=cvview54.cfm?key={MEMBER_KEY}&lactivity={LEGISLATURE}")
SEARCH = f"{SITE}/site/wwwcfm/search/search_new_submit.cfm"

# Same query the MP page sends. AUTEURM_TYPE_KODE 1 or 2 = author of the main
# document; 3 or 4 would be "signataire" (co-signer).
QUERY = (f"(({MEMBER_KEY}<in>AUTEURM_SLEUTEL)<and>(1<or>2<in>AUTEURM_TYPE_KODE))"
         f"<in>AUTEURM<AND>({LEGISLATURE}K*<in>SDOCNAME)<SORT:SDOCNAME desc>")

HEADERS = {
    "User-Agent": "UCR economics PhD research (contact: che.li@email.ucr.edu)",
    "Referer": MP_PAGE,
    "X-Requested-With": "XMLHttpRequest",
}


def doc_type(title):
    """Classify a document from the start of its title."""
    t = title.lower()
    if t.startswith("proposition de loi"):
        return "private member bill"
    if t.startswith("projet de loi"):
        return "government bill"
    if t.startswith("proposition de résolution"):
        return "resolution"
    return "other"


def main():
    s = requests.Session()
    s.headers.update(HEADERS)

    # Step 1: open the MP page first, like a browser would (sets the session).
    s.get(MP_PAGE, timeout=60)
    time.sleep(DELAY)

    # Step 2: ask the search endpoint for this MP's authored documents.
    params = {"start": 0, "language": "fr", "legislist": LEGISLATURE,
              "call": "/site/wwwcfm/depute/cvview54.cfm", "db": "FLWB", "query": QUERY}
    r = s.post(SEARCH, params=params, data={"libelle_fr": "", "libelle_nl": ""}, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.content.decode("utf-8"), "html.parser")

    # Step 3: each document is a row whose first cell links to "56Kxxxx".
    rows = []
    for link in soup.find_all("a"):
        dossier = link.get_text(strip=True)
        if not dossier.startswith(f"{LEGISLATURE}K"):
            continue
        record = {"dossier": dossier, "url": SITE + link["href"]}
        # The fields sit in a small table next to the link: label cell, value cell.
        details = link.find_parent("td").find_next_sibling("td")
        for tr in details.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) == 2:
                label = cells[0].get_text(" ", strip=True).rstrip(" :")
                record[label] = cells[1].get_text(" ", strip=True)
        record["type"] = doc_type(record.get("Titre", ""))
        record["authors"] = [a.strip() for a in record.get("Auteur(s)", "").split("|") if a.strip()]
        record["lead_author"] = record["authors"][0] if record["authors"] else ""
        rows.append(record)

    # Step 4: save. Keep the columns we care about, in a fixed order.
    cols = ["dossier", "type", "Titre", "lead_author", "authors",
            "Chambre (Etat d'avancement)", "Desc. Eurovoc principal", "url"]
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for rec in rows:
            rec = dict(rec, authors=" | ".join(rec["authors"]))
            w.writerow(rec)
    print(f"saved {len(rows)} documents to {OUT}")


if __name__ == "__main__":
    main()
