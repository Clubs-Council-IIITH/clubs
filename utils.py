import os

import requests

inter_communication_secret = os.getenv("INTER_COMMUNICATION_SECRET")


def update_role(uid, cookies=None, role="club"):
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
    Function to call the updateEventsCid & updateMembersCid mutation
    """
    return1, return2 = None, None
    try:
        query = """
                    mutation UpdateEventsCid($oldCid: String!, $newCid: String!, $interCommunicationSecret: String) {
                        updateEventsCid(oldCid: $oldCid, newCid: $newCid, interCommunicationSecret: $interCommunicationSecret)
                    }
                """
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
                """
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
    Function to get a particular user details
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
