from __future__ import annotations
from datetime import datetime
from discord.ext import tasks
from discord.utils import format_dt
from lxml.etree import HTMLParser, parse
from io import StringIO
from json import dumps, loads
from typing import Any, List, Optional
from .exception import NotFoundReleaseNote

import aiofiles
import logging
import re
import pathlib


log = logging.getLogger(__name__)
parser = HTMLParser()  
releasenote_file = pathlib.Path(__file__).parent.parent.resolve() / 'data/releasenotes.json' 

def parse_html(html: str) -> Optional[str]:
    tree = parse(StringIO(html), parser)
    content = tree.xpath("//script[contains(text(), 'newsArticles')]/text()")
    return content


async def get_all_from_json(title : Optional[str] = None):
    async with aiofiles.open(releasenote_file, 'r', encoding='utf-8') as f:
        content = await f.read()
        loaded : List[dict[str, Any]] = loads(content)
        if title:
            data = [item for item in loaded if item.get("title") == title]
            if not data:
                raise NotFoundReleaseNote(f'You Searched :\n{title}')
            data = data[0]
        else:
            data = loaded[0]
        
    return data


async def get_titles_from_json() -> List[str]:
    try:
        async with aiofiles.open(releasenote_file, 'r', encoding='utf-8') as f:
            content = await f.read()
            loaded = loads(content)
            data = [item["title"] for item in loaded]
        return data
        
    except FileNotFoundError:
        return "Missing File : data/releasenotes.json" 


def change_to_dt(string: str):
    string = string.replace('Z', '+00:00')
    dt = datetime.fromisoformat(string)
    other = "[%s] " %str(dt)[2:10]
    other = other.replace('-', '')
    return other, format_dt(dt, 'f')


class PatchNoteManager:
    def __init__(self, app) -> None:
        self.app = app
        self.process.start()
        self.pattern = re.compile(r'newsArticles\\":(.*?),\\"newsArticlesMeta')

    @tasks.loop(minutes=10)
    async def process(self):
        url = "https://asphaltlegendsunite.com/news/"
        async with self.app.session.get(url) as response:
            if response.status != 200:
                return
            html = await response.text()

        content = parse_html(html)
        
        if not content:
            return log.error('아스팔트 패치노트 - newsArticles를 포함하는 스크립트를 검색 실패.')
        
        content = content[0]
        search = self.pattern.search(content)
        
        if search:
            result = search.group(1)
            result = re.sub(r'\\(")', r'\1', result)
            result = result.replace('\\\\', "\\")
            data = loads(result)
            
            del content, html, result
            
            final = []
            for item in data:
                if len(final) > 25:
                    break
                date = change_to_dt(item["publishDate"])
                title = date[0] + (item["title"]).strip() 
                if not final:
                    title = "(Latest) " + title
                final.append(
                    {
                        "url": url + item["slug"],
                        "title": title,
                        "description": (item["excerpt"]).strip(),
                        "publish_dt": date[1],
                        "thumbnail": item["thumbnail"]["url"]
                    }
                )
            try:
                async with aiofiles.open(releasenote_file, 'w+', encoding='utf-8') as f:
                    await f.write(dumps(final, ensure_ascii=False, indent=4))
                    log.warning('아스팔트 패치노트 - 패치노트 저장 완료')
                return

            except Exception as e:
                raise e
            
        else:
            return log.error('아스팔트 패치노트 - 필요한 데이터를 추출할 수 없음.')

    @process.before_loop
    async def ready(self):
        await self.app.wait_until_ready()