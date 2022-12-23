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
    FilePath,
    constr,
    conlist)
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


# sample pydantic model
class Sample(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    attribute: Optional[str]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


def iiit_email_only(v):
    valid_domains = ['@iiit.ac.in',
                     '@students.iiit.ac.in', '@research.iiit.ac.in']
    if any(valid_domain in v for valid_domain in valid_domains):
        return v.lower()

    raise ValueError('Official iiit emails only.')


class EnumStates(str, Enum):
    active = 'active'
    deleted = 'deleted'


class EnumCategories(str, Enum):
    cultural = "CULTURAL"
    technical = "TECHNICAL"
    other = "OTHER"


class Members(BaseModel):
    mail: EmailStr = Field(...)
    role: constr(min_length=1, max_length=99,
                 strip_whitespace=True) = Field(...)
    year: int = Field(default_factory=datetime.now().year, ge=2015, le=2040)
    approved: bool = False

    poc: bool = False
    contact: constr(
        regex="((\+91)|(0))?(-)?\s*?(91)?\s*?([6-9]{1}\d{2})((-?\s*?(\d{3})-?\s*?(\d{4}))|((\d{2})-?\s*?(\d{5})))") | None = None

    # Validator
    _check_email = validator('mail', allow_reuse=True)(iiit_email_only)

    @validator("poc", always=True)
    def check_current_poc(cls, value, values):
        if value==True and values["year"] != datetime.today().year:
            return False
        return value
    
    @validator("contact", always=True)
    def check_poc_contact(cls, value, values):
        if values["poc"] == True and not value:
            raise ValueError("POC Contact Number should be added")
        return value

    # Separate Coordinator & other members roles option in frontend, for better filtering for all_members_query


class Socials(BaseModel):
    website: AnyHttpUrl
    instagram: AnyHttpUrl
    facebook: AnyHttpUrl
    youtube: AnyHttpUrl
    twitter: AnyHttpUrl
    linkedin: AnyHttpUrl
    discord: AnyHttpUrl
    other_links: conlist([str, AnyHttpUrl], unique_items=True)  # Type and URL


class Clubs(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    shortform: str = Field(...)  # To make unique
    state: EnumStates = EnumStates.active
    category: EnumCategories = EnumCategories.other

    logo: FilePath | None = None
    banner: FilePath | None = None
    name: constr(min_length=2, max_length=100,
                 strip_whitespace=True) = Field(...)
    email: EmailStr = Field(...)
    tagline: constr(min_length=2, max_length=200,
                    strip_whitespace=True) | None = Field(...)  # Optional but required
    description: constr(
        max_length=600, strip_whitespace=True) | None = '[{"type":"paragraph", "children":[{"text":""}]}]'
    socials: Socials | None = Field(...)

    members: List[Members] | None = Field(...)

    created_time: datetime = Field(
        default_factory=datetime.utcnow, allow_mutation=False)
    updated_time: datetime = Field(default_factory=datetime.utcnow)

    # Validator
    _check_email = validator('email', allow_reuse=True)(iiit_email_only)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        max_anystr_length = 600
        validate_assignment = True
        extra = Extra.forbid
