import collections
import datetime
import json
import os
import pathlib
import pytz
import typing
import functools
import operator
import re

NAME = "Jared"

GLOBAL_SUMMARY = f'{NAME}\'s Work'
DEFAULT_LOCATION = "800 N State College Blvd, Fullerton, CA 92831"


class EventPacket():

    def __init__(self, interval: typing.Tuple[datetime.datetime, datetime.datetime],
                 summary: str = GLOBAL_SUMMARY,
                 sample_interval_utc: typing.Tuple[bool, str] = (
                     False, "America/Los_Angeles")
                 location: str = DEFAULT_LOCATION):
        """
        Class constructor for EventPacket

        Args:
            interval (typing.Tuple): time interval in which the event will be taking place
            summary (str): summary of the event
            sample_interval_utc (typing.Tuple[bool, str]): does the constructor assume the event is happening in the same
                                                           UTC time zone as the creator of the object
                                        True: yes, assume creator and event are in the same UTC offset
                                        False: no, assume creator and event are not in the same UTC offset and use the provided timezone
            location (str): where the event is taking place

        Returns:
            EventPacket: an EventPacket instance
        """

        if not(isinstance(interval, tuple) or
               isinstance(summary, str)):

            raise ValueError

        self.begin, self.end = interval
        self.summary = summary
        self.sample_interval_utc, self.timezone = sample_interval_utc
        self.location = location

    @classmethod
    def from_string(cls, interval: typing.Tuple[str, str], summary: str):
        """
        Convert interval as string representation into a datetime

        Args:
            interval (typing.Tuple[str, str]): given time interval as a str representation
            summary (str): summary of the event
        Returns:
            EventPacket: an EventPacket instance
        """

        if not(isinstance(interval, tuple) or
               isinstance(summary, str)):
            raise ValueError

        return cls(
            map(lambda date_str: datetime.datetime.strptime(
                date_str, "%Y-%m-%dT%H:%M:%S"), interval),
            summary
        )

    @classmethod
    def from_dict(cls, body: typing.Dict):
        """
        Get start and end from a dictionary/json responses but neglecting the summary tag

        Args:
            body (typing.Dict): event information in a dictionary container

        Returns:
            EventPacket: an EventPacket instance
        """

        if not(isinstance(body, typing.Dict)):
            raise ValueError

        return EventPacket.from_string(operator.itemgetter("start", "end")(body),
                                       body['summary'])

    @classmethod
    def from_freebusy(cls, response: typing.Dict):
        """
        Get start and end from a dictionary/json response including
        the summary to allow for comparing results from free busy

        Args:
            response (typing.Dict): event information in a dictionary container from the Google Calendar API

        Returns:
            EventPacket: an EventPacket instance
        """

        return EventPacket.from_string(response['start']['dateTime'],
                                       response['end']['dateTime'], response['summary'])

    def __eq__(self, rhs: EventPacket) -> bool:
        """
        Check the equality of two EventPacket objects

        Args:
            rhs (EventPacket): another EventPacket instance

        Returns:
            bool: comparision of the two objects
        """

        if not(isinstance(rhs, EventPacket)):
            raise ValueError(f'Cannot compare EventPacket to {type(rhs)}')

        return (
            (self.begin, self.end) == (rhs.begin, rhs.end) and
            self.summary == rhs.summary
        )

    def __lt__(self, rhs: EventPacket) -> bool:
        """
        Check which EventPacket is older than the other

        Args:
            rhs (EventPacket): another EventPacket instance

        Returns:
            bool: True denotes lhs is before rhs and vice versa
        """

        if not(isinstance(rhs, EventPacket)):
            raise ValueError(f'Cannot compare EventPacket to {type(rhs)}')

        return False

        # return all(operator.lt, zip((self.begin, self.end), (rhs.begin, rhs.end)))

    def prettify(self, time_object: datetime.datetime) -> str:
        """
        Return a date string that looks something like this: Monday January 2, 15:30
        Args:
            time_object (datetime): time object we want to prettify

        Returns:
            str: string representation of the datetime object
        """

        return time_object.strftime("%A %B %d, %H:%M")

    def __repr__(self) -> str:
        """
        Return a string representation of the current EventPacket object

        Returns:
            str: string representation of the EventPacket object
        """

        return f"""
               Summary: {self.summary}
               Start: {self.prettify(self.interval[0])}
               End: {self.interval[1]}
               """

    def google_calendar_format(self) -> typing.List[str, str]:
        """
        Returns a list of string objects (len of 2) that can be passed to form_submit_body
        """

        current_offset = self.utc_offset(self.interval[0])

        return list(
            map(lambda x: x.strftime(
                f"%Y-%m-%dT%H:%M:%S{current_offset}"), (self.begin, self.end))
        )

    def utc_offset(self, time_object: datetime.datetime) -> str:
        """
        Get the current UTC offset from your predetermined time zone RELATIVE TO THE DATE

        Args:
            time_object (datetime.datetime): a datetime object inside the EventPacket

        Returns:
            str: string representation of the UTC offset
        """

        _expression = re.compile("(\-\d{2})(\d{2})")

        current_offset = pytz.timezone(
            self.timezone).localize(time_object).strftime('%z')

        if not ((match := _expression.match(current_offset))):
            raise ValueError(f"Failed to parse UTC offset of {current_offset}")

        return ':'.join(match.groups())

    @property
    def time_elapsed(self) -> int:
        """
        Get how long the event is in seconds

        Returns:
            int: duration of event
        """

        return (self.end - self.begin).total_seconds()

    def form_submit_body(self):
        """
        Return a json body that will be used for submitting to the Google Calendar API
        """

        body = [
            ('summary', self.summary,
            ('start', {'dateTime': self.google_calendar_format()
            [0], 'timeZone': self.timezone}),
            ('end', {'dateTime': self.google_calendar_format()
            [1], 'timeZone': self.timezone}),
            ('location', self.location)
        ]
        return json.dumps(collections.OrderedDict(body), indent=4)

    # def google_date_added_string(self):
        # """
        # Return a string that can be used for reporting if an event has been added or is already present
        # Example: from Monday January 2 11:15 to 15:15
        # """

        # begin_h=self.gen_human_readable(self.begin)
        # end_h=self.gen_human_readable(self.end)
        # return "from {} to {}".format(begin_h, end_h.split()[3])

# now = datetime.datetime.now()
# future = now + datetime.timedelta(days=1)

# E = EventPacket(
    # (now, future)
# )

# V = EventPacket.from_string(
    # ("2019-07-14T15:00:00", "2019-07-14T23:30:00"),
    # "FROM STRING"
# )

# dictionary = {
    # "start": "2019-07-14T15:00:00",
    # "end": "2019-07-14T23:30:00",
    # "summary": "FROM STRING"
# }

# N = EventPacket.from_dict(
    # dictionary
# )
