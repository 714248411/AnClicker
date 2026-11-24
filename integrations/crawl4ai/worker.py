"""One isolated Crawl4AI request; imported only by its dedicated Python runtime."""
import asyncio
import json
import sys
from pathlib import Path

async def crawl(request):
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    from bs4 import BeautifulSoup
    from extraction import extract_common
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, page_timeout=request['timeout'] * 1000,
        wait_until='domcontentloaded', css_selector=request['selector'] or None,
        wait_for=('css:' + request['wait_for']) if request['wait_for'] else None,
        word_count_threshold=0, verbose=False,
    )
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False, cdp_url=request['cdp_url'])) as crawler:
        page_info = {}
        table_script = Path(__file__).with_name('table-layout.js').read_text(encoding='utf-8')
        async def capture_title(page, **kwargs):
            page_info['title'] = await page.title()
            page_info['html'] = await page.evaluate("(selector) => {" + table_script + """

                const clone = document.documentElement.cloneNode(true);
                const originals = document.querySelectorAll('video');
                clone.querySelectorAll('video').forEach((v, i) => {
                    if (originals[i].currentSrc) v.setAttribute('src', originals[i].currentSrc);
                });
                const tables = document.querySelectorAll('table');
                const roots=selector?Array.from(document.querySelectorAll(selector)):[document.documentElement];
                let captured=0;
                clone.querySelectorAll('table').forEach((t, i) => {
                    t.removeAttribute('data-anclicker-layout');
                    const source=tables[i];
                    if(captured<20&&roots.some(root=>root===source||root.contains(source))){
                        captured++;const layout=tableLayout(source);
                        if(layout)t.setAttribute('data-anclicker-layout',JSON.stringify(layout));
                        const originals=Array.from(source.rows).filter(row=>row.closest('table')===source);
                        Array.from(t.rows).filter(row=>row.closest('table')===t).slice(0,100).forEach((row,r)=>{
                            Array.from(row.cells).slice(0,50).forEach((cell,c)=>cell.setAttribute('data-anclicker-text',originals[r].cells[c].innerText));
                        });
                    }
                });
                return clone.outerHTML;
            }""", request['selector'])
            page_info['base'] = await page.evaluate('document.baseURI')
            return page
        crawler.crawler_strategy.set_hook('before_retrieve_html', capture_title)
        result = await crawler.arun(url=request['url'], config=config)
        if not result.success or (result.status_code and result.status_code >= 400):
            raise RuntimeError(result.error_message or ('网页返回 HTTP ' + str(result.status_code)))
        markdown = getattr(result.markdown, 'raw_markdown', str(result.markdown or ''))
        text = BeautifulSoup(result.cleaned_html or '', 'html.parser').get_text(' ', strip=True)
        links = []
        for group in ('internal', 'external'):
            for item in (result.links or {}).get(group, []):
                links.append({'url': item.get('href', ''), 'text': item.get('text', '')})
        title = page_info.get('title') or (result.metadata or {}).get('title', '')
        if not title:
            title_tag = BeautifulSoup(result.html or '', 'html.parser').find('title')
            title = title_tag.get_text(strip=True) if title_tag else ''
        limit = request['max_chars']
        extra = extract_common(page_info.get('html', ''), page_info.get('base') or result.url, request['selector'], limit)
        extra['titles'] = {'title': title, 'headings': extra.pop('headings')}
        extra_truncated = extra.pop('truncated')
        return {'url': result.url, 'title': title,
                'markdown': markdown[:limit], 'text': text[:limit], 'links': links[:100], **extra,
                'truncated': len(markdown) > limit or len(text) > limit or len(links) > 100 or extra_truncated}

def main():
    output = Path(sys.argv[2])
    try:
        request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
        value = {'ok': True, 'result': asyncio.run(crawl(request))}
    except ModuleNotFoundError as error:
        value = {'ok': False, 'error': '网页抓取依赖不完整，请运行“准备网页抓取工具.cmd”修复。缺少模块：' + str(error.name)}
    except Exception as error:
        message = str(error)
        if 'Executable doesn' in message or 'playwright install' in message:
            message = '网页抓取浏览器未安装或已损坏，请运行“准备网页抓取工具.cmd”修复。\n' + message
        value = {'ok': False, 'error': message}
    output.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    return 0 if value['ok'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
