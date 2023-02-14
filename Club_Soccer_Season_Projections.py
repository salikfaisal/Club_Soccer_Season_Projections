from datetime import date
import random
import statistics
import pandas as pd
from bs4 import BeautifulSoup
import requests

# gets the date in the form of '2023-02-08'
today = date.today()

# grabs the elo ratings of over 600 soccer clubs from across Europe
url = 'http://api.clubelo.com/' + str(today)
elo_data = requests.get(url).text.split(',')


club_ratings = []
club_data = []
clubs = []
for item in elo_data:
    if "\n" in item:
        sub_items = item.split('\n')
        club_data.append(sub_items[0])
        club_ratings.append(club_data)
        club_data = [sub_items[1]]
    else:
        club_data.append(item)

# changes the names of clubs for a common data point
elo_name_changes = {'Brighton': 'Brighton & Hove Albion', 'Leeds': 'Leeds United', 'Leicester': 'Leicester City',
                    'Man City': 'Manchester City', 'Man United': 'Manchester United', 'Newcastle': 'Newcastle United',
                    'Norwich': 'Norwich City',
                    'Tottenham': 'Tottenham Hotspur', 'West Ham': 'West Ham United',
                    'Wolves': 'Wolverhampton Wanderers',
                    'Atlético': 'Atlético Madrid', 'Atletico': 'Atlético Madrid', 'Betis': 'Real Betis',
                    'Sociedad': 'Real Sociedad',
                    'Bilbao': 'Athletic Bilbao', 'Celta': 'Celta Vigo', 'Cadiz': 'Cádiz', 'Alaves': 'Alavés',
                    'Augsburg': 'FC Augsburg', 'Hertha': 'Hertha BSC', 'Bielefeld': 'Arminia Bielefeld',
                    'Bochum': 'VfL Bochum',
                    'Dortmund': 'Borussia Dortmund', 'Frankfurt': 'Eintracht Frankfurt',
                    'Freiburg': 'SC Freiburg', 'Fürth': 'Greuther Fürth', 'Fuerth': 'Greuther Fürth',
                    'Hoffenheim': '1899 Hoffenheim',
                    'Köln': '1. FC Köln', 'Koeln': '1. FC Köln', 'Leverkusen': 'Bayer Leverkusen', 'Mainz': 'Mainz 05',
                    'Gladbach': 'Borussia Mönchengladbach', 'Bayern': 'Bayern Munich', 'Stuttgart': 'VfB Stuttgart',
                    'Wolfsburg': 'VfL Wolfsburg',
                    'Inter': 'Inter Milan', 'Milan': 'AC Milan', 'Verona': 'Hellas Verona',
                    'Saint-Etienne': 'Saint-Étienne', 'Paris SG': 'Paris Saint-Germain', 'Forest': 'Nottingham Forest',
                    'Almeria': 'Almería',
                    'Werder': 'Werder Bremen', 'Schalke': 'Schalke 04', 'Brugge': 'Club Brugge',
                    'Sporting': 'Sporting CP', 'Salzburg': 'RB Salzburg',
                    'Shakhtar': 'Shakhtar Donetsk', 'FC Kobenhavn': 'Copenhagen', 'Viktoria Plzen': 'Viktoria Plzeň'}
wiki_name_changes = {'Milan': 'AC Milan', 'Paris SG': 'Paris Saint-Germain'}

club_elo_dict = {}
for club in club_ratings:
    if club[1] in elo_name_changes:
        club[1] = elo_name_changes[club[1]]
    club_elo_dict.update({club[1]: club})

# this dictionary retrieves the home field advantage that will be added to each elo rating for a home side in a given
# country
country_codes = ['ENG', 'ESP', 'GER', 'ITA', 'FRA', 'POR', 'NED', 'AUT', 'CRO', 'SCO', 'UKR', 'BEL', 'CZE', 'ISR',
                 'DEN']
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


# this function returns a simulation of the results of a game given the elo ratings of the two teams
def match_result(team_1_elo, team_2_elo):
    # uses the elo formula to get the two-outcome win probability
    team_1_wl = 1 / (10 ** ((team_2_elo - team_1_elo) / 400) + 1)
    # gets the average goal difference expected between the two sides
    # if two sides have an equal rating the probabilities are: 35% Team 1 win, 30% draw, 35% Team 2 win
    team_1_margin_mean = statistics.NormalDist(0, 1.3).inv_cdf(team_1_wl)
    # the goal difference as a result of a random simulation
    team_1_margin = round(statistics.NormalDist(team_1_margin_mean, 1.3).inv_cdf(random.random()))
    # the goal probability distribution from 1826 matches in the 2020-21 season in Europe's top 5 leagues
    goal_prob = [0.25985761226725085, 0.3417305585980285, 0.22343921139101863, 0.1119934282584885, 0.0443592552026287,
                 0.014786418400876232, 0.0024644030668127055, 0.0008214676889375684, 0.0002738225629791895,
                 0.0002738225629791895]
    gp_list = []
    if abs(team_1_margin) > 9:
        winning_goal_count = abs(team_1_margin)
        losing_goal_count = 0
    else:
        gp_list = goal_prob[abs(team_1_margin):]
        total = sum(gp_list)
        cum = 0
        for goal_count, goal_probability in enumerate(gp_list):
            gp_list[goal_count] = goal_probability / total
        goal_result = random.random()
        for gc, gp in enumerate(gp_list):
            cum += gp
            if goal_result < cum:
                winning_goal_count = gc + abs(team_1_margin)
                winning_goal_count = gc + abs(team_1_margin)
                losing_goal_count = winning_goal_count - abs(team_1_margin)
                break
    if team_1_margin >= 0:
        home_goals = winning_goal_count
        away_goals = home_goals - team_1_margin
    else:
        away_goals = winning_goal_count
        home_goals = away_goals + team_1_margin
    return [home_goals, away_goals]


# this function returns the final league standings given season information
def final_standings(country_code, fixtures, table, alpha_teams):
    standings = []
    for club, club_season in table.items():
        club_season.extend([0, 0])
        standings.append(club_season)
    alpha_order = {}
    for order, club in enumerate(alpha_teams):
        alpha_order.update({club: order})
    standings = sorted(standings, key=lambda club_info: (club_info[4], club_info[3], club_info[1]), reverse=True)
    if country_code in ['ESP', 'ITA']:
        ties = []
        tied_teams = []
        tied_teams_start = False
        for position, club in enumerate(standings):
            if position != 0:
                if club[4] == standings[position - 1][4]:
                    tied_teams_start = True
                    tied_teams.append([standings[position - 1][0], 0, 0])
                elif tied_teams_start:
                    tied_teams.append([standings[position - 1][0], 0, 0])
                    tied_teams_start = False
                    ties.append(tied_teams)
                    tied_teams = []
        if len(ties) > 0:
            for tie in ties:
                for team in tie:
                    for other_team in tie:
                        if team != other_team:
                            team_order = alpha_order[team[0]]
                            opp_order = alpha_order[other_team[0]]
                            match = fixtures[team_order][opp_order + 1]
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
            standings = sorted(standings, key=lambda club_info: (club_info[4], club_info[-2], club_info[-1],
                                                                 club_info[3], club_info[1]), reverse=True)
    return standings


# this function is the main function
def league_simulations(country_code):
    country_code_to_league = {'ENG': 'Premier_League', 'GER': 'Bundesliga', 'ITA': 'Serie_A', 'ESP': 'La_Liga',
                              'FRA': 'Ligue_1'}
    league_name = country_code_to_league[country_code]
    home_advantage = home_field_advantage_dict[country_code]
    clubs_in_league = 20
    if country_code == 'GER':
        clubs_in_league = 18
    url = 'https://en.wikipedia.org/wiki/2022%E2%80%9323_' + league_name
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    search = soup.find(class_='wikitable plainrowheaders').text.split('\n')[(clubs_in_league * 2 + 5):]
    club_results_dict = {}
    club_results = []
    alphabetized_teams = []
    # grabs the results and fixture list in the season
    for line_num, line in enumerate(search):
        if line_num % (clubs_in_league * 2 + 3) == 0:
            if len(club_results) != 0:
                club_results_dict.update({club: club_results[:-1]})
            if line in wiki_name_changes:
                club = wiki_name_changes[line]
            else:
                club = line
            club_results = []
            alphabetized_teams.append(club)
        elif line_num % (clubs_in_league * 2 + 3) % 2 == 0:
            result = line.split('–')
            if '–' in line:
                if '[' in result[1]:
                    result[1] = result[1][:-3]
                club_results.append([int(result[0]), int(result[1])])
            else:
                club_results.append(result)
    club_results_dict.update({club: club_results[:-1]})

    # this simulates the league 10,000 times
    rank_needed_for_ucl = 4
    if country_code == 'FRA':
        rank_needed_for_ucl = 3
    simulation_sums = {}
    for team in alphabetized_teams:
        simulation_sums.update({team: [0, 0, 0, 0, 0, 0]})
    for simulation in range(10000):
        table = {}
        league_fixtures = []
        for team in alphabetized_teams:
            # Juventus are facing a 15 point deduction in the 2022-23 Season
            if team == 'Juventus':
                table.update({team: [0, 0, 0, -15]})
            else:
                table.update({team: [0, 0, 0, 0]})
        for club, club_results in club_results_dict.items():
            season_stats = table[club]
            fixtures = [club]
            for row_num, match in enumerate(club_results):
                away_team = alphabetized_teams[row_num]
                away_season_stats = table[away_team]
                if away_team != club:
                    # retrieves the result for the match or simulates it if not played yet
                    match_facts = match
                    if len(match) < 2:
                        home_elo = home_advantage + float(club_elo_dict[club][4])
                        away_elo = float(club_elo_dict[away_team][4])
                        match_facts = match_result(home_elo, away_elo)
                    # updates season standings
                    fixtures.append(match_facts)
                    season_stats[0] += match_facts[0]
                    season_stats[1] += match_facts[1]
                    away_season_stats[0] += match_facts[1]
                    away_season_stats[1] += match_facts[0]
                    away_season_stats[2] = away_season_stats[0] - away_season_stats[1]
                    if match_facts[0] > match_facts[1]:
                        season_stats[3] += 3
                    elif match_facts[0] == match_facts[1]:
                        season_stats[3] += 1
                        away_season_stats[3] += 1
                    else:
                        away_season_stats[3] += 3
                    table.update({away_team: away_season_stats})
                else:
                    fixtures.append([])
            league_fixtures.append(fixtures)
            season_stats[2] = season_stats[0] - season_stats[1]
            table.update({club: season_stats})
        standings = []
        for club, club_season in table.items():
            club_season.insert(0, club)
            standings.append(club_season)
        standings = final_standings(country_code, league_fixtures, table, alphabetized_teams)
        # analyzes and adds current simulation for all teams to main dictionary
        for rank, club_season in enumerate(standings):
            summary_stats = simulation_sums[club_season[0]]
            summary_stats[1] += club_season[4]
            summary_stats[0] += club_season[3]
            summary_stats[-1] += rank + 1
            if rank < rank_needed_for_ucl:
                summary_stats[3] += 1
                if rank < 1:
                    summary_stats[4] += 1
            elif rank >= (clubs_in_league - 3):
                summary_stats[2] += 1
            simulation_sums.update({club_season[0]: summary_stats})
        final_season_probabilities = []
        for club, summary_stats in simulation_sums.items():
            season_probabilities = [club]
            for stat in summary_stats:
                season_probabilities.append(stat / 10000)
            final_season_probabilities.append(season_probabilities)
    final_season_probabilities = sorted(final_season_probabilities, key=lambda club_info: (club_info[-2]
                                                                                           , club_info[-3],
                                                                                           club_info[2],
                                                                                           club_info[1]), reverse=True)
    final_season_probabilities = sorted(final_season_probabilities, key=lambda club_info: club_info[-1])
    return final_season_probabilities


leagues = {'ENG': 'Premier League (England)', 'ESP': 'La Liga (Spain)', 'ITA': 'Serie A (Italy)',
           'GER': 'Bundesliga (Germany)',
           'FRA': 'Ligue 1 (France)'}
league_csv_name = {'ENG': 'Premier_League_Expected_Results.csv', 'ESP': 'La_Liga_Expected_Results.csv',
                   'ITA': 'Serie_A_Expected_Results.csv', 'GER': 'Bundesliga_Expected_Results.csv',
                   'FRA': 'Ligue_1_Expected_Results.csv'}
line_format = '{pos:^4}|{club:^25}|{Avg_Pos:^10}|{GD:^10}|{Pts:^10}|{UCL:^10}|{W:^12}'
league_name_format = '{league:^89}'
for code, league in leagues.items():
    league_probabilities = league_simulations(code)
    league_df = pd.DataFrame(league_probabilities,
                             columns=['Team', 'Avg_Pos', 'Avg_GD', 'Avg_Points', 'Relegated', 'Make UCL', 'Win League'])
    if code == 'GER':
        league_df = league_df.rename(columns={'Relegated': 'Bottom_3'})
    league_df['Position'] = list(range(1, len(league_probabilities) + 1))
    league_df = league_df.set_index("Position")
    csv_name = league_csv_name[code]
    # exports league data to csv file
    league_df.to_csv(csv_name, index=True, header=True)
    print(league_name_format.format(league=league))
    print(line_format.format(pos='Pos', club='Team', Avg_Pos='Avg. Pos', GD='Avg. GD', Pts='Avg. Pts', UCL='Make UCL', W='Win League'))
    print('-' * 89)
    for position, data in enumerate(league_probabilities):
        average_pos = str(round(data[6], 1))
        average_gd = str(round(data[1]))
        average_pts = str(round(data[2]))
        make_ucl = str(round(data[4] * 100)) + '%'
        win_league = str(round(data[5] * 100)) + '%'
        print(line_format.format(pos=position + 1, club=data[0], Avg_Pos=average_pos, GD=average_gd, Pts=average_pts, UCL=make_ucl,
                                 W=win_league))

# Champions League groups initialized
groups = [['Ajax', 'Liverpool', 'Napoli', 'Rangers'], ['Porto', 'Atlético Madrid', 'Bayer Leverkusen', 'Club Brugge'],
          ['Bayern Munich', 'Barcelona', 'Inter Milan', 'Viktoria Plzeň'],
          ['Eintracht Frankfurt', 'Tottenham Hotspur', 'Sporting CP', 'Marseille'],
          ['AC Milan', 'Chelsea', 'RB Salzburg', 'Dinamo Zagreb'],
          ['Real Madrid', 'RB Leipzig', 'Shakhtar Donetsk', 'Celtic'],
          ['Manchester City', 'Sevilla', 'Borussia Dortmund', 'Copenhagen'],
          ['Paris Saint-Germain', 'Juventus', 'Benfica', 'Maccabi Haifa']]

ucl_summary = []
group_summary = {}
for group_number, group in enumerate(groups):
    for team in group:
        ucl_summary.append([team, 0, 0, 0, 0, 0, chr(65 + group_number)])
        group_summary.update({team: [0, 0, 0, 0, 0, 0, chr(65 + group_number)]})


# A class for functions used for the Group Stage
class group_stage:
    def __init__(self, group):
        self.group = group

    # This function returns a list of all of the Group State matches already completed
    def matches_completed(self):
        matches_completed = [['Ajax', 'Rangers', 4, 0], ['Napoli', 'Liverpool', 4, 1], ['Liverpool', 'Ajax', 2, 1],
                             ['Rangers', 'Napoli', 0, 3], ['Atlético Madrid', 'Porto', 2, 1],
                             ['Club Brugge', 'Bayer Leverkusen', 1, 0], ['Porto', 'Club Brugge', 0, 4],
                             ['Bayer Leverkusen', 'Atlético Madrid', 2, 0], ['Barcelona', 'Viktoria Plzeň', 5, 1],
                             ['Inter Milan', 'Bayern Munich', 0, 2], ['Viktoria Plzeň', 'Inter Milan', 0, 2],
                             ['Bayern Munich', 'Barcelona', 2, 0], ['Eintracht Frankfurt', 'Sporting CP', 0, 3],
                             ['Tottenham Hotspur', 'Marseille', 2, 0], ['Sporting CP', 'Tottenham Hotspur', 2, 0],
                             ['Marseille', 'Eintracht Frankfurt', 0, 1], ['Dinamo Zagreb', 'Chelsea', 1, 0],
                             ['RB Salzburg', 'AC Milan', 1, 1], ['AC Milan', 'Dinamo Zagreb', 3, 1],
                             ['Chelsea', 'RB Salzburg', 1, 1], ['Celtic', 'Real Madrid', 0, 3],
                             ['RB Leipzig', 'Shakhtar Donetsk', 1, 4], ['Shakhtar Donetsk', 'Celtic', 1, 1],
                             ['Real Madrid', 'RB Leipzig', 2, 0], ['Borussia Dortmund', 'Copenhagen', 3, 0],
                             ['Sevilla', 'Manchester City', 0, 4], ['Manchester City', 'Borussia Dortmund', 2, 1],
                             ['Copenhagen', 'Sevilla', 0, 0], ['Paris Saint-Germain', 'Juventus', 2, 1],
                             ['Benfica', 'Maccabi Haifa', 2, 0], ['Juventus', 'Benfica', 1, 2],
                             ['Maccabi Haifa', 'Paris Saint-Germain', 1, 3], ['Bayern Munich', 'Viktoria Plzeň', 5, 0],
                             ['Marseille', 'Sporting CP', 4, 1], ['Porto', 'Bayer Leverkusen', 2, 0],
                             ['Club Brugge', 'Atlético Madrid', 2, 0], ['Ajax', 'Napoli', 1, 6],
                             ['Eintracht Frankfurt', 'Tottenham Hotspur', 0, 0], ['Inter Milan', 'Barcelona', 1, 0],
                             ['Liverpool', 'Rangers', 2, 0], ['RB Salzburg', 'Dinamo Zagreb', 1, 0],
                             ['RB Leipzig', 'Celtic', 3, 1], ['Chelsea', 'AC Milan', 3, 0],
                             ['Juventus', 'Maccabi Haifa', 3, 1], ['Real Madrid', 'Shakhtar Donetsk', 2, 1],
                             ['Sevilla', 'Borussia Dortmund', 1, 4], ['Benfica', 'Paris Saint-Germain', 1, 1],
                             ['Manchester City', 'Copenhagen', 5, 0], ['Maccabi Haifa', 'Juventus', 2, 0],
                             ['Copenhagen', 'Manchester City', 0, 0], ['Paris Saint-Germain', 'Benfica', 1, 1],
                             ['Dinamo Zagreb', 'RB Salzburg', 1, 1], ['Borussia Dortmund', 'Sevilla', 1, 1],
                             ['AC Milan', 'Chelsea', 0, 2], ['Shakhtar Donetsk', 'Real Madrid', 1, 1],
                             ['Celtic', 'RB Leipzig', 0, 2], ['Napoli', 'Ajax', 4, 2],
                             ['Atlético Madrid', 'Club Brugge', 0, 0], ['Bayer Leverkusen', 'Porto', 0, 3],
                             ['Rangers', 'Liverpool', 1, 7], ['Barcelona', 'Inter Milan', 3, 3],
                             ['Viktoria Plzeň', 'Bayern Munich', 2, 4],
                             ['Tottenham Hotspur', 'Eintracht Frankfurt', 3, 2], ['Sporting CP', 'Marseille', 0, 2],
                             ['RB Salzburg', 'Chelsea', 0, 2], ['Sevilla', 'Copenhagen', 3, 0],
                             ['Paris Saint-Germain', 'Maccabi Haifa', 7, 2],
                             ['Borussia Dortmund', 'Manchester City', 0, 0], ['Dinamo Zagreb', 'AC Milan', 0, 4],
                             ['Benfica', 'Juventus', 4, 3], ['Celtic', 'Shakhtar Donetsk', 1, 1],
                             ['RB Leipzig', 'Real Madrid', 3, 3], ['Inter Milan', 'Viktoria Plzeň', 4, 0],
                             ['Club Brugge', 'Porto', 0, 4], ['Eintracht Frankfurt', 'Marseille', 2, 1],
                             ['Barcelona', 'Bayern Munich', 0, 3], ['Ajax', 'Liverpool', 0, 3],
                             ['Atlético Madrid', 'Bayer Leverkusen', 2, 2], ['Tottenham Hotspur', 'Sporting CP', 1, 1],
                             ['Napoli', 'Rangers', 3, 0], ['Porto', 'Atlético Madrid', 2, 1],
                             ['Bayer Leverkusen', 'Club Brugge', 0, 0], ['Bayern Munich', 'Inter Milan', 2, 0],
                             ['Liverpool', 'Napoli', 2, 0], ['Marseille', 'Tottenham Hotspur', 1, 2],
                             ['Rangers', 'Ajax', 1, 3], ['Viktoria Plzeň', 'Barcelona', 2, 4],
                             ['Sporting CP', 'Eintracht Frankfurt', 1, 2], ['Real Madrid', 'Celtic', 5, 1],
                             ['Shakhtar Donetsk', 'RB Leipzig', 0, 4], ['AC Milan', 'RB Salzburg', 4, 0],
                             ['Maccabi Haifa', 'Benfica', 1, 6], ['Copenhagen', 'Borussia Dortmund', 1, 1],
                             ['Manchester City', 'Sevilla', 3, 1], ['Juventus', 'Paris Saint-Germain', 1, 2],
                             ['Chelsea', 'Dinamo Zagreb', 2, 1]]
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
                    home_team_original_elo = float(club_elo_dict[team][4])
                    home_team_adjusted_elo = home_team_original_elo + home_field_advantage_dict[club_elo_dict[team][2]]
                    rating.append(home_team_adjusted_elo)
                else:
                    rating.append(float(club_elo_dict[team][4]))
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
                result = match_result(rating[0], rating[1])
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
        round_of_16_matchups = [['Paris Saint-Germain', 'Bayern Munich'], ['AC Milan', 'Tottenham Hotspur'],
                                ['Club Brugge', 'Benfica'], ['Borussia Dortmund', 'Chelsea'],
                                ['Liverpool', 'Real Madrid'], ['Eintracht Frankfurt', 'Napoli'],
                                ['RB Leipzig', 'Manchester City'], ['Inter Milan', 'Porto']
                                ]
        if len(round_of_16_matchups) == 0:
            # this indicates the draw has not occurred yet
            pot_1 = []
            pot_2 = []
            for group_number in range(8):
                pot_1.append([group_number, group_runners_up[group_number]])
                pot_2.append([group_number, group_winners[group_number]])
            draw_works = False
            random.shuffle(pot_1)
            while not draw_works:
                random.shuffle(pot_2)
                matchups = []
                for matchup_number, team_1 in enumerate(pot_1):
                    matchups.append([team_1, pot_2[matchup_number]])
                for matchup_number, matchup in enumerate(matchups):
                    if matchup[0][0] == matchup[1][0]:
                        break
                    elif club_elo_dict[matchup[0][1]][2] == club_elo_dict[matchup[1][1]][2]:
                        break
                    else:
                        if matchup_number == 7:
                            for matchup in matchups:
                                round_of_16_matchups.append([matchup[0][1], matchup[1][1]])
                            draw_works = True
        self.round_of_16_matchups = round_of_16_matchups

    # This returns the nations that advanced to the quarterfinals through simulations or returns the actual quarterfinalists
    # if the matches have been completed
    def round_of_16(self):
        r16_matchups = self.round_of_16_matchups
        quarterfinalists = []
        # if completed it will be in the format of fist_leg = [['Inter Milan' , 'Liverpool', 0, 2], []] in the order of the
        # r_16_matchups list
        first_legs_completed = False
        second_legs_completed = False
        first_legs = []
        # the home side for the fist leg will be first in the second_leg list
        second_legs = []
        for matchup_number, matchup in enumerate(r16_matchups):
            if not first_legs_completed:
                team_1_first_leg_elo = float(club_elo_dict[matchup[0]][4]) + home_field_advantage_dict[
                    club_elo_dict[matchup[0]][2]]
                team_2_first_leg_elo = float(club_elo_dict[matchup[1]][4])
                result = match_result(team_1_first_leg_elo, team_2_first_leg_elo)
                first_legs.append(matchup + result)
            if not second_legs_completed:
                team_1_second_leg_elo = float(club_elo_dict[matchup[0]][4])
                team_2_second_leg_elo = float(club_elo_dict[matchup[1]][4]) + home_field_advantage_dict[
                    club_elo_dict[matchup[1]][2]]
                result = match_result(team_1_second_leg_elo, team_2_second_leg_elo)
                second_legs.append(matchup + result)
            team_1_aggregate = first_legs[matchup_number][2] + second_legs[matchup_number][2]
            team_2_aggregate = first_legs[matchup_number][3] + second_legs[matchup_number][3]
            if team_1_aggregate > team_2_aggregate:
                quarterfinalists.append(matchup[0])
            elif team_1_aggregate < team_2_aggregate:
                quarterfinalists.append(matchup[1])
            else:
                quarterfinalists.append(matchup[random.randrange(0, 2)])
        return quarterfinalists

    # This returns the nations that advanced to the quarterfinals and semifinals through simulations or returns the actual
    # quarterfinalists add semifinalists if the matches have been completed
    def quarterfinals(self):
        quarterfinalists = self.round_of_16()
        semifinalists = []
        # if completed it will be in the format of fist_leg = [['Inter Milan' , 'Liverpool', 0, 2], []] in the order of the
        # r_16_matchups list
        qf_matchups = []
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
        # the home side for the fist leg will be first in the second_leg list
        second_legs = []
        for matchup_number, matchup in enumerate(qf_matchups):
            if not first_legs_completed:
                team_1_first_leg_elo = float(club_elo_dict[matchup[0]][4]) + home_field_advantage_dict[
                    club_elo_dict[matchup[0]][2]]
                team_2_first_leg_elo = float(club_elo_dict[matchup[1]][4])
                result = match_result(team_1_first_leg_elo, team_2_first_leg_elo)
                first_legs.append(matchup + result)
            if not second_legs_completed:
                team_1_second_leg_elo = float(club_elo_dict[matchup[0]][4])
                team_2_second_leg_elo = float(club_elo_dict[matchup[1]][4]) + home_field_advantage_dict[
                    club_elo_dict[matchup[1]][2]]
                result = match_result(team_1_second_leg_elo, team_2_second_leg_elo)
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

    # This returns the nations that advanced to the quarterfinals, semifinals, and final through simulations or returns the actual
    # quarterfinalists, semifinalists, and finalists if the matches have been completed
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
        # the home side for the fist leg will be first in the second_leg list
        second_legs = []
        for matchup_number, matchup in enumerate(sf_matchups):
            if not first_legs_completed:
                team_1_first_leg_elo = float(club_elo_dict[matchup[0]][4]) + home_field_advantage_dict[
                    club_elo_dict[matchup[0]][2]]
                team_2_first_leg_elo = float(club_elo_dict[matchup[1]][4])
                result = match_result(team_1_first_leg_elo, team_2_first_leg_elo)
                first_legs.append(matchup + result)
            if not second_legs_completed:
                team_1_second_leg_elo = float(club_elo_dict[matchup[0]][4])
                team_2_second_leg_elo = float(club_elo_dict[matchup[1]][4]) + home_field_advantage_dict[
                    club_elo_dict[matchup[1]][2]]
                result = match_result(team_1_second_leg_elo, team_2_second_leg_elo)
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

    # This returns the nations that advanced to the quarterfinals, semifinals, final, and champion through simulations or returns
    # the actual quarterfinalists, semifinalists, finalists and champions if the matches have been completed
    def champions_league_final(self):
        quarterfinalists, semifinalists, finalists = self.semifinals()
        team_1_elo = float(club_elo_dict[finalists[0]][4])
        team_2_elo = float(club_elo_dict[finalists[1]][4])
        result = match_result(team_1_elo, team_2_elo)
        if result[0] > result[1]:
            champion = finalists[0]
        elif result[0] < result[1]:
            champion = finalists[1]
        else:
            champion = finalists[random.randrange(0, 2)]
        return quarterfinalists, semifinalists, finalists, champion


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
    # Set to not run. Should be used occasionally to find errors in inputs
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

group_sim_summary = []
for team, data in group_summary.items():
    team_info = [team]
    team_info.extend(data)
    group_sim_summary.append(team_info)
group_sim_summary = sorted(group_sim_summary, key=lambda data: (data[1], data[3], data[4], data[5]), reverse=True)
group_sim_summary = sorted(group_sim_summary, key=lambda data: data[7])
ucl_summary = sorted(ucl_summary, key=lambda data: (data[5], data[4], data[3], data[2], data[1]), reverse=True)

line_format = '{pos:^4}|{team:^25}|{Pts:^15}|{GD:^15}|{KS:^10}|{First:^7}|{Second:^7}|{Third:^7}|{Fourth:^7}|'
group_format = '{group:^105}'

for team_number, team_stats in enumerate(group_sim_summary):
    if team_number % 4 == 0:
        print()
        group = 'Group ' + team_stats[7]
        print(group_format.format(group=group))
        print(line_format.format(pos='Pos', team='Team', Pts='Est. Points', GD='Est. GD', KS='Advance', First='1st',
                                 Second='2nd', Third='3rd', Fourth='4th'))
        print('-' * 105)
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
line_format = '{Pos:^4}|{team:^25}|{R16:^15}|{QF:^18}|{SF:^12}|{F:^10}|{W:^25}|'
ucl_format = '{title:^116}'
print(ucl_format.format(title='2022-23 UEFA Champions League Forecast'))
print()
print(line_format.format(Pos='Pos', team='Team', R16='Round of 16', QF='Quarterfinals', SF='Semifinals', F='Final',
                         W='Win Champions League'))
print('-' * 116)
for rank, team_stats in enumerate(ucl_summary):
    team = team_stats[0]
    make_r16 = str(round(team_stats[1] / 100)) + '%'
    make_qf = str(round(team_stats[2] / 100)) + '%'
    make_sf = str(round(team_stats[3] / 100)) + '%'
    make_final = str(round(team_stats[4] / 100)) + '%'
    win_ucl = str(round(team_stats[5] / 100)) + '%'
    print(line_format.format(Pos=rank + 1, team=team, R16=make_r16, QF=make_qf, SF=make_sf, F=make_final, W=win_ucl))

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
