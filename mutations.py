"""
Mutation Resolvers

Contains mutation resolvers that create, edit, delete and restart a club
"""

from datetime import datetime

import strawberry
from fastapi.encoders import jsonable_encoder

from db import clubsdb
from models import Club

# import all models and types
from otypes import (
    FullClubInput,
    FullClubType,
    Info,
    SimpleClubInput,
    SimpleClubType,
)
from utils import getUser, update_events_members_cid, update_role


@strawberry.mutation
def createClub(clubInput: FullClubInput, info: Info) -> SimpleClubType:
    """
    Create a new Club.

    This resolver/method creates a new club.
    For a new club to be created, prior to the creation a user with a uid same as the cid of the club should exist.
    This user account will be the account of the club.
    Any changes or autherization for actions regarding the club are provided to this account.
    This user profile only exists on the database and not on LDAP.
    
    Iputs:
        clubInput (FullClubInput): Used to take input almost all the fields of the Club Schema.
        info (Info): Contains the user details.
    
    Accessibility:
        Only CC can create a club.

    Returns:
        SimpleClubType: Returns the created club.

    Raises Exception:
        Not Authenticated or Not Authenticated to access this API : If the user is not a CC.
        Club Already Exists : If a club with the same cid already exists.
        Invalid Club ID/Club Email : If there does not exist a user with the same cid or email.
        A club with the same code already exists : If a club with the same code already exists.
    """

    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    club_input = jsonable_encoder(clubInput.to_pydantic())

    if role in ["cc"]:
        club_input["cid"] = club_input["email"].split("@")[0]

        cid_exists = clubsdb.find_one({"cid": club_input["cid"]})
        if cid_exists:
            raise Exception("A club with this cid already exists")

        # Check whether there exists a user with the same cid or email
        clubMember = getUser(club_input["cid"], info.context.cookies)
        if clubMember is None:
            raise Exception("Invalid Club ID/Club Email")

        code_exists = clubsdb.find_one({"code": club_input["code"]})
        if code_exists:
            raise Exception("A club with this short code already exists")

        created_id = clubsdb.insert_one(club_input).inserted_id
        created_sample = Club.model_validate(
            clubsdb.find_one({"_id": created_id})
        )

        if not update_role(club_input["cid"], info.context.cookies):
            raise Exception("Error in updating the role for the club")

        return SimpleClubType.from_pydantic(created_sample)

    else:
        raise Exception("Not Authenticated to access this API")


@strawberry.mutation
def editClub(clubInput: FullClubInput, info: Info) -> FullClubType:
    """
    Edit a club.

    This resolver/method edits a club.
    editing of the club details is allowed to be done either by that specific club or the cc.
    CC can edit any club details.
    the Club can edit only few details.
    If user role is ‘cc’
        If the current and the new cid(Club id) are different then this method changes the role of the user with uid same as the old cid to ‘public’ and changes the role of the user with the same uid as the new cid to ‘club’.
        And then calls the update_events_members_cid method with the old cid and the new cid.
    If the user role is ‘club’
        Does not let the user change the name, email, category of the club.

    Inputs:
        clubInput (FullClubInput): Used to take input almost all the fields of the Club Schema.
        info (Info): Contains the user details.

    Accessibility:
        CC(Full Access), club(Partial Access).

    Returns:
        FullClubType: Returns the edited club's details.

    Raises Exception:
        Not Authenticated or Not Authenticated to access this API : If the user is not a CC or not a member of the club.
        For CC:
            A club with this code doesn't exist : If a club with the same code does not exist.
            Invalid Club ID/Club Email : If there does not exist a user with the same cid or email.
        For club:
            Authentication Error! (CLUB ID CHANGED) : If the user's uid and the clubs cid are not the same.
            Club Does Not Exist : If the club with the given cid does not exist.
            Only CC can edit the club details: If the user is not a CC and trying to change name, email, category of the club.
            
    """  # noqa: E501

    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    uid = user["uid"]

    club_input = jsonable_encoder(clubInput.to_pydantic())

    if role in ["cc"]:
        exists = clubsdb.find_one({"code": club_input["code"]})
        if not exists:
            raise Exception("A club with this code doesn't exist")

        # Check whether this cid is valid or not
        clubMember = getUser(club_input["cid"], info.context.cookies)
        if clubMember is None:
            raise Exception("Invalid Club ID/Club Email")

        club_input["state"] = exists["state"]
        club_input["_id"] = exists["_id"]

        clubsdb.replace_one({"code": club_input["code"]}, club_input)
        if "socials" in club_input.keys():
            clubsdb.update_one(
                {"code": club_input["code"]},
                {
                    "$set": {
                        "socials.website": club_input["socials"]["website"],
                        "socials.instagram": club_input["socials"][
                            "instagram"
                        ],
                        "socials.facebook": club_input["socials"]["facebook"],
                        "socials.youtube": club_input["socials"]["youtube"],
                        "socials.twitter": club_input["socials"]["twitter"],
                        "socials.linkedin": club_input["socials"]["linkedin"],
                        "socials.discord": club_input["socials"]["discord"],
                        "socials.whatsapp": club_input["socials"]["whatsapp"],
                        "socials.other_links": club_input["socials"][
                            "other_links"
                        ],
                    }
                },
            )
        clubsdb.update_one(
            {"code": club_input["code"]},
            {
                "$set": {
                    "created_time": exists["created_time"],
                    "updated_time": datetime.utcnow(),
                }
            },
        )

        if exists["cid"] != club_input["cid"]:
            return1 = update_role(
                exists["cid"], info.context.cookies, role="public"
            )
            return2 = update_role(
                club_input["cid"], info.context.cookies, role="club"
            )
            return3 = update_events_members_cid(
                exists["cid"], club_input["cid"], cookies=info.context.cookies
            )
            if not return1 or not return2 or not return3:
                raise Exception("Error in updating the role/cid.")

        result = Club.model_validate(
            clubsdb.find_one({"code": club_input["code"]})
        )
        return FullClubType.from_pydantic(result)

    elif role in ["club"]:
        if uid != club_input["cid"]:
            raise Exception("Authentication Error! (CLUB ID CHANGED)")

        exists = clubsdb.find_one({"cid": club_input["cid"]})
        if not exists:
            raise Exception("A club with this cid doesn't exist")

        if (
            club_input["name"] != exists["name"]
            or club_input["email"] != exists["email"]
        ):
            raise Exception(
                "You don't have permission to change the name/email of the club. Please contact CC for it"  # noqa: E501
            )

        if club_input["category"] != exists["category"]:
            raise Exception(
                "Only CC is allowed to change the category of club."
            )

        club_input["state"] = exists["state"]
        club_input["_id"] = exists["_id"]

        clubsdb.replace_one({"cid": uid}, club_input)
        if "socials" in club_input.keys():
            clubsdb.update_one(
                {"cid": club_input["cid"]},
                {
                    "$set": {
                        "socials.website": club_input["socials"]["website"],
                        "socials.instagram": club_input["socials"][
                            "instagram"
                        ],
                        "socials.facebook": club_input["socials"]["facebook"],
                        "socials.youtube": club_input["socials"]["youtube"],
                        "socials.twitter": club_input["socials"]["twitter"],
                        "socials.linkedin": club_input["socials"]["linkedin"],
                        "socials.discord": club_input["socials"]["discord"],
                        "socials.whatsapp": club_input["socials"]["whatsapp"],
                        "socials.other_links": club_input["socials"][
                            "other_links"
                        ],
                    }
                },
            )
        clubsdb.update_one(
            {"cid": club_input["cid"]},
            {
                "$set": {
                    "created_time": exists["created_time"],
                    "updated_time": datetime.utcnow(),
                }
            },
        )

        result = Club.model_validate(
            clubsdb.find_one({"cid": club_input["cid"]})
        )
        return FullClubType.from_pydantic(result)

    else:
        raise Exception("Not Authenticated to access this API")


@strawberry.mutation
def deleteClub(clubInput: SimpleClubInput, info: Info) -> SimpleClubType:
    """
    Delete a club.

    This method changes a club's state to "deleted".

    Input:
        clubInput (SimpleClubIput): contains the club's information(its cid).
        info (Info): An Info object containing the user's information.

    Accessibility:
        Only CC.
    
    Returns:
        SimpleClubType: The updated club's information.

    Raises Exception:
        Not Authenticated: If the user is not authenticated.
    """

    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    club_input = jsonable_encoder(clubInput)

    if role not in ["cc"]:
        raise Exception("Not Authenticated to access this API")

    clubsdb.update_one(
        {"cid": club_input["cid"]},
        {"$set": {"state": "deleted", "updated_time": datetime.utcnow()}},
    )

    update_role(club_input["cid"], info.context.cookies, "public")

    updated_sample = Club.model_validate(
        clubsdb.find_one({"cid": club_input["cid"]})
    )

    return SimpleClubType.from_pydantic(updated_sample)


@strawberry.mutation
def restartClub(clubInput: SimpleClubInput, info: Info) -> SimpleClubType:
    """
    Restart a club.

    This method is similar to deleteClub but changes the state of the club to "active".

    Input:
        clubInput (SimpleClubIput): contains the club's information(its cid).
        info (Info): An Info object containing the user's information.
    
    Accessibility:
        Only CC.

    Returns:
        SimpleClubType: The updated club's information.

    Raises Exception:
        Not Authenticated: If the user is not authenticated.
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    club_input = jsonable_encoder(clubInput)

    if role not in ["cc"]:
        raise Exception("Not Authenticated to access this API")

    clubsdb.update_one(
        {"cid": club_input["cid"]},
        {"$set": {"state": "active", "updated_time": datetime.utcnow()}},
    )

    update_role(club_input["cid"], info.context.cookies, "club")

    updated_sample = Club.model_validate(
        clubsdb.find_one({"cid": club_input["cid"]})
    )

    return SimpleClubType.from_pydantic(updated_sample)


# register all mutations
mutations = [
    createClub,
    editClub,
    deleteClub,
    restartClub,
]
