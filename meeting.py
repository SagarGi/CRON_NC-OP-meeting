import requests
import requests.auth
import os
from dotenv import load_dotenv
from datetime import datetime
import json

MEETING_TIME_START = "13:45" #Time in Nepal
TEMP_FILE_FOR_MEETING_AGENDA_STATE = "meeting_agenda_state.json"
OPENPROJECT_SERVER_ID = "openproject"
MATRIX_SERVER_ID = "matrix"

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

def getOpenProjectProjectName():
    return os.getenv("OPENPROJECT_PROJECT_NAME", "")

def getOpenProjectMeetingLink():
    return os.getenv("OPENPROJECT_MEETING_LINK", "")

def getTempJsonFilePath():
    return os.path.join(os.path.dirname(__file__), TEMP_FILE_FOR_MEETING_AGENDA_STATE)

def createMeetingAgendaSentStateFile():
    data = {"delivered": False}
    filename_path = getTempJsonFilePath()
    if not os.path.exists(filename_path):
        with open(filename_path, "w") as file:
            json.dump(data, file)

def setMeetingAgendaStateDelivered():
    filename_path = getTempJsonFilePath()
    with open(filename_path, "r") as file:
        data = json.load(file)
        data["delivered"] = True
    with open(filename_path, "w") as file:
        json.dump(data, file)

def getMeetingAgendaStateDelivered():
    filename_path = getTempJsonFilePath()
    with open(filename_path, "r") as file:
        data = json.load(file)
        return data["delivered"]

def makeHttpRequest(url, method, requestTo, data=None):
    try:
        if method == "GET" and requestTo == OPENPROJECT_SERVER_ID:
            user_access_token = getOpenProjectUserAccessToken()
            if user_access_token == "":
                raise Exception("OpenProject user access token is not provided!")
            response = requests.get(url, auth=requests.auth.HTTPBasicAuth('apikey', user_access_token))
            return response
        elif method == "POST" and requestTo == MATRIX_SERVER_ID:
            response = requests.post(url, json=data)
            return response
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return None
    
def getMeetingIdentifier(meeting_id):
    response_meetings_details = makeHttpRequest(f"{getOpenProjectUrl()}/api/v3/meetings/{meeting_id}", "GET", OPENPROJECT_SERVER_ID)
    response_meetings_details_json =  response_meetings_details.json()
    return response_meetings_details_json["_embedded"]["project"]["identifier"]


def fetchOpenProjectMeetingsDetails():
    query_params = '[{"time":{"operator":"=","values":["future"]}}]'
    meetings_url = f'{getOpenProjectUrl()}/api/v3/meetings?filters={query_params}'
    print(meetings_url)
    response_meetings = makeHttpRequest(meetings_url, "GET", OPENPROJECT_SERVER_ID)
    if response_meetings.status_code != 200:
        raise Exception("Failed to fetch meetings. Status code: " + str(response_meetings.status_code))
    
    meetings_json = response_meetings.json()
    # get only the meetings with title having 'Nextcloud App "OpenProject Integration"'
    our_meetings = [
        element for element in meetings_json["_embedded"]["elements"]
        if element["_links"]["project"]["title"] == getOpenProjectProjectName()
    ]

    no_of_meetings = len(our_meetings)
    meeting_details = {}
    if no_of_meetings == 0:
        meeting_details["number"] = 0
        return meeting_details
    
    if no_of_meetings == 1:
        meeting_id = our_meetings[0]["id"]
        # select and pass only required meeting details
        meeting_identifier = getMeetingIdentifier(meeting_id)
        meeting_details["number"] = 1
        meeting_details["id"] = meeting_id
        meeting_details["identifier"] = meeting_identifier
        return meeting_details
    
    if no_of_meetings > 1:
        meeting_id = our_meetings[0]["id"]
        meeting_identifier = getMeetingIdentifier(meeting_id)
        # here 2 signifies that more than one meeting has been scheduled
        meeting_details["number"] = 2
        meeting_details["identifier"] = meeting_identifier 
        return meeting_details
    

def getMeetingAgendaLink(meetings_details):
    no_of_meetings = meetings_details["number"]
    
    if no_of_meetings == 1:
        meeting_id = meetings_details["id"]
        meeting_identifier = meetings_details["identifier"]
        return f"<p>Agendas for today's meeting: <i>{getOpenProjectUrl()}/projects/{meeting_identifier}/meetings/{meeting_id}</i></p> <p>Join the meeting at:  <i><a href='{getOpenProjectMeetingLink()}'>{getOpenProjectMeetingLink()}</i></p>"
    elif no_of_meetings == 2:
        meeting_identifier = meetings_details["identifier"]
        return f"<p>Agendas for multiple meetings: <i>{getOpenProjectUrl()}/projects/{meeting_identifier}/meetings</i></p> <p>Join the meeting at:  <i><a href='{getOpenProjectMeetingLink()}'>{getOpenProjectMeetingLink()}</i></p>"
    else:
        return "No meetings have been scheduled for the week. Have a great day :)"
    
def getCurrentTimeInHourAndMinute():
    current_time = datetime.now()
    hour_minute_time = current_time.strftime("%H:%M")
    return hour_minute_time

    
def sendMeetingDetailsToOpenProjectNextcloudMatrix():
    element_url= getElementChatUrl()
    element_room_id = getElementRoomId()
    element_bot_access_token = getElementBotAccessToken()

    if element_url == "" or element_room_id == "" or element_bot_access_token == "":
        raise Exception("Element chat url, room id or bot access token is not provided!")
    
    element_chat_full_url = f"{element_url}/_matrix/client/r0/rooms/!{element_room_id}:matrix.org/send/m.room.message?access_token={element_bot_access_token}"
    
    meeting_details = fetchOpenProjectMeetingsDetails()
    data = {
        "msgtype": "m.text",
        "body": "",
        "format": "org.matrix.custom.html",
        "formatted_body": f"<b><p>Integration OpenProject Weekly Meeting:</p></b>{getMeetingAgendaLink(meeting_details)}</p>"
    }
    send_chat = True
    if getCurrentTimeInHourAndMinute() <= MEETING_TIME_START:
        # we check if there is a meeting scheduled for the day
        if meeting_details['number'] == 0:
            send_chat = False

    if send_chat and getMeetingAgendaStateDelivered() == False:
        response_send_chat_to_element = makeHttpRequest(element_chat_full_url, "POST", MATRIX_SERVER_ID, data)
        if response_send_chat_to_element.status_code != 200:
            raise Exception("Failed to send chat to element chat. Status code: " + str(response_send_chat_to_element.status_code))
        setMeetingAgendaStateDelivered()
        print("Chat sent to element chat successfully!")

    # if the current time is greater than the meeting start time, then delete the temporary file
    if getCurrentTimeInHourAndMinute() > MEETING_TIME_START:
        if os.path.exists(getTempJsonFilePath()):
            os.remove(getTempJsonFilePath())

# Load environment variables from .env file
load_dotenv()
# first create the temporary file to store the state of the meeting agenda sent
createMeetingAgendaSentStateFile()
# send the meeting details to the openproject nextcloud matrix
sendMeetingDetailsToOpenProjectNextcloudMatrix()