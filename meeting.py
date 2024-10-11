import requests
import requests.auth
import os
from dotenv import load_dotenv

OPENPROJECT_PROJECT_NAME='Nextcloud App "OpenProject Integration"'
OPENPROJECT_MEETING_LINK = "https://meet.openproject.org/b/storages"

# Load environment variables from .env file
load_dotenv()

def getOpenProjectUrl():
    return os.getenv("OPENPROJECT_HOST_URL", "http://localhost:3000")

def getElementChatUrl():
    return os.getenv("ELEMENT_CHAT_URL", "")

def getElementRoomId():
    return os.getenv("ELEMENT_ROOM_ID", "")

def getElementBotAccessToken():
    return os.getenv("ELEMENT_BOT_ACCESS_TOKEN", "")

def getOpenProjectUserAccessToken():
    return os.getenv("OPENPROJECT_USER_ACCESS_TOKEN", "")

def makeHttpRequest(url, method, requestTo, data=None):
    try:
        if method == "GET" and requestTo == "openproject":
            user_access_token = getOpenProjectUserAccessToken()
            if user_access_token == "":
                raise Exception("OpenProject user access token is not provided!")
            response = requests.get(url, auth=requests.auth.HTTPBasicAuth('apikey', user_access_token))
            return response
        elif method == "POST" and requestTo == "matrix":
            print("Sending chat to element chat!")
            response = requests.post(url, json=data)
            return response
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return None
    
def getMeetingIdentifier(meeting_id):
    response_meetings_details = makeHttpRequest(f"{getOpenProjectUrl()}/api/v3/meetings/{meeting_id}", "GET", "openproject")
    response_meetings_details_json =  response_meetings_details.json()
    return response_meetings_details_json["_embedded"]["project"]["identifier"]


def fetchOpenProjectMeetingsDetails():
    meetings_url = f"{getOpenProjectUrl()}/api/v3/meetings"
    response_meetings = makeHttpRequest(meetings_url, "GET", "openproject")
    if response_meetings.status_code != 200:
        raise Exception("Failed to fetch meetings. Status code: " + str(response_meetings.status_code))
    
    meetings_json = response_meetings.json()
    # get only the meetings with title having 'Nextcloud App "OpenProject Integration"'
    our_meetings = [
        element for element in meetings_json["_embedded"]["elements"]
        if element["_links"]["project"]["title"] == OPENPROJECT_PROJECT_NAME
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
        meeting_identifier = getMeetingIdentifier(meeting_id)
        meeting_details["number"] = 1
        meeting_details["id"] = meeting_id
        meeting_details["identifier"] = meeting_identifier
        return meeting_details
    
    if no_of_meetings > 1:
        print("More than one meeting has been scheduled!")
        meeting_id = our_meetings[0]["id"]
        meeting_identifier = getMeetingIdentifier(meeting_id)
        # here 2 signifies that more than one meeting has been scheduled
        meeting_details["number"] = 2
        meeting_details["identifier"] = meeting_identifier 
        return meeting_details
    

def getMeetingAgendaLink():
    meetings_details = fetchOpenProjectMeetingsDetails()
    no_of_meetings = meetings_details["number"]
    
    if no_of_meetings == 1:
        meeting_id = meetings_details["id"]
        meeting_identifier = meetings_details["identifier"]
        return f"<p>Agendas for today's meeting: <i>{getOpenProjectUrl()}/projects/{meeting_identifier}/meetings/{meeting_id}</i></p> <p>Join the meeting at:  <i><a href='{OPENPROJECT_MEETING_LINK}'>{OPENPROJECT_MEETING_LINK}</i></p>"
    elif no_of_meetings == 2:
        meeting_identifier = meetings_details["identifier"]
        return f"<p>Agendas for multiple meetings: <i>{getOpenProjectUrl()}/projects/{meeting_identifier}/meetings</i></p> <p>Join the meeting at:  <i><a href='{OPENPROJECT_MEETING_LINK}'>{OPENPROJECT_MEETING_LINK}</i></p>"
    else:
        return "No meetings have been scheduled for the week. Have a great day :)"

    
def sendMeetingDetailsToOpenProjectNextcloudMatrix():
    element_url= getElementChatUrl()
    element_room_id = getElementRoomId()
    element_bot_access_token = getElementBotAccessToken()

    if element_url == "" or element_room_id == "" or element_bot_access_token == "":
        print("Element chat details are not provided!")
        return
    
    element_chat_full_url = f"{element_url}/_matrix/client/r0/rooms/!{element_room_id}:matrix.org/send/m.room.message?access_token={element_bot_access_token}"
    meeting_information = getMeetingAgendaLink()
    data = {
        "msgtype": "m.text",
        "body": "",
        "format": "org.matrix.custom.html",
        "formatted_body": f"<b><p>Integration OpenProject Weekly Meeting:</p></b>{meeting_information}</p>"
    }
    response_send_chat_to_element = makeHttpRequest(element_chat_full_url, "POST", "matrix", data)
    if response_send_chat_to_element.status_code != 200:
        raise Exception("Failed to send chat to element chat. Status code: " + str(response_send_chat_to_element.status_code))
    
    print("Chat sent to element chat successfully!")


sendMeetingDetailsToOpenProjectNextcloudMatrix()