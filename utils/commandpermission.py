from __future__ import annotations
from discord import app_commands, Embed, Interaction
from .embed_color import *


async def permissioncheck(interaction : Interaction, *, error : app_commands.BotMissingPermissions):
    missing_list = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_permissions]
    missing = "\n* ".join(s for s in missing_list)

    if interaction.user.guild_permissions.manage_roles:
        bot_embed_owner= Embed(title= "Al9oo is Missing Permission(s)!", description= "Please check interact channel's permission(s)!", color= failed)
                
        if len(missing) > 1:
            bot_embed_owner.add_field(name=f"* {missing}", value="")
        else:
            bot_embed_owner.add_field(name=f"* {missing[0]}", value="")
        
        bot_embed_owner.set_footer(text=str(interaction.created_at)[0:-13])
        return await interaction.response.send_message(embed=bot_embed_owner, ephemeral=True)

    else:
        bot_embed = Embed(
            title="Al9oo is Missing Permission(s)!",
            description="Please Contact Server Moderator you are in to fix permission(s)!",
            color=failed
        )
                
        if len(missing) > 1:
            bot_embed.add_field(name=f"* {missing}", value="")
        else:
            bot_embed.add_field(name=f"* {missing[0]}", value="")
            
        bot_embed.set_footer(text=str(interaction.created_at)[0:-13])
        return await interaction.response.send_message(embed=bot_embed, ephemeral=True)