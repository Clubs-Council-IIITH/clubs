import strawberry
from bson import ObjectId
from datetime import datetime
from enum import Enum
from pydantic import (
    field_validator, 
    ConfigDict,
    BaseModel,
    Field,
    EmailStr,
    AnyHttpUrl,
    ValidationError,
    validator,
)
from pydantic_core import core_schema
from typing import Any, List


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
    rid: str | None = Field(None, description="Unique Identifier for a role")
    name: str = Field(..., min_length=1, max_length=99)
    start_year: int = Field(..., ge=2010, le=2050)
    end_year: int | None = Field(None, gt=2010, le=2051)
    approved: bool = False
    rejected: bool = False
    deleted: bool = False

    # Validators
    @field_validator("end_year")
    def check_end_year(cls, value, values):
        if value != None and value < values["start_year"]:
            return None
        return value
    
    @field_validator("rejected")
    def check_status(cls, value, values):
        if values["approved"] == True and value == True:
            raise ValueError("Role cannot be both approved and rejected")
        return value
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True, 
        str_max_length=100, 
        validate_assignment=True, 
        validate_default=True,
        validate_return=True,
        extra="forbid", 
        str_strip_whitespace=True
        )


class Member(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    cid: str = Field(..., description="Club ID")
    uid: str = Field(..., description="User ID")
    roles: List[Roles] = Field(
        ..., description="List of Roles for that specific person"
    )

    poc: bool = Field(default_factory=(lambda: 0 == 1), description="Club POC")

    @field_validator("uid", mode="before")
    @classmethod
    def transform_uid(cls, v):
        return v.lower()
    
    # contact: str | None = Field(
    #     None, regex=r"((\+91)|(0))?(-)?\s*?(91)?\s*?([6-9]{1}\d{2})((-?\s*?(\d{3})-?\s*?(\d{4}))|((\d{2})-?\s*?(\d{5})))")

    # Validators
    # @validator("contact")
    # def check_poc_contact(cls, value, values):
    #     if values["poc"] == True and not value:
    #         raise ValueError("POC Contact Number should be added")
    #     return value

    # TODO[pydantic]: The following keys were removed: `json_encoders`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(
        arbitrary_types_allowed=True, 
        str_strip_whitespace=True, 
        str_max_length=600, 
        validate_assignment=True,
        validate_default=True,
        validate_return=True,
        extra="forbid", 
        json_encoders={ObjectId: str}, 
        populate_by_name=True
    )

    # Separate Coordinator & other members roles option in frontend, for better filtering for all_members_query


class Social(BaseModel):
    website: AnyHttpUrl | None = None
    instagram: AnyHttpUrl | None = None
    facebook: AnyHttpUrl | None = None
    youtube: AnyHttpUrl | None = None
    twitter: AnyHttpUrl | None = None
    linkedin: AnyHttpUrl | None = None
    discord: AnyHttpUrl | None = None
    other_links: List[AnyHttpUrl] = Field([])  # Type and URL

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
        ..., description="Unique Short Code of Club", max_length=15, min_length=2
    )  # equivalent to club id = short name
    state: EnumStates = EnumStates.active
    category: EnumCategories = EnumCategories.other
    student_body: bool = Field(False, description="Is this a Student Body?")

    name: str = Field(..., min_length=5, max_length=100)
    email: EmailStr = Field(...)  # Optional but required
    logo: str | None = Field(None, description="Club Official Logo pic URL")
    banner: str | None = Field(None, description="Club Long Banner pic URL")
    tagline: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(
        '{ "md": "", "html": "" }',
        max_length=9999,
        description="Club Description",
    )
    socials: Social = Field({}, description="Social Profile Links")

    created_time: datetime = Field(
        default_factory=datetime.utcnow, frozen=True
    )
    updated_time: datetime = Field(default_factory=datetime.utcnow)

    # Validator
    _check_email = validator("email", allow_reuse=True)(iiit_email_only)
    
    # TODO[pydantic]: The following keys were removed: `json_encoders`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(
        populate_by_name=True, 
        arbitrary_types_allowed=True, 
        json_encoders={ObjectId: str}, 
        str_max_length=10000, 
        validate_assignment=True, 
        validate_default=True,
        validate_return=True,
        extra="forbid", 
        str_strip_whitespace=True
    )


# TO ADD CLUB SUBSCRIPTION MODEL - v2
# ADD Descriptions for non-direct fields
