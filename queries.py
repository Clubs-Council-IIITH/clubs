import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List

from db import db

# import all models and types
from otypes import Info

from models import Club, Member
from otypes import SimpleClubType, FullClubType, SimpleClubInput, SimpleMemberInput
from otypes import MemberType


# fetch all active clubs
@strawberry.field
def activeClubs(info: Info) -> List[SimpleClubType]:
    """
    Description: Returns all the currently active clubs.
    Scope: Public
    Return Type: List[SimpleClubType]
    Input: None
    """
    results = db.clubs.find({"state": "active"}, {"_id": 0})
    clubs = [SimpleClubType.from_pydantic(Club.parse_obj(result)) for result in results]

    return clubs


@strawberry.field
def allClubs(info: Info) -> List[SimpleClubType]:
    """
    Description:
        For CC:
            Returns all the currently active/deleted clubs.
        For Public:
            Returns all the currently active clubs.
    Scope: CC (For All Clubs), Public (For Active Clubs)
    Return Type: List[SimpleClubType]
    Input: None
    """
    user = info.context.user
    if user is None:
        role = "public"
    else:
        role = user["role"]

    results = []
    if role in ["cc"]:
        results = db.clubs.find()
    else:
        results = db.clubs.find({"state": "active"}, {"_id": 0})

    clubs = []
    for result in results:
        clubs.append(SimpleClubType.from_pydantic(Club.parse_obj(result)))

    return clubs


@strawberry.field
def club(clubInput: SimpleClubInput, info: Info) -> FullClubType:
    """
    Description: Returns complete details of the club, from its club-id.
        For CC:
            Returns details even for deleted clubs.
        For Public:
            Returns details only for the active clubs.
    Scope: Public
    Return Type: FullClubType
    Input: SimpleClubInput (cid)
    Errors:
        - cid doesn't exist
        - if not cc and club is deleted
    """
    user = info.context.user
    club_input = jsonable_encoder(clubInput)

    result = None
    club = db.clubs.find_one({"cid": club_input["cid"]}, {"_id": 0})

    if not club:
        raise Exception("No Club Found")

    # check if club is deleted
    if club["state"] == "deleted":
        # if deleted, check if requesting user is admin
        if (user is not None) and (user["role"] in ["cc"]):
            result = Club.parse_obj(club)

        # if not admin, raise error
        else:
            raise Exception("No Club Found")

    # if not deleted, return club
    else:
        result = Club.parse_obj(club)

    if result:
        return FullClubType.from_pydantic(result)

    else:
        raise Exception("No Club Result Found")


@strawberry.field
def member(memberInput: SimpleMemberInput, info: Info) -> MemberType:
    """
    Description:
        Returns member details
    Scope: Public
    Return Type: MemberType
    Input: SimpleMemberInput (cid, uid)
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    uid = user["uid"]
    member_input = jsonable_encoder(memberInput)

    if member_input["cid"] != uid and user["role"] != "club":
        raise Exception("Not Authenticated to access this API")

    member = db.members.find_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        },
        {"_id": 0},
    )
    if member == None:
        raise Exception("No such Record")

    return MemberType.from_pydantic(Member.parse_obj(member))


@strawberry.field
def members(clubInput: SimpleClubInput, info: Info) -> List[MemberType]:
    """
    Description:
        For CC & Specific Club:
            Returns all the non-deleted members.
        For Public:
            Returns all the non-deleted and approved members.
    Scope: CC + Club (For All Members), Public (For Approved Members)
    Return Type: List[MemberType]
    Input: SimpleClubInput (cid)
    """
    user = info.context.user
    if user is None:
        role = "public"
    else:
        role = user["role"]

    club_input = jsonable_encoder(clubInput)

    results = db.members.find({"cid": club_input["cid"]}, {"_id": 0})

    if results:
        members = []
        for result in results:
            roles = result["roles"]
            roles_result = []

            for i in roles:
                if i["deleted"] == True:
                    continue
                if not (
                    role in ["cc"]
                    or (role in ["club"] and user["uid"] == club_input["cid"])
                ):
                    if i["approved"] == False:
                        continue
                roles_result.append(i)

            if len(roles_result) > 0:
                result["roles"] = roles_result
                members.append(MemberType.from_pydantic(Member.parse_obj(result)))

        return members
    else:
        raise Exception("No Member Result Found")


@strawberry.field
def pendingMembers(info: Info) -> List[MemberType]:
    """
    Description: Returns all the non-deleted and non-approved members.
    Scope: CC
    Return Type: List[MemberType]
    Input: None
    """
    user = info.context.user
    if user is None or user["role"] not in ["cc"]:
        raise Exception("Not Authenticated")

    results = db.members.find({}, {"_id": 0})

    if results:
        members = []
        for result in results:
            roles = result["roles"]
            roles_result = []

            for i in roles:
                if i["deleted"] == True or i["approved"] == True:
                    continue
                roles_result.append(i)

            if len(roles_result) > 0:
                result["roles"] = roles_result
                members.append(MemberType.from_pydantic(Member.parse_obj(result)))

        return members
    else:
        raise Exception("No Member Result Found")


# register all queries
queries = [
    activeClubs,
    allClubs,
    club,
    member,
    members,
    pendingMembers,
]
