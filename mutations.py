import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List
from datetime import datetime
import requests

from db import db

# import all models and types
from otypes import Info
from models import Club, Member
from otypes import (
    FullClubInput,
    SimpleClubInput,
    SimpleClubType,
    FullClubType,
)
from otypes import FullMemberInput, SimpleMemberInput, MemberType

"""
CLUB MUTATIONS
"""


def updateRole(uid, cookies=None, role="club"):
    """
    Function to call the updateRole mutation
    """
    try:
        query = """
                    mutation UpdateRole($roleInput: RoleInput!) {
                        updateRole(roleInput: $roleInput)
                    }
                """
        variables = {
            "roleInput": {
                "role": role,
                "uid": uid,
            }
        }
        if cookies:
            result = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variables},
                cookies=cookies,
            )
        else:
            result = requests.post(
                "http://gateway/graphql", json={"query": query, "variables": variables}
            )
    except:
        pass


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

        cid_exists = db.clubs.find_one({"cid": club_input["cid"]})
        if cid_exists:
            raise Exception("A club with this cid already exists")

        code_exists = db.clubs.find_one({"code": club_input["code"]})
        if code_exists:
            raise Exception("A club with this short code already exists")

        created_id = db.clubs.insert_one(club_input).inserted_id
        created_sample = Club.parse_obj(db.clubs.find_one({"_id": created_id}))

        updateRole(club_input["cid"], info.context.cookies)

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
        exists = db.clubs.find_one({"cid": club_input["cid"]})
        if not exists:
            raise Exception("A club with this cid doesn't exist")

        club_input["state"] = exists["state"]
        club_input["_id"] = exists["_id"]

        db.clubs.replace_one({"cid": club_input["cid"]}, club_input)
        if "socials" in club_input.keys():
            db.clubs.update_one(
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
                        "socials.other_links": club_input["socials"]["other_links"],
                    }
                },
            )
        db.clubs.update_one(
            {"cid": club_input["cid"]},
            {
                "$set": {
                    "created_time": exists["created_time"],
                    "updated_time": datetime.utcnow(),
                }
            },
        )

        updateRole(exists["cid"], role="public")
        updateRole(club_input["cid"], role="club")

        result = Club.parse_obj(db.clubs.find_one({"cid": club_input["cid"]}))
        return FullClubType.from_pydantic(result)

    elif role in ["club"]:
        exists = db.clubs.find_one({"cid": club_input["cid"]})
        if uid != club_input["cid"]:
            raise Exception("Authentication Error! (CID CHANGED)")

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

        db.clubs.replace_one({"cid": uid}, club_input)
        if "socials" in club_input.keys():
            db.clubs.update_one(
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
                        "socials.other_links": club_input["socials"]["other_links"],
                    }
                },
            )
        db.clubs.update_one(
            {"cid": club_input["cid"]},
            {
                "$set": {
                    "created_time": exists["created_time"],
                    "updated_time": datetime.utcnow(),
                }
            },
        )

        result = Club.parse_obj(db.clubs.find_one({"cid": club_input["cid"]}))
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

    db.clubs.update_one(
        {"cid": club_input["cid"]},
        {"$set": {"state": "deleted", "updated_time": datetime.utcnow()}},
    )

    updateRole(club_input["cid"], info.context.cookies, "public")

    updated_sample = Club.parse_obj(db.clubs.find_one({"cid": club_input["cid"]}))

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

    db.clubs.update_one(
        {"cid": club_input["cid"]},
        {"$set": {"state": "active", "updated_time": datetime.utcnow()}},
    )

    updateRole(club_input["cid"], info.context.cookies, "club")

    updated_sample = Club.parse_obj(db.clubs.find_one({"cid": club_input["cid"]}))

    return SimpleClubType.from_pydantic(updated_sample)


"""
MEMBER MUTATIONS
"""


def non_deleted_members(member_input) -> MemberType:
    """
    Function to return non-deleted members for a particular cid, uid
    Only to be used in admin functions, as it return approved/non-approved members.
    """
    updated_sample = db.members.find_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        },
        {"_id": 0},
    )
    if updated_sample == None:
        raise Exception("No such Record")

    roles = []
    for i in updated_sample["roles"]:
        if i["deleted"] == True:
            continue
        roles.append(i)
    updated_sample["roles"] = roles

    return MemberType.from_pydantic(Member.parse_obj(updated_sample))


def unique_roles_id(uid, cid):
    """
    Function to give unique ids for each of the role in roles list
    """
    pipeline = [
        {
            "$set": {
                "roles": {
                    "$map": {
                        "input": {"$range": [0, {"$size": "$roles"}]},
                        "in": {
                            "$mergeObjects": [
                                {"$arrayElemAt": ["$roles", "$$this"]},
                                {
                                    "rid": {
                                        "$toString": {
                                            "$add": [
                                                {"$toLong": datetime.now()},
                                                "$$this",
                                            ]
                                        }
                                    }
                                },
                            ]
                        },
                    }
                }
            }
        }
    ]
    db.members.update_one(
        {
            "$and": [
                {"cid": cid},
                {"uid": uid},
            ]
        },
        pipeline,
    )


@strawberry.mutation
def createMember(memberInput: FullMemberInput, info: Info) -> MemberType:
    """
    Mutation to create a new member by that specific 'club'
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    uid = user["uid"]
    member_input = jsonable_encoder(memberInput.to_pydantic())

    if member_input["cid"] != uid and role != "club":
        raise Exception("Not Authenticated to access this API")

    if db.members.find_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        }
    ):
        raise Exception("A record with same uid and cid already exists")

    # DB STUFF
    created_id = db.members.insert_one(member_input).inserted_id
    unique_roles_id(member_input["uid"], member_input["cid"])

    created_sample = Member.parse_obj(
        db.members.find_one({"_id": created_id}, {"_id": 0})
    )

    return MemberType.from_pydantic(created_sample)


@strawberry.mutation
def editMember(memberInput: FullMemberInput, info: Info) -> MemberType:
    """
    Mutation to edit an already existing member+roles of that specific 'club'
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    uid = user["uid"]
    member_input = jsonable_encoder(memberInput.to_pydantic())

    if member_input["cid"] != uid and user["role"] != "club":
        raise Exception("Not Authenticated to access this API")

    roles = []
    for role in member_input["roles"]:
        if role["start_year"] > datetime.now().year:
            role["start_year"] = datetime.now().year
            role["end_year"] = None
        roles.append(role)

    # DB STUFF
    db.members.update_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        },
        {"$set": {"roles": roles, "poc": member_input["poc"]}},
    )

    unique_roles_id(member_input["uid"], member_input["cid"])

    return non_deleted_members(member_input)


@strawberry.mutation
def deleteMember(memberInput: SimpleMemberInput, info: Info) -> MemberType:
    """
    Mutation to delete an already existing member role of that specific 'club'
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    uid = user["uid"]
    member_input = jsonable_encoder(memberInput)

    if member_input["cid"] != uid and user["role"] != "club":
        raise Exception("Not Authenticated to access this API")

    existing_data = db.members.find_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        },
        {"_id": 0},
    )
    if existing_data == None:
        raise Exception("No such Record")

    if "rid" not in member_input:
        raise Exception("rid is required")

    roles = []
    for i in existing_data["roles"]:
        if i["rid"] == member_input["rid"]:
            i["deleted"] = True
        roles.append(i)

    # DB STUFF
    db.members.update_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        },
        {"$set": {"roles": roles}},
    )

    unique_roles_id(member_input["uid"], member_input["cid"])

    return non_deleted_members(member_input)


@strawberry.mutation
def approveMember(memberInput: SimpleMemberInput, info: Info) -> MemberType:
    """
    Mutation to approve a member role by 'cc'
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    member_input = jsonable_encoder(memberInput)

    if user["role"] != "cc":
        raise Exception("Not Authenticated to access this API")

    existing_data = db.members.find_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        },
        {"_id": 0},
    )
    if existing_data == None:
        raise Exception("No such Record")

    if "rid" not in member_input:
        raise Exception("rid is required")

    roles = []
    for i in existing_data["roles"]:
        if i["rid"] == member_input["rid"]:
            i["approved"] = True
        roles.append(i)

    # DB STUFF
    db.members.update_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        },
        {"$set": {"roles": roles}},
    )

    unique_roles_id(member_input["uid"], member_input["cid"])

    return non_deleted_members(member_input)


# @strawberry.mutation
# def leaveClubMember(memberInput: SimpleMemberInput, info: Info) -> MemberType:
#     user = info.context.user
#     if user is None:
#         raise Exception("Not Authenticated")

#     role = user["role"]
#     uid = user["uid"]
#     member_input = jsonable_encoder(memberInput.to_pydantic())

#     if member_input["cid"] != uid and role != "club":
#         raise Exception("Not Authenticated to access this API")

#     created_id = db.clubs.update_one(
#         {
#             "$and": [
#                 {"cid": member_input["cid"]},
#                 {"uid": member_input["uid"]},
#                 {"start_year": member_input["start_year"]},
#                 {"deleted": False},
#             ]
#         },
#         {"$set": {"end_year": datetime.now().year}},
#     )

#     created_sample = Member.parse_obj(db.members.find_one({"_id": created_id}))
#     return MemberType.from_pydantic(created_sample)


# register all mutations
mutations = [
    createClub,
    editClub,
    deleteClub,
    restartClub,
    createMember,
    editMember,
    deleteMember,
    approveMember,
]
