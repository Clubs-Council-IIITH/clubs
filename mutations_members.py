import strawberry

from fastapi.encoders import jsonable_encoder
from datetime import datetime

from db import membersdb

# import all models and types
from otypes import Info
from models import Member
from otypes import FullMemberInput, SimpleMemberInput, MemberType

"""
MEMBER MUTATIONS
"""


def non_deleted_members(member_input) -> MemberType:
    """
    Function to return non-deleted members for a particular cid, uid
    Only to be used in admin functions, as it returns both approved/non-approved members.
    """
    updated_sample = membersdb.find_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        },
        {"_id": 0},
    )
    if updated_sample is None:
        raise Exception("No such Record")

    roles = []
    for i in updated_sample["roles"]:
        if i["deleted"] is True:
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
    membersdb.update_one(
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
    Mutation to create a new member by that specific 'club' or cc
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    uid = user["uid"]
    member_input = jsonable_encoder(memberInput.to_pydantic())

    if (member_input["cid"] != uid or user["role"] != "club") and user["role"] != "cc":
        raise Exception("Not Authenticated to access this API")

    if membersdb.find_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        }
    ):
        raise Exception("A record with same uid and cid already exists")

    if len(member_input["roles"]) == 0:
        raise Exception("Roles cannot be empty")

    for i in member_input["roles"]:
        if i["end_year"] and i["start_year"] > i["end_year"]:
            raise Exception("Start year cannot be greater than end year")

    roles0 = []
    for role in member_input["roles"]:
        if role["start_year"] > datetime.now().year:
            role["start_year"] = datetime.now().year
            role["end_year"] = None
        roles0.append(role)

    roles = []
    for role in roles0:
        role["approved"] = user["role"] == "cc"
        roles.append(role)

    member_input["roles"] = roles

    # DB STUFF
    created_id = membersdb.insert_one(member_input).inserted_id
    unique_roles_id(member_input["uid"], member_input["cid"])

    created_sample = Member.parse_obj(
        membersdb.find_one({"_id": created_id}, {"_id": 0})
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

    if (member_input["cid"] != uid or user["role"] != "club") and user["role"] != "cc":
        raise Exception("Not Authenticated to access this API")

    if len(member_input["roles"]) == 0:
        raise Exception("Roles cannot be empty")

    for i in member_input["roles"]:
        if i["end_year"] and i["start_year"] > i["end_year"]:
            raise Exception("Start year cannot be greater than end year")

    member_ref = membersdb.find_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        }
    )

    if member_ref is None:
        raise Exception("No such Record!")
    else:
        member_ref = Member.parse_obj(member_ref)

    member_roles = member_ref.roles

    roles = []
    for role in member_input["roles"]:
        if role["start_year"] > datetime.now().year:
            role["start_year"] = datetime.now().year
            role["end_year"] = None
        role_new = role.copy()

        # if role's start_year, end_year, name is same as existing role, then keep the existing approved status
        found_existing_role = False
        for i in member_roles:
            if (
                i.start_year == role_new["start_year"]
                and i.end_year == role_new["end_year"]
                and i.name == role_new["name"]
            ):
                role_new["approved"] = i.approved
                role_new["rejected"] = i.rejected
                role_new["deleted"] = i.deleted

                found_existing_role = True

                # Remove the existing role from member_roles
                member_roles.remove(i)
                break

        if not found_existing_role:
            role_new["approved"] = user["role"] == "cc"
        roles.append(role_new)

    # DB STUFF
    membersdb.update_one(
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
    Mutation to delete an already existing member (role) of that specific 'club'
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    uid = user["uid"]
    member_input = jsonable_encoder(memberInput)

    if (member_input["cid"] != uid or user["role"] != "club") and user["role"] != "cc":
        raise Exception("Not Authenticated to access this API")

    existing_data = membersdb.find_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        },
        {"_id": 0},
    )
    if existing_data is None:
        raise Exception("No such Record")

    if "rid" not in member_input or not member_input["rid"]:
        membersdb.delete_one(
            {
                "$and": [
                    {"cid": member_input["cid"]},
                    {"uid": member_input["uid"]},
                ]
            }
        )

        return MemberType.from_pydantic(Member.parse_obj(existing_data))

    roles = []
    for i in existing_data["roles"]:
        if i["rid"] == member_input["rid"]:
            i["deleted"] = True
        roles.append(i)

    # DB STUFF
    membersdb.update_one(
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

    existing_data = membersdb.find_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        },
        {"_id": 0},
    )
    if existing_data is None:
        raise Exception("No such Record")

    # if "rid" not in member_input:
    #     raise Exception("rid is required")

    roles = []
    for i in existing_data["roles"]:
        if not member_input["rid"] or i["rid"] == member_input["rid"]:
            i["approved"] = True
            i["rejected"] = False
        roles.append(i)

    # DB STUFF
    membersdb.update_one(
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
def rejectMember(memberInput: SimpleMemberInput, info: Info) -> MemberType:
    """
    Mutation to reject a member role by 'cc'
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    member_input = jsonable_encoder(memberInput)

    if user["role"] != "cc":
        raise Exception("Not Authenticated to access this API")

    existing_data = membersdb.find_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        },
        {"_id": 0},
    )
    if existing_data is None:
        raise Exception("No such Record")

    # if "rid" not in member_input:
    #     raise Exception("rid is required")

    roles = []
    for i in existing_data["roles"]:
        if not member_input["rid"] or i["rid"] == member_input["rid"]:
            i["approved"] = False
            i["rejected"] = True
        roles.append(i)

    # DB STUFF
    membersdb.update_one(
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

#     created_id = clubsdb.update_one(
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

#     created_sample = Member.parse_obj(membersdb.find_one({"_id": created_id}))
#     return MemberType.from_pydantic(created_sample)


# register all mutations
mutations = [
    createMember,
    editMember,
    deleteMember,
    approveMember,
    rejectMember,
]
