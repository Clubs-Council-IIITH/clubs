import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List

from db import db

# import all models and types
from otypes import Info

from models import Club, Member
from otypes import SimpleClubType, FullClubType, SimpleClubInput, SimpleMemberInput
from otypes import MemberType

"""
Club Queries
"""


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
    club = db.clubs.find_one({"cid": club_input["cid"].lower()}, {"_id": 0})

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


"""
Member Queries
"""


@strawberry.field
def member(memberInput: SimpleMemberInput, info: Info) -> MemberType:
    """
    Description:
        Returns member details for a specific club
    Scope: CC & Specific Club
    Return Type: MemberType
    Input: SimpleMemberInput (cid, uid)
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    uid = user["uid"]
    member_input = jsonable_encoder(memberInput)

    if (member_input["cid"] != uid or user["role"] != "club") and user["role"] != "cc":
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
def memberRoles(uid: str, info: Info) -> List[MemberType]:
    """
    Description:
        Returns member roles from each club
    Scope: CC & Specific Club
    Return Type: uid (str)
    Input: SimpleMemberInput (cid, uid, roles)
    """
    user = info.context.user
    if user is None:
        role = "public"
    else:
        role = user["role"]

    results = db.members.find({"uid": uid}, {"_id": 0})

    if not results:
        raise Exception("No Member Result/s Found")

    members = []
    for result in results:
        roles = result["roles"]
        roles_result = []

        for i in roles:
            if i["deleted"] == True:
                continue
            if role != "cc":
                if i["approved"] == False:
                    continue
            roles_result.append(i)

        if len(roles_result) > 0:
            result["roles"] = roles_result
            members.append(MemberType.from_pydantic(Member.parse_obj(result)))

    return members


@strawberry.field
def members(clubInput: SimpleClubInput, info: Info) -> List[MemberType]:
    """
    Description:
        For CC:
            Returns all the non-deleted members.
        For Specific Club:
            Returns all the non-deleted members of that club.
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

    if role not in ["cc"] or club_input["cid"] != "clubs":
        results = db.members.find({"cid": club_input["cid"]}, {"_id": 0})
    else:
        results = db.members.find({}, {"_id": 0})

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
        raise Exception("No Member Result/s Found")


@strawberry.field
def currentMembers(clubInput: SimpleClubInput, info: Info) -> List[MemberType]:
    """
    Description:
        For Everyone:
            Returns all the current non-deleted and approved members of the given clubid.
    
    Scope: Anyone (Non-Admin Function)
    Return Type: List[MemberType]
    Input: SimpleClubInput (cid)
    """
    user = info.context.user
    if user is None:
        role = "public"
    else:
        role = user["role"]
    
    club_input = jsonable_encoder(clubInput)

    if club_input["cid"] == "clubs":
        if role != "cc":
            raise Exception("Not Authenticated")
        
        results = db.members.find({}, {"_id": 0})
    else:
        results = db.members.find({"cid": club_input["cid"]}, {"_id": 0})

    if results:
        members = []
        for result in results:
            roles = result["roles"]
            roles_result = []

            for i in roles:
                if i["deleted"] == True or i["end_year"] is not None:
                    continue
                if i["approved"] == False:
                    continue
                roles_result.append(i)

            if len(roles_result) > 0:
                result["roles"] = roles_result
                members.append(MemberType.from_pydantic(Member.parse_obj(result)))

        return members
    else:
        raise Exception("No Member Result/s Found")


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

            print(roles)

            for i in roles:
                if i["deleted"] or i["approved"] or i["rejected"]:
                    continue
                roles_result.append(i)

            if len(roles_result) > 0:
                result["roles"] = roles_result
                members.append(MemberType.from_pydantic(Member.parse_obj(result)))

        return members
    else:
        raise Exception("No Member Result/s Found")


# register all queries
queries = [
    activeClubs,
    allClubs,
    club,
    member,
    memberRoles,
    members,
    currentMembers,
    pendingMembers,
]
