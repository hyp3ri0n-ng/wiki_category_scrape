import json
import re
import mwclient
import unicodecsv
import requests

def find_url(string):

    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]

def get_box(title):

    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "content",
        "rvslots": "main",
        "formatversion": "2",
        "format": "json",
        "rvsection" : 0
    }

    r = requests.get(url=url, params=params)
#    print(r.url)
    page_box = r.json()["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]
#    print(page_box)
    for line in page_box.split("\n"):
        type(line)
        if line.startswith("| website") or line.startswith("| homepage"):
            return find_url(line)

    return []


site = mwclient.Site('en.wikipedia.org')
disam = re.compile('\(.*\)$')
site_urls = []

def get_pages(cat):
    for p in cat:
        if p.namespace == 0:
            yield p
        elif p.namespace == 14:
            for pp in get_pages(p):
                yield pp


def filter_page(page):
    if not page.page_title:
        return False
    if page.page_title.startswith('List of'):
        return False
    return True


def clean_title(title):
    title = disam.sub('', title)
    return title.strip()


def page_url(page):
    slug = page.normalize_title(page.name)
    return 'http://%s/wiki/%s' % (page.site.host, slug)


def scrape_category(name):
    fh = open('%s.csv' % name, 'wb')
    columns = ['label', 'entity', 'entity_url', 'categories', 'backlinks']
    writer = unicodecsv.DictWriter(fh, fieldnames=columns)
    writer.writeheader()
    cat = site.categories.get(name)
    for page in get_pages(cat):
        if not filter_page(page):
            continue

        data = {
            'entity': page.page_title,
            'entity_url': page_url(page),
            'categories': json.dumps([c.page_title for c in page.categories()])
        }
        aliases = [page.page_title]
        aliases.extend([t for (lang, t) in page.langlinks()])

        backlinks = [x for x in page.backlinks()]
        data['backlinks'] = json.dumps([c.page_title for c in backlinks])
        for bl in backlinks:
            link = bl.redirects_to()
            if link is not None and link.page_title == page.page_title:
                aliases.append(bl.page_title)

        seen = set()
        for alias in aliases:
            alias = clean_title(alias)
            alias_norm = alias.lower()
            if alias_norm in seen:
                continue
            seen.add(alias_norm)
            row = dict(data)
            row['label'] = alias
            writer.writerow(row)

            row.pop('categories')
            row.pop('backlinks')
            title = row["entity"]
            box = get_box(title)
            for s in box:
                print(s)
                site_urls.append(s)
            

    fh.close()
    print(site_urls)
    return set(site_urls)
    
if __name__ == '__main__':
    pass
    #Scrape pages like this https://en.wikipedia.org/wiki/Category:Agriculture_in_the_United_States
    #for url in scrape_category('SOME_CATEGORY'):    
    #    print(url)
