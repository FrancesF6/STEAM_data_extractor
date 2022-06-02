# This includes class definitions for class Game and GameCompany
# and helper functions to parse game release_date format

from datetime import datetime, timezone

class Game:
    """genres are all stored in lowercase"""
    def __init__(self, gameID, title="UNKNOWN", release_date=0, genres="", dev="", pub="") -> None:
        self.gameID = int(gameID)
        self.title = str(title)
        self.date = int(release_date)
        self.genres = set(genres)
        self.devCompanyIDs = set(dev)
        self.pubCompanyIDs = set(pub)
    
    def setTitle(self, title: str) -> None:
        self.title = title

    def setDate(self, date: int) -> None:
        self.date = date

    def addGenre(self, genre: str) -> None:
        self.genres.add(genre.lower())

    def addDevCompany(self, companyID: str) -> None:
        self.devCompanyIDs.add(companyID.lower())
    
    def addPubCompany(self, companyID: str) -> None:
        self.pubCompanyIDs.add(companyID.lower())
    
    def __str__(self) -> str:
        """for human reading"""
        return f"[{self.gameID}] {self.title}\nRelease date: {self.date}\nGenres: {list(self.genres)}\nDevCompanies: {list(self.devCompanyIDs)}\nPubCompanies: {list(self.pubCompanyIDs)}\n"
  
    def toJSON(self) -> dict:
        return {"gameID": self.gameID, "title": self.title, "date": self.date, "genres": list(self.genres), "devCompanyIDs": list(self.devCompanyIDs), "pubCompanyIDs": list(self.pubCompanyIDs)}


class GameReview:
    def __init__(self, userID, gameID, reviewID, timeUpdated) -> None:
        self.userID = int(userID)
        self.gameID = int(gameID)
        self.reviewID = int(reviewID)   # not primary key in DB, but another candidate key
        self.time = int(timeUpdated)   # timestamp updated

    def toJSON(self) -> dict:
        return {"gameID": self.gameID, "userID": self.userID, "reviewID": self.reviewID, "time": self.time}


class User:
    def __init__(self, userID, username, profileName) -> None:
        self.userID = int(userID)   # steam userID
        self.username = username_encrypt(str(username))    # used to login (same as password initially)
        self.profileName = str(profileName)   # displayed on page

    def toJSON(self) -> dict:
        return {"userID": self.userID, "username": self.username, "profileName": self.profileName}


class UserLike:
    def __init__(self, userID, gameID) -> None:
        self.userID = int(userID)
        self.gameID = int(gameID)
    
    def toJSON(self) -> dict:
        return {"userID": self.userID, "gameID": self.gameID}


# data manipulations

def username_encrypt(username, offset=5):
    """Simple Caesar Cipher to encrypt username"""
    if offset == 0:
        return username
        
    result = ""
    for c in username:
        if c.isupper():
            result += chr((ord(c)-65+offset)%26+65)
        else:
            result += chr((ord(c)-97+offset)%26+97)
    return result


# convert date format (string) "(d)d Mmm, yyyy" to timestamp (int) (10 digits, unit on seconds) from 1901-01-01 00:00:00
def parse_date(date) -> int:
    tokens = date.split()
    if len(tokens) < 3:
        return 0   # something wrong

    year = tokens[2]
    day = f'{tokens[0]:>02}'
    month = convert_month(tokens[1][0:3])
    try:
        result = int(datetime(int(year), int(month), int(day), tzinfo=timezone.utc).timestamp())
    except: return 0
    return result


# convert month format "Mmm" to digits
def convert_month(month) -> int:
    monthStrs = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    try:
        return int(f'{str(monthStrs.index(month)+1):>02}')
    except:
        return 0

