from __future__ import annotations
from bson import ObjectId
from dataclasses import dataclass, field
from typing import List, Literal, NamedTuple, Optional, TypedDict, Union
from pydantic import BaseModel, Field, field_validator

import datetime
import discord


ReferenceTypes = Literal['Car Hunt Riot', 'Club Clash', 'Elite', 'Weekly Competition']
SearchTypes = Literal['CAR', 'CLASS', 'MAP']
FollowList = Literal["AL9oo Main Announcement", "AL9oo Urgent Alert", "ALU Release note"]

CommandExecutableGuildChannel = Union[discord.abc.GuildChannel, discord.Thread]
CommandExecutableAllChannel = Union[CommandExecutableGuildChannel, discord.DMChannel]
WebhookMessagableChannel = Union[discord.ForumChannel, discord.TextChannel, discord.StageChannel, discord.VoiceChannel]

Embeds = List[discord.Embed]


class FollowWebhookModel(TypedDict):
    webhook : discord.Webhook
    source_ch : discord.TextChannel


class FollowFailedStatus(NamedTuple):
    target : discord.TextChannel
    reason : str


class FollowResult(NamedTuple):
    done : list[discord.TextChannel]
    failed : list[FollowFailedStatus]
    embed : discord.Embed


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
    id : Optional[ObjectId] = Field(default=None, alias='_id')
    type : str
    detail : str
    author_info : FeedbackAllInfo
    created_at : Optional[float] = Field(discord.utils.utcnow().timestamp())

    class Config:
        arbitrary_types_allowed = True


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
    def from_channel(cls, channel : CommandExecutableAllChannel):
        if isinstance(channel, discord.DMChannel):
            return cls(name='DM', id=channel.id)
        elif isinstance(channel, CommandExecutableGuildChannel):
            return cls(name=channel.name, id=channel.id)
        else:
            raise ValueError(f'Input Class MUST be one of ExecutableGuildChannel or discord.DMChannel, not {channel.__class__.__name__}')


class NumberedObject(BaseModel):
    id : ObjectId = Field(alias='_id')
    object : Union[discord.Embed, discord.File]
    
    @field_validator('object', mode='before')
    @classmethod
    def type_checker(cls, v : Union[discord.Embed, discord.File]):
        if not isinstance(v, discord.Embed) and not isinstance(v, discord.File):
            raise TypeError(f'Any Type not allowed except for discord.Embed or discord.File')
        return v
    
    class Config:
        arbitrary_types_allowed = True
        

class ErrorLogTrace(BaseModel):
    id : Optional[ObjectId] = Field(None, alias='_id')
    error_type : str
    detected_at : Optional[float] = Field(discord.utils.utcnow().timestamp())
    details : str

    @field_validator('detected_at', mode='before')
    @classmethod
    def is_datetime(cls, v : Union[datetime.datetime, float]):
        if isinstance(v, datetime.datetime):
            return v.timestamp()
        elif isinstance(v, float):
            return v
        else:
            raise TypeError(f'Expected class is float or datetime.datetime, not {v.__class__.__name__}')
    
    class Config:
        arbitrary_types_allowed = True