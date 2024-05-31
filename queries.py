from typing import List

import strawberry
from fastapi.encoders import jsonable_encoder

from db import clubsdb
from models import Club

# import all models and types
from otypes import FullClubType, Info, SimpleClubInput, SimpleClubType


# fetch all active clubs
@strawberry.field
def activeClubs(info: Info) -> List[SimpleClubType]:
    """
    Description: Returns all the currently active clubs.
    Scope: Public
    Return Type: List[SimpleClubType]
    Input: None
    """
    results = clubsdb.find({"state": "active"}, {"_id": 0})
    clubs = [
        SimpleClubType.from_pydantic(Club.parse_obj(result))
        for result in results
    ]

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
        results = clubsdb.find()
    else:
        results = clubsdb.find({"state": "active"}, {"_id": 0})

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
    club = clubsdb.find_one({"cid": club_input["cid"].lower()}, {"_id": 0})

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


# register all queries
queries = [
    activeClubs,
    allClubs,
    club,
]
