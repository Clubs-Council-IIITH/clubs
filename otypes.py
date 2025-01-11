"""
Types and Inputs for clubs subgraph
"""

import json
from functools import cached_property
from typing import Dict, List, Optional, Union

import strawberry
from strawberry.fastapi import BaseContext
from strawberry.types import Info as _Info
from strawberry.types.info import RootValueType

from models import Club, PyObjectId, Social


# custom context class
class Context(BaseContext):
    """
    Class provides user metadata and cookies from request headers.
    """
    @cached_property
    def user(self) -> Union[Dict, None]:
        if not self.request:
            return None

        user = json.loads(self.request.headers.get("user", "{}"))
        return user

    @cached_property
    def cookies(self) -> Union[Dict, None]:
        if not self.request:
            return None

        cookies = json.loads(self.request.headers.get("cookies", "{}"))
        return cookies


"""custom info type for user metadata"""
Info = _Info[Context, RootValueType]

"""A scalar type by serializing PyObjectId"""
PyObjectIdType = strawberry.scalar(
    PyObjectId, serialize=str, parse_value=lambda v: PyObjectId(v)
)


# TYPES
@strawberry.experimental.pydantic.type(model=Social)
class SocialsType:
    """
    Type for return of social media handles of a club.
    """
    website: Optional[str] = strawberry.UNSET
    instagram: Optional[str] = strawberry.UNSET
    facebook: Optional[str] = strawberry.UNSET
    youtube: Optional[str] = strawberry.UNSET
    twitter: Optional[str] = strawberry.UNSET
    linkedin: Optional[str] = strawberry.UNSET
    discord: Optional[str] = strawberry.UNSET
    whatsapp: Optional[str] = strawberry.UNSET
    other_links: Optional[List[str]] = strawberry.UNSET


@strawberry.experimental.pydantic.type(
    Club,
    fields=[
        "id",
        "cid",
        "code",
        "state",
        "category",
        "student_body",
        "email",
        "logo",
        "banner",
        "banner_square",
        "name",
        "tagline",
    ],
)
class SimpleClubType:
    """
    Type for return of user-provided club details except social handles.
    """
    pass


@strawberry.experimental.pydantic.type(
    model=Club,
    fields=[
        "id",
        "cid",
        "code",
        "state",
        "category",
        "student_body",
        "logo",
        "banner",
        "banner_square",
        "name",
        "email",
        "tagline",
        "description",
        "socials",
    ],
)
class FullClubType:
    """Type for return of all user-provided club details."""
    # socials: SocialsType
    pass


# CLUBS INPUTS
@strawberry.experimental.pydantic.input(model=Social, all_fields=True)
class SocialsInput:
    """Type for input of social media handles of a club."""
    pass


@strawberry.input
class SimpleClubInput:
    """Type for input of cid(Club id) of a club."""
    cid: str


@strawberry.experimental.pydantic.input(
    model=Club,
    fields=[
        "cid",
        "code",
        "name",
        "email",
        "category",
        "student_body",
        "tagline",
        "description",
        "socials",
    ],
)
class FullClubInput:
    """
    Type for input of all user-provided club details, pictures are optional to fill.
    """
    logo: Optional[str] = strawberry.UNSET
    banner: Optional[str] = strawberry.UNSET
    banner_square: Optional[str] = strawberry.UNSET
