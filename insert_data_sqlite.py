# This script reads STEAM json data from files
# and inserts into a SQLite database
# tables: games, game_genres, companies, develop_publish, users, likes, reviews
# UPDATE: all userIDs have to remove the first 7 digits because of javaScript limitation!

import argparse
import sqlite3
import json
from argon2 import PasswordHasher

from game_classes import *

supportedTables = ["games", "game_genres", "companies", "develop_publish", "users", "likes", "reviews"]

tableInsertionSQLStrs = [
"""CREATE TABLE IF NOT EXISTS games(
    id integer PRIMARY KEY NOT NULL,
    title text NOT NULL,
    date integer NOT NULL) --timestamp from 1901-01-01 00:00:00.000""",

"""CREATE TABLE IF NOT EXISTS game_genres(
    game_id integer NOT NULL,
    genre text NOT NULL,  --lowercase
    PRIMARY KEY (game_id, genre),
    FOREIGN KEY(game_id) REFERENCES games(id))""",

"""CREATE TABLE IF NOT EXISTS companies(
    cid text PRIMARY KEY NOT NULL, --company ID lowercase
    name text NOT NULL)""",

"""CREATE TABLE IF NOT EXISTS develop_publish(
    company_id text NOT NULL,
    game_id integer NOT NULL,
    dev_or_pub text DEFAULT "UNKNOWN", --dev(develop) or pub(publish) or both
    PRIMARY KEY (company_id, game_id),
    FOREIGN KEY(company_id) REFERENCES companies(cid)
    FOREIGN KEY(game_id) REFERENCES games(id))""",

"""CREATE TABLE IF NOT EXISTS users(
    uid integer PRIMARY KEY NOT NULL,
    username text NOT NULL UNIQUE,
    profile_name text NOT NULL,
    privacy integer DEFAULT 0, --profile is not private by default
    password text NOT NULL)""",

"""CREATE TABLE IF NOT EXISTS likes(
    user_id integer NOT NULL,
    game_id integer NOT NULL,
    PRIMARY KEY (user_id, game_id),
    FOREIGN KEY(user_id) REFERENCES users(uid),
    FOREIGN KEY(game_id) REFERENCES games(id))""",

"""CREATE TABLE IF NOT EXISTS reviews(
    user_id integer NOT NULL,
    game_id integer NOT NULL,
    review_id integer NOT NULL,
    timestamp integer NOT NULL, --timestamp from 1901-01-01 00:00:00.000
    UNIQUE (user_id, game_id), --a user can have only one review on a game
    PRIMARY KEY (game_id, review_id),
    FOREIGN KEY(user_id) REFERENCES users(uid),
    FOREIGN KEY(game_id) REFERENCES games(id))"""
]


def insert_data(DBPathname, table, filename):
    """
    table: the table to insert, should be one of ["games", "game_genres", "companies", "develop_publish", "users", "likes", "reviews"]
    DBPathname: the database's pathname
    filename: input JSON file pathname
    """

    if table not in supportedTables:
        print("Table %s not supported. Supported tables: %s" % (table, supportedTables))
        return

    con = sqlite3.connect(DBPathname)
    cur = con.cursor()

    # create table
    index = supportedTables.index(table)
    cur.execute(tableInsertionSQLStrs[index])

    # read json from the file
    try:
        with open(filename, 'r', encoding="UTF-8") as f:
            data = json.load(f)
    except:
        print("Cannot open file %s" % filename)
        return

    # parse json data based on different table rules
    if index == 0:   # games table
        for gameJSON in data:
            try:
                gameID = int(gameJSON["gameID"])
                title = str(gameJSON["title"])
                date = int(gameJSON["date"])
            except: continue
            if gameID == 0 or title == "" or date == 0: continue

            try:
                cur.execute("INSERT INTO games (id, title, date) VALUES (?, ?, ?)", (gameID, title, date))
            except sqlite3.Error as e:
                print("Error:", " ".join(e.args))

    elif index == 1:   # game_genres table
        for gameJSON in data:
            try:
                gameID = int(gameJSON["gameID"])
                genres = set(gameJSON["genres"])
            except: continue
            if gameID == 0 or len(genres) == 0: continue

            for genre in genres:
                try:
                    cur.execute("INSERT INTO game_genres (game_id, genre) VALUES (?, ?)", (gameID, genre))
                except sqlite3.Error as e:
                    print("Error:", " ".join(e.args))

    elif index == 2:   # companies table
        try:
            for cid, name in data.items():
                cid = str(cid).lower()
                try:
                    cur.execute("INSERT INTO companies (cid, name) VALUES (?, ?)", (cid, name))
                except sqlite3.Error as e:
                    print("Error:", " ".join(e.args))
        except: pass

    elif index == 3:   # develop_publish table
        for gameJSON in data:
            try:
                gameID = int(gameJSON["gameID"])
                devCompanyIDs = set(gameJSON["devCompanyIDs"])
                pubCompanyIDs = set(gameJSON["pubCompanyIDs"])
            except: continue
            if gameID == 0: continue

            # dev company first
            for devCompanyID in devCompanyIDs:
                try:
                    cur.execute("INSERT INTO develop_publish (company_id, game_id, dev_or_pub) VALUES (?, ?, ?)", (devCompanyID, gameID, "dev"))
                except sqlite3.Error as e:
                    print("Error:", " ".join(e.args))
            # pub company next
            for pubCompanyID in pubCompanyIDs:
                # search for dev company first
                results = cur.execute("SELECT * FROM develop_publish WHERE company_id = ? AND game_id = ?", (pubCompanyID, gameID)).fetchall()
                if len(results) == 0:
                    try:
                        cur.execute("INSERT INTO develop_publish (company_id, game_id, dev_or_pub) VALUES (?, ?, ?)", (pubCompanyID, gameID, "pub"))
                    except sqlite3.Error as e:
                        print("Error:", " ".join(e.args))
                else:   # already dev company, so change to "both"
                        cur.execute("UPDATE develop_publish SET dev_or_pub = ? WHERE company_id = ? AND game_id = ?", ("both", pubCompanyID, gameID))
    
    elif index == 4:   # users table
        for userJSON in data:
            try:
                userID = int(str(userJSON["userID"])[7:])   # UPDATE - REMOVE first 7 digits
                username = str(userJSON["username"])
                profileName = str(userJSON["profileName"])
            except: continue
            if userID == 0 or username == "" or profileName == "": continue

            # hash password
            hasher = PasswordHasher()
            hashedPassword = hasher.hash(username)
            try:
                cur.execute("INSERT INTO users (uid, username, profile_name, password) VALUES (?, ?, ?, ?)", (userID, username, profileName, hashedPassword))
            except sqlite3.Error as e:
                print("Error:", " ".join(e.args))

    elif index == 5:   # likes table
        for likeJSON in data:
            try:
                userID = int(str(likeJSON["userID"])[7:])   # UPDATE - REMOVE first 7 digits
                gameID = int(likeJSON["gameID"])
            except: continue
            if userID == 0 or gameID == 0: continue

            try:
                cur.execute("INSERT INTO likes (user_id, game_id) VALUES (?, ?)", (userID, gameID))
            except sqlite3.Error as e:
                print("Error:", " ".join(e.args))
    
    elif index == 6:   # reviews table
        for reviewJSON in data:
            try:
                userID = int(str(reviewJSON["userID"])[7:])   # UPDATE - REMOVE first 7 digits
                gameID = int(reviewJSON["gameID"])
                reviewID = int(reviewJSON["reviewID"])
                timestamp = int(reviewJSON["time"])
            except: continue
            if userID == 0 or gameID == 0 or reviewID == 0 or timestamp == 0: continue

            try:
                cur.execute("INSERT INTO reviews (user_id, game_id, review_id, timestamp) VALUES (?, ?, ?, ?)", (userID, gameID, reviewID, timestamp))
            except sqlite3.Error as e:
                print("Error:", " ".join(e.args))

    con.commit()
    con.close()


def main():
    parser = argparse.ArgumentParser(description='Inserts STEAM json data from files into SQLite database')

    parser.add_argument(
        '-i', '--input', help='Input file pathname. For example: "output/gamesData.json"',
        required=True)
    parser.add_argument(
        '-o', '--dbout', help='Output SQLite database pathname',
        required=True)
    parser.add_argument(
        '-t', '--table', help='the table to insert, should be one of {games, game_genres, companies, develop_publish, users, likes, reviews}',
        required=True)

    args = parser.parse_args()

    insert_data(args.dbout, args.table, args.input)


if __name__ == '__main__':
    main()
