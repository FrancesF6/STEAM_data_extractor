# This script reads a set/list of STEAM game IDs,
# extracts game data (title, companies, genres, release date) from HTML page
# saves a list of game data and a set of game company data to JSON files
# any game ID with age gates will be saved to another text file

import argparse
import os
import requests
import json

from bs4 import BeautifulSoup

from game_classes import *

def parse_company_id(URL: str, category: str) -> str:
    """extract STEAM game company ID string from different URL rules
    category: "developer" or  "publisher"
    URL: now support three kinds of URLs:
    1) https://store.steampowered.com/developer/giantssoftware?snr=1_5_9__408
    extract giantssoftware
    2) https://store.steampowered.com/search/?developer=Playground%20Games&snr=1_5_9__408
    extract Playground%20Games
    3) https://store.steampowered.com/curator/33975870?snr=1_5_9__400
    extract curator_33975870
    """
    companyID = ""
    try:
        if (category + "/") in URL:
            companyID = URL.replace(category + "/", " ").replace("?", " ").split()[1]
        elif (category + "=") in URL:
            companyID = URL.replace(category + "=", " ").replace("&", " ").split()[1]
        else:
            companyID = URL.replace(".com/", " ").replace("?", " ").split()[1].replace("/", "_")
    except:
        print("Cannot parse str:" + URL)
        pass

    return companyID


def extract_game_data(maxEmptyLines, timeout, filename, out, begin, count):
    """loops from the set of game IDs and extract data from each game's webpage
    maxEmptyLines: maximum number of empty lines in the input file before stopping reading
    timeout: seconds for HTTP requests
    filename: input file pathname
    out: output base path
    begin: which line (element) to read from within the input file
    count: number of games to extract
    """

    baseURL = "http://store.steampowered.com/app/"

    # initialize collections
    games = []   # list of Game objects
    companies = dict()   # dict of Game Companies
    ageGateGames = []   # list of game IDs with age gates

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
            gameID = f.readline()
            if len(gameID) == 0:
                emptyline += 1
                if emptyline >= maxEmptyLines: break
                else: continue
            
            try:
                pageData = requests.get(baseURL + gameID, timeout=timeout).content
            except:
                print("Request timeout on %s, skip..." % (baseURL + gameID))
                continue
            
            gameSoup = BeautifulSoup(pageData, features="html.parser")

            # check if there's age_gate
            ageGate = gameSoup.find('div', attrs={'id':'app_agegate'})  # would never found? - TODO later
            if ageGate is not None:
                ageGateGames.append(gameID)
                continue

            # no age gate, extract useful data
            newGame = Game(gameID)   # create a Game object
            try:
                dataDiv = gameSoup.find('div', attrs={'id':'genresAndManufacturer'})
                tokens = dataDiv.get_text().split('\n')   # extract game title, date, genres
                companyRows = dataDiv.find_all('div', attrs={"class": "dev_row"})   # extract company infos
            except:
                pass   # new game with a lot of unmeaningful value will be added into collection
            else:
                for s in tokens:
                    if s.startswith("Title:"):
                        newGame.setTitle(s.replace("Title:", "").strip())
                    elif s.startswith("Genre:"):
                        genres = s.replace("Genre:", "").strip().split(",")
                        for genre in genres:
                            newGame.addGenre(genre.strip())
                    elif s.startswith("Release Date:"):
                        newGame.setDate(parse_date(s.replace("Release Date:", "").strip()))
                
                for companyRow in companyRows:
                    try:
                        category = companyRow.find("b").get_text().replace(":", "").lower()   # "developer"
                        htmlTag = companyRow.find("a")   # <a href="https://store.steampowered.com/curator/33975870?snr=1_5_9__408">Eagle Dynamics SA</a>
                        companyName = htmlTag.get_text().strip()   # Eagle Dynamics SA
                        companyURL = htmlTag['href']
                    except:
                        continue

                    if category == "developer":
                        companyID = parse_company_id(companyURL, "developer")
                        if companyID == "": continue
                        newGame.addDevCompany(companyID)
                    elif category == "publisher":
                        companyID = parse_company_id(companyURL, "publisher")
                        if companyID == "": continue
                        newGame.addPubCompany(companyID)
                    
                    # add game company into dict
                    if companyID not in companies:
                        companies[companyID] = companyName

            games.append(newGame.toJSON())

    # save list of games and dict of companies into two files
    with open(os.path.join(out, "gamesData.json"), mode='w', encoding="UTF-8") as f:
        json.dump(games, f)
    
    with open(os.path.join(out, "companiesData.json"), mode='w', encoding="UTF-8") as f:
        json.dump(companies, f)

    # save list of games with age gates
    with open(os.path.join(out, "ageGateGames.txt"), mode='a', encoding="UTF-8") as f:
        for ageGateGame in ageGateGames:
            f.write(str(ageGateGame))

    # print summary
    print("Work done.\nRead %d lines starting at line %d from %s, extracted %d games data and %d company data, saved %d games with age gates." % (count, begin, filename, len(games), len(companies), len(ageGateGames)))


def main():
    parser = argparse.ArgumentParser(description='Extracts STEAM game titles, release dates, companies, and genres')
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
        '-o', '--out', help='Output base path',
        required=False, default='output')
    parser.add_argument(
        '--begin', help='Which line (element) to read from within the input file. Default: 0',
        required=False, type=int, default=0)
    parser.add_argument(
        '-n', '--count', help='number of games to extract. Default: 100',
        required=False, type=int, default=100)
        
    args = parser.parse_args()

    if not os.path.exists(args.out):
        os.makedirs(args.out)

    extract_game_data(args.maxemptylines, args.timeout, args.input, args.out, args.begin, args.count)


if __name__ == '__main__':
    main()
