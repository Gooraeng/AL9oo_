from __future__ import annotations
from datetime import time, timezone
from discord import app_commands, Interaction, Embed
from discord.ext import commands, tasks
from discord.utils import utcnow
from typing import List, Literal, Optional, TYPE_CHECKING
from utils.check import match_helper
from utils.embed_color import failed
from utils.exception import NotFilledRequiredField, SearchFailed, SearchFailedBasic
from utils.paginator import T_Pagination

if TYPE_CHECKING:
    from al9oo import Al9oo

import numpy


loop_when = time(hour=23, minute=59, second=45, tzinfo=timezone.utc)
search_failed_embed = Embed(colour=failed)


class Reference(commands.Cog):
    def __init__(self, app : Al9oo) -> None:
        self.app = app
        self.setup()
        # 레퍼런스 변수
        
    def setup(self):
        self.carhunt_carname = self.app.carhunt_CAR_NAME
        self.carhunt_map = self.app.carhunt_AREA
        self.carhunt_laptime = self.app.carhunt_LAP_TIME
        self.carhunt_link = self.app.carhunt_LINK
        
        self.clash_class = self.app.clash_CLASS
        self.clash_carname = self.app.clash_CAR_NAME
        self.clash_map = self.app.clash_AREA
        self.clash_laptime = self.app.clash_LAP_TIME
        self.clash_link = self.app.clash_LINK
        
        self.elite_class = self.app.elite_CLASS
        self.elite_carname = self.app.elite_CAR_NAME
        self.elite_map = self.app.elite_AREA
        self.elite_laptime = self.app.elite_LAP_TIME
        self.elite_link = self.app.elite_LINK
        
        self.weekly_carname = self.app.weekly_CAR_NAME
        self.weekly_map = self.app.weekly_AREA
        self.weekly_laptime = self.app.weekly_LAP_TIME
        self.weekly_link = self.app.weekly_LINK

    @app_commands.command(
        description='You can watch Car hunt Riot videos!',
        extras={"permissions" :["Embed Links"]}
    )
    @app_commands.describe(car='What\'s the name of Car?')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def carhunt(self, interaction : Interaction, car : str):
        await interaction.response.defer(thinking=True)
        
        car = car.upper()
        car_data = self.carhunt_carname
        map_data = self.carhunt_map
        lap_time_data = self.carhunt_laptime
        link_data = self.carhunt_link
        
        try:   
            if car in car_data:
                # 입력한 차량명과 일치하는 차량의 인덱스 넘버 변수 선언 
                CarName_found = car_data.index(car)
                return await interaction.followup.send(f'```Car    : {car_data[CarName_found]}\nMap    : {map_data[CarName_found]}\nRecord : {lap_time_data[CarName_found]}```{link_data[CarName_found]}')
            else:
                raise SearchFailed('CAR', find=car, original_list=car_data)
        
        except SearchFailed as e:
            search_failed_embed.description = e.message
            await interaction.followup.send(embed=search_failed_embed)

    @carhunt.autocomplete('car')
    async def chs_autocpletion(
        self,
        interaction : Interaction,
        current : str
    ) -> List[app_commands.Choice[str]]:
        car_name = self.carhunt_carname
        
        car_name = [
            app_commands.Choice(name=choice, value=choice)
            for choice in car_name 
            if current.lower().strip() in choice.lower().strip()
        ]
        
        if len(car_name) > 8:
            car_name = car_name[:8]
        return car_name
    
    @app_commands.command(
        description='Check Club Clash references!',
        extras={
            "permissions" : ["Embed Links"],
            "howto" : [
                "**[Way 1]**\n* Search `map` and execute.",
                "**[Way 2]**\n* Search `map`. Then, selectable `class` list will come out. So, Choose it and execute.",
                "**[Way 3]**\n* Same way with Way 2 except for executing. Just select `car` and execute!"
            ],
            "sequence" : "`map` -> `class` -> `car`",
        }
    )
    @app_commands.describe(
        area='Search map.',
        car_class='What class of Car?',
        car_name="What's the name of Car?"
    )
    @app_commands.rename(area='map', car_class='class', car_name='car')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def clash(
        self,
        interaction: Interaction,
        area : str,
        car_class : Optional[str] = None,
        car_name : Optional[str] = None
    ):
        await interaction.response.defer(thinking=True)
        
        map_data = self.clash_map
        class_data = self.clash_class
        car_data = self.clash_carname
        link_data = self.clash_link
        lap_time_data = self.clash_laptime
        same2 = None
        
        try:
            # ./utils/manage_tool.py 참고            
            if area in map_data :
                area_list = list(filter(lambda x: map_data[x]==area, range(len(map_data))))               
                car_data_filtered = [car_data[x] for x in area_list]
                class_data_filtered = [class_data[x] for x in area_list]
                lap_time_data_filtered = [lap_time_data[x] for x in area_list]
                link_data_filtered = [link_data[x] for x in area_list]
                true_class_data = list(set(class_data_filtered))
                true_class_data.sort()
                
                if car_class is None :
                    if car_name is None:
                        embeds = []      
                        
                        for cls in true_class_data:
                            embed = Embed(
                                title=f'<:yt:1178651795472527401>  {area}',
                                description= f"{cls} CLASS",
                                colour=0xff0000
                            )
                            
                            for i, _ in enumerate(area_list):
                                if cls == class_data_filtered[i]:
                                    name = car_data_filtered[i]
                                    record = lap_time_data_filtered[i]
                                    link = link_data_filtered[i]
                                    
                                    embed.add_field(
                                        name=f"{i + 1}. {name}",
                                        value=f"[- {record}]({link})",
                                        inline=False
                                    )
 
                            embeds.append(embed)
                        
                        del class_data_filtered, car_data_filtered, link_data_filtered, lap_time_data_filtered, true_class_data, area_list
                        
                        view = T_Pagination(embeds)
                        view._author = interaction.user
                        view.message = await interaction.edit_original_response(embed=view.initial, view=view)
                    else:
                        raise NotFilledRequiredField('Class must be filled when you try to search cars.')

                else:
                    car_class = car_class.upper()
                    if car_class in true_class_data:
                        if car_name is None:
                            car_name_none_embed = Embed(title= f"<:yt:1178651795472527401>  {area}", description=f"{car_class} CLASS", colour=0xFF0000)
                    
                            rest_list_1 = list(filter(lambda x: map_data[x]==area, range(len(map_data))))
                        
                            for i in rest_list_1:
                                if class_data_filtered[i] == car_class:
                                    car_name_none_embed.add_field(
                                        name="",
                                        value=f"[- `({lap_time_data_filtered[i]})` {car_data_filtered[i]}]({link_data_filtered[i]})\n\n",
                                        inline=False
                                    )
                            return await interaction.followup.send(embed=car_name_none_embed)
                    
                        else:
                            if car_name.upper() in car_data:
                                same2 = int(numpy.intersect1d(
                                    numpy.where(numpy.array(map_data)==area),
                                    numpy.where(numpy.array(car_data)==car_name)
                                ))
                                
                                # 정상 실행
                                if area == map_data[same2] and car_class == class_data[same2] and car_name == car_data[same2]:
                                    return await interaction.followup.send(f'```Car    : {car_data[same2]}\nMap    : {map_data[same2]}\nRecord : {lap_time_data[same2]}```{link_data[same2]}')  
                                raise SearchFailedBasic('Club Clash')
                            else:
                                raise SearchFailed(type='CAR', find=car_name, original_list=car_data)
                    else:
                        raise SearchFailed(type='CLASS', find=car_class, original_list=class_data)  
            else:
                raise SearchFailed(type='MAP', find=area, original_list=map_data)       
        
        except TypeError as e:
            if area not in map_data:
                area_suggestion = match_helper(area, map_data)
                area_suggestion = f'* Map : {area_suggestion}\n'
            else:
                area_suggestion = ''
            
            if car_name.upper() not in car_data:
                car_suggestion = match_helper(car_name, car_data)
                car_suggestion = f'* Car : {car_suggestion}'
            else:
                car_suggestion = ''
                
            suggest = f'I think you tried to search..\n{area_suggestion}{car_suggestion}'
            search_failed_embed.description = f'Parameters that you selected don\'t match. Please Check again.\n{suggest}'
            await interaction.followup.send(embed=search_failed_embed)
            
        except (SearchFailed, SearchFailedBasic, NotFilledRequiredField) as e:
            search_failed_embed.description = e.message
            await interaction.followup.send(embed=search_failed_embed)
            
    @clash.autocomplete('area')
    async def area_autocompletion(
        self,
        interaciton : Interaction,
        current : str,
    ) -> List[app_commands.Choice[str]]:

        result1 = [
            app_commands.Choice(name=choice, value=choice)
            for choice in list(set(self.clash_map))
            if current.lower().strip() in choice.lower().strip()
        ]
    
        if len(result1) > 10:
            result1 = result1[:10] 
        return result1 
    
    @clash.autocomplete('car_class')
    async def class_autocompletion(
        self,
        interaction : Interaction,
        current : str,    
    ) -> List[app_commands.Choice[str]]:
        
        # 리스트 선언
        map_data = self.clash_map
        class_data = self.clash_class
        
        # area_autocompletion을 통해 찾으려는 맵과 관련된 요소를 불러옴.
        # 여기선 딕셔너리를 이용하여 불러옴 >> dict_values(['Sacred Heart', ''])
        # 리스트로 변환
        aa = list(interaction.namespace.__dict__.values())
        
        # 검색된 맵의 행들을 인덱스로 가지는 리스트를 선언함
        # 이 때, map_data와 aa의 value가 일치하도록 필터링 (aa[0])
        rest_list : List[str] = list(filter(lambda x: map_data[x]==str(aa[0]), range(len(map_data))))
        rest_list = list(set([class_data[i] for i in rest_list]))
        
        rest_list = [
            app_commands.Choice(name=choice,value=choice)
            for choice in rest_list
            if current.lower().strip() in choice.lower().strip()
        ]
        return rest_list
        
    @clash.autocomplete(name='car_name')
    async def car_autocompletion(
        self,
        interaction : Interaction,
        current : str, 
    ) -> List[app_commands.Choice[str]]:
        # 리스트 선언
        map_data = self.clash_map
        class_data = self.clash_class
        car_data = self.clash_carname
        
        # class_autocompletion의 결과와 연동이 어려워 같은 방법 반복
        aa = list(interaction.namespace.__dict__.values())
        
        rest_list = list(filter(lambda x: map_data[x]==str(aa[0]), range(len(map_data))))  
        rest_list = list(set([car_data[i] for i in rest_list if class_data[i]==str(aa[1])]))
        
        rest_list = [
            app_commands.Choice(name=choice, value=choice)
            for choice in rest_list
            if current.lower().strip() in choice.lower().strip()
        ]
        
        if len(rest_list) > 25:
            rest_list = rest_list[:25]
        return rest_list 

    @app_commands.command(
        description='Let you know elite cup reference!',
        extras={
            "permissions" : ["Embed Links"],
            "howto" : [
                "**[Way 1]**\n* Select `class` and execute.",
                "**[Way 2]**\n* Select `class`. Then, selectable `car` list will come out. So, Choose it and execute."
            ],
            "sequence" : "`class` -> `car`",
        }
    )
    @app_commands.describe(class_type='What class of Car?', car_name='What\'s the name of Car?')
    @app_commands.rename(class_type='class', car_name='car')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def elite(
        self,
        interaction: Interaction,
        class_type : Literal["S", "A", "B", "C"], 
        car_name : Optional[str] = None
    ):     
        await interaction.response.defer(thinking=True)
        class_type = class_type.upper() 
        
        class_data = self.elite_class
        map_data = self.elite_map
        car_data = self.elite_carname
        lap_time_data = self.elite_laptime
        link_data = self.elite_link
        
        try:         
            if car_name is None:       
                rest_list_1 = list(filter(lambda x: class_data[x]==class_type, range(len(class_data))))
                
                car_name_none_embed = Embed(
                    title=f"<:yt:1178651795472527401>  Elite {class_type}",
                    description=f"{map_data[rest_list_1[0]]}",
                    colour=0xFF0000
                )
            
                for i in rest_list_1:
                    car_name_none_embed.add_field(
                        name="",
                        value=f"[- `({lap_time_data[i]})` {car_data[i]}]({link_data[i]})\n\n",
                        inline=False
                    )

                await interaction.followup.send(embed=car_name_none_embed)
                    
            else:
                if car_name in car_data:
                    same_num_list = int(numpy.intersect1d(
                        numpy.where(numpy.array(class_data)==class_type),
                        numpy.where(numpy.array(car_data)==car_name)
                    ))
                    
                    if class_type == class_data[same_num_list] and car_name.upper() == car_data[same_num_list]:
                        return await interaction.followup.send(f'```Car    : {car_data[same_num_list]}\nMap    : {map_data[same_num_list]}\nRecord : {lap_time_data[same_num_list]}```{link_data[same_num_list]}') 
                    raise SearchFailedBasic('Elite')
                else:
                    raise SearchFailed('CAR', find=car_name, original_list=car_data)

        except (SearchFailed, SearchFailedBasic) as e:
            search_failed_embed.description = e.message
            await interaction.followup.send(embed=search_failed_embed)
        
        except TypeError:           
            if car_name.upper() not in car_data:
                car_suggestion = match_helper(car_name, car_data)
                car_suggestion = f'* Car : {car_suggestion}'
            else:
                car_suggestion = ''
                
            suggest = f'I think you tried to search..\n{car_suggestion}'
            search_failed_embed.description = f'Parameters that you selected don\'t match. Please Check again.\n{suggest}'
            
            await interaction.followup.send(embed=search_failed_embed)

    @elite.autocomplete('car_name')
    async def area_autocompletion(
        self,
        interaction : Interaction,
        current : str,    
    ) -> List[app_commands.Choice[str]]:            
        # 리스트 선언
        class_type_data = self.elite_class
        car_data = self.elite_carname
        
        # class_type_autocompletion을 통해 찾으려는 맵과 관련된 요소를 불러옴.
        # 여기선 딕셔너리를 이용하여 불러옴 >> dict_values(['Weekly Competition', ''])
        # 리스트로 변환
        aa = list(interaction.namespace.__dict__.values())

        rest_list = list(filter(lambda x: class_type_data[x]==str(aa[0]), range(len(class_type_data))))
        rest_list = list(set([car_data[i] for i in rest_list]))
        
        rest_list = [
            app_commands.Choice(name=choice,value=choice)
            for choice in rest_list
            if current.lower().strip() in choice.lower().strip()
        ]
        
        if len(rest_list) > 10:
            rest_list = rest_list[:10]
        return rest_list   
    
    @app_commands.command(
        description='Let you know Weekly Competition references!',
        extras= {
            "permissions" : ["Embed Links"],
            "howto" : [
                "**[Way 1]**\n* Search `map` and execute.",
                "**[Way 2]**\n* Search `map`. Then, selectable `car` list will come out. So, Choose it and execute."
            ],
            "sequence" : "`map` -> `car`",
        }
    )
    @app_commands.describe(area='Search map.', car_name='What\'s the name of Car?')
    @app_commands.rename(area='map', car_name='car')
    @app_commands.guild_only()
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def weekly(
        self,
        interaction: Interaction,
        area : str,
        car_name : Optional[str] = None
    ):        
        await interaction.response.defer(thinking=True)
        
        map_data = self.weekly_map
        car_data = self.weekly_carname
        lap_time_data = self.weekly_laptime
        link_data = self.weekly_link
        
        try:                    
            if area in list(set(map_data)):
                if car_name is None:
                    rest_list_1 = list(filter(lambda x: map_data[x]==area, range(len(map_data))))

                    car_name_none_embed = Embed(
                        title=f"<:yt:1178651795472527401>  {area}",
                        colour=0xFF0000
                    )
                    for i in rest_list_1:
                        car_name_none_embed.add_field(
                            name="",
                            value=f"[- `({lap_time_data[i]})` {car_data[i]}]({link_data[i]})\n\n",
                            inline=False
                        )

                    return await interaction.followup.send(embed=car_name_none_embed)
                 
                else:
                    pure_car_data = list(set(car_data))
                    if car_name.upper() in pure_car_data:
                        same_num_list = int(numpy.intersect1d(
                            numpy.where(numpy.array(map_data)==area),
                            numpy.where(numpy.array(car_data)==car_name.upper())
                        ))
                        
                        if area == map_data[same_num_list] and car_name == car_data[same_num_list]:
                            return await interaction.followup.send(f'```Car    : {car_data[same_num_list]}\nMap    : {map_data[same_num_list]}\nRecord : {lap_time_data[same_num_list]}```{link_data[same_num_list]}')
                        
                    else:
                        raise SearchFailed('CAR', find=car_name, original_list=pure_car_data)
            else:
                raise SearchFailed('MAP', find=area, original_list=map_data)
                
        except (SearchFailedBasic, SearchFailed) as e:
            search_failed_embed.description = e.message
            await interaction.followup.send(embed=search_failed_embed)

        except TypeError as e:
            if area not in map_data:
                area_suggestion = match_helper(area, map_data)
                area_suggestion = f'* Map : {area_suggestion}\n'
            else:
                area_suggestion = ''
            
            if car_name.upper() not in car_data:
                car_suggestion = match_helper(car_name, car_data)
                car_suggestion = f'* Car : {car_suggestion}'
            else:
                car_suggestion = ''
                
            suggest = f'I think you tried to search..\n{area_suggestion}{car_suggestion}'
            
            search_failed_embed.description = f'Parameters that you selected don\'t match. Please Check again.\n{suggest}'
            await interaction.followup.send(embed=search_failed_embed)

    @weekly.autocomplete(name='area')
    async def area_autocompletion(
        self,
        interaction : Interaction,
        current : str,    
    ) -> List[app_commands.Choice[str]]:        
        # emp_list 내 존재하는 중복 요소 제거

        filetered = [
            app_commands.Choice(name=choice,value=choice)
            for choice in list(set(self.weekly_map)) 
            if current.lower().strip() in choice.lower().strip()
        ]
        
        if len(filetered) > 10:
            filetered = filetered[:10]
        return filetered
    
    @weekly.autocomplete(name='car_name')
    async def car_autocompletion(
        self,
        interaction : Interaction,
        current : str, 
    ) -> List[app_commands.Choice[str]]:
        # 리스트 선언
        map_data = self.weekly_map
        car_data = self.weekly_carname

        aa = list(interaction.namespace.__dict__.values())
        
        rest_list = list(filter(lambda x: map_data[x]==str(aa[0]), range(len(map_data))))
        rest_list = list(set([car_data[i] for i in rest_list]))
        
        rest_list = [
            app_commands.Choice(name=choice,value=choice) for choice in rest_list
            if current.lower().strip() in choice.lower().strip()
        ]
        
        if len(rest_list) > 10:
            rest_list = rest_list[:10]
        return rest_list 

        
async def setup(app : Al9oo):
    await app.add_cog(Reference(app))