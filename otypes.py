"""
Types and Inputs

It contains both Inputs and Types for taking inputs and returning outputs.
It also contains the Context class which is used to pass the user details to the resolvers.

Types:
    Info : used to pass the user details to the resolvers.
    PyObjectId : used to return ObjectId of a document.
    SocialType : used to return Social handles, if they are present.
    SimpleClubType : used to return only few fields defined within the Club schema.
    FullClubType : used to return almost all the fields within the Club Schema.

Inputs
    SocialsInput : used to take Social handles as input.All of its fields are optional to fill.
    SimpleClubInput : used to take club id as input.
    FullClubInput : used to take almost all the fields within the Club Schema as input.
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
    To pass user details

    This class is used to pass the user details to the resolvers.
    It will be used through the Info type.
    """

    @cached_property
    def user(self) -> Union[Dict, None]:
        """
        Returns User Details
        
        It will be used in the resolvers to check the user details.

        Returns:
            user (Dict): Contains User Details.
        """
        
        if not self.request:
            return None

        user = json.loads(self.request.headers.get("user", "{}"))
        return user

    @cached_property
    def cookies(self) -> Union[Dict, None]:
        """
        Returns Cookies Details

        It will be used in the resolvers to check the cookies details.

        Returns:
            cookies (Dict): Contains Cookies Details.
        """

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
@strawberry.experimental.pydantic.type(model=Social)
class SocialsType:
    """
    Type for Social Handles

    This type is used to return Social handles, if they are present.
    All of its fields(Attributes) are optional to fill and defaultly set to UNSET.
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
    pass

# This type is used to return almost all the fields within the Club Schema.
# except created and updated time fields.
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
    Full Club Details Input

    This class is used to take almost all the fields within the Club Schema as input.
    It does not take created and updated time fields as input.
    logo, banner, banner_square fields are optional to fill.
    """

    logo: Optional[str] = strawberry.UNSET
    banner: Optional[str] = strawberry.UNSET
    banner_square: Optional[str] = strawberry.UNSET
