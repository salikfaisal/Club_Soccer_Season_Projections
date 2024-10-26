import math
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options  # Import Options from chrome module
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common import NoSuchElementException
import statistics
import pandas as pd
import club_name_changes
import time
from datetime import datetime
from scipy.stats import poisson

# Use Service to install the ChromeDriver
service = Service(ChromeDriverManager().install())

# Initialize Chrome options
options = Options()
options.add_argument('--headless')  # Add headless argument

# Pass both service and options to Chrome WebDriver
driver = webdriver.Chrome(service=service, options=options)


def get_url_with_retries(driver, url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            driver.get(url)
            return  # Exit if successful
        except TimeoutException:
            print(f"TimeoutException on attempt {attempt + 1}. Retrying...")
            time.sleep(delay)  # Wait before retrying
    print("Failed to load the URL after multiple attempts")

# gets today's date
today = datetime.today().date()
# Format today's date as 'YYYY-MM-DD'
formatted_today = today.strftime('%Y-%m-%d')

# grabs the elo ratings of over 600 soccer clubs from across Europe
url = 'http://api.clubelo.com/' + str(formatted_today)

# Read the CSV data into a DataFrame
elo_ratings_df = pd.read_csv(url)

# imports the name change dictionaries to match clubs across different datasets
elo_name_changes = club_name_changes.elo_name_changes
football_transfers_name_changes = club_name_changes.football_transfers_name_changes
fbref_name_changes = club_name_changes.fbref_name_changes

# changes the names of clubs in the original Elo Ratings Data Frame
elo_ratings_df['Club'] = elo_ratings_df['Club'].replace(elo_name_changes)

# reads previous match data and drops any incomplete Data and duplicates
matches = pd.read_csv("Matches.csv")
matches.drop_duplicates(inplace=True)
matches.dropna(inplace=True)
# Convert the 'Date' column to datetime format
matches['Date'] = pd.to_datetime(matches['Date'])

# reads a Data Frame showing the line number last read during web scraping and converts it to a dictionary
last_row_nums = pd.read_csv("Row_Update.csv")
last_row_dict = last_row_nums.set_index('Competition')['Last_Row'].to_dict()

# list of codes for each league
league_comp_codes = {'Premier-League': '9', 'La-Liga': '12', 'Serie-A': '11', 'Ligue-1': '13', 'Bundesliga': '20',
                     'Primeira-Liga': '32', 'Eredivisie': '23', 'Championship': '10'}
# list of leagues with only 18 teams
eighteen_team_leagues = ['Bundesliga', 'Primeira-Liga', 'Eredivisie']
# codes for European Club Competitions
euro_comp_codes = {'Champions-League': '8', 'Europa-League': '19', 'Europa-Conference-League': '882'}

# lists to be used as columns in the data frame
dates = []
home_teams = []
away_teams = []
home_xgs = []
away_xgs = []
leagues = []

season_start_time = time.time()
for comp, comp_code in euro_comp_codes.items():
    # Gets the last row of the last web scrape run
    starting_row = last_row_dict[comp]
    previous_comp_matches = matches[matches['Competition'] == comp]
    date_of_last_update = previous_comp_matches['Date'].max().date()
    # gets the url for the season page
    print("Getting URL")
    url = 'https://fbref.com/en/comps/' + comp_code + '/2024-2025/schedule/2024-2025-' + comp + \
          '-Scores-and-Fixtures'
    driver.get(url)
    print("Got URL. Implicit Wait Begins")

    # waits 10 seconds for the page to load
    driver.implicitly_wait(10)
    print("Implicit Wait Finished")

    # finds the elements in the page with match information
    rows = driver.find_element(By.XPATH,
                               "//body[@class='fb']/div[@id='wrap']/div[@id='content']/div[@id='all_sched']"
                               "/div[@id='switcher_sched']/div[@id='div_sched_all']/table[@id='sched_all']"
                               "/tbody")
    print("starting", comp)
    # extracts match information by iterating over row numbers
    # starts at 15 rows below to account for jumps in rows without match data
    for row_num in range(starting_row - 15, 213):
        # if comp == 'Champions-League' and row_num == 132:
        #     break
        # elif comp == 'Europa-League' and row_num == 149:
        #     break
        element_finder = "//tr[@data-row='" + str(row_num) + "']"
        data = rows.find_element(By.XPATH, element_finder)

        # Use the 'data' element as the context for finding sub-elements
        try:
            # Try to extract the date
            date_str = data.find_element(By.XPATH, ".//td[@data-stat='date']").text
        except NoSuchElementException:
            # If date cannot be found, skip this row
            continue
        if date_str != '':
            date = pd.Timestamp(datetime.strptime(date_str, '%Y-%m-%d')).date()
            if date > today:
                break
            # elif date < date_of_last_update:
            #     continue
        else:
            continue
        try:
            # Use the 'data' element as the context for finding sub-elements
            home_team = data.find_element(By.XPATH, ".//td[@data-stat='home_team']/a").text
        except NoSuchElementException:
            # If home_team cannot be found, skip this row
            continue
        home_xg = data.find_element(By.XPATH, ".//td[@data-stat='home_xg']").text
        away_team = data.find_element(By.XPATH, ".//td[@data-stat='away_team']/a").text
        away_xg = data.find_element(By.XPATH, ".//td[@data-stat='away_xg']").text
        dates.append(date)
        home_teams.append(home_team)
        home_xgs.append(home_xg)
        away_teams.append(away_team)
        away_xgs.append(away_xg)
        leagues.append(comp)
        print(date, comp, home_team, "vs", away_team, "Match Expected Goals Added")
    # updates the last_row_dict to account for the last row examined in the webscraping
    last_row_dict[comp] = row_num
    end_time = time.time()
    print(comp, "Update Finished in", round((end_time - season_start_time) / 60, 2), "minutes")
    print("Current Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

for league, comp_code in league_comp_codes.items():
    # Gets the last row of the last web scrape run
    starting_row = last_row_dict[league]
    previous_league_matches = matches[matches['Competition'] == league]
    date_of_last_update = previous_league_matches['Date'].max().date()
    start_time = time.time()
    print("Getting URL")
    url = 'https://fbref.com/en/comps/' + comp_code + '/2024-2025/schedule/2024-2025-' + league + \
          '-Scores-and-Fixtures'
    print(url)
    get_url_with_retries(driver, url)
    print("Got URL. Implicit Wait Begins")

    # waits 10 seconds for the page to load
    driver.implicitly_wait(10)
    print("Implicit Wait Finished")
    try:
        rows = driver.find_element(By.XPATH, "//body[@class='fb']/div[@id='wrap']/div[@id='content']"
                                             "/div[@id='all_sched']"
                                             "/div[@id='div_sched_2024-2025_" + comp_code + "_1']"
                                                                                            "/table[@id='sched_2024-2025_" + comp_code + "_1']"
                                                                                                                                         "/tbody")
    except NoSuchElementException:
        rows = driver.find_element(By.XPATH,
                                   "//body[@class='fb']/div[@id='wrap']/div[@id='content']/div[@id='all_sched']"
                                   "/div[@id='switcher_sched']/div[@id='div_sched_all']/table[@id='sched_all']"
                                   "/tbody")
    print("starting", league)
    # extracts match information by iterating over row numbers
    # starts at 15 rows below to account for jumps in rows without match data
    for row_num in range(starting_row - 15, 700):
        element_finder = "//tr[@data-row='" + str(row_num) + "']"
        data = rows.find_element(By.XPATH, element_finder)

        # Use the 'data' element as the context for finding sub-elements
        try:
            # Try to extract the date
            date_str = data.find_element(By.XPATH, ".//td[@data-stat='date']").text
        except NoSuchElementException:
            # If date cannot be found, skip this row
            continue
        if date_str != '':
            date = pd.Timestamp(datetime.strptime(date_str, '%Y-%m-%d')).date()
            if date > today:
                break
            # elif date < date_of_last_update:
            #     continue
        else:
            continue
        try:
            # Use the 'data' element as the context for finding sub-elements
            home_team = data.find_element(By.XPATH, ".//td[@data-stat='home_team']/a").text
        except NoSuchElementException:
            # If home_team cannot be found, skip this row
            continue
        home_xg = data.find_element(By.XPATH, ".//td[@data-stat='home_xg']").text
        away_team = data.find_element(By.XPATH, ".//td[@data-stat='away_team']/a").text
        away_xg = data.find_element(By.XPATH, ".//td[@data-stat='away_xg']").text
        dates.append(date)
        home_teams.append(home_team)
        home_xgs.append(home_xg)
        away_teams.append(away_team)
        away_xgs.append(away_xg)
        leagues.append(league)
        print(date, league, home_team, "vs", away_team, "Match Expected Goals Added")
    # updates the last_row_dict to account for the last row examined in the webscraping
    if row_num < 15:
        last_row_dict[league] = 15
    else:
        last_row_dict[league] = row_num
    end_time = time.time()
    print(league, "Season Updated Expected Goals in", round((end_time - start_time) / 60, 2), "minutes")
    print("Current Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Convert the dictionary to a DataFrame
last_row_df = pd.DataFrame(list(last_row_dict.items()), columns=['Competition', 'Last_Row'])
last_row_df.to_csv("Row_Update.csv", index=False, header=True)

season_end_time = time.time()
print("Expected Goals Match Data updated in", round((season_end_time - season_start_time) / 60, 2), "minutes")

# creates a Data Frame of Expected Goals Data for All Leagues until the end of the 2022-23 Season and exports it
# to a CSV file
updated_matches = pd.DataFrame({"Competition": leagues, "Date": dates, "Home Team": home_teams, "Home XG": home_xgs,
                                "Away XG": away_xgs, "Away Team": away_teams})

matches = pd.concat([matches, updated_matches], ignore_index=True)

# exports to a CSV file
matches.to_csv('Matches.csv', index=False, header=True)

# reads the updated data frame
matches = pd.read_csv("Matches.csv")

# Changes Format of the 'Date' column to datetime
matches['Date'] = pd.to_datetime(matches['Date'])
# Drops any Duplicate or NA rows and sorts the rows by date
matches.drop_duplicates(inplace=True)
matches.dropna(inplace=True)
matches.sort_values(by='Date', ascending=True, inplace=True)

# exports to a CSV file
matches.to_csv('Matches.csv', index=False, header=True)

# URL for Starting Elo Ratings
url = 'http://api.clubelo.com/2017-08-01'

# Read the CSV data into a DataFrame
xg_elo_ratings_df = pd.read_csv(url)

# changes the names of clubs in the original Expected Goals Elo Ratings Data Frame
xg_elo_ratings_df['Club'] = xg_elo_ratings_df['Club'].replace(elo_name_changes)

xg_missing_club_df = club_name_changes.xg_missing_club_df
xg_elo_ratings_df = pd.concat([xg_elo_ratings_df, xg_missing_club_df], ignore_index=True)


# updates the names of the Clubs in the 'matches' Data Frame
matches['Home Team'] = matches['Home Team'].replace(fbref_name_changes)
matches['Away Team'] = matches['Away Team'].replace(fbref_name_changes)

# Get the unique values in the "Clubs" column of xg_elo_ratings_df
xg_elo_clubs = xg_elo_ratings_df['Club'].unique()
# Find values in the "Home Team" and "Away_Team" column of matches that are not in elo_clubs
missing_home_teams = matches[~matches['Home Team'].isin(xg_elo_clubs)]['Home Team'].unique()
missing_away_teams = matches[~matches['Away Team'].isin(xg_elo_clubs)]['Away Team'].unique()
# Combine the missing teams from both columns
missing_teams = set(missing_home_teams) | set(missing_away_teams)

if len(missing_teams) > 0:
    print("Teams in Matches Data Frame but Missing from XG Elo Ratings:")
    print(missing_teams)
print()

# Each Nation in the Model is given a starting Home Field Advantage of 50 and it is updated after every match examined
hfas = {'ENG': 50, 'ESP': 50, 'GER': 50, 'ITA': 50, 'FRA': 50, 'NED': 50, 'POR': 50}

# This a list of dates where a match was played at a neutral venue in a European Club Competition
euro_neutral_dates = ['2018-05-26', '2019-06-01', '2020-08-12', '2020-08-13', '2020-08-14', '2020-08-15', '2020-08-18',
                      '2020-08-19', '2020-08-23', '2021-05-29', '2022-05-28', '2023-06-10', '2018-05-16', '2019-05-29',
                      '2020-08-05', '2020-08-06', '2020-08-10', '2020-08-11', '2020-08-16', '2020-08-17', '2020-08-21',
                      '2021-05-26', '2022-05-28', '2023-05-31', '2022-05-25', '2023-06-07', '2024-06-01', '2024-05-29',
                      '2024-05-22']
# Convert date strings to datetime objects
euro_neutral_dates = [datetime.strptime(date_str, '%Y-%m-%d') for date_str in euro_neutral_dates]

print("Reading Expected Goals Match Data")
start_time = time.time()
number_of_total_matches = len(matches)
for idx, match in matches.iterrows():
    # gets key information regarding the match
    home_team = match['Home Team']
    away_team = match['Away Team']
    home_xg = float(match['Home XG'])
    away_xg = float(match['Away XG'])
    home_xg_elo_info = xg_elo_ratings_df[xg_elo_ratings_df["Club"] == home_team].iloc[0]
    away_xg_elo_info = xg_elo_ratings_df[xg_elo_ratings_df["Club"] == away_team].iloc[0]
    home_elo = home_xg_elo_info["Elo"]
    away_elo = away_xg_elo_info["Elo"]
    home_team_country = home_xg_elo_info["Country"]
    # adjusts for home field advantage in matches with non-neutral venues
    if not (match['Competition'] in euro_comp_codes and match['Date'] in euro_neutral_dates):
        if home_team_country in hfas:
            home_elo += hfas[home_team_country]
        else:
            # sets the home field advantage to 50 elo points for countries not examined
            home_elo += 50
    # calculates the home team's win expectancy based on both teams' elo ratings
    home_we = 1 / (10 ** ((away_elo - home_elo) / 400) + 1)
    # calculates the mean expected goal difference based on the home team's win expectancy
    home_mean_gd = statistics.NormalDist(0, 1.3).inv_cdf(home_we)
    # gets the pre-match win and loss probabilities for the home team
    z_loss_mark = (-0.5 - home_mean_gd) / 1.3
    z_win_mark = (0.5 - home_mean_gd) / 1.3
    home_pre_match_win_prob = 1 - statistics.NormalDist().cdf(z_win_mark)
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
            change_in_elo += (0 - home_we) * 20 * math.sqrt(abs(gd)) * prob / loss_pts_exchange_den \
                             * math.sqrt(abs(gd))
        elif gd == 0:
            change_in_elo += (0.5 - home_we) * 20 * prob
        else:
            change_in_elo += (1 - home_we) * 20 * math.sqrt(gd) * prob / win_pts_exchange_den * math.sqrt(gd)
    # gets the new home and away elo ratings and updates the dictionary
    xg_elo_ratings_df.loc[xg_elo_ratings_df['Club'] == home_team, 'Elo'] += change_in_elo
    xg_elo_ratings_df.loc[xg_elo_ratings_df['Club'] == away_team, 'Elo'] -= change_in_elo
    # adjusts the effect of home field advantage depending on the home team's result
    if home_team_country in hfas:
        hfas[home_team_country] += 0.075 * change_in_elo
    if (idx + 1) % (number_of_total_matches // 20) == 0:
        print((idx + 1) / number_of_total_matches * 100, "% Complete")
        current_time = time.time()
        seconds_since_start = current_time - start_time
        expected_total_seconds = seconds_since_start / ((idx + 1) / number_of_total_matches)
        seconds_remaining = expected_total_seconds - seconds_since_start
        print(round(seconds_remaining / 60, 2), "minutes remaining")

end_time = time.time()
print("Extracted Elo Ratings for Clubs Based on Expected Goals in", round((end_time - start_time) / 60, 2), "minutes")

# Leagues that have 0 teams in any UEFA Club Competitions or will not be modeled
leagues_of_non_interest = ['Serie B', '2. Bundesliga', 'Ligue 2', 'LaLiga 2 (Segunda División)',
                           'Keuken Kampioen Divisie', 'League One', 'Challenger Pro League', 'Serie C - Girone C',
                           'Challenge League', 'Segunda Liga', '1. Division', 'Regionalliga Ost', 'Serie C - Girone B',
                           '2 Liga']

# iterates over 12 pages of Data
clubs = []
leagues = []
ratings = []
start_time = time.time()
print()
for page_num in range(1, 13):
    # Open the URL
    driver.get('https://www.footballtransfers.com/en/teams/europe/' + str(page_num))

    # Wait 10 seconds for the website to load
    driver.implicitly_wait(10)

    # Find all matching <tr> elements using the XPath expression
    rows = driver.find_elements(By.XPATH, "//section[@id='template']"
                                          "/section[@id='layout']/main[@id='content-part']"
                                          "/section[@class='main-bar mainarticle-bar5']"
                                          "/div[@class='container relative']"
                                          "/div[@class='row']/div[@class='column-left']/div[@class='bg-white']"
                                          "/div[@class='main-article auto-placeholder-table']"
                                          "/table[@class='table table-striped table-hover ft-table team-overview-table mb-0']"
                                          "/tbody[@id='player-table-body']/tr")
    # Iterate over each <tr> element and print its text content
    for row in rows:
        # extracts key data for each Club
        columns = row.find_elements(By.TAG_NAME, "td")
        league = columns[2].text
        # does not record data for Leagues that will not be used in for the Model
        if league in leagues_of_non_interest:
            continue
        rating = float(columns[0].text.split()[0])
        club_name = columns[1].text
        # edits out the prefixes in each Club's Name to reduce matching issues
        if club_name[-3:] in [' FC', ' CF', ' FK', ' SK', ' NK', ' IF', ' SC', ' BK', ' BC', ' AC', ' KV', ' FF', ' GF',
                              ' VV', ' TC']:
            club_name = club_name[:-3]
        elif club_name[-4:] in [' AFC', ' HSC', ' CFC', ' GFS']:
            club_name = club_name[:-4]
        elif club_name[:3] in ['FC ', 'AS ', 'UD ', 'IF ', 'US ', 'FK ', 'RS ', 'IF ', 'SS ', 'CA ', 'SV ', 'GD ',
                               'AC ', 'SC ', 'SL ', 'SK ', 'NK ', 'KV ', 'RC ', 'BK ']:
            club_name = club_name[3:]
        elif club_name[:4] in ['AFC ', 'RSC ', 'GNK ', 'MTK ', 'IFK ', 'MSK ', 'ACF ', 'KAA ', 'SSC ', 'RKC ', 'PSC ',
                               'BSC ', 'AIK ', 'HNK ', 'OGC ', 'TSC ', 'DAC ', 'TSG ', 'PEC ', 'TSV ', 'NEC ', 'RCD ',
                               'KRC ', 'KAS ', 'KVC ', 'TSC ', 'WSG ', 'OFI ']:
            club_name = club_name[4:]
        # adds data to lists needed to create a Data Frame
        if club_name in football_transfers_name_changes:
            club_name = football_transfers_name_changes[club_name]
        # To avoid a duplicate of a specific Romanian Club
        if club_name == 'Farul Constanța' and 'Farul Constanța' in clubs:
            continue
        # Ensures there are no Clubs with a Rating of 0
        elif rating <= 0:
            continue
        if club_name not in set(xg_elo_ratings_df['Club']):
            print(club_name, "In Football Transfers Data, but not in Elo Ratings Data Frame")
        clubs.append(club_name)
        leagues.append(league)
        ratings.append(rating)
driver.quit()
print()

end_time = time.time()
print("Examined Club Transfer Values in", round((end_time - start_time) / 60, 2), "minutes")

# creates a Data Frame from the extracted Information

transfer_value_df = pd.DataFrame({'Club': clubs, 'League': leagues, 'Rating': ratings})
print()
for row_num, row in xg_elo_ratings_df.iterrows():
    club = row['Club']
    country = row["Country"]
    if club not in clubs and country in ['ENG', 'GER', 'ESP', 'FRA', 'ITA', 'POR', 'NED', 'BEL', 'UKR', 'CRO', 'AUT',
                                         'SER', 'SUI', 'SCO', 'SVK', 'CZE']:

        print(club, country, "is in XG El Ratings but not in Football Transfers")
print()
transfer_value_df = elo_ratings_df.merge(transfer_value_df, on='Club')

# Calculate z-score for the 'Rating' column
z_score = (transfer_value_df['Rating'] - transfer_value_df['Rating'].mean()) / transfer_value_df['Rating'].std()


# Define a function to estimate 'Elo' based on z-score
def estimate_elo(z_score, mean_elo, std_elo):
    return mean_elo + z_score * std_elo


# Mean and standard deviation of 'Elo' column
mean_elo = elo_ratings_df['Elo'].mean()
std_elo = elo_ratings_df['Elo'].std()

# changes the name of a column in the XG Elo Ratings Data Frame
xg_elo_ratings_df.rename(columns={"Elo": "XG Elo"}, inplace=True)

# Estimate 'Elo' based on z-score
transfer_value_df['Transfer_Elo'] = estimate_elo(z_score, mean_elo, std_elo)

# Merge elo_ratings_df with xg_ratings_df using a left join
merged_df = elo_ratings_df.merge(xg_elo_ratings_df[["Club", "XG Elo"]], on='Club', how='left')

# Merge the merged_df with transfer_value_df using a left join
grand_elo_df = merged_df.merge(transfer_value_df[["Club", "Transfer_Elo"]], on='Club', how='left')


def calculate_combined_elo_rating(row):
    original_elo = row["Elo"]
    xg_elo = row["XG Elo"]
    transfer_elo = row["Transfer_Elo"]
    if pd.isna(xg_elo):
        xg_elo = original_elo
    if pd.isna(np.NaN):
        transfer_elo = original_elo
    original_weight = 0.5
    xg_weight = 0.25
    transfer_weight = 0.25
    return original_elo * original_weight + xg_elo * xg_weight + transfer_elo * transfer_weight


grand_elo_df['Adjusted_Elo_Rating'] = grand_elo_df.apply(calculate_combined_elo_rating, axis=1)

grand_elo_df.sort_values(by='Adjusted_Elo_Rating', ascending=False, inplace=True)
grand_elo_df.reset_index(inplace=True)
grand_elo_df['Rank'] = grand_elo_df.index + 1
grand_elo_df.drop(columns=["From", "To", "index"], inplace=True)
grand_elo_df.to_csv("Elo Ratings for European Clubs.csv", index=False, header=True)
grand_elo_df.set_index("Club", inplace=True)
