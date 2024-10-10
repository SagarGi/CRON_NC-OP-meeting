import requests
import requests.auth
import os
from dotenv import load_dotenv

OPENPROJECT_NAME='Nextcloud App "OpenProject Integration"'

# Load environment variables from .env file
load_dotenv()

def makeHttpRequest(url, method, requestTo, data=None):
    try:
        if method == "GET" and requestTo == "openproject":
            user_access_token = os.getenv("OPENPROJECT_USER_ACCESS_TOKEN", "")
            if user_access_token == "":
                print("User access token is not provided!")
                return None
            response = requests.get(url, auth=requests.auth.HTTPBasicAuth('apikey', user_access_token))
            return response
        elif method == "POST" and requestTo == "matrix":
            print("Sending chat to element chat!")
            response = requests.post(url, json=data)
            return response
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return None
    
def getMeetingIdentifier(openproject_host_url, meeting_id):
    response_meetings_details = makeHttpRequest(f"{openproject_host_url}/api/v3/meetings/{meeting_id}", "GET", "openproject")
    response_meetings_details_json =  response_meetings_details.json()
    return response_meetings_details_json["_embedded"]["project"]["identifier"]


def fetchOpenProjectMeetingsDetails():
    openproject_host_url = os.getenv("OPENPROJECT_HOST_URL", "http://localhost:3000")
    meetings_url = f"{openproject_host_url}/api/v3/meetings"
    response_meetings = makeHttpRequest(meetings_url, "GET", "openproject")
    meetings_json = response_meetings.json()
    # get only the meetings with title having 'Nextcloud App "OpenProject Integration"'
    our_meetings = [
        element for element in meetings_json["_embedded"]["elements"]
        if element["_links"]["project"]["title"] == OPENPROJECT_NAME
    ]

    no_of_meetings = len(our_meetings)
    meeting_details = {}
    if no_of_meetings == 0:
        print("No meeting has been scheduled!")
        meeting_details["number"] = 0
        return meeting_details
    
    if no_of_meetings == 1:
        print("Only one meeting has been scheduled!")
        meeting_id = our_meetings[0]["id"]
        # select and pass only required meeting details
        meeting_identifier = getMeetingIdentifier(openproject_host_url, meeting_id)
        meeting_details["number"] = 1
        meeting_details["id"] = meeting_id
        meeting_details["identifier"] = meeting_identifier
        return meeting_details
    
    if no_of_meetings > 1:
        print("More than one meeting has been scheduled!")
        meeting_id = our_meetings[0]["id"]
        meeting_identifier = getMeetingIdentifier(openproject_host_url, meeting_id)
        # here 2 signifies that more than one meeting has been scheduled
        meeting_details["number"] = 2
        meeting_details["identifier"] = meeting_identifier 
        return meeting_details
    

    
def sendMeetingDetailsToOpenProjectNextcloudMatrix():
    meetings_details = fetchOpenProjectMeetingsDetails()
    element_url= os.getenv("ELEMENT_CHAT_URL", "")
    element_room_id = os.getenv("ELEMENT_ROOM_ID", "")
    element_bot_access_token = os.getenv("ELEMENT_BOT_ACCESS_TOKEN", "")

    if element_url == "" or element_room_id == "" or element_bot_access_token == "":
        print("Element chat details are not provided!")
        return
    
    element_chat_full_url = f"{element_url}/_matrix/client/r0/rooms/!{element_room_id}:matrix.org/send/m.room.message?access_token={element_bot_access_token}"
    data = {
        "msgtype": "m.text",
        "body": "",
        "format": "org.matrix.custom.html",
        "formatted_body": "<b><i>This is request check from NC+OP bot</i></b>"
    }
    response_send_chat_to_element = makeHttpRequest(element_chat_full_url, "POST", "matrix", data)
    print(response_send_chat_to_element)
    


sendMeetingDetailsToOpenProjectNextcloudMatrix()