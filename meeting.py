import notify2
import requests
import requests.auth
import os
from dotenv import load_dotenv

OPENPROJECT_NAME='Nextcloud App "OpenProject Integration"'

# Load environment variables from .env file
load_dotenv()

def fetchOpenProjectMeetingsDetails():
    auth_username= os.getenv("OPENPROJECT_USERNAME", "admin")
    auth_password = os.getenv("OPENPROJECT_PASSWORD", "admin")
    openproject_host_url = os.getenv("OPENPROJECT_HOST_URL", "http://localhost:3000")
    meetings_url = f"{openproject_host_url}/api/v3/meetings"
    try:
        response_meetings = requests.get(meetings_url, auth=requests.auth.HTTPBasicAuth(auth_username, auth_password))
        if response_meetings.status_code == 200:
            meetings_json = response_meetings.json()
            # get only the meetings with title having 'Nextcloud App "OpenProject Integration"'
            our_meetings = [
            element for element in meetings_json["_embedded"]["elements"]
            if element["_links"]["project"]["title"] == OPENPROJECT_NAME
            ]
            try:
                if len(our_meetings) == 1:
                    meeting_id = our_meetings[0]["id"]
                    response_meetings_details = requests.get(f"{meetings_url}/{meeting_id}", auth=requests.auth.HTTPBasicAuth(auth_username, auth_password))
                    response_meetings_details_json = response_meetings_details.json()
                    meeting_identifier = response_meetings_details_json["_embedded"]["project"]["identifier"]
                    print(meeting_identifier)
                    return response_meetings_details.json()
            except requests.exceptions.RequestException as req_err:
                print("Could not get meeting details for id ", meeting_id)
        else:
            print("Failed to fetch meetings!")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")

    
def sendMeetingDetailsToOpenProjectNextcloudMatrix():
    meetings = fetchOpenProjectMeetingsDetails()
    element_url= os.getenv("ELEMENT_CHAT_URL", "")
    element_room_id = os.getenv("ELEMENT_ROOM_ID", "")
    element_bot_access_token = os.getenv("ELEMENT_BOT_ACCESS_TOKEN", "")
    openproject_host_url = os.getenv("OPENPROJECT_HOST_URL", "http://localhost:3000")
    if len(meetings) == 1:
        # get meeting url
        meeting_id = meetings[0]["id"]
        meetings_url = f"{openproject_host_url}/projects/{OPENPROJECT_NAME}/meetings/{meeting_id}"
        print(meetings_url)
        # try:
        #     element_chat_full_url = f"{element_url}/_matrix/client/r0/rooms/!{element_room_id}:matrix.org/send/m.room.message?access_token={element_bot_access_token}"
        #     print(element_chat_full_url)
        #     data = {
        #         "msgtype": "m.text",
        #         "body": "",
        #         "format": "org.matrix.custom.html",
        #         "formatted_body": "<b><i>This is request check from NC+OP bot</i></b>"
        #     }
        #     response_send_chat_to_element = requests.post(element_chat_full_url, json=data)
        #     print(response_send_chat_to_element)
        #     if response_send_chat_to_element.status_code == 200:
        #         print("Chat has been sent to the element chat!")
        #     else:
        #         print("Failed to send it to element chat!")
        # except requests.exceptions.RequestException as req_err:
        #     print("Error occurred while sending chat to element chat: ", req_err)


sendMeetingDetailsToOpenProjectNextcloudMatrix()