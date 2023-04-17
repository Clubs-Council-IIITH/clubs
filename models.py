import strawberry
from bson import ObjectId
from datetime import datetime
from enum import Enum
from pydantic import (
    BaseModel,
    Extra,
    Field,
    EmailStr,
    AnyHttpUrl,
    ValidationError,
    validator,
)
from typing import List, Optional


# for handling mongo ObjectIds
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


def iiit_email_only(v: str) -> str:
    valid_domains = ["@iiit.ac.in", "@students.iiit.ac.in", "@research.iiit.ac.in"]
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
    other = "other"


class Roles(BaseModel):
    roleid: str | None = Field(None, description = "Unique Identifier for a role")
    role: str = Field(..., min_length=1, max_length=99)
    start_year: int = Field(..., ge=2015, le=2040)
    end_year: int | None = Field(None, ge=2015, le=2041)
    approved: bool = False
    deleted: bool = False

    # Validators
    @validator("end_year", always=True)
    def check_end_year(cls, value, values):
        if value != None and value < values["start_year"]:
            return values["start_year"]
        return value

    class Config:
        arbitrary_types_allowed = True
        max_anystr_length = 100
        validate_assignment = True
        extra = Extra.forbid
        anystr_strip_whitespace = True


class Member(BaseModel):
    cid: str = Field(...)
    uid: str = Field(...)
    roles: List[Roles] = Field(...,
                               description="List of Roles for that specific person")

    poc: bool = Field(default_factory=(lambda: 0 == 1), description="Club POC")

    # contact: str | None = Field(
    #     None, regex=r"((\+91)|(0))?(-)?\s*?(91)?\s*?([6-9]{1}\d{2})((-?\s*?(\d{3})-?\s*?(\d{4}))|((\d{2})-?\s*?(\d{5})))")

    # Validators
    # @validator("contact", always=True)
    # def check_poc_contact(cls, value, values):
    #     if values["poc"] == True and not value:
    #         raise ValueError("POC Contact Number should be added")
    #     return value

    class Config:
        arbitrary_types_allowed = True
        anystr_strip_whitespace = True
        max_anystr_length = 600
        validate_assignment = True
        extra = Extra.forbid

    # Separate Coordinator & other members roles option in frontend, for better filtering for all_members_query


class Social(BaseModel):
    website: AnyHttpUrl | None
    instagram: AnyHttpUrl | None
    facebook: AnyHttpUrl | None
    youtube: AnyHttpUrl | None
    twitter: AnyHttpUrl | None
    linkedin: AnyHttpUrl | None
    discord: AnyHttpUrl | None
    other_links: List[AnyHttpUrl] = Field([], unique_items=True)  # Type and URL


class Club(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    cid: str = Field(
        ..., description="Club ID/Unique Short Name of Club"
    )  # equivalent to club id = short name
    state: EnumStates = EnumStates.active
    category: EnumCategories = EnumCategories.other

    name: str = Field(..., min_length=5, max_length=100)
    email: EmailStr = Field(...)  # Optional but required
    logo: str | None = Field(None, description="Club Official Logo pic URL")
    banner: str | None = Field(None, description="Club Long Banner pic URL")
    tagline: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(
        '[{"type":"paragraph", "children":[{"text":""}]}]',
        max_length=5000,
        description="Club Description",
    )
    socials: Social = Field({}, description="Social Profile Links")

    # members: List[Member] | None = Field(None)

    created_time: datetime = Field(
        default_factory=datetime.utcnow, allow_mutation=False
    )
    updated_time: datetime = Field(default_factory=datetime.utcnow)

    # Validator
    _check_email = validator("email", allow_reuse=True)(iiit_email_only)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        max_anystr_length = 5001
        validate_assignment = True
        extra = Extra.forbid
        anystr_strip_whitespace = True


# TO ADD CLUB SUBSCRIPTION MODEL - v2
# ADD Descriptions for non-direct fields
