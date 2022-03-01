from icalendar import Calendar, Event
from icalendar.cal import Alarm
from icalendar.prop import vText
from get import get_courses
import datetime
import json
import xmltodict

start_date = datetime.datetime.strptime("01/08/22", "%m/%d/%y")
start_date_int = 5124

def get_enrollment_keys(data):
    return [x["enr"] for x in data["cnfs"]]

def process_time(time):
    hour = int(time) // 60
    minute = int(time) % 60
    return datetime.timedelta(hours=hour, minutes=minute)

def get_entry(start, end, summary, location, teacher):
    event = Event()
    event.add('summary', summary)
    event.add('dtstart', start)
    event.add('dtend', end)
    event.add('description', 'Proffessor: ' + teacher)
    event['location'] = vText(location)
    alarm = Alarm()
    alarm.add('action', 'DISPLAY')
    alert_time = datetime.timedelta(minutes=-10)
    alarm.add('trigger', alert_time)
    event.add_component(alarm)
    return event

def process_timeblock(timeblock, title, location, teacher):
    entries = []
    start_time = process_time(int(timeblock["@t1"]))
    end_time = process_time(int(timeblock["@t2"]))
    start = int(timeblock["@d1"])
    end = int(timeblock["@d2"])
    day = int(timeblock["@day"])
    total_days = (end - start) // 7
    current_date = start_date + datetime.timedelta(days=day + (start - start_date_int))
    entries.append(get_entry(current_date + start_time, current_date + end_time, title, location, teacher))
    for _ in range(total_days):
        current_date = current_date + datetime.timedelta(days=7)
        entries.append(get_entry(current_date + start_time, current_date + end_time, title, location, teacher))
    return entries

def process_course(course, keys):
    print(course["@key"])
    uselection = course["uselection"]

    if not isinstance(uselection, list):
        uselection = [uselection]
    content = [x for x in uselection if x["@key"] in keys][0]
    titles = {}
    locations = {}
    blocks = content["selection"]["block"]
    if not isinstance(blocks, list):
        blocks = [blocks]
    for block in blocks:
        title = course["@key"] + " " + block["@type"]
        teacher = block["@teacher"]
        for timeid in block["@timeblockids"].split(","):
            titles[timeid] = title
            locations[timeid] = block["@location"]
    events = []
    for timeblock in content["timeblock"]:
        events += process_timeblock(timeblock, titles[timeblock["@id"]], locations[timeblock["@id"]], teacher)
    return events

if __name__ == "__main__":
    get_courses()
    enrollment = json.load(open("enrollment.json"))
    classdata = xmltodict.parse(open("classdata.xml").read())
    
    keys = get_enrollment_keys(enrollment)

    events = []
    courses = classdata["addcourse"]["classdata"]["course"]

    for course in courses:
        events += process_course(course, keys)

    cal = Calendar()
    for event in events:
        cal.add_component(event)

    f = open('enrollment.ics', 'wb')
    f.write(cal.to_ical())
    f.close()
