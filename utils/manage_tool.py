from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor

import os, sys
import csv
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

__slots__ = (
    'Clubclash',
    'Weeklycompetition',
    'Elite',
    'Carhunt'
)


class ClubClash:
    def __init__(self) -> None:
        self.executor = ThreadPoolExecutor()  
    
    async def open_db(self, num: int, /):
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(
            self.executor, self.read_csv, num
        )
        return data

    def read_csv(self, num):
        with open(file='data/clash_db.csv', mode='r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            data = [row[num] for row in reader]
        data.pop(0)  # 첫 번째 행 제거
        return data

    async def area(self):
        return await self.open_db(0)

    async def car_name(self):
        return await self.open_db(1)

    async def car_class(self):
        return await self.open_db(2)

    async def laptime(self):
        return await self.open_db(3)

    async def link(self):
        return await self.open_db(4)


class WeeklyCompetition:
    def __init__(self) -> None:
        self.executor = ThreadPoolExecutor()  
    
    async def open_db(self, num: int, /):
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(
            self.executor, self.read_csv, num
        )
        return data

    def read_csv(self, num):
        with open(file='data/weekly_db.csv', mode='r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            data = [row[num] for row in reader]
        data.pop(0)  # 첫 번째 행 제거
        return data

    async def area(self):
        return await self.open_db(0)
    
    async def car_name(self):
        return await self.open_db(1)
    
    async def laptime(self):
        return await self.open_db(3)
    
    async def link(self):
        return await self.open_db(4)


class EliteCup:
    def __init__(self) -> None:
        self.executor = ThreadPoolExecutor()  
    
    async def open_db(self, num: int, /):
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(
            self.executor, self.read_csv, num
        )
        return data

    def read_csv(self, num):
        with open(file='data/elite_db.csv', mode='r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            data = [row[num] for row in reader]
        data.pop(0)  # 첫 번째 행 제거
        return data

    async def car_class(self):
        return await self.open_db(0)

    async def area(self):
        return await self.open_db(1)

    async def car_name(self):
        return await self.open_db(2)
    
    async def laptime(self):
        return await self.open_db(3)
    
    async def link(self):
        return await self.open_db(4)


class CarhuntRiot:
    def __init__(self) -> None:
        self.executor = ThreadPoolExecutor()  
    
    async def open_db(self, num: int, /):
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(
            self.executor, self.read_csv, num
        )
        return data

    def read_csv(self, num):
        with open(file='data/carhunt_db.csv', mode='r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            data = [row[num] for row in reader]
        data.pop(0)  # 첫 번째 행 제거
        return data

    async def car_name(self):
        return await self.open_db(0)

    async def area(self):
        return await self.open_db(1)

    async def laptime(self):
        return await self.open_db(3)

    async def link(self):
        return await self.open_db(4)


Carhunt = CarhuntRiot()
Clubclash = ClubClash()
Elite = EliteCup()
Weeklycompetition = WeeklyCompetition()