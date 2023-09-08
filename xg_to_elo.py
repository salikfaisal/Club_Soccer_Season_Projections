import pandas as pd
import requests
from scipy.stats import poisson
from datetime import datetime
import math
import statistics
import club_name_changes

# grabs the elo ratings of over 600 soccer clubs from across Europe
url = 'http://api.clubelo.com/2017-08-01'
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
elo_name_changes = club_name_changes.elo_name_changes
fbref_name_changes = club_name_changes.fbref_name_changes

club_elo_dict = {}
for club in club_ratings:
    if club[1] in elo_name_changes:
        club[1] = elo_name_changes[club[1]]
    club_elo_dict.update({club[1]: club})

matches = pd.read_csv("Matches.csv")
matches.dropna(inplace=True)

# Convert the 'Date' column to datetime format
matches['Date'] = pd.to_datetime(matches['Date'])
matches = matches.sort_values(by='Date').reset_index()


matches['Home Team'] = matches['Home Team'].replace(fbref_name_changes)
matches['Away Team'] = matches['Away Team'].replace(fbref_name_changes)

# elo ratings for these teams was not found in the
missing_starting_elos = {'Mallorca': ['None', 'Mallorca', 'ESP', '3', '1501.40551758', '2017-08-01', '2017-08-01'],
                'SC Paderborn': ['None', 'None', 'GER', '3', '1357.40759277', '2017-08-01', '2017-08-01'],
                'Lecce': ['None', 'None', 'ITA', '3', '1373.2545166', '2017-08-01', '2017-08-01'],
                'Elche': ['None', 'None', 'ESP', '3', '1470.01879883', '2017-08-01', '2017-08-01'],
                'Monza': ['None', 'None', 'ITA', '3', '1386.21459961', '2017-08-01', '2017-08-01'],
                'Wigan Athletic': ['None', 'None', 'ENG', '3', '1374.68078613', '2017-08-01', '2017-08-01'],
                'Blackburn Rovers': ['None', 'None', 'ENG', '3', '1374.68078613', '2017-08-01', '2017-08-01'],
                'Luton Town': ['None', 'None', 'ENG', '3', '1418.29626465', '2017-08-01', '2017-08-01'],
                'Coventry City': ['None', 'None', 'ENG', '3', '1356.68652344', '2017-08-01', '2017-08-01'],
                'Wycombe Wanderers': ['None', 'None', 'ENG', '3', '1356.68652344', '2017-08-01', '2017-08-01'],
                'Rotterham United': ['None', 'None', 'ENG', '3', '1374.68078613', '2017-08-01', '2017-08-01'],
                'Charlton Athletic': ['None', 'None', 'ENG', '3', '1418.28491211', '2017-08-01', '2017-08-01'],
                'Blackpool': ['None', 'None', 'ENG', '3', '1443.22253418', '2017-08-01', '2017-08-01'],
                'Famalicão': ['None', 'None', 'POR', '3', '1382.99597168', '2017-08-01', '2017-08-01'],
                'Casa Pia': ['None', 'None', 'POR', '3', '1399.82580566', '2017-08-01', '2017-08-01'],
                'Gil Vicente': ['None', 'None', 'POR', '3', '1382.99597168', '2017-08-01', '2017-08-01'],
                'Vizela': ['None', 'None', 'POR', '3', '1359.59082031', '2017-08-01', '2017-08-01'],
                'Go Ahead Eagles': ['None', 'None', 'NED', '3', '1295.49084473', '2017-08-01', '2017-08-01'],
                'RKC Waalwijk': ['None', 'None', 'NED', '3', '1320.58068848', '2017-08-01', '2017-08-01'],
                'Arouca': ['None', 'None', 'POR', '3', '1359.26000977', '2017-08-01', '2017-08-01'],
                'Farense': ['None', 'None', 'POR', '3', '1351.43603516', '2017-08-01', '2017-08-01'],
                'NEC Nijmegen': ['None', 'None', 'NED', '3', '1295.49084473', '2017-08-01', '2017-08-01'],
                'Nacional': ['None', 'None', 'POR', '3', '1360.27355957', '2017-08-01', '2017-08-01'],
                'Emmen': ['None', 'None', 'NED', '3', '1275.10205078', '2017-08-01', '2017-08-01'],
                'AC Omonia': ['None', 'None', 'CYP', '3', '1459.00878906', '2017-08-01', '2017-08-01'],
                'Cambuur': ['None', 'None', 'NED', '3', '1295.49084473', '2017-08-01', '2017-08-01'],
                'Mura': ['None', 'None', 'SVN', '3', '1161.25476074', '2017-08-01', '2017-08-01'],
                'Volendam': ['None', 'None', 'NED', '3', '1380.20788574', '2017-08-01', '2017-08-01'],
                'Spartak Trnava': ['None', 'None', 'SLK', '3', '1384.20422363', '2017-08-01', '2017-08-01'],
                'Ballkani': ['None', 'None', 'KOS', '3', '1014.16369629', '2017-08-01', '2017-08-01'],
                'Anorthosis': ['None', 'None', 'CYP', '3', '1445.86584473', '2017-08-01', '2017-08-01'],
                'Fortuna Sittard': ['None', 'None', 'NED', '3', '1275.10205078', '2017-08-01', '2017-08-01'],
                'De Graafschap': ['None', 'None', 'NED', '3', '1275.10205078', '2017-08-01', '2017-08-01'],
                'Santa Clara': ['None', 'None', 'POR', '3', '1360.27355957', '2017-08-01', '2017-08-01'],
                'Bodø/Glimt': ['None', 'None', 'NOR', '3', '1180.12976074', '2017-08-01', '2017-08-01'],
                'RFS': ['None', 'None', 'LAT', '3', '1128.54516602', '2017-08-01', '2017-08-01'],
                'Dnipro-1': ['None', 'None', 'UKR', '3', '1350.01940918', '2017-08-01', '2017-08-01'],
                'Union SG': ['None', 'None', 'BEL', '3', '1315.92456055', '2017-08-01', '2017-08-01'],
                'Peterborough United': ['None', 'None', 'ENG', '3', '1443.22253418', '2017-08-01', '2017-08-01']}
club_names = []
countries = []
ratings = []
for club, club_data in missing_starting_elos.items():
    club_names.append(club)
    countries.append(club_data[2])
    ratings.append(float(club_data[4]))
print(club_names)
print()
print(countries)
print()
print(ratings)
missing_clubs_df = pd.DataFrame({'Club': club_names, 'Country': countries, "Rating": ratings})
print(missing_clubs_df)



names_not_in_elos = []
for name in matches['Home Team'].unique():
    if name not in club_elo_dict:
        names_not_in_elos.append(name)
        print(name)
print()
print(names_not_in_elos)
hfas = {'ENG': 50, 'ESP': 50, 'GER': 50, 'ITA': 50, 'FRA': 50, 'NED': 50, 'POR': 50}

ucl_neutral_dates = ['2018-05-26', '2019-06-01', '2020-08-12', '2020-08-13', '2020-08-14', '2020-08-15', '2020-08-18',
                     '2020-08-19', '2020-08-23', '2021-05-29', '2022-05-28', '2023-06-10']
# Convert date strings to datetime objects
ucl_neutral_dates_datetime = [datetime.strptime(date_str, '%Y-%m-%d') for date_str in ucl_neutral_dates]

for idx, match in matches.iterrows():
    # gets key information regarding the match
    home_team = match['Home Team']
    away_team = match['Away Team']
    home_xg = match['Home XG']
    away_xg = match['Away XG']
    home_elo = float(club_elo_dict[home_team][4])
    away_elo = float(club_elo_dict[away_team][4])
    home_team_country = club_elo_dict[home_team][2]
    # adjusts for home field advantage in matches with non-neutral venues
    if not (match['Competition'] == 'Champions League' and match['Date'] in ucl_neutral_dates_datetime):
        if home_team_country in hfas:
            home_elo += hfas[home_team_country]
        else:
            home_elo += 50
    # calculates the home team's win expectancy based on both teams' elo ratings
    home_we = 1 / (10 ** ((away_elo - home_elo) / 400) + 1)
    # calculates the mean expected goal difference based on the home team's win expectancy
    home_mean_gd = statistics.NormalDist(0, 1.3).inv_cdf(home_we)
    # gets the pre-match win and loss probabilities for the home team
    z_loss_mark = (-0.5 - home_mean_gd) / 1.3
    z_win_mark = (0.5 - home_mean_gd) / 1.3
    home_pre_match_win_prob =  1 - statistics.NormalDist().cdf(z_win_mark)
    home_pre_match_loss_prob = statistics.NormalDist().cdf(z_loss_mark)
    # gets a list based on a Poisson distribution of Expected Goals in a Match for both teams
    home_gps = []
    away_gps = []
    for goal_count in range(11):
        home_goal_prob = poisson.pmf(k=goal_count, mu=home_xg)
        away_goal_prob = poisson.pmf(k=goal_count, mu=away_xg)
        home_gps.append(home_goal_prob)
        away_gps.append(away_goal_prob)
    win_pts_exchange_den = 0
    loss_pts_exchange_den = 0
    # gets a dictionary of goal differences and the probabilities based on the expected goals
    gd_probabilities = {}
    for gd in range(-10, 11):
        z_lower = (gd - 0.5 - home_mean_gd) / 1.3
        z_upper = (gd + 0.5 - home_mean_gd) / 1.3
        # Approximate the probabilities using the standard normal distribution
        probability_lower = statistics.NormalDist().cdf(z_upper)
        probability_upper = statistics.NormalDist().cdf(z_lower)
        # gets the pre-match probability for a particular Goal Difference Margin
        pre_match_gd_prob = probability_lower - probability_upper
        # adds the value for the goal difference to assist with calculating the elo points exchanged
        if gd < 0:
            loss_pts_exchange_den += math.sqrt(abs(gd)) * pre_match_gd_prob / home_pre_match_loss_prob
        elif gd > 0:
            win_pts_exchange_den += math.sqrt(gd) * pre_match_gd_prob / home_pre_match_win_prob
        # creates a value for the goal difference in the dictionary
        gd_probabilities.update({gd: 0})
    # estimates the probability of each goal difference based on the expected goals statistic
    for home_gc, home_gp in enumerate(home_gps):
        for away_gc, away_gp, in enumerate(away_gps):
            gd = home_gc - away_gc
            prob = home_gp * away_gp
            gd_probabilities[gd] += prob
    # calculates the change in elo rating based on the probabilities from the expected goal statistic
    change_in_elo = 0
    for gd, prob in gd_probabilities.items():
        if gd < 0:
            change_in_elo += (0 - home_we) * 20 * math.pow(abs(gd), 0.25) * prob / loss_pts_exchange_den\
                             * math.sqrt(abs(gd))
        elif gd == 0:
            change_in_elo += (0.5 - home_we) * 20 * prob
        else:
            change_in_elo += (1 - home_we) * 20 * math.sqrt(gd) * prob / win_pts_exchange_den * math.sqrt(gd)
    # gets the new home and away elo ratings and updates the dictionary
    new_home_rating = float(club_elo_dict[home_team][4]) + change_in_elo
    new_away_rating = float(club_elo_dict[away_team][4]) - change_in_elo
    club_elo_dict[home_team][4] = new_home_rating
    club_elo_dict[away_team][4] = new_away_rating
    # adjusts the effect of home field advantage depending on the home team's result
    if home_team_country in hfas:
        hfas[home_team_country] += 0.075 * change_in_elo
    if idx % 500 == 0 or (match['Date'] in ucl_neutral_dates_datetime):
        top_50_clubs_ratings = {}
        count = 0
        for club in club_elo_dict:
            if count == 0:
                count += 1
                continue
            top_50_clubs_ratings.update({club: float(club_elo_dict[club][4])})
            count += 1
            if count == 51:
                print("Date:", match["Date"])
                sorted_clubs = sorted(top_50_clubs_ratings.items(), key=lambda x: x[1], reverse=True)
                rank = 1
                for club, rating in sorted_clubs:
                    print(rank, club, rating)
                    rank += 1
                print()
                break