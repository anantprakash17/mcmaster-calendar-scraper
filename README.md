# Enrollment Calendar Generator
This project exists to help you import all your classes and work into your calander without having to go through it all manually.
My main reason for creating this was because the Outlook tool was not working and I did not want to add everything by hand. 
Another thing added later was the ability to pull tasks from Avenue, which means all the things that you need to get done will be in your calendar. 

## Installation and Requirements
For this to work, you need the following python packages installed. I am working on making a setup.py file, but for now you can install packages
using [pip](https://pip.pypa.io/en/stable/) like this: 
```bash
python3 -m pip install <package name>
# you can also use this. 
pip3 install <package name>
```
| Package       |
| ------------  |
| icalendar     |
| datetime      |
| json          |
| xmltodict     |
| selenium      |
| selenium-wire |
| urllib        |

You will also need a copy of chromedriver which can be found [here](https://chromedriver.chromium.org/downloads).

## Usage

From your terminal, run the following commands.
```bash
#If you want to import your courses from MyTimetable, use this.
python3 get_enrollment.py <Your MacID> <Your Password>

#If you want to get your assignments and quizzes, use this. 
python3 worktodo/get_todo.py <Your MacID> <Your Password>
```
Once you run this, you will find either a .ics file in the current directory (if you needed courses) or a .txt and .ics file in worktodo (if you needed coursework).

You can use this .ics file with any popular calendar app. Double click to use your computer's default one.

To add to Google Calendar, you can follow this support [link](https://support.google.com/calendar/thread/3231927/how-do-i-import-ics-files-into-google-calendar?hl=en).

## Contribution

I am in Computer Science and I have accounted for most assignment and quiz categories for the courses I have taken. However, there are some things that I probably missed
because I did not account for all programs due to lack of access to these course requests.

If you want to add a specific assignment type or if your courses do not import properly, please create an issue.

## License
Selenium is a great tool that made this project possible. Their licensing and attributions can be found [here](https://www.selenium.dev/documentation/about/copyright/#license)

[Apache](https://choosealicense.com/licenses/apache-2.0/)
