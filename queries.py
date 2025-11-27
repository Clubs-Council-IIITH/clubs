"""
Queries for Clubs
"""

from typing import List

import strawberry
from cachetools import TTLCache
from fastapi.encoders import jsonable_encoder

from db import clubsdb
from models import Club

# import all models and types
from otypes import FullClubType, Info, SimpleClubInput, SimpleClubType

active_clubs = TTLCache(maxsize=1, ttl=86400)  # 24 hours
club_cache = TTLCache(maxsize=50, ttl=86400)  # 24 hours


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

    Note: The results are cached for 24 hours for public access.

    Args:
        info (otypes.Info): User metadata and cookies.
        onlyActive (bool): If true, returns only active clubs.
            Default is False.

    Returns:
        (List[otypes.SimpleClubType]): List of all clubs.
    """
    user = info.context.user
    is_admin = user is not None and user["role"] in ["cc"] and not onlyActive

    # For public, serve from cache if available
    if not is_admin:
        if "active_clubs" in active_clubs:
            return active_clubs["active_clubs"]

    results = []
    if is_admin:
        results = await clubsdb.find().to_list(length=None)
    else:
        results = await clubsdb.find({"state": "active"}, {"_id": 0}).to_list(
            length=None
        )

    clubs = []
    for result in results:
        clubs.append(SimpleClubType.from_pydantic(Club.model_validate(result)))

    # Update the cache if not admin
    if not is_admin:
        active_clubs["active_clubs"] = clubs

    return clubs


@strawberry.field
async def club(clubInput: SimpleClubInput, info: Info) -> FullClubType:
    """
    Fetches all Club Details of a club

    Used to get all the details of a deleted/active club by its cid.
    Returns deleted clubs also for CC and not for public.
    Accessible to both public and CC(Clubs Council).

    Note: The results are cached for 24 hours for public access.

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
    is_admin = user is not None and user["role"] in ["cc"]

    club_input = jsonable_encoder(clubInput)
    cid = club_input["cid"].lower()

    # serve from cache if available for public
    if not is_admin and cid in club_cache:
        return club_cache[cid]

    result = None
    club = await clubsdb.find_one({"cid": cid}, {"_id": 0})

    if not club:
        raise Exception("No Club Found")

    # check if club is deleted
    if club["state"] == "deleted":
        # if deleted, check if requesting user is admin
        if is_admin:
            result = Club.model_validate(club)

        # if not admin, raise error
        else:
            raise Exception("No Club Found")

    # if not deleted, return club
    else:
        result = Club.model_validate(club)

    if result:
        full_club = FullClubType.from_pydantic(result)

        # cache the club if not admin and not deleted
        if not is_admin and club["state"] != "deleted":
            club_cache[cid] = full_club

        return full_club
    else:
        raise Exception("No Club Result Found")


# register all queries
queries = [
    allClubs,
    club,
]
