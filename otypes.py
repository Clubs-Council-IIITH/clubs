import json
import strawberry

from strawberry.fastapi import BaseContext
from strawberry.types import Info as _Info
from strawberry.types.info import RootValueType

from typing import Union, Dict, List, Optional
from functools import cached_property

from models import PyObjectId, Club, Social, Member


# custom context class
class Context(BaseContext):
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


# custom info type
Info = _Info[Context, RootValueType]

# serialize PyObjectId as a scalar type
PyObjectIdType = strawberry.scalar(
    PyObjectId, serialize=str, parse_value=lambda v: PyObjectId(v)
)


# TYPES
@strawberry.experimental.pydantic.type(
    model=Member, fields=["cid", "uid", "start_year", "end_year", "role", "approved"]
)
class MemberType:
    pass


@strawberry.experimental.pydantic.type(model=Social)
class SocialsType:
    website: Optional[str] = strawberry.UNSET
    instagram: Optional[str] = strawberry.UNSET
    facebook: Optional[str] = strawberry.UNSET
    youtube: Optional[str] = strawberry.UNSET
    twitter: Optional[str] = strawberry.UNSET
    linkedin: Optional[str] = strawberry.UNSET
    discord: Optional[str] = strawberry.UNSET
    other_links: Optional[List[str]] = strawberry.UNSET


@strawberry.experimental.pydantic.type(
    Club, fields=["cid", "state", "category", "logo", "name", "tagline"]
)
class SimpleClubType:
    pass


@strawberry.experimental.pydantic.type(
    model=Club,
    fields=[
        "cid",
        "state",
        "category",
        "logo",
        "banner",
        "name",
        "email",
        "tagline",
        "description",
        "socials",
    ],
)
class FullClubType:
    # socials: SocialsType
    pass


# CLUBS INPUTS


@strawberry.experimental.pydantic.input(model=Social, all_fields=True)
class SocialsInput:
    pass


@strawberry.input
class SimpleClubInput:
    cid: str


@strawberry.experimental.pydantic.input(
    model=Club, fields=["cid", "name", "email", "category"]
)
class NewClubInput:
    tagline: strawberry.auto
    description: strawberry.auto
    socials: strawberry.auto
    banner: Optional[str] = strawberry.UNSET
    logo: Optional[str] = strawberry.UNSET


@strawberry.experimental.pydantic.input(
    model=Club,
    fields=["cid", "name", "email", "category", "tagline", "description", "socials"],
)
class EditClubInput:
    banner: Optional[str] = strawberry.UNSET
    logo: Optional[str] = strawberry.UNSET


# MEMBERS INPUTS


@strawberry.experimental.pydantic.input(
    model=Member, fields=["cid", "uid", "role", "start_year"]
)
class NewMemberInput:
    poc: Optional[bool] = strawberry.UNSET


@strawberry.experimental.pydantic.input(
    model=Member, fields=["cid", "uid", "start_year"]
)
class FullMemberInput:
    poc: Optional[bool] = strawberry.UNSET
    end_year: Optional[int] = strawberry.UNSET
    role: Optional[str] = strawberry.UNSET


@strawberry.experimental.pydantic.input(
    model=Member, fields=["cid", "uid", "start_year", "role"]
)
class SimpleMemberInput:
    pass
