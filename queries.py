"""
Queries for Clubs
"""

from typing import List

import strawberry
from fastapi.encoders import jsonable_encoder

from db import clubsdb
from models import Club

# import all models and types
from otypes import FullClubType, Info, SimpleClubInput, SimpleClubType


@strawberry.field
async def allClubs(
    info: Info, onlyActive: bool = False
) -> List[SimpleClubType]:
    """
    Fetches all the clubs

    This method returns all the clubs when accessed CC.
    When accessed by public or onlyActive is True, 
    it returns only the active clubs.
    Access to both public and CC (Clubs Council).

    Args:
        info (otypes.Info): User metadata and cookies.
        onlyActive (bool): If true, returns only active clubs.
            Default is False.

    Returns:
        (List[otypes.SimpleClubType]): List of all clubs.
    """
    user = info.context.user
    isAdmin = False
    if user is not None and user["role"] in ["cc"] and not onlyActive:
        isAdmin = True

    results = []
    if isAdmin:
        results = await clubsdb.find().to_list(length=None)
    else:
        results = await clubsdb.find({"state": "active"}, {"_id": 0}).to_list(
            length=None
        )

    clubs = []
    for result in results:
        clubs.append(SimpleClubType.from_pydantic(Club.model_validate(result)))

    return clubs


@strawberry.field
async def club(clubInput: SimpleClubInput, info: Info) -> FullClubType:
    """
    Fetches all Club Details of a club

    Used to get all the details of a deleted/active club by its cid.
    Returns deleted clubs also for CC and not for public.
    Accessible to both public and CC(Clubs Council).

    Args:
        clubInput (otypes.SimpleClubInput): The club cid.
        info (otypes.Info): User metadata and cookies.

    Returns:
        (otypes.FullClubType): Contains all the club details.

    Raises:
        Exception: If the club is not found.
        Exception: If the club is deleted and the user is not CC.
    """
    user = info.context.user
    club_input = jsonable_encoder(clubInput)

    result = None
    club = await clubsdb.find_one(
        {"cid": club_input["cid"].lower()}, {"_id": 0}
    )

    if not club:
        raise Exception("No Club Found")

    # check if club is deleted
    if club["state"] == "deleted":
        # if deleted, check if requesting user is admin
        if (user is not None) and (user["role"] in ["cc"]):
            result = Club.model_validate(club)

        # if not admin, raise error
        else:
            raise Exception("No Club Found")

    # if not deleted, return club
    else:
        result = Club.model_validate(club)

    if result:
        return FullClubType.from_pydantic(result)

    else:
        raise Exception("No Club Result Found")


# register all queries
queries = [
    allClubs,
    club,
]
