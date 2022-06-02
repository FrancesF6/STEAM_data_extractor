# This script downloads all STEAM game IDs from search based on filter
# and save the set of game IDs into a text file

import argparse
import os
import requests
from bs4 import BeautifulSoup


def get_game_ids(maxFailures, timeout, out, beginPage, maxResults):
    """downloads all STEAM game IDs from search and save to a file, and returns the set
    maxFailures: maximum number of failures during extracting
    timeout: seconds for http connections
    out: output base path
    beginPage: page number to start searching
    maxResults: A rough maximum number of results (not counted each time the set updates)
    """

    searchURL = 'http://store.steampowered.com/search/results?sort_by=_ASC&ignore_preferences=1&page='

    gameIDs = set()   # initialize set of game ids (int)

    pageNo = beginPage
    failures = 0

    # loop over the pages
    while True:
        # check if reached max results
        if len(gameIDs) >= maxResults: break
        if failures >= maxFailures: break

        try:
            pageData = requests.get(searchURL+str(pageNo), timeout=timeout).content
        except:
            print("Request time out on %s, skip..." % searchURL+str(pageNo))
            failures += 1   # a timeout considered as a failure
            continue

        pageSoup = BeautifulSoup(pageData, features="html.parser")

        if pageSoup is None:
            print('Failed to parse the URL: %s, skipped.' % searchURL+str(pageNo))
            failures += 1
            continue
        

        try:
            gameTags = pageSoup.find('div', attrs={'id':'search_resultsRows'}).find_all('a', recursive=False)
        except:
            print("Failed to extract search results on page %s, skip..." % str(pageNo))
            failures += 1
            continue

        if gameTags is None:
            print("No search results on page %s, skip..." % str(pageNo))
            failures += 1
            continue


        for gameTag in gameTags:
            try:
                gameURL = gameTag['href']
                gameID = gameURL.split("app/")[1].replace("/", " ").split()[0]
            except:
                print("Cannot extract gameID from href: %s, skip..." % gameURL)
                continue
            gameIDs.add(int(gameID))   # add each game ID

        pageNo += 1
    
    # save set of game IDs to file
    with open(os.path.join(out, "gameids.txt"), mode='a') as f:
        for item in gameIDs:
            f.write("%d\n" % item)


def main():
    parser = argparse.ArgumentParser(description='Downloads all STEAM game IDs from search and save into a file')
    parser.add_argument(
        '-r', '--maxretries', help='Max retries to download data from a webpage. Default: 5',
        required=False, type=int, default=5)
    parser.add_argument(
        '-t', '--timeout', help='Timeout in seconds for http connections. Default: 120',
        required=False, type=int, default=120)

    parser.add_argument(
        '-o', '--out', help='Output base path', required=False, default='output')
    parser.add_argument(
        '--begin', help='page number to start searching. Default: 0',
        required=False, type=int, default=0)
    parser.add_argument(
        '-n', '--count', help='A rough number of game IDs. Default: 1000',
        required=False, type=int, default=1000)

    args = parser.parse_args()

    if not os.path.exists(args.out):
        os.makedirs(args.out)
    
    get_game_ids(args.maxretries, args.timeout, args.out, args.begin, args.count)


if __name__ == '__main__':
    main()
