import time
import copy
import random
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
    url = 'https://en.wikipedia.org/wiki/2023%E2%80%9324_' + league
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
                        result = line.split("–")
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
        # Everton were deducted 10 points for the 2023-24 season
        if club == 'Everton':
            current_table.update({club: [0, 0, 0, -10]})
        # Nottingham Forest were deducted 10 points for the 2023-24 season
        elif club == 'Nottingham Forest':
            current_table.update({club: [0, 0, 0, -4]})
        else:
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
country_codes = ['ENG', 'ESP', 'GER', 'ITA', 'FRA', 'POR', 'NED', 'TUR', 'DEN', 'AUT', 'SCO', 'SRB', 'SUI', 'UKR',
                 'BEL']
home_field_advantage_dict = {}
for country_code in country_codes:
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

# Champions League groups initialized
groups = [['Bayern Munich', 'Manchester United', 'Copenhagen', 'Galatasaray'],
          ['Sevilla', 'Arsenal', 'PSV Eindhoven', 'Lens'], ['Napoli', 'Real Madrid', 'Braga', 'Union Berlin'],
          ['Benfica', 'Inter Milan', 'RB Salzburg', 'Real Sociedad'],
          ['Feyenoord', 'Atlético Madrid', 'Lazio', 'Celtic'],
          ['Paris Saint-Germain', 'Borussia Dortmund', 'AC Milan', 'Newcastle United'],
          ['Manchester City', 'RB Leipzig', 'Red Star Belgrade', 'Young Boys'],
          ['Barcelona', 'Porto', 'Shakhtar Donetsk', 'Antwerp']]
# In order to facilitate faster run times, the elo rating and country for each team in the Champions League is stored
# in a dictionary
ucl_elos = {}
ucl_country_codes = {}
# creates dictionaries to help summarize the expected results for the UEFA Champions League
ucl_summary = []
group_summary = {}
for group_number, group in enumerate(groups):
    for team in group:
        ucl_summary.append([team, 0, 0, 0, 0, 0, chr(65 + group_number)])
        group_summary.update({team: [0, 0, 0, 0, 0, 0, chr(65 + group_number)]})
        country = elo_df.loc[team]['Country']
        elo = elo_df.loc[team]["Adjusted_Elo_Rating"]
        ucl_elos.update({team: elo})
        ucl_country_codes.update({team: country})


# A class for functions used for the Group Stage
class group_stage:
    def __init__(self, group):
        self.group = group

    # This function returns a list of all of the Group State matches already completed
    def matches_completed(self):
        matches_completed = [['AC Milan', 'Newcastle United', 0, 0], ['Galatasaray', 'Copenhagen', 2, 2],
                             ['Bayern Munich', 'Manchester United', 4, 3], ['Sevilla', 'Lens', 1, 1],
                             ['Arsenal', 'PSV Eindhoven', 4, 0], ['Real Madrid', 'Union Berlin', 1, 1],
                             ['Braga', 'Napoli', 1, 2], ['Real Sociedad', 'Inter Milan', 1, 1],
                             ['Benfica', 'RB Salzburg', 0, 2], ['Feyenoord', 'Celtic', 2, 0],
                             ['Lazio', 'Atlético Madrid', 1, 1], ['Paris Saint-Germain', 'Borussia Dortmund', 2, 0],
                             ['Young Boys', 'RB Leipzig', 1, 3], ['Manchester City', 'Red Star Belgrade', 3, 1],
                             ['Barcelona', 'Antwerp', 5, 0], ['Shakhtar Donetsk', 'Porto', 1, 3],
                             ['Union Berlin', 'Braga', 2, 3], ['RB Salzburg', 'Real Sociedad', 0, 2],
                             ['Inter Milan', 'Benfica', 2, 0], ['PSV Eindhoven', 'Sevilla', 2, 2],
                             ['Copenhagen', 'Bayern Munich', 1, 2], ['Manchester United', 'Galatasaray', 2, 3],
                             ['Napoli', 'Real Madrid', 2, 3], ['Lens', 'Arsenal', 2, 1],
                             ['Atlético Madrid', 'Feyenoord', 3, 2], ['Antwerp', 'Shakhtar Donetsk', 2, 3],
                             ['Red Star Belgrade', 'Young Boys', 2, 2], ['Borussia Dortmund', 'AC Milan', 0, 0],
                             ['Newcastle United', 'Paris Saint-Germain', 4, 1], ['RB Leipzig', 'Manchester City', 1, 3],
                             ['Porto', 'Barcelona', 0, 1], ['Celtic', 'Lazio', 1, 2],
                             ['Galatasaray', 'Bayern Munich', 1, 3], ['Inter Milan', 'RB Salzburg', 2, 1],
                             ['Union Berlin', 'Napoli', 0, 1], ['Sevilla', 'Arsenal', 1, 2],
                             ['Braga', 'Real Madrid', 1, 2], ['Lens', 'PSV Eindhoven', 1, 1],
                             ['Benfica', 'Real Sociedad', 0, 1], ['Manchester United', 'Copenhagen', 1, 0],
                             ['Barcelona', 'Shakhtar Donetsk', 2, 1], ['Feyenoord', 'Lazio', 3, 1],
                             ['Newcastle United', 'Borussia Dortmund', 0, 1], ['RB Leipzig', 'Red Star Belgrade', 3, 1],
                             ['Young Boys', 'Manchester City', 1, 3], ['Paris Saint-Germain', 'AC Milan', 3, 0],
                             ['Celtic', 'Atlético Madrid', 2, 2], ['Antwerp', 'Porto', 1, 4],
                             ['Borussia Dortmund', 'Newcastle United', 2, 0], ['Shakhtar Donetsk', 'Barcelona', 1, 0],
                             ['Lazio', 'Feyenoord', 1, 0], ['Porto', 'Antwerp', 2, 0],
                             ['Manchester City', 'Young Boys', 3, 0], ['AC Milan', 'Paris Saint-Germain', 2, 1],
                             ['Atlético Madrid', 'Celtic', 6, 0], ['Red Star Belgrade', 'RB Leipzig', 1, 2],
                             ['Real Sociedad', 'Benfica', 3, 1], ['Napoli', 'Union Berlin', 1, 1],
                             ['Copenhagen', 'Manchester United', 4, 3], ['RB Salzburg', 'Inter Milan', 0, 1],
                             ['Bayern Munich', 'Galatasaray', 2, 1], ['Arsenal', 'Sevilla', 2, 0],
                             ['PSV Eindhoven', 'Lens', 1, 0], ['Real Madrid', 'Braga', 3, 0], ['Lazio', 'Celtic', 2, 0],
                             ['Shakhtar Donetsk', 'Antwerp', 1, 0], ['AC Milan', 'Borussia Dortmund', 1, 3],
                             ['Feyenoord', 'Atlético Madrid', 1, 3], ['Paris Saint-Germain', 'Newcastle United', 1, 1],
                             ['Barcelona', 'Porto', 2, 1], ['Young Boys', 'Red Star Belgrade', 2, 0],
                             ['Manchester City', 'RB Leipzig', 3, 2], ['Galatasaray', 'Manchester United', 3, 3],
                             ['Sevilla', 'PSV Eindhoven', 2, 3], ['Bayern Munich', 'Copenhagen', 0, 0],
                             ['Real Madrid', 'Napoli', 4, 2], ['Real Sociedad', 'RB Salzburg', 0, 0],
                             ['Braga', 'Union Berlin', 1, 1], ['Arsenal', 'Lens', 6, 0],
                             ['Benfica', 'Inter Milan', 3, 3], ['Lens', 'Sevilla', 2, 1],
                             ['PSV Eindhoven', 'Arsenal', 1, 1], ['Union Berlin', 'Real Madrid', 2, 3],
                             ['RB Salzburg', 'Benfica', 1, 3], ['Napoli', 'Braga', 2, 0],
                             ['Inter Milan', 'Real Sociedad', 0, 0], ['Copenhagen', 'Galatasaray', 1, 0],
                             ['Manchester United', 'Bayern Munich', 0, 1], ['RB Leipzig', 'Young Boys', 2, 1],
                             ['Red Star Belgrade', 'Manchester City', 2, 3], ['Antwerp', 'Barcelona', 3, 2],
                             ['Porto', 'Shakhtar Donetsk', 5, 3], ['Celtic', 'Feyenoord', 2, 1],
                             ['Borussia Dortmund', 'Paris Saint-Germain', 1, 1], ['Atlético Madrid', 'Lazio', 2, 0],
                             ['Newcastle United', 'AC Milan', 1, 2]]
        # [Home, Away, Home Goals, Away Goals]
        return matches_completed

    # This function returns the various matchups within a particular group
    def group_matches(self):
        matches = []
        for team_1_pos, team_1 in enumerate(self.group):
            for team_2_pos, team_2 in enumerate(self.group):
                if team_1_pos != team_2_pos:
                    matches.append([team_1, team_2])
        return matches

    # This function returns the elo ratings for each team in a Group Stage match
    def match_ratings(self):
        matches = self.group_matches()
        ratings = []
        for match in matches:
            rating = []
            for team_number, team in enumerate(match):
                if team_number == 0:
                    home_country = ucl_country_codes[team]
                    home_team_elo = ucl_elos[team] + home_field_advantage_dict[home_country]
                    rating.append(home_team_elo)
                else:
                    away_elo = ucl_elos[team]
                    rating.append(away_elo)
            ratings.append(rating)
        return ratings

    # This function returns a final simulated group
    def group_simulation(self):
        table = {}
        group_ratings = self.match_ratings()
        matches_completed = self.matches_completed()
        for team in self.group:
            table.update({team: [0, 0, 0, 0]})
        match_results = []
        for match_number, match in enumerate(self.group_matches()):
            simulation_needed = True
            rating = group_ratings[match_number]
            team_1_standings = table[match[0]]
            team_2_standings = table[match[1]]
            for finished_match in matches_completed:
                # This checks to see if the match has already been played
                if match == finished_match[0:2]:
                    simulation_needed = False
                    result = finished_match[2:]
            # This simulates the match if it has not been played yet
            if simulation_needed:
                result = gp.match_result(rating[0], rating[1])
            match_results.append(result)
            # This updates the standings to reflect the match
            if result[0] > result[1]:
                team_1_standings[0] = team_1_standings[0] + 3
            elif result[0] == result[1]:
                team_1_standings[0] = team_1_standings[0] + 1
                team_2_standings[0] = team_2_standings[0] + 1
            else:
                team_2_standings[0] = team_2_standings[0] + 3
            team_1_standings[1] += result[0]
            team_2_standings[1] += result[1]
            team_1_standings[2] += result[1]
            team_2_standings[2] += result[0]
            team_1_standings[3] = team_1_standings[1] - team_1_standings[2]
            team_2_standings[3] = team_2_standings[1] - team_2_standings[2]
            table[match[0]] = team_1_standings
            table[match[1]] = team_2_standings
        standings = []
        for team in table:
            standing = [team]
            standing.extend(table[team])
            standings.append(standing)
        standings = sorted(standings, key=lambda data: (data[1], data[4], data[2]), reverse=True)
        ties = []
        tied_teams = []
        tied_teams_start = False
        for position, club_group_stage_standings in enumerate(standings):
            if position != 0:
                if club_group_stage_standings[1] == standings[position - 1][1]:
                    tied_teams_start = True
                    tied_teams.append([standings[position - 1][0], 0, 0])
                elif tied_teams_start:
                    tied_teams.append([standings[position - 1][0], 0, 0])
                    tied_teams_start = False
                    ties.append(tied_teams)
                    tied_teams = []
        if len(ties) > 0:
            group_order = {}
            for original_order, club in enumerate(self.group):
                group_order.update({club: original_order})
            for club, group_stats in table.items():
                group_stats.insert(0, club)
                group_stats.extend([0, 0])
                standings.append(group_stats)
            for tie in ties:
                for team in tie:
                    for other_team in tie:
                        if team != other_team:
                            team_order = group_order[team[0]]
                            opp_order = group_order[other_team[0]]
                            match = match_results[team_order * 3 + opp_order]
                            if match[0] > match[1]:
                                team[1] += 3
                            elif match[0] < match[1]:
                                other_team[1] += 3
                            else:
                                team[1] += 1
                                other_team[1] += 1
                            team[2] += match[0] - match[1]
                            other_team[2] += match[1] - match[0]
                tie = sorted(tie, key=lambda club_info: (club_info[1], club_info[2]), reverse=True)
                for club in tie:
                    table[club[0]][5] = club[1]
                    table[club[0]][6] = club[2]
            standings = []
            for club, club_season in table.items():
                standings.append(club_season)
            standings = sorted(standings, key=lambda club_info: (club_info[1], club_info[-2], club_info[-1],
                                                                 club_info[4], club_info[2]), reverse=True)

        return standings


# A class for functions used during the knockout stage
class knockout_stage:
    # This sets the matchups for the knockout stage based on the results of the Group Stage
    def __init__(self, group_winners, group_runners_up):
        round_of_16_matchups = [['Porto', 'Arsenal'], ['Napoli', 'Barcelona'], ['Paris Saint-Germain', 'Real Sociedad'],
                                ['Inter Milan', 'Atlético Madrid'], ['PSV Eindhoven', 'Borussia Dortmund'],
                                ['Lazio', 'Bayern Munich'], ['Copenhagen', 'Manchester City'],
                                ['RB Leipzig', 'Real Madrid']]
        if len(round_of_16_matchups) == 0:
            # this indicates the draw has not occurred yet
            # pot 1 consists of the group runners-up and pot 2 consists of the group winners
            pot_1 = []
            pot_2 = []
            for group_number in range(8):
                pot_1.append([group_number, group_runners_up[group_number]])
                pot_2.append([group_number, group_winners[group_number]])
            draw_works = False
            # shuffles the order of the group runners-up
            random.shuffle(pot_1)
            while not draw_works:
                # shuffles the order of the group winners
                random.shuffle(pot_2)
                # after shuffling both pots, we determine matchups
                matchups = []
                for matchup_number, team_1 in enumerate(pot_1):
                    matchups.append([team_1, pot_2[matchup_number]])
                # We check to see if every matchup follows the rules in order to be valid
                for matchup_number, matchup in enumerate(matchups):
                    team_1 = matchup[0][1]
                    team_2 = matchup[1][1]
                    team_1_group = matchup[0][0]
                    team_2_group = matchup[1][0]
                    if team_1_group == team_2_group:
                        # if both teams in a matchup were from the same group, this breaks a rule
                        break
                    elif elo_df.loc[team_1]['Country'] == elo_df.loc[team_2]['Country']:
                        # if both teams in a matchup are from the same country, this breaks a rule
                        break
                    elif matchup_number == 7:
                        # this means that every matchup has passed all tests and we can confirm the order as the result
                        # of the draw
                        for matchup in matchups:
                            round_of_16_matchups.append([team_1, team_2])
                        draw_works = True
        self.round_of_16_matchups = round_of_16_matchups

    # This returns the clubs that advanced to the quarterfinals through simulations or returns the actual
    # quarterfinalists if the matches have been completed
    def round_of_16(self):
        r16_matchups = self.round_of_16_matchups
        quarterfinalists = []
        # if completed it will be in the format of first_leg = [['Inter Milan' , 'Liverpool', 0, 2], []]
        # in the order of the r_16_matchups list
        first_legs_completed = True
        second_legs_completed = True
        first_legs = [['Porto', 'Arsenal', 1, 0], ['Napoli', 'Barcelona', 1, 1],
                      ['Paris Saint-Germain', 'Real Sociedad', 2, 0], ['Inter Milan', 'Atlético Madrid', 1, 0],
                      ['PSV Eindhoven', 'Borussia Dortmund', 1, 1], ['Lazio', 'Bayern Munich', 1, 0],
                      ['Copenhagen', 'Manchester City', 1, 3], ['RB Leipzig', 'Real Madrid', 0, 1]]
        # the home side for the first leg will be first in the second_leg list
        second_legs = [['Porto', 'Arsenal', 0, 1], ['Napoli', 'Barcelona', 1, 3],
                      ['Paris Saint-Germain', 'Real Sociedad', 2, 1], ['Inter Milan', 'Atlético Madrid', 1, 2],
                      ['PSV Eindhoven', 'Borussia Dortmund', 0, 2], ['Lazio', 'Bayern Munich', 0, 3],
                      ['Copenhagen', 'Manchester City', 1, 3], ['RB Leipzig', 'Real Madrid', 1, 1]]
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
        # return quarterfinalists
        return ['Atlético Madrid', 'Borussia Dortmund', 'Paris Saint-Germain', 'Barcelona', 'Arsenal', 'Bayern Munich',
                'Real Madrid', 'Manchester City']

    # This returns the clubs that advanced to the quarterfinals and semifinals through simulations or returns the
    # actual quarterfinalists add semifinalists if the matches have been completed
    def quarterfinals(self):
        quarterfinalists = self.round_of_16()
        semifinalists = []
        # if completed it will be in the format of first_leg = [['Inter Milan' , 'Liverpool', 0, 2], []] in the order
        # of the qf_matchups list
        qf_matchups = [['Atlético Madrid', 'Borussia Dortmund'], ['Paris Saint-Germain', 'Barcelona'],
                       ['Arsenal', 'Bayern Munich'], ['Real Madrid', 'Manchester City']]
        if len(qf_matchups) == 0:
            # this means the quarterfinals draw hasn't occurred yet
            random.shuffle(quarterfinalists)
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
        return quarterfinalists, semifinalists

    # This returns the clubs that advanced to the quarterfinals, semifinals, and final through simulations or returns
    # the actual quarterfinalists, semifinalists, and finalists if the matches have been completed
    def semifinals(self):
        quarterfinalists, semifinalists = self.quarterfinals()
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
        return quarterfinalists, semifinalists, finalists

    # This returns the clubs  that advanced to the quarterfinals, semifinals, final, and champion through simulations or
    # returns the actual quarterfinalists, semifinalists, finalists and champions if the matches have been completed
    def champions_league_final(self):
        quarterfinalists, semifinalists, finalists = self.semifinals()
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
        return quarterfinalists, semifinalists, finalists, champion


start_time = time.time()
for simulation in range(10000):
    group_winners = []
    group_runners_up = []

    # Simulates the Group Stage and stores data for each Group
    for group in groups:
        group_sim = group_stage(group)
        group_sim_results = group_sim.group_simulation()
        for position, team in enumerate(group_sim_results):
            summary_info = group_summary[team[0]]
            summary_info[0] += team[1]
            summary_info[1] += team[4]
            summary_info[position + 2] += 1
            group_summary.update({team[0]: summary_info})
            if position == 0:
                group_winners.append(team[0])
            elif position == 1:
                group_runners_up.append(team[0])
    # Checks to see if games registered when inputted
    # # Set to not run. Should be used occasionally to find errors in inputs
    # if simulation == 0:
    #     completed_matches_dict = {}
    #     for club in group_summary:
    #         completed_matches_dict.update({club: 0})
    #     completed_matches = group_sim.matches_completed()
    #     for match in completed_matches:
    #         home_team = match[0]
    #         away_team = match[1]
    #         completed_matches_dict.update({home_team: completed_matches_dict[home_team] + 1})
    #         completed_matches_dict.update({away_team: completed_matches_dict[away_team] + 1})
    #     for club, matches_played in completed_matches_dict.items():
    #         print(club, matches_played)
    ks_sim = knockout_stage(group_winners, group_runners_up)
    # Simulates Knockout Stage
    quarterfinalists, semifinalists, finalists, champion = ks_sim.champions_league_final()
    # Stores the results of the Knockout Stage
    for team in ucl_summary:
        if team[0] == champion:
            team[1] += 1
            team[2] += 1
            team[3] += 1
            team[4] += 1
            team[5] += 1
        elif team[0] in finalists:
            team[1] += 1
            team[2] += 1
            team[3] += 1
            team[4] += 1
        elif team[0] in semifinalists:
            team[1] += 1
            team[2] += 1
            team[3] += 1
        elif team[0] in quarterfinalists:
            team[1] += 1
            team[2] += 1
        elif team[0] in group_winners or team[0] in group_runners_up:
            team[1] += 1
end_time = time.time()
print("\nUEFA Champions League Simulated 10,000 Times in", round((end_time - start_time) / 60, 2), "minutes")

group_sim_summary = []
for team, data in group_summary.items():
    team_info = [team]
    team_info.extend(data)
    group_sim_summary.append(team_info)
group_sim_summary = sorted(group_sim_summary, key=lambda data: (data[1], data[3], data[4], data[5]), reverse=True)
group_sim_summary = sorted(group_sim_summary, key=lambda data: data[7])
ucl_summary = sorted(ucl_summary, key=lambda data: (data[5], data[4], data[3], data[2], data[1]), reverse=True)

line_format = '{pos:^4}|{team:^25}|{Pts:^15}|{GD:^15}|{KS:^10}|{First:^7}|{Second:^7}|{Third:^7}|{Fourth:^7}|'
group_format = '{group:^106}'

for team_number, team_stats in enumerate(group_sim_summary):
    if team_number % 4 == 0:
        print()
        group = 'Group ' + team_stats[7]
        print(group_format.format(group=group))
        print(line_format.format(pos='Pos', team='Team', Pts='Est. Points', GD='Est. GD', KS='Advance', First='1st',
                                 Second='2nd', Third='3rd', Fourth='4th'))
        print('-' * 106)
    position = team_number % 4 + 1
    team = team_stats[0]
    points = round(team_stats[1] / 10000, 2)
    gd = round(team_stats[2] / 10000, 2)
    advance = str(round((team_stats[3] + team_stats[4]) / 100)) + '%'
    first = str(round(team_stats[3] / 100)) + '%'
    second = str(round(team_stats[4] / 100)) + '%'
    third = str(round(team_stats[5] / 100)) + '%'
    fourth = str(round(team_stats[6] / 100)) + '%'
    print(line_format.format(pos=position, team=team, Pts=points, GD=gd, KS=advance, First=first, Second=second,
                             Third=third,
                             Fourth=fourth))

print()
print()
# line_format = '{Pos:^4}|{team:^25}|{R16:^15}|{QF:^18}|{SF:^12}|{F:^10}|{W:^25}|'
line_format = '{Pos:^4}|{team:^25}|{SF:^12}|{F:^10}|{W:^25}|'
ucl_format = '{title:^81}'
print(ucl_format.format(title='2022-23 UEFA Champions League Forecast'))
print()
print(line_format.format(Pos='Pos', team='Team', QF='Quarterfinals', SF='Semifinals', F='Final',
                         W='Win Champions League'))
print('-' * 81)
for rank, team_stats in enumerate(ucl_summary):
    team = team_stats[0]
    make_r16 = str(round(team_stats[1] / 100)) + '%'
    make_qf = str(round(team_stats[2] / 100)) + '%'
    make_sf = str(round(team_stats[3] / 100)) + '%'
    make_final = str(round(team_stats[4] / 100)) + '%'
    win_ucl = str(round(team_stats[5] / 100)) + '%'
    print(line_format.format(Pos=rank + 1, team=team, QF=make_qf, SF=make_sf, F=make_final, W=win_ucl))

gs_pd = pd.DataFrame(group_sim_summary, columns=['Club', 'Avg_GS', 'Avg_GA', '1st', '2nd', '3rd', '4th', 'Group'])
ks_pd = pd.DataFrame(ucl_summary, columns=['Club', 'Make_R16', 'Make_QF', 'Make_SF', 'Make_Final', 'Win_UCL', 'Group'])


# converts values in data frame to a percentage
def percentage_converter(row):
    if len(row) == 8:
        row['Avg_GS'] /= 10000
        row['Avg_GA'] /= 10000
        row['1st'] /= 10000
        row['2nd'] /= 10000
        row['3rd'] /= 10000
        row['4th'] /= 10000
    else:
        row['Make_R16'] /= 10000
        row['Make_QF'] /= 10000
        row['Make_SF'] /= 10000
        row['Make_Final'] /= 10000
        row['Win_UCL'] /= 10000
    return row


gs_pd = gs_pd.apply(percentage_converter, axis='columns')
ks_pd = ks_pd.apply(percentage_converter, axis='columns')

# changing the order of the columns in the data frame
gs_pd = gs_pd[['Group', 'Club', 'Avg_GS', 'Avg_GA', '1st', '2nd', '3rd', '4th']]
ks_pd = ks_pd.drop(['Group'], axis=1)

gs_pd.to_csv('UCL_Group_Stage_Expected_Results.csv', index=False, header=True)
ks_pd.to_csv('UCL_Knockout_Stage_Expected_Results.csv', index=False, header=True)
