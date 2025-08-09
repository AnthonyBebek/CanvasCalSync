#!bin/python3
import argparse
import os
import re
from dotenv import load_dotenv
from caldav import DAVClient
from datetime import datetime

from ManageCalendar import CalClient, Assignment
from requests.exceptions import InvalidSchema

from pathvalidate import sanitize_filename
from canvasapi import Canvas
from canvasapi.course import Course
from canvasapi.exceptions import Unauthorized, ResourceDoesNotExist, Forbidden, InvalidAccessToken
from canvasapi.file import File
from canvasapi.module import Module, ModuleItem

CalendarMode = False

Assignments = []

def extract_files(text):
    text_search = re.findall("/files/(\\d+)", text, re.IGNORECASE)
    groups = set(text_search)
    return groups

def get_course_files(course):
    modules = course.get_modules()

    files_downloaded = set() # Track downloaded files for this course to avoid duplicates

    for module in modules:
        module: Module = module
        module_items = module.get_module_items()
        for item in module_items:
            item: ModuleItem = item
            
            try:
                path = f"{output}/" \
                    f"{sanitize_filename(course.name)}/" \
                    f"{sanitize_filename(module.name)}/"
            except Exception as e:
                print(e)
                continue
            if not os.path.exists(path):
                os.makedirs(path)

            item_type = item.type
            print(f"{course.name} - "
                  f"{module.name} - "
                  f"{item.title} ({item_type})")

            if item_type == "File":
                file = canvas.get_file(item.content_id)
                files_downloaded.add(item.content_id)
                file.download(path + sanitize_filename(file.filename))
            elif item_type == "Page":
                page = course.get_page(item.page_url)
                with open(path + sanitize_filename(item.title) + ".html", "w", encoding="utf-8") as f:
                    f.write(page.body or "")
                files = extract_files(page.body or "")
                for file_id in files:
                    if file_id in files_downloaded:
                        continue
                    try:
                        file = course.get_file(file_id)
                        files_downloaded.add(file_id)
                        file.download(path + sanitize_filename(file.filename))
                    except ResourceDoesNotExist:
                        pass
            elif item_type == "ExternalUrl":
                url = item.external_url
                with open(path + sanitize_filename(item.title) + ".url", "w") as f:
                    f.write("[InternetShortcut]\n")
                    f.write("URL=" + url)
            elif item_type == "Assignment":
                assignment = course.get_assignment(item.content_id)
                with open(path + sanitize_filename(item.title) + ".html", "w", encoding="utf-8") as f:
                    f.write(assignment.description or "")
                files = extract_files(assignment.description or "")
                for file_id in files:
                    if file_id in files_downloaded:
                        continue
                    try:
                        file = course.get_file(file_id)
                        files_downloaded.add(file_id)
                        file.download(path + sanitize_filename(file.filename))
                    except ResourceDoesNotExist:
                        pass
                    except Unauthorized:
                        pass
                    except Forbidden:
                        pass

    try:
        files = course.get_files()
        for file in files:
            file: File = file
            if not file.id in files_downloaded:
                print(f"{course.name} - {file.filename}")
                path = f"{output}/{sanitize_filename(course.name)}/" \
                    f"{sanitize_filename(file.filename)}"
                file.download(path)
    except Unauthorized:
        pass
    except Forbidden:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download all content from Canvas")
    parser.add_argument("url", help="URL to the Canvas website, e.g. https://canvas.utwente.nl", nargs="?")
    parser.add_argument("token", help="Token generated in the settings page on Canvas", nargs="?")
    parser.add_argument("output", help="Path to the output folder, e.g. output/", nargs="?")
    parser.add_argument("courses", help="Comma-separated course IDs or 'all'", nargs="?", const="all")
    args = parser.parse_args()

    if args.courses is None:
        args.courses = "all"


    dotenv_path = '.env'
    load_dotenv()

    # If the user uses arguments, use args, try .env otherwise throw error

    if args.url and args.token and args.courses:
        output = args.output.rstrip("/") + "/"
        canvas = Canvas(args.url, args.token)

    elif os.path.exists(dotenv_path) and os.path.isfile(dotenv_path):
        try:
            canvas = Canvas(os.getenv('URL'), os.getenv('TOKEN'))
            output = os.getenv('OUTPUT')
            # Convert DAV_DISABLE_SSL variable to boolean datatype
            disable_ssl = os.getenv('DAV_DISABLE_SSL', 'TRUE').lower() in ('0', 'false', 'no')

            scraping_files = os.getenv('SCRAPE_FILES', 'False').lower() in ('1', 'true', 'yes')
            scraping_assignments = os.getenv('SCRAPE_ASSIGNMENTS', 'False').lower() in ('1', 'true', 'yes')

            try:
                if scraping_assignments:

                    if disable_ssl:
                        print("Warning SSL has been disabled! Use at own risk!")
                    CalendarName = os.getenv('DAV_CALENDAR')
                    # Create a Calendar object where we can easily add entries to 
                    Calendar = CalClient(TimeZone=os.getenv('TIMEZONE'),CalendarName=os.getenv('DAV_CALENDAR'), DavUrl=os.getenv('DAV_URL'), DavUser=os.getenv('DAV_USERNAME'), DavPass=os.getenv('DAV_PASSWORD'), sslVerify=disable_ssl)
                
            except Exception as e:
                if scraping_files:
                    print(f"{e} Not using calendar, will only scrape data")
                else:
                    print(f"{e} Not using calendar, and not scraping data")

        except InvalidSchema:
            print(f"Cannot connect to {os.getenv('URL')}")
        except Exception as e:
            print(e)
    else:
        raise Exception("Either use arguments with -h or create a .env file. Read README for more details")

        
    courses = [] # courses to scrape

    # Select courses to scrape, default to all
    if args.courses != "all":
        courses = []
        ids = args.courses.split(",")
        for id in ids:
            courses.append(canvas.get_course( int(id) ))
    else:
        try:
            courses = canvas.get_courses()
        except InvalidSchema:
            print(f"Cannot connect to {os.getenv('URL')}")

    if scraping_assignments:
        try:
            # Look for future due dates, if due date plot on calendar
            for course in courses:
                    try:
                        print(f"\n=== {course.name} ===")
                        assignments = course.get_assignments()

                        for assignment in assignments:
                            if assignment.due_at:
                                due_date = assignment.due_at  # keep as string for Assignment object
                                assignment_id = str(assignment.id)  # make sure it's string
                                name = assignment.name or "No Title"
                                # Use assignment.html_url or fallback to something else as description/link
                                description = getattr(assignment, 'html_url', None) or "No link available"

                                print(f"{name} — due {due_date}")

                                # Create your Assignment object here with these values
                                new_assignment = Assignment(
                                    ID=assignment_id,
                                    Due=due_date,
                                    Name=name,
                                    Desc=description
                                )
                                
                                # Now call your calendar update function with this object
                                Calendar.UpdateAssignment(new_assignment)

                            else:
                                print(f"{assignment.name} — no due date")
                    except Exception as e:
                        print(f"Failed to get assignment data because {e}")

        except InvalidSchema:
            print(f"Cannot connect to {os.getenv('URL')}")

        except Exception as e:
            print(f"Failed to get assignment data because {e}")



    if scraping_files:
        # Perform scrape
            for course in courses:
                try:
                    course: Course = course
                    get_course_files(course)

                except InvalidSchema:
                    print(f"Cannot connect to {os.getenv('URL')}")

                except Exception as e:
                    print(f"Failed to get course because {e}")
