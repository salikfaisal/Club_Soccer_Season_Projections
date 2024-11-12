import time
import copy
import random

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
import Getting_Elo_Ratings
import Goal_Probabilities as gp
import club_name_changes

# imports elo data frame
elo_df = Getting_Elo_Ratings.grand_elo_df

# this will be used to assist in getting information about a specific league
country_code_to_league = {'ENG': 'Premier_League', 'GER': 'Bundesliga', 'ITA': 'Serie_A', 'ESP': 'La_Liga',
                          'FRA': 'Ligue_1', 'NED': 'Eredivisie', 'POR': 'Primeira_Liga'}


# This function returns a Data Frame of league results so far in the season for the country_code in the parameters
def get_league_results_so_far(country_code):
    # gets specific league information to help with later parts of the function
    league = country_code_to_league[country_code]
    clubs_in_league = 20
    if country_code in ['GER', 'NED', 'POR', 'FRA']:
        clubs_in_league = 18
    # extracts data from the League's Wikitable
    url = 'https://en.wikipedia.org/wiki/2024%E2%80%9325_' + league
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    search = soup.find(class_='wikitable plainrowheaders').text.split('\n')[(clubs_in_league * 2 + 5):]
    # grabs the results and fixture list in the season
    all_club_results = []
    club_names = []
    for line_num, line in enumerate(search):
        if line_num % (clubs_in_league * 2 + 3) % 2 == 0:
            # this determines if the line represents a club's name
            if line_num % (clubs_in_league * 2 + 3) == 0:
                club_names.append(line)
                club_results = []
            # this represents the end of reading a club's results
            elif line_num % (clubs_in_league * 2 + 3) == (clubs_in_league * 2 + 2):
                all_club_results.append(club_results)
            else:
                if len(line) > 2:
                    # this means the match has yet to be played
                    if any(c.isalpha() for c in line):
                        result = "TBD"
                    else:
                        # gets the result of the match
                        if "–" in line:
                            result = line.split("–")
                        elif "−" in line:
                            result = line.split("−")
                        result = [int(result[0]), int(result[1])]
                # this means the match has yet to be played
                else:
                    result = "TBD"
                club_results.append(result)
    # appends club results for the last club
    all_club_results.append(club_results)
    # changes the name of clubs if needed
    for club_num, club in enumerate(club_names):
        if club in club_name_changes.wiki_name_changes:
            club_names[club_num] = club_name_changes.wiki_name_changes[club]
    # creates a Data Frame where the intersection between a column and row represents a fixture
    results_df = pd.DataFrame(columns=club_names, index=club_names, data=all_club_results)
    # creates a list of matches yet to be played in the season in the form of [home team, away team]
    future_matches = []
    # creates a dictionary to store season standings based on completed matches
    # Dictionary in the form of {Club: [GF, GA, GD, Points]}
    # Goal Difference isn't needed until the end of the season, so we will keep it as 0 in this function
    current_table = {}
    for club in club_names:
        current_table.update({club: [0, 0, 0, 0]})
    # These variables assist in locating "column" numbers
    gf_col = 0
    ga_col = 1
    gd_col = 2
    pts_col = 3
    # determines the league table based on completed matches
    for home_team in club_names:
        for away_team in club_names:
            if home_team == away_team:
                continue
            result = results_df.loc[home_team, away_team]
            # appends the match to a list of future matches if it hasn't been played yet
            if result == 'TBD':
                future_matches.append([home_team, away_team])
            else:
                # edits the current table based on match results
                current_table[home_team][gf_col] += result[0]
                current_table[away_team][gf_col] += result[1]
                current_table[home_team][ga_col] += result[1]
                current_table[away_team][ga_col] += result[0]
                current_table[home_team][gd_col] += result[0] - result[1]
                current_table[away_team][gd_col] += result[1] - result[0]
                if result[0] > result[1]:
                    current_table[home_team][pts_col] += 3
                elif result[0] < result[1]:
                    current_table[away_team][pts_col] += 3
                else:
                    current_table[home_team][pts_col] += 1
                    current_table[away_team][pts_col] += 1

    return results_df, current_table, future_matches


start_time = time.time()
# this dictionary retrieves the home field advantage that will be added to each elo rating for a home side in a given
# country
country_codes = ['GER', 'FRA', 'ESP', 'POR', 'GER', 'ENG', 'ITA', 'CZE', 'SCO', 'BEL', 'NED', 'UKR', 'CRO', 'AUT', 'SRB',
                 'SUI', 'SLK']
home_field_advantage_dict = {}
for country_code in country_codes:
    if country_code == 'SLK':
        home_field_advantage = np.average(list(home_field_advantage_dict.values()))
        home_field_advantage_dict.update({country_code: float(home_field_advantage)})
        continue
    url = 'http://clubelo.com/' + country_code
    page = requests.get(url)

    soup = BeautifulSoup(page.content, 'html.parser')
    search = soup.find(class_='astblatt').text
    decimal_found = False
    home_field_advantage = ''
    for char_num, char in enumerate(search):
        if char == '.' or char.isdigit():
            if char == '.':
                home_field_advantage += char + search[char_num + 1]
                break
            home_field_advantage += char
    home_field_advantage_dict.update({country_code: float(home_field_advantage)})
end_time = time.time()
print("Determined UEFA Home Field Advantages in", round((end_time - start_time) / 60, 2), "minutes")


# this function helps sort the league table dictionary
def sort_table_dict(item):
    # These variables assist in locating "column" numbers
    gf_col = 0
    gd_col = 2
    pts_col = 3
    club, stats = item
    return (stats[pts_col], stats[gd_col], stats[gf_col])


# this returns the league table if the tiebreakers are determined from head to head results
def head_to_head_tiebreaker(league_table, results):
    # These variables assist in locating "column" numbers
    gf_col = 0
    ga_col = 1
    gd_col = 2
    pts_col = 3
    # determines preliminary rankings with each internal list containing the number of tied teams at a specific point
    # for example: [[Manchester City], [Liverpool, Arsenal]....] if Liverpool and Arsenal have the same number of points
    prelim_rankings = []
    teams_at_a_point = []
    for club, season_stats in league_table.items():
        # this should initialize the lists with the maximum points total
        if len(teams_at_a_point) == 0:
            unique_point_val = season_stats[pts_col]
        # finds teams that have the same number of points
        if season_stats[pts_col] == unique_point_val:
            teams_at_a_point.append(club)
        # looks for a new list of tied teams
        else:
            prelim_rankings.append(teams_at_a_point)
            teams_at_a_point = [club]
            unique_point_val = season_stats[pts_col]
    # appends the last group of teams at a point to the list
    prelim_rankings.append(teams_at_a_point)
    # this list will determine the final rankings for the league
    final_rankings = []
    for teams in prelim_rankings:
        if len(teams) == 1:
            final_rankings.append(teams[0])
        # re-ranks clubs based on head-to-head results
        else:
            # creates a new mini table to determine the standings of head to head matches
            tied_teams_table = {}
            for club in teams:
                # {Club: [GF, GA, GD, Points]}
                tied_teams_table.update({club: [0, 0, 0, 0]})
            for home_team in teams:
                for away_team in teams:
                    if home_team == away_team:
                        continue
                    # finds the result between the 2 teams
                    result = results.loc[home_team, away_team]
                    # updates the mini table based on the match results
                    tied_teams_table[home_team][gf_col] += result[0]
                    tied_teams_table[away_team][gf_col] += result[1]
                    tied_teams_table[home_team][ga_col] += result[1]
                    tied_teams_table[away_team][ga_col] += result[0]
                    tied_teams_table[home_team][gd_col] += result[0] - result[1]
                    tied_teams_table[away_team][gd_col] += result[1] - result[0]
                    if result[0] > result[1]:
                        tied_teams_table[home_team][pts_col] += 3
                    elif result[0] < result[1]:
                        tied_teams_table[away_team][pts_col] += 3
                    else:
                        tied_teams_table[home_team][pts_col] += 1
                        tied_teams_table[away_team][pts_col] += 1
            # sorts the teams tied on points based on the mini-table standings
            final_tied_teams_table = dict(sorted(tied_teams_table.items(), key=sort_table_dict, reverse=True))
            final_rankings.extend(list(final_tied_teams_table.keys()))
    # returns the final table in the correct order based on head-to-head tiebreakers
    final_table = {}
    for club in final_rankings:
        final_table.update({club: league_table[club]})

    return final_table


def league_simulations(country_code):
    start_time = time.time()
    # this simulates the league 10,000 times
    # gets results of the season so far
    results_so_far, current_table, future_matches = get_league_results_so_far(country_code)
    # gets a dictionary of all elo ratings for the league
    elo_dict = elo_df[elo_df["Country"] == country_code]["Adjusted_Elo_Rating"].to_dict()
    # These variables assist in locating "column" numbers
    gf_col = 0
    ga_col = 1
    gd_col = 2
    pts_col = 3
    # gets list of clubs in the league
    club_names = results_so_far.index.to_list()
    # This gets the rank needed for a team to qualify for the UEFA Champions League
    rank_needed_for_ucl = 4
    # This assumes that England and Spain finish top 2 in the UEFA Club Coefficients for the 2023-2024 Season
    # will update an additional spot later in the season
    # if country_code in ['ENG', 'ESP']:
    #     rank_needed_for_ucl = 5
    if country_code == 'NED':
        rank_needed_for_ucl = 3
    elif country_code == 'POR':
        rank_needed_for_ucl = 2
    # gets the number of teams in the league
    number_of_teams = 20
    # gets a list of potential positions at the end of the season. This will become the index at the end of iterating
    # through simulations
    if country_code in ['GER', 'FRA', 'NED', 'POR']:
        number_of_teams = 18
    # gets the home field advantage for the league
    home_field_advantage = home_field_advantage_dict[country_code]
    # creates a summary dictionary to store data for the simulations
    summary_dict = {}
    # dictionary is in the form of {club: [Tot_Pos, Tot_Pts, Tot_GD, Win_Leagues, Make_UCLs, 'Rels']}
    for club in club_names:
        summary_dict.update({club: [0, 0, 0, 0, 0, 0]})
    tot_pos_col = 0
    tot_pts_col = 1
    tot_gd_col = 2
    tot_win_leagues = 3
    tot_make_ucls = 4
    tot_rels = 5
    for sim in range(10000):
        # imports the current table based on current results to start
        table_dict = copy.deepcopy(current_table)
        # {Club: [GF, GA, GD, Points]}
        # gets the results of one simulation. Only needed for leagues with head to heads
        if country_code in ['ITA', 'ESP', 'POR']:
            results = results_so_far.copy()
        # Iterates over Fixtures and Updates the Table
        for match in future_matches:
            home_club = match[0]
            away_club = match[1]
            # determines the elo ratings for both teams with home field advantage and simulates the match
            home_elo = elo_dict[home_club] + home_field_advantage
            away_elo = elo_dict[away_club]
            result = gp.match_result(home_elo, away_elo)
            # updates the results data frame for leagues where tiebreakers are determined by head-to-head results
            if country_code in ['ITA', 'ESP', 'POR']:
                results.loc[home_club, away_club] = result
            # updates the table based on the match result
            table_dict[home_club][gf_col] += result[0]
            table_dict[away_club][gf_col] += result[1]
            table_dict[home_club][ga_col] += result[1]
            table_dict[away_club][ga_col] += result[0]
            table_dict[home_club][gd_col] += (result[0] - result[1])
            table_dict[away_club][gd_col] += (result[1] - result[0])
            if result[0] > result[1]:
                table_dict[home_club][pts_col] += 3
            elif result[0] < result[1]:
                table_dict[away_club][pts_col] += 3
            else:
                table_dict[home_club][pts_col] += 1
                table_dict[away_club][pts_col] += 1
        league_table = dict(sorted(table_dict.items(), key=sort_table_dict, reverse=True))
        # determines the final table in the correct order for leagues
        if country_code in ['ITA', 'ESP', 'POR']:
            league_table = head_to_head_tiebreaker(league_table, results)
        # iterates the position a club finished in the season
        position = 1
        for team, season_stats in league_table.items():
            # updates the summary table based on the simulation results
            summary_dict[team][tot_pos_col] += position
            summary_dict[team][tot_pts_col] += season_stats[pts_col]
            summary_dict[team][tot_gd_col] += season_stats[gd_col]
            # updates if a club won the league
            if position == 1:
                summary_dict[team][tot_win_leagues] += 1
                summary_dict[team][tot_make_ucls] += 1
            # updates if a club qualified for the Champions League
            elif position <= rank_needed_for_ucl:
                summary_dict[team][tot_make_ucls] += 1
            # Updates if a club got relegated or is in the relegation playoffs
            elif position >= (number_of_teams - 2):
                summary_dict[team][tot_rels] += 1
            position += 1
        # prints out time estimates for when the league simulations will finish
        if (sim + 1) % 1000 == 0:
            print(country_code, "Simulations", (sim + 1) / 100, "% complete")
            current_time = time.time()
            expected_total_time = (current_time - start_time) / ((sim + 1) / 10000)
            time_left_minutes = round((expected_total_time - (current_time - start_time)) / 60, 2)
            print(time_left_minutes, "Minutes left")
    # creates a data frame based on the summary_dict
    summary_table = pd.DataFrame(index=club_names, columns=['Avg_Pos', 'Avg_Points', 'Avg_GD', 'Win_League', 'Make_UCL',
                                                            'Relegation_or_Playoffs'], data=list(summary_dict.values()))
    # gets the Average for each column where simulation data was added
    summary_table['Avg_Pos'] /= 10000
    summary_table['Avg_Points'] /= 10000
    summary_table['Avg_GD'] /= 10000
    summary_table['Win_League'] /= 10000
    summary_table['Make_UCL'] /= 10000
    summary_table['Relegation_or_Playoffs'] /= 10000
    summary_table.insert(0, "Club", club_names)
    # sorts the summary table by average position
    summary_table.sort_values(by='Avg_Pos', inplace=True)
    # creates a new index for how the Clubs will be viewed in Data Frames
    summary_table['Position'] = list(range(1, number_of_teams + 1))
    summary_table.set_index("Position", inplace=True)

    return summary_table


leagues = {'ENG': 'Premier League (England)', 'ESP': 'La Liga (Spain)', 'ITA': 'Serie A (Italy)',
           'GER': 'Bundesliga (Germany)', 'FRA': 'Ligue 1 (France)', 'NED': 'Eredivisie (Netherlands)',
           'POR': 'Primeira Liga (Portugal)'}
league_csv_name = {'ENG': 'Premier_League_Expected_Results.csv', 'ESP': 'La_Liga_Expected_Results.csv',
                   'ITA': 'Serie_A_Expected_Results.csv', 'GER': 'Bundesliga_Expected_Results.csv',
                   'FRA': 'Ligue_1_Expected_Results.csv', 'NED': 'Eredivisie_Expected_Results.csv',
                   'POR': 'Primeira_Liga_Expected_Results.csv'}
line_format = '{pos:^4}|{club:^25}|{Avg_Pos:^10}|{GD:^10}|{Pts:^10}|{UCL:^10}|{W:^12}|'
league_name_format = '{league:^88}'
for code, league in leagues.items():
    start_time = time.time()
    league_df = league_simulations(code)
    csv_name = league_csv_name[code]
    # exports league data to csv file
    league_df.to_csv(csv_name, index=True, header=True)
    end_time = time.time()
    print("Simulated", league, "10,000 times in", round((end_time - start_time) / 60, 2), "minutes")
    print(league_name_format.format(league=league))
    print(line_format.format(pos='Pos', club='Team', Avg_Pos='Avg. Pos', GD='Avg. GD', Pts='Avg. Pts', UCL='Make UCL',
                             W='Win League'))
    print('-' * 88)
    for position, data in league_df.iterrows():
        average_pos = str(round(data['Avg_Pos'], 1))
        average_gd = str(round(data['Avg_GD']))
        average_pts = str(round(data['Avg_Points']))
        make_ucl = str(round(data['Make_UCL'] * 100)) + '%'
        win_league = str(round(data['Win_League'] * 100)) + '%'
        print(line_format.format(pos=position, club=data['Club'], Avg_Pos=average_pos, GD=average_gd, Pts=average_pts,
                                 UCL=make_ucl,
                                 W=win_league))


url = 'https://en.wikipedia.org/wiki/2024%E2%80%9325_UEFA_Champions_League_league_phase'
page = requests.get(url)

# Parse the page content
soup = BeautifulSoup(page.content, 'html.parser')

# Lists to store data
home_teams = []
away_teams = []
scores = []

# Find all the relevant tables with class 'wikitable sports-series'
tables = soup.find_all('table', class_='wikitable sports-series')

# Loop through each table and extract the rows
for table in tables:
    rows = table.find_all('tr')

    for row in rows[1:]:  # Skip the header row
        columns = row.find_all('td')  # Get all table cells (td)
        if len(columns) >= 3:  # Ensure the row has enough columns
            # Extract and clean up text for home team, score, and away team
            home_team = columns[0].text.strip()
            score = columns[1].text.strip()
            away_team = columns[2].text.strip()

            if home_team == 'Milan':
                home_team = 'AC Milan'
            elif home_team == 'Red Bull Salzburg':
                home_team = 'RB Salzburg'
            if away_team == 'Milan':
                away_team = 'AC Milan'
            elif away_team == 'Red Bull Salzburg':
                away_team = 'RB Salzburg'

            # Append to respective lists
            home_teams.append(home_team)
            scores.append(score)
            away_teams.append(away_team)

# UEFA Champions League
# creates dictionary of all UCL Teams
current_table = {}
# in the form of {team: [points, GD, GF, Away Goals Scored, Wins, Away Wins, Opponents' Points, Opponents' GD', Opponents' GF]}
for team in home_teams:
    if team not in current_table:
        current_table.update({team: [0, 0, 0, 0, 0, 0, 0, 0, 0]})

future_fixtures = []
for match_num in range(144):
    if "–" in scores[match_num]:
        result = scores[match_num].split("–")
        result = [int(result[0]), int(result[1])]
        home_team = home_teams[match_num]
        away_team = away_teams[match_num]
        if result[0] > result[1]:
            current_table[home_team][0] += 3
            current_table[home_team][4] += 1
            current_table[away_team][6] += 3
        elif result[0] < result[1]:
            current_table[home_team][6] += 3
            current_table[away_team][0] += 3
            current_table[away_team][4] += 1
            current_table[home_team][5] += 1
        else:
            current_table[home_team][0] += 1
            current_table[away_team][0] += 1
            current_table[home_team][6] += 1
            current_table[away_team][6] += 1
        current_table[home_team][1] += result[0] - result[1]
        current_table[away_team][1] += result[1] - result[0]
        current_table[home_team][2] += result[0]
        current_table[away_team][2] += result[1]
        current_table[away_team][3] += result[1]
        current_table[home_team][7] += result[1] - result[0]
        current_table[away_team][7] += result[0] - result[1]
        current_table[home_team][8] += result[1]
        current_table[home_team][8] += result[0]

    else:
        future_fixtures.append([home_teams[match_num], away_teams[match_num]])

# In order to facilitate faster run times, the elo rating and country for each team in the Champions League is stored
# in a dictionary
ucl_elos = {}
ucl_country_codes = {}
# creates dictionaries to help summarize the expected results for the UEFA Champions League
ucl_summary = {}
# ucl_summary = {club: [Average League Position, Average Points, Average GD, Top 8, Playoffs, R16, QF, SF, F, C]}
for team in current_table:
    ucl_summary.update({team: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]})
    country = elo_df.loc[team]['Country']
    elo = elo_df.loc[team]["Adjusted_Elo_Rating"]
    ucl_elos.update({team: elo})
    ucl_country_codes.update({team: country})


# A class for functions used for the Group Stage


# A class for functions used during the knockout stage
class knockout_stage:
    # This sets the matchups for the knockout stage based on the results of the Group Stage
    def __init__(self, seeded_r16, playoffs):
        self.seeded_r16 = seeded_r16
        playoff_matchups = []
        # if the draw is complete for this, remember to arrange playoff_matchups by the specific order detailed
        # below. It will come in handy later
        if len(playoff_matchups) == 0:
            playoff_seeding_matchups = [[[17, 18], [15, 16]], [[23, 24], [9, 10]], [[21, 22], [11, 12]],
                                        [[19, 20], [13, 14]]]
            top_bracket_teams = []
            bottom_bracket_teams = []
            for four_team_possibility in playoff_seeding_matchups:
                for two_team_possibility in four_team_possibility:
                    random.shuffle(two_team_possibility)
                    top_bracket_teams.append(two_team_possibility[0])
                    bottom_bracket_teams.append(two_team_possibility[1])
            matchup = []
            for team_num in range(8):
                team_seed = top_bracket_teams[team_num]
                team = playoffs[team_seed - 9]
                matchup.append(team)
                if team_num % 2 == 1:
                    playoff_matchups.append(matchup)
                    matchup = []

            matchup = []
            for team_num in range(8):
                team_seed = bottom_bracket_teams[team_num]
                team = playoffs[team_seed - 9]
                matchup.append(team)
                if team_num % 2 == 1:
                    playoff_matchups.append(matchup)
                    matchup = []
        self.playoff_matchups = playoff_matchups
    # This returns the advancing teams to the round of 16 from the playoffs
    def playoffs(self):
        playoff_matchups = self.playoff_matchups
        playoff_winners = []
        # if completed it will be in the format of first_leg = [['Inter Milan' , 'Liverpool', 0, 2], []]
        # in the order of the playoff_matchups list
        first_legs_completed = False
        second_legs_completed = False
        first_legs = []
        # the home side for the first leg will be first in the second_leg list
        second_legs = []
        for matchup_number, matchup in enumerate(playoff_matchups):
            team_1 = matchup[0]
            team_2 = matchup[1]
            team_1_home_country = ucl_country_codes[team_1]
            team_2_home_country = ucl_country_codes[team_2]
            if not first_legs_completed:
                team_1_first_leg_elo = ucl_elos[team_1] + home_field_advantage_dict[team_1_home_country]
                team_2_first_leg_elo = ucl_elos[team_2]
                result = gp.match_result(team_1_first_leg_elo, team_2_first_leg_elo)
                first_legs.append(matchup + result)
            if not second_legs_completed:
                team_1_second_leg_elo = ucl_elos[team_1]
                team_2_second_leg_elo = ucl_elos[team_2] + home_field_advantage_dict[team_2_home_country]
                result = gp.match_result(team_1_second_leg_elo, team_2_second_leg_elo)
                second_legs.append(matchup + result)
            team_1_aggregate = first_legs[matchup_number][2] + second_legs[matchup_number][2]
            team_2_aggregate = first_legs[matchup_number][3] + second_legs[matchup_number][3]
            if team_1_aggregate > team_2_aggregate:
                playoff_winners.append(matchup[0])
            elif team_1_aggregate < team_2_aggregate:
                playoff_winners.append(matchup[1])
            else:
                playoff_winners.append(matchup[random.randrange(0, 2)])

        return playoff_winners
    # This returns the clubs that advanced to the quarterfinals through simulations or returns the actual
    # quarterfinalists if the matches have been completed
    def round_of_16(self):
        playoff_winners = self.playoffs()
        seeded_r16 = self.seeded_r16

        r16_matchups = []
        # if the draw hasn't happened yet
        if len(r16_matchups) == 0:
            r16_seeding_matchups = [[1, 2], [7, 8], [5, 6], [3, 4]]
            top_bracket_teams = []
            bottom_bracket_teams = []

            for seeding_matchup in r16_seeding_matchups:
                random.shuffle(seeding_matchup)
                top_bracket_teams.append(seeding_matchup[0])
                bottom_bracket_teams.append(seeding_matchup[1])

            for team_num in range(4):
                team_seed = top_bracket_teams[team_num]
                team = seeded_r16[team_seed - 1]
                matchup = [playoff_winners[team_num], team]
                r16_matchups.append(matchup)

            for team_num in range(4):
                team_seed = bottom_bracket_teams[team_num]
                team = seeded_r16[team_seed - 1]
                matchup = [playoff_winners[team_num + 4], team]
                r16_matchups.append(matchup)

        quarterfinalists = []
        # if completed it will be in the format of first_leg = [['Inter Milan' , 'Liverpool', 0, 2], []]
        # in the order of the r_16_matchups list
        first_legs_completed = False
        second_legs_completed = False
        first_legs = []
        # the home side for the first leg will be first in the second_leg list
        second_legs = []
        for matchup_number, matchup in enumerate(r16_matchups):
            team_1 = matchup[0]
            team_2 = matchup[1]
            team_1_home_country = ucl_country_codes[team_1]
            team_2_home_country = ucl_country_codes[team_2]
            if not first_legs_completed:
                team_1_first_leg_elo = ucl_elos[team_1] + home_field_advantage_dict[team_1_home_country]
                team_2_first_leg_elo = ucl_elos[team_2]
                result = gp.match_result(team_1_first_leg_elo, team_2_first_leg_elo)
                first_legs.append(matchup + result)
            if not second_legs_completed:
                team_1_second_leg_elo = ucl_elos[team_1]
                team_2_second_leg_elo = ucl_elos[team_2] + home_field_advantage_dict[team_2_home_country]
                result = gp.match_result(team_1_second_leg_elo, team_2_second_leg_elo)
                second_legs.append(matchup + result)
            team_1_aggregate = first_legs[matchup_number][2] + second_legs[matchup_number][2]
            team_2_aggregate = first_legs[matchup_number][3] + second_legs[matchup_number][3]
            if team_1_aggregate > team_2_aggregate:
                quarterfinalists.append(matchup[0])
            elif team_1_aggregate < team_2_aggregate:
                quarterfinalists.append(matchup[1])
            else:
                quarterfinalists.append(matchup[random.randrange(0, 2)])
        return playoff_winners, quarterfinalists

    # This returns the clubs that advanced to the quarterfinals and semifinals through simulations or returns the
    # actual quarterfinalists add semifinalists if the matches have been completed
    def quarterfinals(self):
        playoff_winners, quarterfinalists = self.round_of_16()
        semifinalists = []
        # if completed it will be in the format of first_leg = [['Inter Milan' , 'Liverpool', 0, 2], []] in the order
        # of the qf_matchups list
        qf_matchups = []
        if len(qf_matchups) == 0:
            # this means the quarterfinals draw hasn't occurred yet
            matchup = []
            for club in quarterfinalists:
                matchup.append(club)
                if len(matchup) == 2:
                    qf_matchups.append(matchup)
                    matchup = []

        first_legs_completed = False
        second_legs_completed = False
        first_legs = []
        # the home side for the first leg will be first in the second_leg list
        second_legs = []
        for matchup_number, matchup in enumerate(qf_matchups):
            team_1 = matchup[0]
            team_2 = matchup[1]
            team_1_home_country = ucl_country_codes[team_1]
            team_2_home_country = ucl_country_codes[team_2]
            if not first_legs_completed:
                team_1_first_leg_elo = ucl_elos[team_1] + home_field_advantage_dict[team_1_home_country]
                team_2_first_leg_elo = ucl_elos[team_2]
                result = gp.match_result(team_1_first_leg_elo, team_2_first_leg_elo)
                first_legs.append(matchup + result)
            if not second_legs_completed:
                team_1_second_leg_elo = ucl_elos[team_1]
                team_2_second_leg_elo = ucl_elos[team_2] + home_field_advantage_dict[team_2_home_country]
                result = gp.match_result(team_1_second_leg_elo, team_2_second_leg_elo)
                second_legs.append(matchup + result)
            team_1_aggregate = first_legs[matchup_number][2] + second_legs[matchup_number][2]
            team_2_aggregate = first_legs[matchup_number][3] + second_legs[matchup_number][3]
            if team_1_aggregate > team_2_aggregate:
                semifinalists.append(matchup[0])
            elif team_1_aggregate < team_2_aggregate:
                semifinalists.append(matchup[1])
            else:
                semifinalists.append(matchup[random.randrange(0, 2)])
        return playoff_winners, quarterfinalists, semifinalists

    # This returns the clubs that advanced to the quarterfinals, semifinals, and final through simulations or returns
    # the actual quarterfinalists, semifinalists, and finalists if the matches have been completed
    def semifinals(self):
        playoff_winners, quarterfinalists, semifinalists = self.quarterfinals()
        finalists = []
        sf_matchups = []
        matchup = []
        for club in semifinalists:
            matchup.append(club)
            if len(matchup) == 2:
                sf_matchups.append(matchup)
                matchup = []

        first_legs_completed = False
        second_legs_completed = False
        first_legs = []
        # the home side for the first leg will be first in the second_leg list
        second_legs = []
        for matchup_number, matchup in enumerate(sf_matchups):
            team_1 = matchup[0]
            team_2 = matchup[1]
            team_1_home_country = ucl_country_codes[team_1]
            team_2_home_country = ucl_country_codes[team_2]
            if not first_legs_completed:
                team_1_first_leg_elo = ucl_elos[team_1] + home_field_advantage_dict[team_1_home_country]
                team_2_first_leg_elo = ucl_elos[team_2]
                result = gp.match_result(team_1_first_leg_elo, team_2_first_leg_elo)
                first_legs.append(matchup + result)
            if not second_legs_completed:
                team_1_second_leg_elo = ucl_elos[team_1]
                team_2_second_leg_elo = ucl_elos[team_2] + home_field_advantage_dict[team_2_home_country]
                result = gp.match_result(team_1_second_leg_elo, team_2_second_leg_elo)
                second_legs.append(matchup + result)
            team_1_aggregate = first_legs[matchup_number][2] + second_legs[matchup_number][2]
            team_2_aggregate = first_legs[matchup_number][3] + second_legs[matchup_number][3]
            if team_1_aggregate > team_2_aggregate:
                finalists.append(matchup[0])
            elif team_1_aggregate < team_2_aggregate:
                finalists.append(matchup[1])
            else:
                finalists.append(matchup[random.randrange(0, 2)])
        return playoff_winners, quarterfinalists, semifinalists, finalists

    # This returns the clubs  that advanced to the quarterfinals, semifinals, final, and champion through simulations or
    # returns the actual quarterfinalists, semifinalists, finalists and champions if the matches have been completed
    def champions_league_final(self):
        playoff_winners, quarterfinalists, semifinalists, finalists = self.semifinals()
        team_1 = finalists[0]
        team_2 = finalists[1]
        team_1_elo = ucl_elos[team_1]
        team_2_elo = ucl_elos[team_2]
        result = gp.match_result(team_1_elo, team_2_elo)
        if result[0] > result[1]:
            champion = finalists[0]
        elif result[0] < result[1]:
            champion = finalists[1]
        else:
            champion = finalists[random.randrange(0, 2)]
        return playoff_winners, quarterfinalists, semifinalists, finalists, champion


start_time = time.time()
for simulation in range(10000):
    simulation_table = copy.deepcopy(current_table)
    seeded_r16 = []
    playoffs = []

    for fixture in future_fixtures:
        home_team = fixture[0]
        away_team = fixture[1]
        home_country = ucl_country_codes[home_team]
        home_elo = ucl_elos[home_team] + home_field_advantage_dict[home_country]
        away_elo = ucl_elos[away_team]
        result = gp.match_result(home_elo, away_elo)
        if result[0] > result[1]:
            simulation_table[home_team][0] += 3
            simulation_table[home_team][4] += 1
            simulation_table[away_team][6] += 3
        elif result[0] < result[1]:
            simulation_table[home_team][6] += 3
            simulation_table[away_team][0] += 3
            simulation_table[away_team][4] += 1
            simulation_table[home_team][5] += 1
        else:
            simulation_table[home_team][0] += 1
            simulation_table[away_team][0] += 1
            simulation_table[home_team][6] += 1
            simulation_table[away_team][6] += 1

        simulation_table[home_team][1] += result[0] - result[1]
        simulation_table[away_team][1] += result[1] - result[0]
        simulation_table[home_team][2] += result[0]
        simulation_table[away_team][2] += result[1]
        simulation_table[away_team][3] += result[1]
        simulation_table[home_team][7] += result[1] - result[0]
        simulation_table[away_team][7] += result[0] - result[1]
        simulation_table[home_team][8] += result[1]
        simulation_table[home_team][8] += result[0]

    # sorts the table
    sorted_table = dict(sorted(simulation_table.items(), key=lambda x: x[1], reverse=True))
    rank = 1
    # ucl_summary = {club: [Average League Position, Average Points, Average GD, Top 8, Playoffs, R16, QF, SF, F, C]}

    for team, team_stats in sorted_table.items():
        ucl_summary[team][0] += rank
        ucl_summary[team][1] += team_stats[0]
        ucl_summary[team][2] += team_stats[1]
        if rank < 9:
            seeded_r16.append(team)
            ucl_summary[team][3] += 1
        elif rank < 25:
            playoffs.append(team)
            ucl_summary[team][4] += 1
        rank += 1
    ks_sim = knockout_stage(seeded_r16, playoffs)
    # Simulates Knockout Stage
    playoff_winners, quarterfinalists, semifinalists, finalists, champion = ks_sim.champions_league_final()
    # Stores the results of the Knockout Stage
    for team, values in ucl_summary.items():
        if team == champion:
            values[5] += 1
            values[6] += 1
            values[7] += 1
            values[8] += 1
            values[9] += 1
        elif team in finalists:
            values[5] += 1
            values[6] += 1
            values[7] += 1
            values[8] += 1
        elif team in semifinalists:
            values[5] += 1
            values[6] += 1
            values[7] += 1
        elif team in quarterfinalists:
            values[5] += 1
            values[6] += 1
        elif team in playoff_winners:
            values[5] += 1

end_time = time.time()
print("\nUEFA Champions League Simulated 10,000 Times in", round((end_time - start_time) / 60, 2), "minutes")

ucl_summary_sorted = sorted(ucl_summary.items(), key=lambda data: (data[1][9], data[1][1]), reverse=True)
ucl_summary = dict(ucl_summary_sorted)


print()

line_format = '{Pos:^4}|{team:^21}|{Avg_Pos:^10}|{Avg_Pts:^10}|{Avg_GD:^9}|{T8:^8}|' \
              '{PO:^10}|{R16:^13}|{QF:^6}|{SF:^6}|{F:^8}|{W:^13}|'
ucl_format = '{title:^129}'
print(ucl_format.format(title='2024-2025 UEFA Champions League Forecast'))
print()
print(line_format.format(Pos='Pos', team='Team', Avg_Pos='Avg. Pos', Avg_Pts='Avg. Pts', Avg_GD='Avg. GD', T8='Top 8',
                         PO='Playoffs', R16='Round of 16', QF='QF', SF='SF', F='Final',
                         W='Win UCL'))
rank = 0
print('-' * 129)
for team, team_stats in ucl_summary.items():
    rank += 1
    avg_pos = str(round(team_stats[0] / 10000, 1))
    avg_pts = str(round(team_stats[1] / 10000))
    avg_gd = str(round(team_stats[2] / 10000))
    top_8 = str(round(team_stats[3] / 100)) + '%'
    make_po = str(round(team_stats[4] / 100)) + '%'
    make_r16 = str(round(team_stats[5] / 100)) + '%'
    make_qf = str(round(team_stats[6] / 100)) + '%'
    make_sf = str(round(team_stats[7] / 100)) + '%'
    make_final = str(round(team_stats[8] / 100)) + '%'
    win_ucl = str(round(team_stats[9] / 100)) + '%'
    print(line_format.format(Pos=rank, team=team, Avg_Pos=avg_pos, Avg_Pts=avg_pts, Avg_GD=avg_gd, T8=top_8,
                             PO=make_po, R16=make_r16, QF=make_qf, SF=make_sf, F=make_final, W=win_ucl))


ucl_summary_list = [(club, stats) for club, stats in ucl_summary.items()]

# Create the DataFrame with two columns: 'Club' and 'Stats'
ks_pd = pd.DataFrame(ucl_summary_list, columns=['Club', 'Stats'])

# Optionally, split the 'Stats' list into separate columns
stats_columns = ['Average Pos', 'Average Points', 'Average GD', 'Top 8',
                                           'Make Playoffs', 'Make R16', 'Make QF', 'Make SF', 'Make Final', 'Win UCL']
df_stats = pd.DataFrame(ks_pd['Stats'].to_list(), columns=stats_columns)

# Merge the 'Team' column with the stats columns
ks_pd = pd.concat([ks_pd['Club'], df_stats], axis=1)

# converts values in data frame to a percentage
def percentage_converter(row):
    row['Average Pos'] /= 10000
    row['Average Points'] /= 10000
    row['Average GD'] /= 10000
    row['Top 8'] /= 10000
    row['Make Playoffs'] /= 10000
    row['Make R16'] /= 10000
    row['Make QF'] /= 10000
    row['Make SF'] /= 10000
    row['Make Final'] /= 10000
    row['Win UCL'] /= 10000
    return row

ks_pd = ks_pd.apply(percentage_converter, axis='columns')
print("Part 3: after percentage converter")
print(ks_pd)

ks_pd.to_csv('UCL_Expected_Results.csv', index=False, header=True)
