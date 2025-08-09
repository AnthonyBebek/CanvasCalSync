# Canvas scraper
Forked from [john-hix](https://github.com/john-hix/scrape-canvas), which was originally forked from [Koenvh1](https://gist.github.com/Koenvh1/6386f8703766c432eb4dfa19acdb0244)

This script was written to downloads resources from canvas, however i've cleaned up some code and added the ability to add assignment due dates to a given CalDAV server.

## Please double-check the data

Two reasons:

1. This script does not save resources to which you do not have access.
Pending further updates to the code, you need to manually ensure the script
has downloaded all the resources from Canvas!

2. Often professors will embed videos that require authentication to view, etc.
At time of writing, this script does not handle such embeds.
Please make sure you can view all resources without authentication before
considering the export done
.

# Setup

This script can be setup to run locally, however if you are using this to update a CalDAV server, I recommend, you create a cron job or schedule to keep your calendar up to date.

## Running locally

Install the requirements with `pip install -r requirements.txt`, then run the program with `python canvas-scraper.py {Canvas URL} {Canvas Token} {Courses}`

Run `python canvas-scraper.py -h` for more help on the arguments.

You can also create a .env file from the template.env file in this repository to skip passing arguments every time

Due to the fact that it isn't a good idea to pass your username, password and CalDAV url through the command prompt in clear text, you can only use the calendar function if you have .env file present in the system.

## Docker

**I have not updated the docker files! Don't expect it to work with docker**

I have left the previous docker image and instructions in this readme if someone wants to map this over to docker themselves, I didn't check if this works with docker so it might work first try.

>A Docker image is provided for convenience. You can configure it to write to a
data directory of your choice. To make a data directory named `data` and bind
mount it to the Docker container, perform the following commands:

>`mkdir ./data`

>```
>docker run \
>  -u "$(id -u)" \
>  -v "$(pwd)"/data:/usr/src/app/data \
>  johnhix/scrape-canvas:0.0.3 \
>  https://institution.canvas-address.edu \
>  canvas-api-key \
>  ./data \
>  all

>```
>The last option, `all`, can be replaced with a comma-separated list
>of course ids.
