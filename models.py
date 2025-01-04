"""
Data Models for Clubs Microservice

This file decides what and how the Club information is stored in its MongoDB document.
It creates many custom data types for this purpose.

It defines the following models:
    Club: Represents a Club.
    Socials: Represents Social Media Links of a Club.
"""

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


# A custom  type for HttpUrls that validates the URL when assigned a value and converts it to a string.
http_url_adapter = TypeAdapter(HttpUrl)
HttpUrlString = Annotated[
    str,
    BeforeValidator(
        lambda value: str(http_url_adapter.validate_python(value))
    ),
]

# method that returns the current UTC(timezone) time
def create_utc_time():
    return datetime.now(timezone("UTC"))

class PyObjectId(ObjectId):
    """
    MongoDB ObjectId handler

    This class contains clasmethods to validate and serialize ObjectIds.
    ObjectIds of documents under the Clubs collection are stored under the 'id' field.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        """
        Defines custom schema for Pydantic validation

        This method is used to define the schema for the Pydantic model.

        Inputs:
            source_type (Any): The source type.
            handler: The handler.

        Returns:
            dict: The schema for the Pydantic model.
        """

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
        """
        Validates the given ObjectId

        Inputs:
            v (Any): The value to validate.

        Returns:
            ObjectId: The validated ObjectId.

        Raises:
            ValueError: If the given value is not a valid ObjectId.
        """
        
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        """
        Generates JSON schema

        This method is used to generate the JSON schema for the Pydantic model.

        Inputs:
            field_schema (dict): The field schema.
        """
        
        field_schema.update(type="string")


def iiit_email_only(v: str) -> str:
    """
    Email validator for IIIT-H emails

    This function validates the given email address according to valid IIIT-H email formats.

    Inputs:
        v (str): The email address to validate.

    Returns:
            str: The validated email address in lower case.

    Raises:
        ValueError: If the given email address is not a valid IIIT-H email.        
    """

    valid_domains = [
        "@iiit.ac.in",
        "@students.iiit.ac.in",
        "@research.iiit.ac.in",
    ]
    if any(valid_domain in v for valid_domain in valid_domains):
        return v.lower()

    raise ValueError("Official iiit emails only.")


def current_year() -> int:
    """
    Returns the current year

    Returns:
        int: The current year.
    """

    return datetime.now().year

# Enum for the status of a Club(active or deleted)
@strawberry.enum
class EnumStates(str, Enum):
    active = "active"
    deleted = "deleted"

# Enum for the categories of a Club(cultural, technical, affinity or other)
@strawberry.enum
class EnumCategories(str, Enum):
    cultural = "cultural"
    technical = "technical"
    affinity = "affinity"
    other = "other"


class Social(BaseModel):
    """
    Social Media Links Model

    This class atrributes represent the social media links of a Club.
    It also checks for duplicate URLs in the 'other_links' field.
    All the attributes are optional and use the HttpUrlString type to validate and store the URLs.

    Atrributes:
        website (HttpUrlString | None): The website URL of the Club.
        instagram (HttpUrlString | None): The Instagram URL of the Club.
        facebook (HttpUrlString | None): The Facebook URL of the Club.
        youtube (HttpUrlString | None): The YouTube URL of the Club.
        twitter (HttpUrlString | None): The Twitter URL of the Club.
        linkedin (HttpUrlString | None): The LinkedIn URL of the Club.
        discord (HttpUrlString | None): The Discord URL of the Club.
        whatsapp (HttpUrlString | None): The WhatsApp URL of the Club.
        other_links (List[HttpUrlString]): The other social media links of the Club.

    Raises:
        ValueError: If duplicate URLs are found in the 'other_links' field.
    """

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
    """
    Club Model

    This class represents a Club.
    Its attributes store all the details of a Club.
    It also validates the email address of the Club using the iiit_email_only method.

    Attributes:
        id (PyObjectId): Stores the ObjectId of the Club's document in MongoDB.Uses the PyObjectId class.
        cid (str): The unique identifier of the Club.
        code (str): The unique short code of the Club.
        state (EnumStates): The state of the Club.Uses the EnumStates enum.
        category (EnumCategories): The category of the Club.Uses the EnumCategories enum.
        student_body (bool): Whether the Club is a Student Body or not.
        name (str): The name of the Club.
        email (EmailStr): The email address of the Club.
        logo (str | None): The URL of the Club's official logo.
        banner (str | None): The URL of the Club's official banner.
        banner_square (str | None): The URL of the Club's official square banner.
        tagline (str): The tagline of the Club.
        description (str): The description of the Club.
        social (Social): The social media links of the Club.Uses the Social class.
        created_time (datetime): The date and time when the Club was created.Uses the current_utc_time method.
        updated_time (datetime): The date and time when the Club was last updated.
    """

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
