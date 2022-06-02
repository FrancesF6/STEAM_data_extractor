# This script reads a set/list of STEAM user IDs,
# extracts user data (username, profile name) from STEAM's API
# saves user avatars as images
# and saves user data into to a JSON file
# UPDATE: removed userIDs' first 7 digits to form their avatar filenames (because of javaScript limitation), other no change

import argparse
import os
import string
import json
import requests

from game_classes import *


def process_username(profilename: str, profileURL: str) -> str:
    """If user has set profileURL with unique IDs, use this as username;
    if not, make fake username from profile name"""

    if "steamcommunity.com/id/" in profileURL:
        username = profileURL.split("steamcommunity.com/id/")[1].split("/")[0]
    else:
        # set lowercase, remove all special chars
        username = ''.join(c for c in profilename.lower() if c.isalnum())
    
    return username


def extract_user_data(APIKey, maxEmptyLines, timeout, filename, out, begin, count):
    """loops from the set of user IDs and extract data from STEAM's API
    APIKey: the API key used to retrieve data from STEAM's API
    maxEmptyLines: maximum number of empty lines in the input file before stopping reading
    timeout: seconds for HTTP requests
    filename: input file pathname
    out: output base path
    begin: which line (element) to read from within the input file
    count: number of users to extract
    """

    urlTemplate = string.Template(
        'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2?key=$key&steamids=$userid')

    users = []   # list of User JSON objects

    # read userIDs from the file
    try:
        f = open(filename, 'r')
    except:
        print("Cannot open file %s" % filename)
        return

    with f:
        # skip the first begin lines
        for i in range(begin):
            f.readline()

        emptyline = 0
        # start reading game IDs from file
        for i in range(count):
            userID = f.readline()
            if len(userID) == 0:
                emptyline += 1
                if emptyline >= maxEmptyLines: break
                else: continue

            # get json data from STEAM API
            try:
                text = requests.get(urlTemplate.substitute({'key': APIKey, 'userid': userID}), timeout=timeout).text
                data = json.loads(text)
            except:
                print("Errors occur when reading user data of user ID %s, skip..." % userID)
                continue

            try:
                userJSON = data["response"]["players"][0]
                profileName = userJSON["personaname"]
                profileURL = userJSON["profileurl"]
            except:
                continue

            username = process_username(profileName, profileURL)
            users.append(User(userID, username, profileName).toJSON())

            # download user avatars
            try:
                image = requests.get(userJSON["avatarfull"]).content
                avatarFilename = f"uid_{int(str(userID)[7:])}"   # UPDATE - REMOVE first 7 digits
            except:
                continue

            with open(os.path.join(out, "avatars", avatarFilename), mode='wb') as img:
                img.write(image)

    # save list of User objects into a file
    with open(os.path.join(out, "usersData.json"), mode='w', encoding="UTF-8") as f:
        json.dump(users, f)
    
    # print summary
    print("Work done.\nRead %d lines starting at line %d from %s, extracted %d users data." % (count, begin, filename, len(users)))


def main():
    parser = argparse.ArgumentParser(description='Extracts STEAM user profile names and downloads user avatars')
    parser.add_argument(
        '-r', '--maxemptylines', help='Maximum number of empty lines in the input file before stopping reading. Default: 5',
        required=False, type=int, default=5)
    parser.add_argument(
        '-t', '--timeout', help='Timeout in seconds for http connections. Default: 120',
        required=False, type=int, default=120)

    parser.add_argument(
        '-i', '--input', help='Input file pathname. Default: output/userids.txt',
        required=False, default='output/userids.txt')
    parser.add_argument(
        '-o', '--out', help='Output base path', required=False, default='output')
    parser.add_argument(
        '--begin', help='Which line (element) to read from within the input file. Default: 0',
        required=False, type=int, default=0)
    parser.add_argument(
        '-n', '--count', help='number of user IDs to extract. Default: 100',
        required=False, type=int, default=100)
    
    parser.add_argument(
        '-k', '--key', help="the API key used to retrieve data from STEAM's API (required)",
        required=True, type=str)

    args = parser.parse_args()

    # make output folder
    if not os.path.exists(args.out):
        os.makedirs(args.out)

    # make avatars folder
    avatarsPath = os.path.join(args.out, "avatars")
    if not os.path.exists(avatarsPath):
        os.makedirs(avatarsPath)

    extract_user_data(args.key, args.maxemptylines, args.timeout, args.input, args.out, args.begin, args.count)


if __name__ == '__main__':
    main()
