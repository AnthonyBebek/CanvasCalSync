from datetime import datetime, timedelta
from caldav import DAVClient
from caldav.elements.dav import DisplayName

from typing import Optional

class Assignment():
    """
    Create a assignment class to manage all assignment related stuff
    """
    def __init__(self, ID : str, Due : str, Name : str, Desc : Optional[str]) -> None:
        """
        :param ID: ID of assignment
        :type ID: str
        :param Due: Due date of assignment in string format
        :type Due: str
        :param Name: Name of assignment
        :type Name: str
        :param Desc: Description of assignment
        :type Desc: str
        """

        self.id = ID
        self.due = Due
        self.name = Name
        self.desc = Desc

    @property
    def AssignmentID(self) -> str:
        return self.id

    @property
    def DueDetails(self) -> str:
        return self.due

    @property
    def AssignmentTitle(self) -> str:
        return self.name

    @property
    def AssignmentDetails(self) -> str:
        return self.desc or "No description"


class CalClient():
    """
    Create a calendar class to manage all calendar related stuff away from the downloading stuff
    """

    def __init__(self, TimeZone: str, CalendarName: str, DavUrl: str, DavUser: str, DavPass: str, sslVerify: bool = True) -> None:
        """
        :param TimeZone: Current timezone
        :type TimeZone: str
        :param CalendarName: Name of calendar you want to edit
        :type CalendarName: str
        :param DavUrl: URL for DAV server
        :type DavUrl: str
        :param DavUser: Username for DAV
        :type DavUser: str
        :param DavPass: Password for DAV
        :type DavPass: str
        :param sslVerify: Enable SSL Verify (Default True)
        :type sslVerify: bool
        """

        if not sslVerify:
            # If the person has disabled the SSL, ignore the warnings
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.client = DAVClient(url=DavUrl, username=DavUser, password=DavPass, ssl_verify_cert=sslVerify)

        self.CalendarName = CalendarName
        self.Timezone = TimeZone


        print("Connecting to the CALDAV server")
        self.Principal = self.client.principal()
        self.Calendars = self.Principal.calendars()

        for cal in self.Calendars:
            if str(cal).lower() == str(self.CalendarName).lower():
                print(f"Found calendar {cal}")
                self.Calendar = cal
                break

        if not hasattr(self, 'Calendar'):
            raise ValueError(f"Calendar named '{self.CalendarName}' not found!")

    def UpdateAssignment(self, assignment: Assignment) -> None:
        assignment_uid = f"canvas-assignment-{assignment.AssignmentID}"

        # Remove old duplicated events
        events = self.Calendar.events()
        for event in events:
            raw = event.data
            if assignment_uid in raw:
                event.delete()

        # Create new event for this assignment
        start = datetime.fromisoformat(assignment.DueDetails.replace("Z", "+00:00"))
        end = start + timedelta(hours=1)

        event_data = "\r\n".join([
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//AnthonyBebek//CanvasCalSync//EN",
            "BEGIN:VEVENT",
            f"UID:{assignment_uid}",
            f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART;TZID={self.Timezone}:{start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND;TZID={self.Timezone}:{end.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{assignment.AssignmentTitle}",
            f"DESCRIPTION:{assignment.AssignmentDetails}",
            "END:VEVENT",
            "END:VCALENDAR"
        ])
        self.Calendar.add_event(event_data)