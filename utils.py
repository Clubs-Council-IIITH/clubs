import os

import requests

inter_communication_secret = os.getenv("INTER_COMMUNICATION_SECRET")


def update_role(uid, cookies=None, role="club"):
    """
    Function to call the updateRole mutation

    Makes a mutation resolved by the `updateRole` method from Users Microservice.
    Used to change a user's role field.

    Args:
        uid (str): User ID.
        cookies (dict): Cookies from the request. Defaults to None.
        role (str): Role of the user to be updated to. Defaults to 'club'.

    Returns:
        dict: Response from the mutation.
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

    Makes a mutation resolved by the `updateEventsCid` method from Events Microservice.
    Makes another mutation resolved by the `updateMembersCid` method from Members Microservice.
    Used when club changes its cid to change its members and events data accordingly.

    Args:
        old_cid (str): Old CID of the club.
        new_cid (str): New CID of the club.
        cookies (dict): Cookies from the request. Defaults to None.

    Returns:
        bool: True if both mutations are successful, False otherwise.
    """
    return1, return2 = None, None
    # Update Events CID
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

    # Update Members CID
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
    Function to get a particular user details

    Makes a query resolved by the `userProfile` method from Users Microservice.
    Used to get a users details.

    Args:
        uid (str): User ID of the user to be fetched.
        cookies (dict): Cookies from the request. Defaults to None.

    Returns:
        dict: User details as a result of the query.
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


def delete_file(filename):
    """
    Method for deleting a file from the files microservice
    
    Args:
        filename (str): Name of the file to be deleted
    
    Returns:
        Response from the files microservice
    """
    response = requests.post(
        "http://files/delete-file",
        params={
            "filename": filename,
            "inter_communication_secret": inter_communication_secret,
        },
    )

    if response.status_code != 200:
        raise Exception(response.text)

    return response.text


def check_remove_old_file(old_obj, new_obj, name="logo"):
    """
    Method to remove old files.
    
    Args:
        old_obj (dict): Old object containing the old file
        new_obj (dict): New object containing the new file
        name (str): Name of the file to be removed. Defaults to "logo" as mostly they are images of club logo's

    Returns:
        bool: True if the old file is removed, False otherwise
    """
    old_file = old_obj.get(name)
    new_file = new_obj.get(name)

    if old_file and new_file and old_file != new_file:
        try:
            delete_file(old_file)
        except Exception as e:
            print(f"Error in deleting old {name} file: {e}")
            return False

    return True
