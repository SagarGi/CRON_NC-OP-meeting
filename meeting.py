import notify2
import requests
import requests.auth
import os
from dotenv import load_dotenv

def fetchMeetingsAndSendToMatrix():
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
            if element["_links"]["project"]["title"] == 'Demo project'
            ]

            no_of_meetings_scheduled = len(our_meetings)
            # body to be send according to the no of meetings available in the matrix chat
            data = {
                "msgtype": "m.text",
                "body": "",
                "format": "org.matrix.custom.html",
                "formatted_body": "<b><i>This is request check from NC+OP bot</i></b>"
            }

            if no_of_meetings_scheduled > 0:
                print("There is a meeting scheduled")
                try:
                    element_url= os.getenv("ELEMENT_CHAT_URL", "")
                    element_room_id = os.getenv("ELEMENT_ROOM_ID", "")
                    element_bot_access_token = os.getenv("ELEMENT_BOT_ACCESS_TOKEN", "")
                    element_chat_full_url = f"{element_url}/_matrix/client/r0/rooms/!{element_room_id}:matrix.org/send/m.room.message?access_token={element_bot_access_token}"
                    print(element_chat_full_url)
                    response_send_chat_to_element = requests.post(element_chat_full_url, json=data)
                    print(response_send_chat_to_element)
                    if response_send_chat_to_element.status_code == 200:
                        print("Chat has been sent to the element chat!")
                    else:
                        print("Failed to send it to element chat!")
                except requests.exceptions.RequestException as req_err:
                    print(f"Request error occurred: {req_err}")

            else:
                print("There are no available meeting as of now!")
            
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    
load_dotenv()
fetchMeetingsAndSendToMatrix()