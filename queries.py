"""
Query Resolvers

This file contains the 3 different query resolvers.
each resolves a different query, each providing a different set of information.

Resolvers:
    activeClubs: Returns all the currently active clubs.
    allClubs: Returns a specific club.
    clubs: Returns all the clubs.
"""

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
    For Active Clubs

    Returns all the currently active clubs

    Inputs:
        info (Info): Contains the user details.

    Accessibility: 
        Public.

    Returns : 
        List[SimpleClubType] : Returns a list of all the currently active clubs.
    """

    results = clubsdb.find({"state": "active"}, {"_id": 0})
    clubs = [
        SimpleClubType.from_pydantic(Club.model_validate(result))
        for result in results
    ]

    return clubs


@strawberry.field
def allClubs(info: Info) -> List[SimpleClubType]:
    """
    For All Clubs

    This method returns a list of all the clubs.
    For CC it returns details even for deleted clubs.
    For public users it returns only the active clubs.
    
    Inputs:
        info (Info): Contains the user details.

    Accessibility:
        Public(partial access), CC(Full Access).
    
    Returns :
        List[SimpleClubType] : Returns a list of all the clubs.
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
        clubs.append(SimpleClubType.from_pydantic(Club.model_validate(result)))

    return clubs


@strawberry.field
def club(clubInput: SimpleClubInput, info: Info) -> FullClubType:
    """
    For Specific Club

    This method returns a specific club.
    For users with role 'cc', it returns details even for a deleted club.
    For public users it returns info only if it is an active club.

    Inputs:
        clubInput (SimpleClubInput): Contains the club id of the club to be searched.
        info (Info): Contains the user details.

    Accessibility:
            Public(partial access), CC(Full Access).

    Returns:
        FullClubType: Returns the club details.
    
    Raises Exceptions:
        No club Found: If a club with the given club id is not found.
        No Club Result Found: If the club is deleted and requesting user does not have a role of 'cc'.
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
    activeClubs,
    allClubs,
    club,
]
