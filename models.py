from datetime import datetime
from enum import Enum
from typing import Annotated, Any, List

import strawberry
from bson import ObjectId
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    TypeAdapter,
    field_validator,
)
from pydantic_core import core_schema
from pytz import timezone

http_url_adapter = TypeAdapter(HttpUrl)
HttpUrlString = Annotated[
    str,
    BeforeValidator(
        lambda value: str(http_url_adapter.validate_python(value))
    ),
]


def create_utc_time():
    return datetime.now(timezone("UTC"))


# for handling mongo ObjectIds
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        return core_schema.union_schema(
            [
                # check if it's an instance first before doing any further work
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(cls.validate),
            ],
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


def iiit_email_only(v: str) -> str:
    valid_domains = [
        "@iiit.ac.in",
        "@students.iiit.ac.in",
        "@research.iiit.ac.in",
    ]
    if any(valid_domain in v for valid_domain in valid_domains):
        return v.lower()

    raise ValueError("Official iiit emails only.")


def current_year() -> int:
    return datetime.now().year


@strawberry.enum
class EnumStates(str, Enum):
    active = "active"
    deleted = "deleted"


@strawberry.enum
class EnumCategories(str, Enum):
    cultural = "cultural"
    technical = "technical"
    affinity = "affinity"
    admin = "admin"
    body = "body"
    other = "other"


class Social(BaseModel):
    website: HttpUrlString | None = None
    instagram: HttpUrlString | None = None
    facebook: HttpUrlString | None = None
    youtube: HttpUrlString | None = None
    twitter: HttpUrlString | None = None
    linkedin: HttpUrlString | None = None
    discord: HttpUrlString | None = None
    whatsapp: HttpUrlString | None = None
    other_links: List[HttpUrlString] = Field([])  # Type and URL

    @field_validator("other_links")
    @classmethod
    def validate_unique_links(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Duplicate URLs are not allowed in 'other_links'")
        return value


class Club(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    cid: str = Field(..., description="Club ID")
    code: str = Field(
        ...,
        description="Unique Short Code of Club",
        max_length=15,
        min_length=2,
    )  # equivalent to club id = short name
    state: EnumStates = EnumStates.active
    category: EnumCategories = EnumCategories.other

    # TODO: Remove this field
    student_body: bool = Field(False, description="Is this a Student Body?")

    name: str = Field(..., min_length=5, max_length=100)
    email: EmailStr = Field(...)  # Optional but required
    logo: str | None = Field(None, description="Club Official Logo pic URL")
    banner: str | None = Field(None, description="Club Long Banner pic URL")
    banner_square: str | None = Field(
        None, description="Club Square Banner pic URL"
    )
    tagline: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(
        "No Description Provided!",
        max_length=9999,
        description="Club Description",
    )
    socials: Social = Field({}, description="Social Profile Links")

    created_time: datetime = Field(
        default_factory=create_utc_time, frozen=True
    )
    updated_time: datetime = Field(default_factory=create_utc_time)

    # Validator
    @field_validator("email", mode="before")
    def _check_email(cls, v):
        return iiit_email_only(v)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        str_max_length=10000,
        validate_assignment=True,
        validate_default=True,
        validate_return=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


# TODO: ADD CLUB SUBSCRIPTION MODEL - v2
# ADD Descriptions for non-direct fields
