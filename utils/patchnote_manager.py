from __future__ import annotations
from aiohttp import ClientSession
from discord.ext import tasks
from discord.utils import format_dt
from lxml import etree
from io import StringIO
from datetime import datetime
from json import dumps, loads
from typing import List, Optional

import aiofiles
import logging
import re
import os, sys


sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
log = logging.getLogger(__name__)


class PatchNoteManager:
    def __init__(self) -> None:
        pass


    async def get_all_from_json(self) -> List[dict]:
        try:
            async with aiofiles.open('data/releasenotes.json', 'r', encoding= 'utf-8') as f:
                content = await f.read()
                loaded = loads(content)
                data = [item for item in loaded]
            return data
            
        except Exception:
            raise FileNotFoundError("Missing File : data/releasenotes.json")
        

    async def get_titles_from_json(self) -> List[str]:
        try:
            async with aiofiles.open('data/releasenotes.json', 'r', encoding= 'utf-8') as f:
                content = await f.read()
                loaded = loads(content)
                data = [item["title"] for item in loaded]
            return data
            
        except Exception:
            raise FileNotFoundError("Missing File : data/releasenotes.json")  


    def change_to_dt(self, string: str, /):
        string = string.replace('Z', '+00:00')
        dt = datetime.fromisoformat(string)
        other = "[%s] " %str(dt)[2:10]
        other = other.replace('-', '')
        return other, format_dt(dt, 'f')


    async def fetch_html(self, url: str) -> Optional[str]:
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return
                return await response.text()


    def parse_html(self, html: str):
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(html), parser=parser)
        return tree


    @tasks.loop(minutes= 5)
    async def process(self):
        name = 'data/releasenotes.json'
        url = "https://asphaltlegends.com/news/"
        
        html = await self.fetch_html(url)
        tree = self.parse_html(html)

        content : str = tree.xpath("//script[contains(text(), 'newsArticles')]/text()")
        
        if not content:
            return log.error('newsArticles를 포함하는 스크립트를 검색 실패.')
        
        content = content[0]
        pattern = re.compile(r'newsArticles\\":(.*?),\\"newsArticlesMeta')
        search = pattern.search(content)
        
        if search:
            result = search.group(1)
            result = re.sub(r'\\(")', r'\1', result)
            result = result.replace('\\\\', "\\")
            data = loads(result)
            
            del content, html, result, pattern, tree
            
            final = []
            for item in data:
                if len(final) >= 25:
                    break
                if not item['hideInFeed']:
                    date = self.change_to_dt(item["publishDate"])
                    title = date[0] + (item["title"]).strip() if final else "(Latest) " + date[0] + (item["title"]).strip()
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
                with open(name, 'w+', encoding='utf-8') as f:
                    f.write(dumps(final, ensure_ascii= False, indent= 4))
                return None

            except Exception as e:
                raise e
            
        else:
            return log.error('필요한 데이터를 추출할 수 없음.')

patchnotemanager = PatchNoteManager()