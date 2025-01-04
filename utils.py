"""
Helper functions

This file contains methods which make queries and mutations to different microservices within the backend.
"""

import os

import requests

inter_communication_secret = os.getenv("INTER_COMMUNICATION_SECRET")


def update_role(uid, cookies=None, role="club"):
    """
    Updates Role of a user

    This function is used to update the role of a user.
    It makes a mutation to the Users Microservice.
    Which is resolved by the updateRole function.
    Updating a user's role to 'club'(or 'cc','slo','slc') makes the user a member of the club or committee.

    Inputs:
        uid (str): The uid(User id) of the user whose role is to be changed.
        cookies (dict): The cookies of the user.(Default: None)
        role (str): The role to be updated to.(Default: 'club')
    
    Returns:
        result of the mutation if successful.
        else returns None.
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
                "interCommunicationSecret": inter_communication_secret,
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
                "http://gateway/graphql",
                json={"query": query, "variables": variables},
            )

        return result.json()
    except Exception:
        return None


def update_events_members_cid(old_cid, new_cid, cookies=None) -> bool:
    """
    Function to change the cid of events and members of a club

    It is used when a club changes their cid.
    It makes 2 mutations one to the Events and another to the Members Microservice.
    Which are resolved by the updateEventsCid and updateMembersCid functions.
    They change the club's cid in all the events and members of the club.

    Inputs:
        old_cid (str): The old cid of the club.
        new_cid (str): The new cid of the club.
        cookies (dict): The cookies of the user.(Default: None)

    Returns:
        True if both mutations are successful.
        else returns False.
    """

    return1, return2 = None, None
    try:
        query = """
                    mutation UpdateEventsCid($oldCid: String!, $newCid: String!, $interCommunicationSecret: String) {
                        updateEventsCid(oldCid: $oldCid, newCid: $newCid, interCommunicationSecret: $interCommunicationSecret)
                    }
                """  # noqa: E501
        variables = {
            "oldCid": old_cid,
            "newCid": new_cid,
            "interCommunicationSecret": inter_communication_secret,
        }
        if cookies:
            result = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variables},
                cookies=cookies,
            )
        else:
            result = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variables},
            )

        return1 = result.json()
    except Exception:
        return False

    try:
        query = """
                    mutation UpdateMembersCid($oldCid: String!, $newCid: String!, $interCommunicationSecret: String) {
                        updateMembersCid(oldCid: $oldCid, newCid: $newCid, interCommunicationSecret: $interCommunicationSecret)
                    }
                """  # noqa: E501
        variables = {
            "oldCid": old_cid,
            "newCid": new_cid,
            "interCommunicationSecret": inter_communication_secret,
        }
        if cookies:
            result = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variables},
                cookies=cookies,
            )
        else:
            result = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variables},
            )

        return2 = result.json()
    except Exception:
        return False

    if return1 and return2:
        return True
    else:
        return False


def getUser(uid, cookies=None):
    """
    Function to get a user's details

    This function is used to fetch a specific user's details.
    It makes a query to the Users Microservice.
    Which is resolved by the userProfile function.

    Inputs:
        uid (str): The uid of the user whose details are to be fetched.
        cookies (dict): The cookies of the user.(Default: None)
    
    Returns:
        The user's details if successful.
        else returns None.
    """

    try:
        query = """
            query GetUserProfile($userInput: UserInput!) {
                userProfile(userInput: $userInput) {
                    firstName
                    lastName
                    email
                    rollno
                }
            }
        """
        variable = {"userInput": {"uid": uid}}
        if cookies:
            request = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variable},
                cookies=cookies,
            )
        else:
            request = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variable},
            )

        return request.json()["data"]["userProfile"]
    except Exception:
        return None
