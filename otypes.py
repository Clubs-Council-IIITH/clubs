import json
import strawberry

from strawberry.fastapi import BaseContext
from strawberry.types import Info as _Info
from strawberry.types.info import RootValueType

from typing import Union, Dict, List, Optional
from functools import cached_property

from models import Sample
from models import PyObjectId, Club, Social, Member


# custom context class
class Context(BaseContext):
    @cached_property
    def user(self) -> Union[Dict, None]:
        if not self.request:
            return None

        user = json.loads(self.request.headers.get("user", "{}"))
        return user


# custom info type
Info = _Info[Context, RootValueType]

# serialize PyObjectId as a scalar type
PyObjectIdType = strawberry.scalar(
    PyObjectId, serialize=str, parse_value=lambda v: PyObjectId(v)
)

# sample object type from pydantic model with all fields exposed
@strawberry.experimental.pydantic.type(model=Sample, all_fields=True)
class SampleType:
    pass


# sample query's input type from pydantic model
@strawberry.experimental.pydantic.input(model=Sample)
class SampleQueryInput:
    id: strawberry.auto


# sample mutation's input type from pydantic model
@strawberry.experimental.pydantic.input(model=Sample)
class SampleMutationInput:
    attribute: strawberry.auto


# TYPES
# @strawberry.experimental.pydantic.type(model=Member, all_fields=True)
# class MemberType:
#     pass

@strawberry.experimental.pydantic.type(model=Social, all_fields=True)
class SocialType:
    pass


@strawberry.experimental.pydantic.type(Club, fields=[
    "cid",
    "state",
    "category",
    "logo",
    "name",
    "tagline"
])
class SimpleClubType:
    pass


@strawberry.experimental.pydantic.type(model=Club, fields=[
    "cid",
    "state",
    "category",
    "logo",
    "banner",
    "name",
    "email",
    "tagline",
    "description",
    "socials"
])
class FullClubType:
    # socials: SocialType
    pass

# QUERY INPUTS


@strawberry.experimental.pydantic.input(model=Club, fields=["cid",])
class SimpleClubInput:
    pass


@strawberry.experimental.pydantic.input(model=Club, fields=[
    "cid",
    "state",
    "category",
    "name",
    "email"
])
class NewClubInput:
    pass


@strawberry.experimental.pydantic.input(model=Club, fields=[
    "cid",
    "state",
    "category",
    "name",
    "email",
    "tagline",
    "description",
    "socials"
])
class EditClubInput:
    pass

# MUTATION INPUTS
@strawberry.experimental.pydantic.input(model=Member)
class FullMemberInput:
    cid: str
    rollno: strawberry.auto
    uid: strawberry.auto
    role: strawberry.auto
    start_year: strawberry.auto
    poc: Optional[strawberry.auto]


@strawberry.experimental.pydantic.input(model=Member)
class SimpleMemberInput:
    cid: str
    rollno: Optional[strawberry.auto]
    uid: strawberry.auto


@strawberry.experimental.pydantic.input(model=Social, all_fields=True)
class SocialInput:
    pass
