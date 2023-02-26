# NBA Player Stats Projection

This model utilised Monte Carlo Simulation in order to predict an NBA player's stats in their upcoming matchup.
- Predictions were made using the player's projected minutes, their stats per minute (points, rebounds, assists, etc), and
is adjusted based on how many points/rebounds/assists the opponents gives up to the player's respective position.
- A lot of web scraping from different basketball statistic websites were required in order to acquire the necessary data.
- Joining of multiple dataframes were executed. 
- Normal distribution was used to simulate the results. 
- .csv file containing the results was the output. Examples can be found in the Projections file.

## Code and Resources Used
**Python Version**: 3.8.8\
**Packages**: pandas, requests, datetime, json, unidecode, BeautifulSoup, numpy

## Background Information
The idea behind this project was to create a tool where it can used for daily fantasy or betting purposes. Within the fantasy basketball world, one of the 
most important statistic is a player's minutes played, since the player would not be able to produce any meaningful statistic if he isn't even going to touch the court.
A similar idea can also be derived from the stat of a team's defense against a stat from different position, as a player who plays in the Center position
would be tipped to secure more rebounds if the opponent gives up more rebound to a Center. Furthermore, the choice of using stats per minute was an attempt to mitigate 
the effect of a player getting more minutes as a replacement to an injury player, or vice versa.

## Web Scraping
- Data about Projected Minutes were scraped from dfsCafe and NumberFire.
- Roster data and related statistics were scraped from basketball-reference.

## Data Cleaning
Several transformations were required in order to join all the data from different sources:
- Player's names had to be unified as different versions existed on different websites.
- Stats were needed to be adjusted to be per minute.
- Position names were abbreviated (Point Guard -> PG, Shooting Guard -> SG, etc).
- Team names were also required to be abbreviated.
- Missing values from dfsCafe and NumberFire were replaced with value from the other.
- Values were required to be transformed into floats.

## Limitations
Although per minute stats are a way of adjusting to a player getting a sudden inflate or deflate in minutes, it still does not do the best job since the player would
receive different usage due to the change in offensive system. Similarly, the stat of adjusting to opponent defense is less effective if the opponent is missing key
defensive players. This projection would also be significant less accurate in earlier season due to the lack of data. Future improvement for this project could involve
the use of Bayes' infeerence to mitigate that issue. Finally, improvements could be made to adjust for player recent form (perhaps the last 5-10 games) rather than 
using whole season, along with a more sophisticated model which would be likely to produce more accurate and convincing results.
