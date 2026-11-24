"""Bounded common data extraction from rendered HTML; no page code execution."""
import json
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup


def extract_common(html, base, selector='', limit=20000):
    soup = BeautifulSoup(html, 'html.parser')
    roots = soup.select(selector) if selector else [soup]
    def elements(name):
        seen = set()
        for root in roots:
            candidates = ([root] if root.name in name else []) + root.find_all(name)
            for element in candidates:
                if id(element) not in seen:
                    seen.add(id(element))
                    yield element
    truncated = False
    budget = limit
    def text(value):
        nonlocal budget, truncated
        value = str(value or '')
        count = min(len(value), 2000, budget)
        truncated |= count < len(value)
        budget -= count
        return value[:count]
    images, headings, tables = [], [], []
    seen_images = set()
    for element in elements(['img']):
        source = element.get('data-src') or element.get('data-original') or element.get('src', '')
        url = urljoin(base, source)
        if not source or urlsplit(url).scheme not in ('http', 'https') or url in seen_images:
            continue
        seen_images.add(url)
        if len(images) == 100:
            truncated = True; break
        images.append({'url': text(url), 'alt': text(element.get('alt', ''))})
    budget = limit
    for element in elements(['h1','h2','h3','h4','h5','h6']):
        if len(headings) == 100:
            truncated = True; break
        headings.append({'level': int(element.name[1]), 'text': text(element.get_text(' ', strip=True))})
    budget = limit
    for table in elements(['table']):
        if len(tables) == 20:
            truncated = True; break
        rows, occupied = [], {}
        table_rows = [row for row in table.find_all('tr') if row.find_parent('table') is table]
        for ri, row in enumerate(table_rows[:100]):
            column = 0
            for cell in row.find_all(['td','th'], recursive=False):
                while (ri, column) in occupied: column += 1
                if column >= 50:
                    truncated = True; break
                try:
                    rowspan = max(1, int(cell.get('rowspan', 1)))
                    colspan = max(1, int(cell.get('colspan', 1)))
                except (ValueError, TypeError):
                    rowspan = colspan = 1
                truncated |= rowspan > 100-ri or colspan > 50-column
                value = text(cell.get('data-anclicker-text', cell.get_text(' ', strip=True)))
                for r in range(ri, min(100, ri+rowspan)):
                    for c in range(column, min(50, column+colspan)):
                        occupied[r,c] = value if (r,c) == (ri,column) else text(value)
                column += colspan
            width = max((c+1 for r,c in occupied if r==ri), default=0)
            rows.append([occupied.get((ri,c), '') for c in range(width)])
        truncated |= len(table_rows) > 100
        width = max(map(len, rows), default=0)
        rows = [row+['']*(width-len(row)) for row in rows]
        header = bool(table_rows and table_rows[0].find('th') and not table_rows[0].find('td'))
        caption = table.find('caption', recursive=False)
        tables.append({'caption': text(caption.get_text(' ',strip=True) if caption else ''),
                       'headers': rows[0] if header and rows else [], 'rows': rows[1:] if header else rows})
        try:
            geometry=json.loads(table.get('data-anclicker-layout', 'null'))
            if isinstance(geometry,dict):tables[-1]['layout']=geometry
        except (ValueError,TypeError):pass
    videos, seen_videos = [], set()
    for element in elements(['video', 'source', 'a', 'meta']):
        if element.name == 'source' and not element.find_parent('video'):
            continue
        source = element.get('src', '') if element.name in ('video', 'source') else element.get('href', '') if element.name == 'a' else element.get('content', '') if element.get('property', '') in ('og:video', 'og:video:url', 'og:video:secure_url') else ''
        url = urljoin(base, source)
        suffix = urlsplit(url).path.lower()
        if element.name == 'a' and not suffix.endswith(('.mp4', '.webm', '.mov', '.m4v', '.ogv', '.m3u8', '.mpd')):
            continue
        if not source or url in seen_videos or urlsplit(url).scheme not in ('http', 'https', 'blob'):
            continue
        seen_videos.add(url)
        if len(videos) >= 100:
            truncated = True
            break
        unsupported = url.startswith('blob:') or suffix.endswith(('.m3u8', '.mpd'))
        videos.append({'url': url, 'type': element.get('type', ''), 'name': element.get('title', '') or element.get_text(' ', strip=True)[:200], 'status': '分段流或临时地址，无法直接另存' if unsupported else '可尝试另存'})
    return {'videos': videos, 'images': images, 'headings': headings, 'tables': tables, 'truncated': truncated}
