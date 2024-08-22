from __future__ import annotations
from discord import (
    app_commands, 
    Button, 
    ButtonStyle, 
    Embed, 
    Interaction,
    TextChannel, 
    ui
)
from typing import (
    TYPE_CHECKING, 
    Union, 
    Literal,
    Optional, 
    List
)
from discord.ext import commands
from utils.commandpermission import permissioncheck
from utils.embed_color import al9oo_point

if TYPE_CHECKING:
    from al9oo import Al9oo

import discord


al9oo_channels = [1160568027377578034, 1161584379571744830]
arn_channel = [1188494656170901546]



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


async def follow_al9oo(interaction : Interaction, *, target : TextChannel):
    done = []
    webhooks = await interaction.guild.webhooks()
    
    if not webhooks:
        for a in al9oo_channels:
            departure = interaction.client.get_channel(a) or await interaction.client.fetch_channel(a)
            await departure.follow(destination=target)
            done.append(departure.mention)

    else:
        webhook_ids = [
            webhook.source_channel.id
            for webhook in webhooks if webhook.source_channel is not None
        ]
        
        for a in al9oo_channels:
            if a not in webhook_ids:
                departure = interaction.client.get_channel(a) or await interaction.client.fetch_channel(a)
                await departure.follow(destination=target)
                done.append(departure.mention)
    return done


async def follow_arn(interaction : Interaction, *, target : TextChannel):
    channel = arn_channel[0]
    done = []
    webhooks = await interaction.guild.webhooks()

    if not webhooks:
        departure = interaction.client.get_channel(channel) or await interaction.client.fetch_channel(channel)
        await departure.follow(destination=target)
        done.append(departure.mention)

    else:
        webhook_ids = [
            webhook.source_channel.id
            for webhook in webhooks if webhook.source_channel is not None
        ]
        
        if channel not in webhook_ids:
            departure = interaction.client.get_channel(channel) or await interaction.client.fetch_channel(channel)
            await departure.follow(destination=target)
            done.append(departure.mention)
            
    return done


async def follow_both(interaction : Interaction, target : TextChannel):
    done_1 = await follow_al9oo(interaction, target=target)
    done_2 = await follow_arn(interaction, target=target)
    return done_1 + done_2


@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
class Follow(commands.GroupCog):
    __cog_group_name__ = 'follow'

    def __init__(self, app : Al9oo) -> None:
        self.app = app
    
    @app_commands.command(name='help', description="Get small tip of alert commands!")
    async def help(self, interaction : Interaction):
        try:
            embed1 = Embed(
                title=f"/{self.clear_channel.qualified_name}",
                description=self.clear_channel.description,
                color=al9oo_point)
            embed1.add_field(name="Don't worry!", value="I don't delete any webhook that I didn't make")
            
            embed2 = Embed(
                title=f"/{self.set_channel.qualified_name}",
                description=self.set_channel.description,
                color=al9oo_point)

            a9 = "Asphalt Legends Unite"
            embed2.add_field(name="1. AL9oo", value="Get nofitications about my updates!")
            embed2.add_field(name=f"2. {a9}", value=f"Get notifications from {a9} Release Notes faster than anyone else!")
            embeds = [embed1, embed2]
            
            view = AlertHelpView(embeds=embeds)
            return await interaction.response.send_message(view=view, embed=view.initial, ephemeral=True)
        
        except Exception as e:
            await interaction.response.defer(thinking=True, ephemeral=True)
            await interaction.followup.send(content="Sorry, something error occured.", ephemeral=True)
            raise e

    @app_commands.command(name='start', description="Create webhook(s) to get notifications in AL9oo announcements or Asphalt 9 Release Notes.")
    @app_commands.describe(target="Choose Channel", select='What do you want follow?')
    @app_commands.rename(target="channel")
    @app_commands.checks.cooldown(3, 30, key=lambda i : (i.guild_id, i.user.id))
    @app_commands.checks.bot_has_permissions(manage_webhooks=True)
    async def set_channel(self, interaction : Interaction, target : TextChannel, select : Optional[Literal["AL9oo", "Asphalt 9 Release note"]] = None):        
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            match select:
                case "AL9oo":
                    done_1 = await follow_al9oo(interaction, target=target)
                    done_2 = []
                case "Asphalt 9 Release note":
                    done_1 = []
                    done_2 = await follow_arn(interaction, target=target)
                case None:
                    done = await follow_both(interaction, target=target)
            try:
                done = done_1 + done_2
            except UnboundLocalError:
                pass
            
            if not done:
                return await interaction.followup.send(embed=Embed(
                    title="Warn",
                    description=f"You are already following all announcements.\nif you want to change setup, Run `/alert clear`, then run `/alert set`.",
                    color=al9oo_point
                ), ephemeral=True)
              
            if done:
                followed = "\n* " + "\n* ".join(s for s in done)
            else:
                followed = ""
    
            return await interaction.followup.send(embed=Embed(
                title="Warn",
                description=f"You will receive notifications here from now.\n## {target.mention}\n### Following Channel" + followed,
                color=al9oo_point
            ), ephemeral=True)

        except discord.Forbidden:
            return await interaction.followup.send(f"I am not in AL9oo server!", ephemeral=True)
    
        except Exception:
            return await interaction.followup.send(
                f"Failed run this command due to error.\nFirst, please check whether I can see {target.mention}",
                ephemeral=True
            )
    
    @app_commands.command(name='stop', description="Only remove webhooks that AL9oo created!")
    @app_commands.describe(select="Select one, or not, I'll clear all webhooks that I made!")
    @app_commands.checks.cooldown(3, 30, key=lambda i : (i.guild_id, i.user.id))
    @app_commands.checks.bot_has_permissions(manage_webhooks=True)
    async def clear_channel(self, interaction : Interaction, select : Optional[Literal["AL9oo", "Asphalt 9 Release note"]] = None):        
        await interaction.response.defer(thinking=True, ephemeral=True)         
        webhooks = await interaction.guild.webhooks()
        
        if not webhooks:
            return await interaction.followup.send("It's clear already.", ephemeral=True)
        
        if select == "AL9oo":
            channels = al9oo_channels
        elif select == "Asphalt 9 Release note":
            channels = arn_channel
        else:
            channels = al9oo_channels + arn_channel
        
        deleted = []; failed = []
        for webhook in webhooks:
            source = webhook.source_channel
            if source is not None:
                for i in channels:
                    if source.id == i:
                        target = await interaction.client.fetch_channel(i)
                        try:
                            await webhook.delete()
                            deleted.append(target.mention)
                        except Exception:
                            failed.append(target.mention)
                            
        if not deleted:
            return await interaction.followup.send("It's clear already.", ephemeral=True)
        
        elif not failed:
            deleted = "\n* ".join(s for s in deleted)
            return await interaction.followup.send(embed=Embed(
                title="Warn", description=f"Deleted webhooks.", color=al9oo_point
            ), ephemeral=True)
        
        else:
            failed = "\n* ".join(s for s in failed)
            return await interaction.followup.send(embed=Embed(
                title="Warn",
                description=f"Deleted webhooks Except for...\n* {failed}\nYou may delete manually for run this command again without any choice.",
                color=al9oo_point
            ), ephemeral=True)

    @clear_channel.error
    @set_channel.error
    async def alert_err(self, interaction : Interaction, error : Union[app_commands.AppCommandError, discord.DiscordException]):
        if isinstance(error, app_commands.BotMissingPermissions):
            await permissioncheck(interaction, error=error)
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f"Too much requests! Please wait for {int(error.retry_after)} second(s)!")


async def setup(app : Al9oo):
    await app.add_cog(Follow(app))