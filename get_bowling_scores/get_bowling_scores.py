import math
import requests
import pandas as pd
import numpy as np
import bowler_profile as bwl

from bs4 import BeautifulSoup
from datetime import datetime, date


def get_urls(url_file: str) -> list:
    """Get url links from a text file containing links separated by a new line

    Args:
        url_file (string): path and file name containing list of urls

    Returns:
      list: list containing urls
    """
    file = open(url_file, "r")
    data = file.read().split("\n")
    file.close()
    return data


def get_dates(url_list: list) -> list:
    """Open scoresheet url and extract a list of dates. The dates are the date for each
       cooresponding scoresheet. Assumption that dates are in the form "Day mm/dd/yyyy"
       which needs to be evaluated to just "mm/dd/yyy"

    Args:
        url_list (list): List of URL links to scoresheet files

    Returns:
        list: List of dates in datetime.date format
    """
    dates = list()
    for url in url_list:
        if len(url) > 1:
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")
            date = soup.find(class_="scoredate").string
            date = date.string.split(' ')
            if len(date) > 1:
                current_date = datetime.strptime(date[1], '%m/%d/%Y').date()
                dates.append(current_date)
    return dates


def read_scoresheets(url_list: list, bowler_list: list) -> list:
    """Read all of the scoresheet data for all url links for a given bowling outing

    Args:
        url_list (list): url links containing syncpassport scoresheet data in html
        bowler_list (list): list of bowlers to search for in the scoresheet data. Currently only the first bowler is checked.
            A future improvement would be to grab the sheet as long as at least 1 bowler in the bowler_list could be obtained.

    Returns:
        list: scoresheet data as pandas objects
    """
    sheets = list()

    for url in url_list:
        if len(url) > 0:
            sheets.append(pd.read_html(url, match=bowler_list[0]))
    return sheets


def frame_str_to_int(frame_data: str) -> list:
    """Convert string data for a frame into integer values. 
        'X' has a value of 10. 
        '-' has a value of 0.
        '/' has a value of (10 - <previous_throw>)
        '1-9' string data containing a score of 1 through 9

    Args:
        frame_data (str): Frame data containing the value of each throw and the score for that frame

    Returns:
        list: Frame throws plus score data as list of integers
    """
    # Exit if no data
    if len(frame_data) == 0:
        return None
    
    frame_data = frame_data.split(" ")
    frame_int = list()
    for data in frame_data:
        # Skip invalid data
        if data == "":
            continue

        # Valid data of strike, miss, spare, or pin count
        if data == "X":
            frame_int.append(10)
        elif data == "-":
            frame_int.append(0)
        elif data == "/":

            # Spare in 3rd ball of 10th frame
            if len(frame_int) > 1:
                frame_int.append(10 - frame_int[1])

            # Special case of 0/ where the 0 isn't recorded
            elif len(frame_int) == 0:
                frame_int.append(0)
                frame_int.append(10)

            # Spare not in 3rd ball of 10th frame
            else:
                frame_int.append(10 - frame_int[0])
        else:
            frame_int.append(int(data))
    return frame_int


def get_bowling_game(game_data):
    """ Pre-Process a game of bowling for a single bowler into numeric values

    Args:
        game_data (pandas dataFrame table): A single game in a pandas table for a single bowler.
            The table contains the bowlers and all games

    Returns:
       game (numpy matrix): 3 x 10 matrix where the column is each frame and row is each throw.
            Note: The third throw is only possible in the 10th frame
            A value of 10 would be a strike ("X"). If the first and second ball sum is 10,
            without having a strike ("X"), it would be a spare ("/")
    
       score (int): Total score for the given game of bowling

    """
    NUMBER_OF_THROWS = 3
    NUMBER_OF_FRAMES = 10
    game = np.zeros([NUMBER_OF_THROWS, NUMBER_OF_FRAMES])

    frame_score = list()

    # Total score for the game is in the 11th index of the pandas dataFrame
    score = int(game_data.loc[11])

    # Loop through each of the frames numbered 1 to 10
    for frame in range(1, 11):

        frame_data = game_data.loc[frame]
        # Exit if no data
        if isinstance(frame_data, str):
            frame_data = frame_str_to_int(frame_data)
        else:
            return None, None
        
        # Frame score is last element in frame data
        frame_score.append(frame_data[-1])

        frame_idx = frame - 1
        # 10th frame with mark
        if len(frame_data) > 3:
            game[0, frame_idx] = frame_data[0]
            game[1, frame_idx] = frame_data[1]
            game[2, frame_idx] = frame_data[2]
        
        # Non-Strike frame
        elif len(frame_data) > 2:
            game[0, frame_idx] = frame_data[0]
            game[1, frame_idx] = frame_data[1]

        # Strike frame
        elif len(frame_data) > 1:
            game[0, frame_idx] = frame_data[0]

        # Missing throws, total frame score only here
        else: 
            if frame == 1:
                return None, None
            # Data missing
            else:
                game[0, frame_idx] = None

    frame_score.append(score)

    return game, score


def add_games_to_series(series: object, scoresheet: object, current_bowler: str) -> object:
    """Add Bowling Games that can later be applied to a series. Games come from the scoresheet and added for selected bowler

    Args:
        series (object): New Bowling Series object to add bowling games to
        scoresheet (object): Pandas DataFrame with scoresheet data for a single game
        current_bowler (str): Name of bowler as it appears in the scoresheet

    Returns:
        object: Bowling series object
    """
    total_games = math.floor(len(scoresheet) / 2)
    for game_num in range(1, total_games + 1):
        scoresheet_data = scoresheet[2 * game_num - 1] # scoresheet data has data in odd indicies

        # Replace random index location identifer with bowler names and remove the bowler name column
        bowlers = scoresheet_data[0][:]
        scoresheet_data.rename(index=bowlers, inplace=True)
        game_data = scoresheet_data.drop(columns=0, axis=1)

        # Skip if game data not present
        try:
            game = game_data.loc[current_bowler]
        except:
            continue

        new_game = bwl.Bowling_Game()
        new_game.game_data, new_game.game_score = get_bowling_game(game)

        # Skip if game not present
        if new_game.game_score == None or new_game.game_score < 20:
            continue
        if new_game.game_data.any() == None:
            continue
        
        new_game.add_game_stats()

        series.add_game(new_game)

    series.add_series_stats()
    return series


def add_series(scoresheets: list, sheet_dates: list, bowlers: list, season: object) -> list:
    """Create a new bowling series and add games to it

    Args:
        scoresheets (list): List of pandas DataFrames containing scoresheets
        sheet_dates (list): List of date objects
        bowlers (list): List of bowler names in a series
        season (object): Bowling Season object where the series will be added

    Returns:
        list: List of bowler names in a series
    """
    for sheet_idx, date in enumerate(sheet_dates):
        if date > season.start_date and date < season.end_date:
            for bowler in bowlers:
                series = bwl.Bowling_Series(date)
                series = add_games_to_series(series, scoresheets[sheet_idx], bowler)
                bowler.season[0].add_series(series)
    return bowlers


def add_series_to_season(scoresheets: list, sheet_dates: list, bowler: str, season: object) -> object:
    """Add bowling series' to a season

    Args:
        scoresheets (list): List of pandas DataFrames containing scoresheet
        sheet_dates (list): List of date objects
        bowler (str): Name of bowler to add season to
        season (object): Bowling Season object where the series will be added

    Returns:
        object: Bowling Season with multiple series each containing multiple games
    """
    new_season = bwl.Season(season.start_date, season.end_date)
    for sheet_idx, date in enumerate(sheet_dates):
        if date > season.start_date and date < season.end_date:
            series = bwl.Bowling_Series(date)
            series = add_games_to_series(series, scoresheets[sheet_idx], bowler)
            new_season.add_series(series)
    new_season.add_season_stats()    
    
    return new_season


bowler_list = ["Bruce Brewer", "Jeremy Ferack", "Andy Brockman", "Mike Rose", "Lance Howard", "Josh Woodford"]

# 1. Get dates from each input file with urls
url_list = get_urls("bowling_score_links.txt")
dates = get_dates(url_list)

# 2. Read scoresheet data from input file with urls
scoresheets = read_scoresheets(url_list, bowler_list)

# 3. Define the season
start_date = date(2023, 9, 1)
end_date = date(2024, 4, 30)

# 4. Add all game and series info for each bowler
bowlers = list()
for bowler in bowler_list:
    current_season = bwl.Season(start_date, end_date)
    new_season = add_series_to_season(scoresheets, dates, bowler, current_season)
    current_bowler = bwl.Bowler(bowler)
    current_bowler.add_season(new_season)
    bowlers.append(current_bowler)
