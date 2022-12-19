from bson import ObjectId
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, AnyHttpUrl, PositiveInt
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


class EnumStates(str, Enum):
    active = 'active'
    deleted = 'deleted'


class EnumCategories(str, Enum):
    cultural = "CULTURAL"
    technical = "TECHNICAL"
    other = "OTHER"


class Members(BaseModel):
    mail: EmailStr = Field(...)
    role: str = Field(...)
    year: PositiveInt = Field(default_factory=datetime.now().year)
    approved: bool = False


class Socials(BaseModel):
    website: AnyHttpUrl
    instagram: AnyHttpUrl
    facebook: AnyHttpUrl
    youtube: AnyHttpUrl
    twitter: AnyHttpUrl
    linkedin: AnyHttpUrl
    discord: AnyHttpUrl
    other_links: List[str, AnyHttpUrl]  # Type and URL


class Clubs(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    state: EnumStates = EnumStates.active
    category: EnumCategories = EnumCategories.other

    # img: ??
    name: str = Field(...)
    email: EmailStr = Field(...)
    tagline: str | None = Field(...)  # Optional but required
    description: str | None = '[{"type":"paragraph", "children":[{"text":""}]}]'
    socials: Socials | None = Field(...)

    members: List[Members] | None = Field(...)

    created_time: datetime = Field(default_factory=datetime.utcnow)
    updated_time: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
