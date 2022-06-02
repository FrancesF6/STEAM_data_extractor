# This script reads a set/list of STEAM game IDs (without age gates)
# extracts game reviews index and likes data from STEAM's API and saves to JSON files
# saves game reviews content into text files with gameID and reviewID as path
# also saves a list of userIDs into a text file

import argparse
import os
import requests
import string
import json

from game_classes import *


def extract_game_reviews(maxEmptyLines, timeout, filename, out, begin, count):
    """loops from the set of game IDs, extract reviews and userIDs from STEAM's API
    maxEmptyLines: maximum number of empty lines in the input file before stopping reading
    timeout: seconds for HTTP requests
    filename: input file pathname
    out: output base path
    begin: which line (element) to read from within the input file
    count: number of games to extract
    """

    urlTemplate = string.Template('https://store.steampowered.com/appreviews/$id?json=1')

    users = set()   # set of userIDs
    reviewIndexes = []   # set of review indexes
    userlikes = []   # list of UserLike objects

    # read gameIDs from the file
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
            gameID = f.readline().strip()
            if len(gameID) == 0:
                emptyline += 1
                if emptyline >= maxEmptyLines: break
                else: continue

            # get json data from STEAM API
            try:
                text = requests.get(urlTemplate.substitute({'id': gameID}), timeout=timeout).text
                data = json.loads(text)
            except:
                print("Errors occur when reading reviews of game %s, skip..." % gameID)
                continue
            
            if data["success"] != 1: continue   # unsuccessful
            reviews = data["reviews"]
            for review in reviews:
                try:
                    reviewID = review["recommendationid"]
                    userID = review["author"]["steamid"]
                    content = review["review"]
                    timestamp = review["timestamp_updated"]
                except:
                    continue

                reviewIndexes.append(GameReview(userID, gameID, reviewID, timestamp).toJSON())   # save review index into list
                users.add(userID)   # save user id into list

                # save review content as plain text into file
                filePath = os.path.join(out, "reviews", gameID)
                if not os.path.exists(filePath):
                    os.makedirs(filePath)
                with open(os.path.join(filePath, reviewID), mode='w', encoding="UTF-8") as rf:
                    rf.write(content)

                # if user likes this game, save as a UserLike dict
                try:
                    if review["voted_up"]:
                        userlikes.append(UserLike(userID, gameID).toJSON())
                except:
                    pass


    users = list(users)   # convert set to list

    # save list of unique userIDs into a text file (later extract user data)
    with open(os.path.join(out, "userids.txt"), mode='a', encoding="UTF-8") as f:
        for userID in users:   # here is str, without "\n"
            f.write(userID+"\n")
    
    # save list of userlikes into a JSON file
    with open(os.path.join(out, "likes.json"), mode='w', encoding="UTF-8") as f:
        json.dump(userlikes, f)

    # save list of review indexes into a JSON file
    with open(os.path.join(out, "reviews.json"), mode='w', encoding="UTF-8") as f:
        json.dump(reviewIndexes, f)

    # print summary
    print("Work done.\nRead %d lines starting at line %d from %s, extracted %d reviews data, %d likes data, saved %d userIDs." % (count, begin, filename, len(reviewIndexes), len(userlikes), len(users)))


def main():
    parser = argparse.ArgumentParser(description='Extracts STEAM game reviews (as well as a list of userIDs)')
    parser.add_argument(
        '-r', '--maxemptylines', help='Maximum number of empty lines in the input file before stopping reading. Default: 5',
        required=False, type=int, default=5)
    parser.add_argument(
        '-t', '--timeout', help='Timeout in seconds for http connections. Default: 120',
        required=False, type=int, default=120)

    parser.add_argument(
        '-i', '--input', help='Input file pathname. Default: output/gameids.txt',
        required=False, default='output/gameids.txt')
    parser.add_argument(
        '-o', '--out', help='Output base path', required=False, default='output')
    parser.add_argument(
        '--begin', help='Which line (element) to read from within the input file. Default: 0',
        required=False, type=int, default=0)
    parser.add_argument(
        '-n', '--count', help='number of game IDs to extract. Default: 100',
        required=False, type=int, default=100)
    
    args = parser.parse_args()

    if not os.path.exists(args.out):
        os.makedirs(args.out)

    extract_game_reviews(args.maxemptylines, args.timeout, args.input, args.out, args.begin, args.count)


if __name__ == '__main__':
    main()
