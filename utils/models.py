from __future__ import annotations
from typing import Literal, NamedTuple, Optional, TypedDict, Union
from pydantic import BaseModel, field_validator, Field

import datetime
import discord


ReferenceTypes = Literal[
    'Car Hunt Riot',
    'Club Clash',
    'Elite',
    'Weekly Competition'
]


SearchTypes = Literal[
    'CAR',
    'CLASS',
    'MAP'
]

ExecutableGuildChannel = Union[discord.abc.GuildChannel, discord.Thread]
ExecutableAllChannel = Union[ExecutableGuildChannel, discord.DMChannel]


class ModalResponse(NamedTuple):
    title : str
    detail : Optional[str] 


class CommandDetails(TypedDict):
    parameters : Optional[str]
    permissions : Optional[str]
    sequence : Optional[str]
    how_to : str


class CommandUsageModel(NamedTuple):
    name : str
    description : str
    guild_only : bool
    default_permission : Optional[str]
    details : CommandDetails


class FeedbackToMongo(BaseModel):
    type : str
    detail : str
    author_info : FeedbackAllInfo
    created_at : Optional[datetime.datetime] = Field(discord.utils.utcnow())


class FeedbackAllInfo(BaseModel):
    guild : Optional[FeedbackGuild] = None
    channel : FeedbackChannel
    author : FeedbackAuthor
    
    @classmethod
    def from_interaction(cls, interaction : Optional[discord.Interaction]):
        if not isinstance(interaction, discord.Interaction):
            raise ValueError(f'Input Type MUST BE discord.Interaction, not {interaction.__class__.__name__}')
        return cls(
            guild=FeedbackGuild.from_guild(interaction.guild),
            channel=FeedbackChannel.from_channel(interaction.channel),
            author=FeedbackAuthor.from_user(interaction.user)
        )


class FeedbackAuthor(BaseModel):
    name : str
    id : int
    
    @classmethod
    def from_user(cls, user : Union[discord.Member, discord.User]):
        if isinstance(user, Union[discord.Member, discord.User]):
            return cls(name=user.name, id=user.id)
        raise ValueError(f'Input Class MUST be one of discord.Member or discord.User, not {user.__class__.__name__}')


class FeedbackGuild(BaseModel):
    name : Optional[str]
    id : Optional[int]

    @classmethod
    def from_guild(cls, guild : Optional[discord.Guild]):
        if isinstance(guild, discord.Guild):
            return cls(name=guild.name, id=guild.id)
        elif isinstance(guild, None):
            return cls(name=None, id=None)
        raise ValueError(f'Input Class MUST be , not {guild.__class__.__name__}')


class FeedbackChannel(BaseModel):
    name : Optional[str] = 'DM'
    id : int
    
    @classmethod
    def from_channel(cls, channel : ExecutableAllChannel):
        if isinstance(channel, discord.DMChannel):
            return cls(name='DM', id=channel.id)
        elif isinstance(channel, ExecutableGuildChannel):
            return cls(name=channel.name, id=channel.id)
        else:
            raise ValueError(f'Input Class MUST be one of ExecutableGuildChannel or discord.DMChannel, not {channel.__class__.__name__}')