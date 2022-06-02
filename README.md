# Run the scripts in order

1. extract_game_ids.py
> python .\extract_game_ids.py <options>
This script downloads all STEAM game IDs from search and save the set of game IDs into a text file.

Options:
-n --count       A (rough) max number of game IDs to extract. Default: 1000
-o --out         Output base path. default: ./output
--begin          Page number to start searching. Default: 0
-r --maxretries  Max retries to download data from a webpage. Default: 5
-t --timeout     Timeout in seconds for http connections. Default: 120


2. extract_game_data.py
This script reads a set/list of STEAM game IDs, extracts game data (title, companies, genres, release date) from HTML page, saves a list of game data and a set of game company data to JSON files. Any game ID with age gates will be saved to another text file.
> python .\extract_game_data.py <options>

Options:
-n --count          Number of games to extract. Default: 100
-i --input          Input file pathname. Default: ./output/gameids.txt
-o --out            Output base path. Default: ./output
--begin             Which line (element) to read from within the input file. Default: 0
-r --maxemptylines  Maximum number of empty lines in the input file before stopping reading. Default: 5
-t --timeout        Timeout in seconds for http connections. Default: 120


3. extract_game_reviews.py
This script reads a set/list of STEAM game IDs (without age gates), extracts game reviews index and likes data from STEAM's API and saves to JSON files, saves game reviews content into text files with gameID and reviewID as path, also saves a list of userIDs into a text file.
> python .\extract_game_reviews.py <options>

Options:
-n --count          Number of game IDs to extract. Default: 100
-i --input          Input file pathname. Default: ./output/gameids.txt
-o --out            Output base path. Default: ./output
--begin             Which line (element) to read from within the input file. Default: 0
-r --maxemptylines  Maximum number of empty lines in the input file before stopping reading. Default: 5
-t --timeout        Timeout in seconds for http connections. Default: 120


4. extract_user_data.py
> python .\extract_user_data.py -k=<STEAM_API_KEY> <options>
This script reads a set/list of STEAM user IDs, extracts user data (username, profile name) from STEAM's API, saves user avatars as images, and user data into to a JSON file.
UPDATE: removed userIDs' first 7 digits to form their avatar filenames (because of JavaScript limitation)

Options:
-k --key            *must* The API key used to retrieve data from STEAM's API
-n --count          Number of user IDs to extract. Default: 100
-i --input          Input file pathname. Default: ./output/userids.txt
-o --out            Output base path. Default: ./output
--begin             Which line (element) to read from within the input file. Default: 0
-r --maxemptylines  Maximum number of empty lines in the input file before stopping reading. Default: 5
-t --timeout        Timeout in seconds for http connections. Default: 120


5. insert_data_sqlite.py
> python .\insert_data_sqlite.py <options>
This script reads STEAM json data from files and inserts into a SQLite database
Tables: games, game_genres, companies, develop_publish, users, likes, reviews
UPDATE: all userIDs have to remove the first 7 digits because of javaScript limitation

Options:
-i --input    Input file pathname. For example: ./output/gamesData.json
-o --dbout    Output SQLite database pathname
-t --table    The table to insert, should be one of: games, game_genres, companies, develop_publish, users, likes, reviews
