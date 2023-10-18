import math

class Bowling_Statistics:
    total_games = 0
    total_pins = 0
    total_frames = 0
    total_strikes = 0
    total_spares = 0
    total_opens = 0
    total_single_pin_leaves = 0
    total_single_pin_makes = 0
    total_strike_frames = 0
    total_spare_frames = 0
    average_score = 0
    strike_percentage = 0
    spare_percentage = 0
    single_pin_percentage = 0
    open_percentage = 0
    
    def safe_divide_stats(self, num, den):
        output = 0
        if den > 0:
            output = num / den
        return output

    def get_average_score(self):
        return self.safe_divide_stats(self.total_pins, self.total_games)

    def get_strike_percentage(self):
        return 100 * self.safe_divide_stats(self.total_strikes, self.total_strike_frames)
    
    def get_spare_percentage(self):
        return 100 * self.safe_divide_stats(self.total_spares, self.total_spare_frames)
    
    def get_single_pin_percentage(self):
        return 100 * self.safe_divide_stats(self.total_single_pin_makes, self.total_single_pin_leaves)
    
    def get_open_percentage(self):
        return 100 * self.safe_divide_stats(self.total_opens, self.total_frames)
    
    def calculate_percentages(self):
        self.average_score = self.get_average_score()
        self.spare_percentage = self.get_spare_percentage()
        self.strike_percentage = self.get_strike_percentage()
        self.single_pin_percentage = self.get_single_pin_percentage()
        self.open_percentage = self.get_open_percentage() 
        return self

    def update_counts(self, stat):
        self.total_games += stat.total_games
        self.total_opens += stat.total_opens
        self.total_frames += stat.total_frames
        self.total_pins += stat.total_pins
        self.total_single_pin_leaves += stat.total_single_pin_leaves
        self.total_single_pin_makes += stat.total_single_pin_makes
        self.total_spare_frames += stat.total_spare_frames
        self.total_spares += stat.total_spares
        self.total_strike_frames += stat.total_strike_frames
        self.total_strikes += stat.total_strikes
        return self
    
    def add_game_stats(self, game):
        self.total_games = 1
        self.total_pins = game.game_score

        

        # Loop over frame, which is contained in the columns
        for throw in game.game_data.T:

            # Skip missing frames
            if math.isnan(throw[0]):
                continue
            else:
                self.total_frames += 1
                self.total_strike_frames += 1

            # Valid frames
            if throw[0] == 10: # Strike on first ball
                self.total_strikes += 1
            else:
                self.total_spare_frames += 1
            
            if throw[0] == 9: # 9 pins on first ball
                self.total_single_pin_leaves += 1
                if throw[1] == 1: # 9/ (9 for first ball, 1 for second ball)
                    self.total_single_pin_makes += 1
                    self.total_spares += 1
            elif (throw[0] < 9) and (throw[0] + throw[1] == 10): # Any other spare
                self.total_spares += 1
            elif throw[0] < 9: # Open 
                self.total_opens += 1

        # Special case for 10th frame stats
    
        # Strike on first ball only
        if throw[0] == 10 and throw[1] < 10:
            self.total_spare_frames += 1
            self.total_strike_frames += 1

            if throw[1] + throw[2] == 10:
                self.total_spares += 1

        # Strike on first and second ball
        if throw[0] == 10 and throw[1] == 10:
            self.total_strikes += 1
            self.total_strike_frames += 1

            # Strike on third ball
            if throw[2] == 10:
                self.total_strikes += 1
                self.total_strike_frames += 1
        # Spare in 10th frame
        if throw[0] < 10 and throw[0] + throw[1] == 10:
            self.total_strike_frames += 1

            # Strike on third ball
            if throw[2] == 10:
                 self.total_strikes += 1
        
        self.calculate_percentages()

        return self


class Bowling_Game:

    def __init__(self, game_data=[], score=0):
        self.game_data = game_data
        self.game_score = score
        self.game_stats = Bowling_Statistics()

    def add_game_stats(self):
        self.game_stats = self.game_stats.add_game_stats(self)
        return self


class Bowling_Series:
    def __init__(self, date):
        self.date = date
        self.games = list()

    def add_game(self, game):
        self.games.append(game)

    def add_series_stats(self):
        self.series_stats = Bowling_Statistics()
        for game in self.games:
            self.series_stats.update_counts(game.game_stats)

        self.series_stats.calculate_percentages()
        

class Season:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.series = list()

    def add_series(self, series):
        self.series.append(series)

    def add_season_stats(self):
        self.season_stats = Bowling_Statistics()
        for series in self.series:
            self.season_stats.update_counts(series.series_stats)
        
        self.season_stats.calculate_percentages()
    

class Bowler:
    def __init__(self, name):
        self.name = name
        self.season = list()
    
    def add_season(self, season):
        self.season.append(season)

    def add_bowler_stats(self):
        self.bowler_stats = Bowling_Statistics()
        for season in self.season:
            self.bowler_stats.update_counts(season.season_stats)
        
        self.bowler_stats.calculate_percentages()
   