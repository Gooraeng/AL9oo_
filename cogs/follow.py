from __future__ import annotations
from discord import (
    app_commands, 
    Button, 
    ButtonStyle, 
    Embed, 
    Interaction,
    TextChannel, 
    ui,
    Webhook,
)
from typing import (
    List,
    Optional, 
    TYPE_CHECKING, 
)
from discord.ext import commands
from utils.embed_color import al9oo_point, failed
from utils.models import FollowList, FollowResult, FollowWebhookModel, FollowFailedStatus

if TYPE_CHECKING:
    from al9oo import Al9oo

import asyncio
import discord


class AlertHelpView(ui.View):
    def __init__(
        self,
        embeds : List[Embed] = None
    ):
        super().__init__(timeout=None)
        self._embeds = embeds
        try:
            self.children[0].disabled = True
        except:
            if self.children[0].disabled is True:
                self.children[1].disabled = False
            else:
                self.children[1].disabled = True

    async def button_update(self, interaction : Interaction, *, num : int):
        self.children[num].disabled = True
        for i in range(0, len(self.children)):
            if num != i:
                self.children[i].disabled = False              
        await interaction.response.edit_message(embed=self._embeds[num], view=self)

    @ui.button(label='Clear', style=ButtonStyle.blurple, custom_id='help-al9oo-noti')
    async def Clear(self, interaction : Interaction, button : Button):
        await self.button_update(interaction, num=0)

    @ui.button(label='Set', style=ButtonStyle.blurple, custom_id='help-a9-releasenote')
    async def Set(self, interaction : Interaction, button : Button):
        await self.button_update(interaction, num=1)
    
    @property
    def initial(self):
        return self._embeds[0]


@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
class Follow(commands.GroupCog):
    __cog_group_name__ = 'follow'
    
    def __init__(self, app : Al9oo) -> None:
        self.app = app
    
    async def cog_load(self) -> None:
        self.followable : dict[FollowList, int] = {
            "AL9oo Main Announcement" : self.app.al9oo_main_announcement.id,
            "AL9oo Urgent Alert" : self.app.al9oo_urgent_alert.id,
            "ALU Release note" : self.app.arn_channel.id
        }
        self.followable_id : dict[int, TextChannel] = {
            self.app.al9oo_main_announcement.id : self.app.al9oo_main_announcement,
            self.app.al9oo_urgent_alert.id : self.app.al9oo_urgent_alert,
            self.app.arn_channel.id : self.app.arn_channel
        }        
        self.channels = list(self.followable_id.values())
        self.channel_ids = list(self.followable_id.keys())

    async def handle_following(self, following_webhooks : List[FollowWebhookModel], *, choose : Optional[FollowList] = None) :
        # 여기까지 왔으면 follow 중이 아닌 채널의 수가 0, 1, 2인 상태
        if choose:
            selected_channel_id = self.followable[choose]
        # 팔로우가 0일 때 신규 팔로우
        if len(following_webhooks) == 0 or not following_webhooks:
            if not choose:
                return self.channels.copy()
            return [channel for channel in self.channels if selected_channel_id == channel.id]
        
        # 추가 팔로우 시
        wh_ids = [wh["source_ch"].id for wh in following_webhooks]
        if not choose:
            return [channel for channel in self.channels if channel.id not in wh_ids]
        return [
            channel for channel in self.channels
            if selected_channel_id == channel.id and selected_channel_id not in wh_ids
        ]
        
    async def handle_unfollowing(self, following_webhooks : List[FollowWebhookModel], *, choose : Optional[FollowList] = None) -> List[Webhook]:
        # 여기까지 왔으면 follow 중인 채널의 수가 1, 2, 3인 상태
        if not choose:
            return [wh["webhook"] for wh in following_webhooks]
        return [
            wh["webhook"] for wh in following_webhooks for channel in self.channels
            if channel.id == self.followable[choose] == wh["source_ch"].id
        ]
    
    def get_following_channel_info(self, webhooks : List[FollowWebhookModel], embed : Embed):
        for webhook in webhooks:
            for k, v in self.followable.items():
                src_id = webhook["source_ch"].id
                if v == src_id:
                    to = webhook["webhook"].channel
                    start = self.followable_id[src_id]
                    embed.add_field(name=k, value=f"From : {start.mention}\nTo : {to.mention}", inline=False)
    
    async def follow_configure(
        self,
        interaction : Interaction,
        choose : Optional[FollowList] = None,
        target : Optional[TextChannel] = None,
        *,
        unfollow : bool = False,
    ):
        if target and unfollow:
            raise ValueError('"target" and "unfollow" must not be None at the same time.')
        
        embed = Embed(description='', color=al9oo_point)
        embed.title = "Task Terminated" 
        embed.set_footer(text='Remember. Following webhook could be quite slower than receving from that server.')
        try:
            guild_webhook = await interaction.guild.webhooks()
        except discord.Forbidden:
            embed.description = "I am not granted to check Webhooks. Please take a look permission I have and consider to run `/invite`, so you may understand why I require corresponding permission from it."
            return embed
        
        following = [
            FollowWebhookModel(webhook=wh, source_ch=self.followable_id[wh.source_channel.id])
            for wh in guild_webhook
            if wh.type.name == 'channel_follower' and wh.source_channel.id in self.channel_ids            
        ]
        
        if unfollow and not following:      
            embed.description = "You don't following any channel."
            return embed
        if len(following) == 3 and not unfollow:
            self.get_following_channel_info(following, embed=embed)
            embed.description = "You are following all channels."
            return embed
        
        done : List[TextChannel] = []
        failed : List[FollowFailedStatus] = []
        
        if unfollow:
            existing_webhook = await self.handle_unfollowing(following, choose=choose)
            
            embed.title = "Deleting Follows..."
            await interaction.edit_original_response(embed=embed)

            for wh in existing_webhook:
                unfollowed_channel = self.followable_id[wh.source_channel.id]
                try:
                    await wh.delete()
                    done.append(unfollowed_channel)
                except discord.HTTPException as e:
                    failed.append(FollowFailedStatus(target=unfollowed_channel, reason=e.text))
                else:
                    embed.description = f'{len(done)} / {len(existing_webhook)}'
                    await interaction.edit_original_response(embed=embed)
                    await asyncio.sleep(3)
                    
        else:
            # 여기서부터 팔로우와 관련된 걸 다루면 됨
            temp = await self.handle_following(following, choose=choose)
            
            if not temp:
                embed.description = "You are following that channel."
                return embed
        
            embed.title = "Configuring Follows..."
            await interaction.edit_original_response(embed=embed)
            
            for channel in temp:
                try:
                    await channel.follow(destination=target)
                    done.append(channel)
                except discord.ClientException as e:
                    failed.append(FollowFailedStatus(target=channel, reason=e))
                except discord.HTTPException as e:
                    failed.append(FollowFailedStatus(target=channel, reason=e.text))
                else:
                    embed.description = f'{len(done)} / {len(temp)}'
                    await interaction.edit_original_response(embed=embed)
                    await asyncio.sleep(3)
                    
        return FollowResult(done=done, failed=failed, embed=embed)
        
    @app_commands.command(name='help', description="Get small tip of alert commands!")
    async def help(self, interaction : Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            # Unfollow
            embed1 = Embed(
                title=f"/{self.clear_channel.qualified_name}",
                description=self.clear_channel.description,
                color=al9oo_point
            )
            embed1.add_field(name="Don't worry!", value="I don't delete any webhook that I didn't make")
            
            # Follow
            embed2 = Embed(
                title=f"/{self.set_channel.qualified_name}",
                description=self.set_channel.description,
                color=al9oo_point
            )

            a9 = "Asphalt Legends Unite"
            embed2.add_field(name="1. AL9oo", value="Get nofitications about my updates! You will have 2 options : Main Annoucement, Urgent Alert.")
            embed2.add_field(name=f"2. {a9}", value=f"Get notifications from {a9} Release Notes faster than anyone else!")
            embeds = [embed1, embed2]
            
            view = AlertHelpView(embeds)
            await interaction.followup.send(view=view, embed=view.initial, ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(content="Sorry, something error occured.", ephemeral=True)
            raise e

    @app_commands.command(name='start', description="Create webhook(s) to get notifications in AL9oo announcements or ALU Release notes.")
    @app_commands.describe(target="Choose Channel to receive alerts", select='What do you want to follow?')
    @app_commands.rename(target="channel")
    @app_commands.checks.cooldown(3, 120, key=lambda i : i.guild_id)
    @app_commands.checks.bot_has_permissions(manage_webhooks=True)
    async def set_channel(
        self,
        interaction : Interaction,
        target : TextChannel,
        select : Optional[FollowList] = None
    ):        
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        result = await self.follow_configure(interaction, target=target, choose=select)
        if isinstance(result, Embed):
            result.color = failed
            return await interaction.followup.send(embed=result, ephemeral=True)
        
        if result.done:
            _success = "\n * " + "\n * ".join(s.mention for s in result.done)
        else:
            _success = None
        
        if result.failed:
            _failed = ''
            for item in result.failed:
                _failed += f'\n * {item.target.mention} - {item.reason}'
        else:
            _failed = None
        
        embed = result.embed
        embed.title = "Result"

        if _success:
            embed.add_field(
                name='Success',
                value=f"* Notification Channel : {target.mention}{_success}"
            )
        if _failed:
            embed.add_field(name='Failed', value=f'* Failed Channel(s) with Reason{_failed}')
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name='stop', description="Stop receiving AL9oo announcements or ALU Release note.")
    @app_commands.describe(select="Select one, or I'll clear all webhooks that I made!")
    @app_commands.checks.cooldown(3, 90, key=lambda i : i.guild_id)
    @app_commands.checks.bot_has_permissions(manage_webhooks=True)
    async def clear_channel(self, interaction : Interaction, select : Optional[FollowList] = None):        
        await interaction.response.defer(thinking=True, ephemeral=True)         
                
        result = await self.follow_configure(interaction=interaction, choose=select, unfollow=True)
        if isinstance(result, Embed):
            result.colour = failed
            return await interaction.followup.send(embed=result, ephemeral=True)
        
        if result.done:
            _success = "\n * ".join(s.mention for s in result.done)
        else:
            _success = None
        
        if result.failed:
            _failed = ''
            for item in result.failed:
                _failed += f'\n * {item.target.mention} - {item.reason}'
        else:
            _failed = None

        embed = result.embed
        embed.title = "Result"
        
        if _success:
            embed.add_field(name='Success', value=f"* Unfollowed Channel\n * {_success}")
        if _failed:
            embed.add_field(name='Failed', value=f'* Failed Channel(s) with Reason{_failed}')
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(app : Al9oo):
    await app.add_cog(Follow(app))