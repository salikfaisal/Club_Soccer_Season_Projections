# Club_Soccer_Season_Projections

Club_Soccer_Season_Projections utilizes Expected Goals (xG) data and squad quality ratings within an elo-based Monte Carlo model to predict the final standings in 7 major European soccer leagues and the UEFA Champions League. These projections are generated through 10,000 simulations for each competition.

## Overview

Each league's summary includes estimated final positions, points, goal differences, title chances, chances of qualifying for the UEFA Champions League, and relegation possibilities.

These simulations are calculated using a combination of actual league results and simulated matches based on [Elo ratings](https://github.com/salikfaisal/Club_Soccer_Season_Projections/blob/main/Elo%20Ratings%20for%20European%20Clubs.csv). Elo Ratings are weighted based on three different metrics, as shown in the following table:

| Weight | Short Description         | Long Description                                                                                                                   |
| ------ | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 50%    | [Club Elo](http://clubelo.com/) | Club Elo ratings are derived from real match results using the formula provided by [Club Elo](http://clubelo.com/System).        |
| 25%    | Expected Goals            | Expected Goals (xG) ratings utilize a Poisson Distribution model to predict the points exchanged in a match between two teams. These statistics focus on the quality of scoring chances created during a match and do not consider the actual match results. The Expected Goals data is sourced from [fbref.com](https://fbref.com/en/) based on [Opta's](https://www.statsperform.com/opta/) estimation of expected goals. |
| 25%    | Squad Quality             | Squad Quality Metrics are determined by the quality of players within a club. Ratings on a scale of 0 to 100, provided by [footballtransfers.com](https://www.footballtransfers.com/en), are converted into an Elo rating. This rating is combined with other metrics to assess a team's overall strength on paper, considering any boosts from incoming transfers. |

Expect regular updates, typically on a weekly basis, though the frequency may vary depending on the match calendar.

## Simulations Include Results For:

- [UEFA Champions League](https://github.com/salikfaisal/Club_Soccer_Season_Projections/blob/main/UCL_Expected_Results.csv)
- [Premier League (England)](https://github.com/salikfaisal/Club_Soccer_Season_Projections/blob/main/Premier_League_Expected_Results.csv)
- [La Liga (Spain)](https://github.com/salikfaisal/Club_Soccer_Season_Projections/blob/main/La_Liga_Expected_Results.csv)
- [Serie A (Italy)](https://github.com/salikfaisal/Club_Soccer_Season_Projections/blob/main/Serie_A_Expected_Results.csv)
- [Bundesliga (Germany)](https://github.com/salikfaisal/Club_Soccer_Season_Projections/blob/main/Bundesliga_Expected_Results.csv)
- [Ligue 1 (France)](https://github.com/salikfaisal/Club_Soccer_Season_Projections/blob/main/Ligue_1_Expected_Results.csv)
- [Eredivisie (Netherlands)](https://github.com/salikfaisal/Club_Soccer_Season_Projections/blob/main/Eredivisie_Expected_Results.csv)
- [Primeira Liga (Portugal)](https://github.com/salikfaisal/Club_Soccer_Season_Projections/blob/main/Primeira_Liga_Expected_Results.csv)
