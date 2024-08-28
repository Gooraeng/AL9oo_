from __future__ import annotations
from al9oo import Al9oo
from typing import Any, Optional
from utils.embed_color import failed

import discord
import inspect


class BaseView(discord.ui.View):
    """Base View Class inherits from ``discord.discord.ui.View``
    When there's error in here, automatically reported to AL9oo Management Team.
    
    ## Parameters
    * bot : ``class`` AL9oo
    * timeout : ``class`` Optional[float] = 180
    
    ## Methods
    * on_error : An unknown error occurs, then reports to management team.
    """
    def __init__(self, *, bot : Al9oo, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.app = bot
    
    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[Any]) -> None:
        embed = discord.Embed(
            title='Unknown Error Occured',
            description=inspect.cleandoc(
                """
                We are sorry, this error was automatically reported to AL9oo Management Team.
                But, We don't investigate about Discord's fault. We appreciate to your patience.
                """
            ),
            color=failed
        )
        await self.app.err_handler.send_error(interaction, embed=embed, error=error)


class InviteLinkView(discord.ui.View):
    def __init__(self, label : str, url : Optional[str] = None):
        if not url:
            # AL9oo Support Server Invitation Link
            url = "https://discord.gg/8dpAFYXk8s"
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label=label, url=url))
