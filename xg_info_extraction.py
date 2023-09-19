import pandas as pd
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

# took around 750 minutes to extract ALL match data
total_start_time = time.time()

# installs driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# list of seasons examined
seasons = ['2017-2018', '2018-2019', '2019-2020', '2020-2021', '2021-2022', '2022-2023']
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

# iterates through seasons and scrapes information for each season
for season in seasons:
    season_start_time = time.time()
    for comp, comp_code in euro_comp_codes.items():
        # skips over seasons where there is no Europa Conference League
        if comp == 'Europa-Conference-League' and (season not in ['2021-2022', '2022-2023']):
            continue
        # gets the url for the season page
        url = 'https://fbref.com/en/comps/' + comp_code + '/' + season + '/schedule/' + season + '-' + comp + \
              '-Scores-and-Fixtures'
        driver.get(url)

        # waits 10 seconds for the page to load
        driver.implicitly_wait(10)

        # finds the elements in the page with match information
        rows = driver.find_element(By.XPATH,
                                   "//body[@class='fb']/div[@id='wrap']/div[@id='content']/div[@id='all_sched']"
                                   "/div[@id='switcher_sched']/div[@id='div_sched_all']/table[@id='sched_all']"
                                   "/tbody")

        # extracts match information by iterating over row numbers
        print("starting", season, comp)
        for row_num in range(213):
            element_finder = "//tr[@data-row='" + str(row_num) + "']"
            try:
                data = rows.find_element(By.XPATH, element_finder)
            except NoSuchElementException:
                # this means that all the matches have been extracted
                break
            # Use the 'data' element as the context for finding sub-elements
            try:
                # Try to extract the date
                date = data.find_element(By.XPATH, ".//td[@data-stat='date']").text
            except NoSuchElementException:
                # If date cannot be found, skip this row
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
        end_time = time.time()
        print(season, comp, "Season Finished in", round((end_time - season_start_time) / 60, 2), "minutes")


    for league, comp_code in league_comp_codes.items():
        # There is no expected goals data for these leagues in the 2017-2018 Season
        if season == '2017-2018' and league in ['Primeira-Liga', 'Eredivisie', 'Championship']:
            continue
        start_time = time.time()
        url = 'https://fbref.com/en/comps/' + comp_code + '/' + season + '/schedule/' + season + '-' + league +\
              '-Scores-and-Fixtures'
        driver.get(url)

        # waits 10 seconds for the page to load
        driver.implicitly_wait(10)
        try:
            rows = driver.find_element(By.XPATH, "//body[@class='fb']/div[@id='wrap']/div[@id='content']"
                                                 "/div[@id='all_sched']"
                                                 "/div[@id='div_sched_" + season + "_" + comp_code + "_1']"
                                                 "/table[@id='sched_" + season + "_" + comp_code + "_1']"
                                                 "/tbody")
        except NoSuchElementException:
            rows = driver.find_element(By.XPATH,
                                       "//body[@class='fb']/div[@id='wrap']/div[@id='content']/div[@id='all_sched']"
                                       "/div[@id='switcher_sched']/div[@id='div_sched_all']/table[@id='sched_all']"
                                       "/tbody")
        print("starting", season, league)
        # extracts match information by iterating over row numbers
        total_num_of_matches = 380
        if league in eighteen_team_leagues:
            total_num_of_matches = 306
        elif league == 'Championship':
            total_num_of_matches = 552
        num_of_matches = 0
        for row_num in range(700):
            if num_of_matches == total_num_of_matches:
                break
            element_finder = "//tr[@data-row='" + str(row_num) + "']"
            data = rows.find_element(By.XPATH, element_finder)

            # Use the 'data' element as the context for finding sub-elements
            try:
                # Try to extract the date
                date = data.find_element(By.XPATH, ".//td[@data-stat='date']").text
            except NoSuchElementException:
                # If date cannot be found, skip this row
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
            num_of_matches += 1
            if num_of_matches % 3 == 0:
                current_time = time.time()
                expected_finish_time = (current_time - start_time) / (num_of_matches / total_num_of_matches)
                print(season, league, "Season", num_of_matches / (total_num_of_matches / 100), "% complete")
                print((expected_finish_time - (current_time - start_time)) / 60, "minutes left")
        end_time = time.time()
        print(season, league, "Season Finished in", round((end_time - start_time) / 60, 2), "minutes")
    season_end_time = time.time()
    print(season, "Season examined in", round((season_end_time - season_start_time) / 60, 2), "minutes")
driver.quit()

# creates a Data Frame of Expected Goals Data for All Leagues until the end of the 2022-23 Season and exports it
# to a CSV file
matches = pd.DataFrame({"Competition": leagues, "Date": dates, "Home Team": home_teams, "Home XG": home_xgs,
                        "Away XG": away_xgs, "Away Team": away_teams})
matches.to_csv('Matches.csv', index=False, header=True)

total_end_time = time.time()
print("Total code executed in", round((total_end_time - total_start_time) / 60, 2), "minutes")