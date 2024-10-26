from bs4 import BeautifulSoup
import requests
import statistics
import random

# This is done before the start of each season to determine the range of goal probabilities

# # this will be used to assist in getting information about a specific league
# country_code_to_league = {'ENG': 'Premier_League', 'GER': 'Bundesliga', 'ITA': 'Serie_A', 'ESP': 'La_Liga',
#                           'FRA': 'Ligue_1', 'NED': 'Eredivisie', 'POR': 'Primeira_Liga'}
#
# # Examines scorelines for every country and adds them to a list
# club_results = []
# for country_code, league in country_code_to_league.items():
#     url = 'https://en.wikipedia.org/wiki/2023%E2%80%9324_' + league
#     clubs_in_league = 20
#     if country_code in ['GER', 'FRA', 'NED', 'POR']:
#         clubs_in_league = 18
#     page = requests.get(url)
#     soup = BeautifulSoup(page.content, 'html.parser')
#     search = soup.find(class_='wikitable plainrowheaders').text.split('\n')[(clubs_in_league * 2 + 5):]
#     # grabs the results and fixture list in the season
#     for line_num, line in enumerate(search):
#         if line_num % (clubs_in_league * 2 + 3) % 2 == 0:
#             result = line.split('–')
#             if '–' in line:
#                 if '[' in result[1]:
#                     result[1] = result[1][:-3]
#                 club_results.append([int(result[0]), int(result[1])])
#
# # Examines each result and finds the distribution of goals
# goal_summary = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
# total_goals = 0
# for result in club_results:
#     home_goals = result[0]
#     away_goals = result[1]
#     goal_summary[home_goals] += 1
#     goal_summary[away_goals] += 1
#     total_goals += home_goals + away_goals
# number_of_games = len(club_results)
# goal_probabilities = [x / (number_of_games * 2) for x in goal_summary]
# print("Average Number of Total Goals Per Game:", total_goals / number_of_games)
# print("Total Number of Games Examined:", number_of_games)
# for goals, probability in enumerate(goal_probabilities):
#     print("Probability of", goals, "total goals scored for a team:", round(probability * 100, 2), "%")
# print(goal_probabilities)

# this function returns a simulation of the results of a game given the elo ratings of the two teams
def match_result(team_1_elo, team_2_elo):
    # uses the elo formula to get the two-outcome win probability
    team_1_wl = 1 / (10 ** ((team_2_elo - team_1_elo) / 400) + 1)
    # gets the average goal difference expected between the two sides
    # if two sides have an equal rating the probabilities are: 35% Team 1 win, 30% draw, 35% Team 2 win
    team_1_margin_mean = statistics.NormalDist(0, 1.3).inv_cdf(team_1_wl)
    # the goal difference as a result of a random simulation
    team_1_margin = round(statistics.NormalDist(team_1_margin_mean, 1.3).inv_cdf(random.random()))
    # the goal probability distribution from 1826 matches in the 2022-23 season in Europe's top 7 leagues
    goal_prob = [0.2533840947546531, 0.32719966159052455, 0.22715736040609136, 0.12119289340101523, 0.04589678510998308,
                 0.018824027072758036, 0.004018612521150592, 0.0012690355329949238, 0.0010575296108291032, 0.0, 0.0]


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