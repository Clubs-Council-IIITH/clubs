import strawberry

from fastapi.encoders import jsonable_encoder
from datetime import datetime

from db import clubsdb
from utils import update_role, update_events_members_cid, getUser

# import all models and types
from otypes import Info
from models import Club
from otypes import (
    FullClubInput,
    SimpleClubInput,
    FullClubType,
    SimpleClubType,
)


@strawberry.mutation
def createClub(clubInput: FullClubInput, info: Info) -> SimpleClubType:
    """
    Create a new Club.
    Checks for the 'cc' role, else raises an Error.
    Checks for uniqueness of the club code.
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

        # Check whether this cid is valid or not
        clubMember = getUser(club_input["cid"], info.context.cookies)
        if clubMember is None:
            raise Exception("Invalid Club ID")

        code_exists = clubsdb.find_one({"code": club_input["code"]})
        if code_exists:
            raise Exception("A club with this short code already exists")

        created_id = clubsdb.insert_one(club_input).inserted_id
        created_sample = Club.parse_obj(clubsdb.find_one({"_id": created_id}))

        if not update_role(club_input["cid"], info.context.cookies):
            raise Exception("Error in updating the role for the club")

        return SimpleClubType.from_pydantic(created_sample)

    else:
        raise Exception("Not Authenticated to access this API")


@strawberry.mutation
def editClub(clubInput: FullClubInput, info: Info) -> FullClubType:
    """
    Mutation for editing of the club details either by that specific club or the cc.
    """
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
            raise Exception("Invalid Club ID")

        club_input["state"] = exists["state"]
        club_input["_id"] = exists["_id"]

        clubsdb.replace_one({"code": club_input["code"]}, club_input)
        if "socials" in club_input.keys():
            clubsdb.update_one(
                {"code": club_input["code"]},
                {
                    "$set": {
                        "socials.website": club_input["socials"]["website"],
                        "socials.instagram": club_input["socials"]["instagram"],
                        "socials.facebook": club_input["socials"]["facebook"],
                        "socials.youtube": club_input["socials"]["youtube"],
                        "socials.twitter": club_input["socials"]["twitter"],
                        "socials.linkedin": club_input["socials"]["linkedin"],
                        "socials.discord": club_input["socials"]["discord"],
                        "socials.whatsapp": club_input["socials"]["whatsapp"],
                        "socials.other_links": club_input["socials"]["other_links"],
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
            return1 = update_role(exists["cid"], info.context.cookies, role="public")
            return2 = update_role(club_input["cid"], info.context.cookies, role="club")
            return3 = update_events_members_cid(
                exists["cid"], club_input["cid"], cookies=info.context.cookies
            )
            if not return1 or not return2 or not return3:
                raise Exception("Error in updating the role/cid.")

        result = Club.parse_obj(clubsdb.find_one({"code": club_input["code"]}))
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
                "You don't have permission to change the name/email of the club. Please contact CC for it"
            )

        if club_input["category"] != exists["category"]:
            raise Exception("Only CC is allowed to change the category of club.")

        club_input["state"] = exists["state"]
        club_input["_id"] = exists["_id"]

        clubsdb.replace_one({"cid": uid}, club_input)
        if "socials" in club_input.keys():
            clubsdb.update_one(
                {"cid": club_input["cid"]},
                {
                    "$set": {
                        "socials.website": club_input["socials"]["website"],
                        "socials.instagram": club_input["socials"]["instagram"],
                        "socials.facebook": club_input["socials"]["facebook"],
                        "socials.youtube": club_input["socials"]["youtube"],
                        "socials.twitter": club_input["socials"]["twitter"],
                        "socials.linkedin": club_input["socials"]["linkedin"],
                        "socials.discord": club_input["socials"]["discord"],
                        "socials.whatsapp": club_input["socials"]["whatsapp"],
                        "socials.other_links": club_input["socials"]["other_links"],
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

        result = Club.parse_obj(clubsdb.find_one({"cid": club_input["cid"]}))
        return FullClubType.from_pydantic(result)

    else:
        raise Exception("Not Authenticated to access this API")


@strawberry.mutation
def deleteClub(clubInput: SimpleClubInput, info: Info) -> SimpleClubType:
    """
    Mutation for the cc to move a club to deleted state.
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

    updated_sample = Club.parse_obj(clubsdb.find_one({"cid": club_input["cid"]}))

    return SimpleClubType.from_pydantic(updated_sample)


@strawberry.mutation
def restartClub(clubInput: SimpleClubInput, info: Info) -> SimpleClubType:
    """
    Mutation for cc to move a club from deleted state to asctive state.
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

    updated_sample = Club.parse_obj(clubsdb.find_one({"cid": club_input["cid"]}))

    return SimpleClubType.from_pydantic(updated_sample)


# register all mutations
mutations = [
    createClub,
    editClub,
    deleteClub,
    restartClub,
]
