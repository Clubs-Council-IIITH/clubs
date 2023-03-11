import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List

from db import db

# import all models and types
from otypes import Info

from models import Club, Member
from otypes import SimpleClubType, FullClubType, SimpleClubInput
from otypes import MemberType


# fetch all active clubs
@strawberry.field
def activeClubs(info: Info) -> List[SimpleClubType]:
    results = db.clubs.find({"state": "active"})
    clubs = [SimpleClubType.from_pydantic(Club.parse_obj(result)) for result in results]

    return clubs


@strawberry.field
def allClubs(info: Info) -> List[SimpleClubType]:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]

    results = []
    if role in ["cc"]:
        results = db.clubs.find()

    else:
        raise Exception("Not Authenticated to access this API")

    clubs = []
    for result in results:
        clubs.append(SimpleClubType.from_pydantic(Club.parse_obj(result)))

    return clubs


@strawberry.field
def club(clubInput: SimpleClubInput, info: Info) -> FullClubType:
    user = info.context.user
    club_input = jsonable_encoder(clubInput)

    result = None
    club = db.clubs.find_one({"cid": club_input["cid"]})

    # check if club is deleted
    if club["state"] == "deleted":
        # if deleted, check if requesting user is admin
        if (user is not None) and (user["role"] in ["cc"]):
            result = Club.parse_obj(club)

        # if not admin, raise error
        else:
            raise Exception("Not Authenticated")

    # if not deleted, return club
    else:
        result = Club.parse_obj(club)

    if result:
        return FullClubType.from_pydantic(result)

    else:
        raise Exception("No Club Result Found")


@strawberry.field
def members(clubInput: SimpleClubInput, info: Info) -> List[MemberType]:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]

    results = None
    club_input = jsonable_encoder(clubInput)

    if role in ["cc"]:
        results = db.members.find(
            {"$and": [{"cid": club_input["cid"]}, {"deleted": False}]}, {"_id": 0}
        )
    elif role in ["club"] and user["uid"] == club_input["cid"]:
        results = db.members.find(
            {"$and": [{"cid": club_input["cid"]}, {"deleted": False}]}, {"_id": 0}
        )
    else:
        results = db.members.find(
            {
                "$and": [
                    {"cid": club_input["cid"]},
                    {"deleted": False},
                    {"approved": True},
                ]
            },
            {"_id": 0},
        )

    if results:
        members = []
        for result in results:
            members.append(MemberType.from_pydantic(Member.parse_obj(result)))
        return members
    else:
        raise Exception("No Member Result Found")


@strawberry.field
def pendingMembers(info: Info) -> List[MemberType]:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]

    results = None

    if role in ["cc"]:
        results = db.members.find(
            {"$and": [{"approved": False}, {"deleted": False}]}, {"_id": 0}
        )

    if results:
        members = []
        for result in results:
            members.append(MemberType.from_pydantic(Member.parse_obj(result)))
        return members
    else:
        raise Exception("No Member Result Found")


# register all queries
queries = [
    activeClubs,
    allClubs,
    club,
    members,
    pendingMembers,
]
