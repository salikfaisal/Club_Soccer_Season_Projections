from datetime import date
import random
import statistics
import time

from bs4 import BeautifulSoup
import requests

today = date.today()
t0 = time.time()

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
'Man City': 'Manchester City', 'Man United': 'Manchester United', 'Newcastle': 'Newcastle United', 'Norwich': 'Norwich City',
'Tottenham': 'Tottenham Hotspur', 'West Ham': 'West Ham United', 'Wolves': 'Wolverhampton Wanderers',
'Atlético': 'Atlético Madrid', 'Atletico': 'Atlético Madrid', 'Betis': 'Real Betis',  'Sociedad': 'Real Sociedad', 
'Bilbao': 'Athletic Bilbao', 'Celta': 'Celta Vigo', 'Cadiz': 'Cádiz', 'Alaves': 'Alavés',
'Augsburg': 'FC Augsburg', 'Hertha': 'Hertha BSC', 'Bielefeld': 'Arminia Bielefeld', 'Bochum': 'VfL Bochum', 
'Dortmund': 'Borussia Dortmund', 'Frankfurt': 'Eintracht Frankfurt', 
'Freiburg': 'SC Freiburg', 'Fürth': 'Greuther Fürth', 'Fuerth': 'Greuther Fürth', 'Hoffenheim': '1899 Hoffenheim', 
'Köln': '1. FC Köln', 'Koeln': '1. FC Köln', 'Leverkusen': 'Bayer Leverkusen', 'Mainz': 'Mainz 05', 
'Gladbach': 'Borussia Mönchengladbach', 'Bayern': 'Bayern Munich', 'Stuttgart': 'VfB Stuttgart', 'Wolfsburg': 'VfL Wolfsburg',
'Inter': 'Inter Milan', 'Milan': 'AC Milan', 'Verona': 'Hellas Verona',
'Saint-Etienne': 'Saint-Étienne', 'Paris SG': 'Paris Saint-Germain', 'Forest': 'Nottingham Forest', 'Almeria': 'Almería',
'Werder': 'Werder Bremen', 'Schalke': 'Schalke 04'}
wiki_name_changes = {'Milan': 'AC Milan', 'Paris SG': 'Paris Saint-Germain'}

club_elo_dict = {}
for club in club_ratings:
    if club[1] in elo_name_changes:
        club[1] = elo_name_changes[club[1]]
    club_elo_dict.update({club[1]: club})
t1 = time.time()


# this function retrieves the home field advantage that will be added to each elo rating for a home side in a given country
def home_field_advantage(country_code):
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
    return float(home_field_advantage)



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
    0.014786418400876232, 0.0024644030668127055, 0.0008214676889375684, 0.0002738225629791895, 0.0002738225629791895]
    gp_list = []
    if abs(team_1_margin) > 9:
        winning_goal_count = abs(team_1_margin)
        losing_goal_count = 0
    else:
        gp_list = goal_prob[abs(team_1_margin):]
        total = sum(gp_list)
        cum = 0
        for goal_count, goal_probability in enumerate(gp_list):
            gp_list[goal_count] = goal_probability/total
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
    country_code_to_league = {'ENG': 'Premier_League', 'GER': 'Bundesliga', 'ITA': 'Serie_A', 'ESP': 'La_Liga', 'FRA': 'Ligue_1'}
    league_name = country_code_to_league[country_code]
    home_advantage = home_field_advantage(country_code)
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
        simulation_sums.update({team: [0, 0, 0, 0]})
    for simulation in range(10000):
        table = {}
        league_fixtures = []
        for team in alphabetized_teams:
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
            if rank < rank_needed_for_ucl:
                summary_stats[2] +=1
                if rank < 1:
                    summary_stats[3] += 1
            simulation_sums.update({club_season[0]: summary_stats})
        final_season_probabilities = []
        for club, summary_stats in simulation_sums.items():
            season_probabilities = [club]
            for stat in summary_stats:
                season_probabilities.append(stat / 10000)
            final_season_probabilities.append(season_probabilities)
    final_season_probabilities = sorted(final_season_probabilities, key=lambda club_info: (club_info[-1], club_info[-2],
    club_info[-3], club_info[-4]), reverse=True)
    return final_season_probabilities

leagues = {'ENG': 'Premier League (England)', 'ESP': 'La Liga (Spain)', 'ITA': 'Serie A (Italy)', 'GER': 'Bundesliga (Germany)', 
           'FRA': 'Ligue 1 (France)'}
line_format = '{pos:^4}|{club:^25}|{GD:^10}|{Pts:^10}|{UCL:^10}|{W:^10}'
league_name_format = '{league:^75}'
for code, league in leagues.items():
    league_probabilities = league_simulations(code)
    print(league_name_format.format(league=league))
    print(line_format.format(pos='Pos', club='Team', GD='Avg. GD', Pts='Avg. Pts', UCL='Make UCL', W='Win League'))
    print('-' * 75)
    for position, data in enumerate(league_probabilities):
        average_gd = str(round(data[1]))
        average_pts = str(round(data[2]))
        make_ucl = str(round(data[3] * 100)) + '%'
        win_league = str(round(data[4] * 100)) + '%'
        print(line_format.format(pos=position+1, club=data[0], GD=average_gd, Pts=average_pts, UCL=make_ucl, W=win_league))