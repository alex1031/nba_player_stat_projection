import pandas as pd
import requests, datetime, json, unidecode
from bs4 import BeautifulSoup
import numpy as np

namechange = json.load(open("playernamechange.json", encoding="utf8"))
nbateamnames = json.load(open("nbateamnames.json", encoding="utf8"))
month = datetime.date.today().strftime("%b")
day = datetime.date.today().strftime("%d")
date = month+day

def getRosters():
    # Scrapes roster data from basketball-reference #
    teams=['ATL', 'BOS', 'BRK', 'CHI', 'CHO', 'CLE', 'DAL', 'DEN', 'DET', 'GSW', 'HOU',
    'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN', 'NOP', 'NYK', 'OKC', 'ORL',
    'PHI', 'PHO', 'POR', 'SAC' , 'SAS', 'TOR', 'UTA', 'WAS']

    masterdf = pd.DataFrame(columns=["Player", "Pos", "Team"])
    for team in teams:
        url = 'https://www.basketball-reference.com/teams/{}/2022.html'.format(team)
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", {"class": "sortable stats_table", "id": "roster"})
        table_body = table.find("tbody")

        playerlist = []
        for td in table_body.findAll("td", {"data-stat": "player"}):
            player = unidecode.unidecode(td.text)
            player = player.replace("(TW)", "")
            player = player.rstrip()
            player = player.lower()
            playerlist.append(player)
        
        poslist = []
        for td in table_body.findAll("td", {"data-stat": "pos"}):
            pos = td.text
            pos = pos.strip()
            poslist.append(pos)
        
        df = pd.DataFrame(columns = ["Player", "Pos", "Team"])
        df["Player"] = playerlist
        df["Pos"] = poslist
        # df["Pos"] = df["Pos"].replace(poschange)
        df["Team"] = team.lower()
        masterdf = pd.concat([masterdf, df])

    rosterdict = dict(zip(masterdf.Player,masterdf.Team))
    posdict = dict(zip(masterdf.Player,masterdf.Pos))

    with open("rosterdict.json", "w") as fp:
        json.dump(rosterdict, fp)

    with open("posdict.json", "w") as fp:
        json.dump(posdict, fp)

getRosters()
posdict = json.load(open("posdict.json", encoding="utf-8"))

def getplayerdf(player):
    # Returns Related Statistics to the Model #
    season = 2022
    url = "https://www.basketball-reference.com/leagues/NBA_{}_per_game.html".format(season)
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", {"id": "per_game_stats"})
    link = table.findAll("a")
    for a in link:
        if unidecode.unidecode(a.text).lower() == player: # eliminate all team abbreviations
            addon = a["href"]
    
    newurl = "https://www.basketball-reference.com" + addon[:-5] + "/gamelog/{}".format(season)
    r = requests.get(newurl)
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", id="pgl_basic")
    column_headers = [th.text for th in table.findAll("tr")[0].findAll("th")][1:]
    data_rows = table.findAll("tr")[1:]
    gamedata = [[td.text for td in data_rows[i].findAll("td")] for i in range(len(data_rows))]
    df = pd.DataFrame(gamedata, columns=column_headers)
    df = df[["Tm", "Opp", "MP", "TRB", "AST", "PTS", "PF"]].dropna()
    df = df.reset_index()
    df["TRB"] = df["TRB"].astype("int32")
    df["AST"] = df["AST"].astype("int32")
    df["PTS"] = df["PTS"].astype("int32")

    # Change Minutes Played to decimal #
    min_sec_split = df["MP"].str.split(":", expand=True)
    min_sec_split[0] = min_sec_split[0].astype("int32")
    min_sec_split[1] = min_sec_split[1].astype("int32")
    minutes = min_sec_split[0] + (min_sec_split[1]/60)
    df["MP"] = minutes
    try:
        df["MP"] = round(df["MP"], 1)
    except:
        ("Problem with rounding, moving on")
    
    # Get Stats Per Minute #
    df["RPM"] = df["TRB"] / df["MP"]
    df["APM"] = df["AST"] / df["MP"]
    df["PPM"] = df["PTS"] / df["MP"]

    # Build Dataframe for trial #
    trialdf = pd.DataFrame()
    trialdf["Player"] = [player.lower()]
    trialdf["Team"] = list(df["Tm"])[-1]
    trialdf["Team"] = trialdf["Team"].replace(nbateamnames)
    trialdf["Pos"] = trialdf["Player"].map(posdict)
    trialdf["Median RPM"] = round(df["RPM"].median(), 4)
    trialdf["StDev RPM"] = round(df["RPM"].std(), 4)
    trialdf["Median APM"] = round(df["APM"].median(), 4)
    trialdf["StDev APM"] = round(df["APM"].std(), 4)
    trialdf["Median PPM"] = round(df["PPM"].median(), 4)
    trialdf["StDev PPM"] = round(df["PPM"].std(), 4)

    return trialdf

def dfsCafeMinutes():
    # Scrape projected minutes from dfsCafe #
    url = "https://www.dailyfantasycafe.com/tools/minutes/nba"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    divstr = str(soup.find("div", id="minutes-tool"))
    divstr = divstr.replace("&quot;", "\"")

    begin = divstr.find("data-players=\"")
    end = divstr.find("data-sites")
    cut = divstr[begin+14:end-2]
    
    data = json.loads(cut)
    playerdata = data.get("data")
    playerslist = []
    minuteslist = []

    for player in playerdata:
        name = unidecode.unidecode(player.get("full_name"))
        playerslist.append(name)
        minuteslist.append(player.get("minutes"))
    
    pmindf = pd.DataFrame(columns=["Player", "PMin"])
    pmindf["Player"] = playerslist
    pmindf['Player'] = pmindf['Player'].str.lower()
    pmindf['Player'] = pmindf['Player'].replace(namechange)
    pmindf["PMin"] = minuteslist
    pmindf = pmindf[['Player','PMin']]
    pmindf['PMin'] = pd.to_numeric(pmindf['PMin'])
    pmindf = pmindf.sort_values(by='PMin', ascending=False)

    return pmindf

def getNumFireProjMins():
    # Scrape Projected Minutes from NumberFire #
    url = 'https://www.numberfire.com/nba/daily-fantasy/daily-basketball-projections#_=_'
    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", {"class": "stat-table fixed-head"})
    table_body = table.find("tbody")
    trlist = []
    for tr in table_body.findAll("tr"):
        trlist.append(tr)
    
    players = []
    for row in trlist:
        for a in row.findAll("a", {"class": "full"}):
            playername = a.text.rstrip()
            playername = playername.lstrip()
            players.append(playername)
    
    pmins = []
    for row in trlist:
        for td in row.findAll("td", {"class": "min"}):
            pmin = td.text.rstrip()
            pmin = pmin.lstrip()
            pmins.append(pmin)
    
    pmindict = dict(zip(players, pmins))
    pmindf = pd.DataFrame(list(pmindict.items()), columns=['Player', 'Min'])
    pmindf['Player'] = pmindf['Player'].str.lower()
    pmindf['Player'] = pmindf['Player'].replace(namechange)

    return pmindf

def combineMins():
    # Combining data from dfsCafe and NumberFire #
    try:
        dfsCafe_mins = dfsCafeMinutes()
    except:
        dfsCafe_mins = 0
        print("Problem with DFS Cafe Projections")
    
    try:
        numFire_mins = getNumFireProjMins()
    except:
        print("Problem with Number Fire Projections")

    if len(dfsCafe_mins) == 0:
        dfsCafe_mins = numFire_mins.copy()
        dfsCafe_mins.columns = ["Player", "DC_Mins"]
        print("Problem with DFS Cafe")
    
    if len(numFire_mins) == 0:
        numFire_mins = dfsCafe_mins.copy()
        numFire_mins.columns = ["Player", "NF_Mins", "Team"]
        print("Problem with Number Fire")
    
    minsdf = pd.merge(dfsCafe_mins, numFire_mins, on="Player", how="outer")
    minsdf = minsdf.fillna(0)
    minsdf.columns = ["Player", "DC", "NF"]
    minsdf["DC"] = pd.to_numeric(minsdf["DC"])
    minsdf["NF"] = pd.to_numeric(minsdf["NF"])
    minsdf["Avg"] = minsdf.mean(axis=1, skipna=True, numeric_only=True)
    minsdf["Low"] = minsdf.min(axis=1, skipna=True, numeric_only=True)
    minsdf = minsdf[minsdf["Avg"] >= 20].reset_index()

    return minsdf

def getAverages():
    # Gets Average Points, Rebound and Assists given up by Each Position on Each Team #
    # 8 - Small Forward
    # 9 - Power Forward
    # 10 - Center
    # 11 - Shooting Guard
    # 12 - Point Guard
    season = 22
    position = ["12", "11", "8", "9", "10"]
    dfls = []

    for i in range(len(position)):
        url = "http://www.hoopsstats.com/basketball/fantasy/nba/opponentstats/{}/{}/pts/1-1".format(season, position[i])
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        headline = soup.findAll("table", {"class": "tableheadline"})
        headers = [td.text for td in headline[2].findAll("td")]
        table = soup.findAll("table", {"class": "statscontent"})
        data_rows = [[td.text for td in table[i].findAll("td")] for i in range(len(table))]
        df = pd.DataFrame(data_rows, columns=headers)
        df = df[["Team", "Pts", "Reb", "Ast"]].set_index("Team")
        df["Pts"] = df["Pts"].astype("float64")
        df["Reb"] = df["Reb"].astype("float64")
        df["Ast"] = df["Ast"].astype("float64")

        if position[i] == "12":
            pos = "PG"
        elif position[i] == "11":
            pos = "SG"
        elif position[i] == "8":
            pos = "SF"
        elif position[i] == "9":
            pos = "PF"
        elif position[i] == "10":
            pos = "C"
            
        df = df.rename(columns=lambda x:pos+"_"+x)
        dfls.append(df)

    masterdf = pd.concat(dfls, axis=1).sort_values(by="Team").reset_index()
    leaguepgpts = sum(masterdf["PG_Pts"]) / len(masterdf)
    leaguepgreb = sum(masterdf["PG_Reb"]) / len(masterdf)
    leaguepgast = sum(masterdf["PG_Ast"]) / len(masterdf)
    leaguesgpts = sum(masterdf["SG_Pts"]) / len(masterdf)
    leaguesgreb = sum(masterdf["SG_Reb"]) / len(masterdf)
    leaguesgast = sum(masterdf["SG_Ast"]) / len(masterdf)
    leaguesfpts = sum(masterdf["SF_Pts"]) / len(masterdf)
    leaguesfreb = sum(masterdf["SF_Reb"]) / len(masterdf)
    leaguesfast = sum(masterdf["SF_Ast"]) / len(masterdf)
    leaguepfpts = sum(masterdf["PF_Pts"]) / len(masterdf)
    leaguepfreb = sum(masterdf["PF_Reb"]) / len(masterdf)
    leaguepfast = sum(masterdf["PF_Ast"]) / len(masterdf)
    leaguecpts = sum(masterdf["C_Pts"]) / len(masterdf)
    leaguecreb = sum(masterdf["C_Reb"]) / len(masterdf)
    leaguecast = sum(masterdf["C_Ast"]) / len(masterdf)
    league = {"Team": "League Average", "PG_Pts": round(leaguepgpts, 1), "PG_Reb": round(leaguepgreb, 1), "PG_Ast": round(leaguepgast, 1), "SG_Pts": round(leaguesgpts, 1), 
             "SG_Reb": round(leaguesgreb, 1), "SG_Ast": round(leaguesgast, 1), "SF_Pts": round(leaguesfpts, 1), "SF_Reb": round(leaguesfreb, 1), "SF_Ast": round(leaguesfast, 1),
             "PF_Pts": round(leaguepfpts, 1), "PF_Reb": round(leaguepfreb, 1), "PF_Ast": round(leaguepfast, 1), "C_Pts": round(leaguecpts, 1), "C_Reb": round(leaguecreb, 1),
             "C_Ast": round(leaguecast, 1)}

    masterdf["Team"] = masterdf["Team"].replace(nbateamnames)
    masterdf = masterdf.append(league, ignore_index=True)

    return masterdf

def getTeamPos(df, team, position):

    df = df.set_index("Team")
    poscol = [x for x in df.columns if position in x]
    posdf = df[poscol].reset_index()

    # League Average #
    league = posdf[posdf["Team"] == "League Average"].reset_index()

    # Team Average #
    teamdf = posdf[posdf["Team"] == team].reset_index()
    teamdf = teamdf[["Team", position+"_Pts", position+"_Reb", position+"_Ast"]]
    teamdf.columns = ["Team", "Opp "+position+" Pts", "Opp "+position+" Reb", "Opp "+position+" Ast"]
    teamdf["Pts Adj"] = teamdf["Opp "+position+" Pts"] / league[position+"_Pts"]
    teamdf["Reb Adj"] = teamdf["Opp "+position+" Reb"] / league[position+"_Reb"]
    teamdf["Ast Adj"] = teamdf["Opp "+position+" Ast"] / league[position+"_Ast"]

    return teamdf

def getMatchup():
    # Get Related Betting Information on the Matchup #
    url = 'https://rotogrinders.com/schedules/nba/dfs'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    scripts = soup.findAll("script")
    raw = str(scripts[-1])
    raw = raw.replace("\n", " ")
    begin = raw.find("[")
    end = raw.rfind("}];")
    cut = raw[begin:end+2]
    data = json.loads(cut)

    mykeys = ["team", "opponent", "line", "moneyline", "overunder", "projected"]
    masterdf = pd.DataFrame(columns = ["team", "opponent", "line", "moneyline", "overunder", "projected"])

    for i in range(len(data)):
        team = data[i]
        newdict = {}

        for key, value in team.items():
            if key in mykeys:
                newdict[key] = value
        
        df = pd.DataFrame(newdict, index=[0])
        masterdf = pd.concat([df, masterdf])
    
    masterdf["opponent"] = masterdf["opponent"].str.replace("@ ", "")
    masterdf["opponent"] = masterdf["opponent"].str.replace("vs. ", "")
    masterdf["team"] = masterdf["team"].str.replace("BKN", "BRK")
    masterdf["team"] = masterdf["team"].str.replace("CHA", "CHO")
    masterdf["opponent"] = masterdf["opponent"].str.replace("CHA", "CHO")
    masterdf["opponent"] = masterdf["opponent"].str.replace("BKN", "BRK")
    masterdf["opponent"] = masterdf["opponent"].replace(nbateamnames)
    masterdf["team"] = masterdf["team"].replace(nbateamnames)
    masterdf["line"] = pd.to_numeric(masterdf["line"])
    masterdf["projected"] = pd.to_numeric(masterdf["projected"])

    masterdf = masterdf[['team','opponent','line','moneyline','overunder','projected']]
    masterdf.columns = ["Team", "Opp", "Line", "MoneyLine", "OU", "Proj"]

    return masterdf

def combineAll():
    dfls = []
    mins = combineMins()
    line = getMatchup()
    averages = getAverages()

    oppdict = dict(zip(line.Team, line.Opp))
    for player in list(mins["Player"]):
        print(player)
        try:
            playerdf = getplayerdf(player)
        except:
            print("Error for {}".format(player))
            continue
        
        # Change Team to Opponent Team #
        playerdf["Team"] = playerdf["Team"].map(oppdict)
        try:
            teamdf = getTeamPos(averages, list(playerdf["Team"])[0], list(playerdf["Pos"])[0])
        except:
            print("Error for {}".format(list(playerdf["Team"]))[0])

        try:
            playermin = mins[mins["Player"] == player]
        except:
            print("Error for {} minutes".format(player))
            continue

        if list(playermin["Avg"])[0] >= 20:
            combinedf = playerdf.merge(playermin, on="Player")
            # Get opponent stat adjustments #
            combinedf = combinedf.merge(teamdf, on="Team")

            combinedf = combinedf[["Player", "Team", "Pos", "Avg", "Median RPM", "StDev RPM", "Median APM", "StDev APM", "Median PPM", "StDev PPM", "Reb Adj", "Ast Adj", "Pts Adj"]]
            combinedf.columns = ["Player", "Opponent", "Pos", "Min", "Median RPM", "StDev RPM", "Median APM", "StDev APM", "Median PPM", "StDev PPM", "Reb Adj", "Ast Adj", "Pts Adj"]

            dfls.append(combinedf)
        else:
            print("Skipping {}".format(player))
            continue
    
    return dfls

def playerSim():
    playerls = combineAll()

    trials = 1000
    masterdf = pd.DataFrame()
    # Run Trials #
    for player in playerls:
        rebls = []
        astls = []
        ptsls = []
        try:
            for i in range(trials):
                rpm = np.random.normal(player["Median RPM"], player["StDev RPM"])
                apm = np.random.normal(player["Median APM"], player["StDev APM"])
                ppm = np.random.normal(player["Median PPM"], player["StDev PPM"])
                reb = player["Min"] * rpm * player["Reb Adj"]
                ast = player["Min"] * apm * player["Ast Adj"]
                pts = player["Min"] * ppm * player["Pts Adj"]
                rebls.append(round(list(reb)[0], 1))
                astls.append(round(list(ast)[0], 1))
                ptsls.append(round(list(pts)[0], 1))
        except:
            print("Error")
            continue
        
        dfdict = {"Reb Est": [round(np.mean(rebls), 1)], "Ast Est": [round(np.mean(astls), 1)], "Pts Est": [round(np.mean(ptsls), 1)]}
        df = pd.DataFrame.from_dict(dfdict, )
        df["Player"] = list(player["Player"])[0]
        df["Opponent"] = list(player["Opponent"])[0]
        df["Min"] = list(player["Min"])[0]
        df["Pts+Reb Est"] = df["Pts Est"] + df["Reb Est"]
        df["Pts+Ast Est"] = df["Pts Est"] + df["Ast Est"]
        df["Reb+Ast Est"] = df["Reb Est"] + df["Ast Est"]
        df["Pts+Reb+Ast Est"] = df["Pts+Ast Est"] + df["Reb Est"]
        df = df[["Player", "Opponent", "Min", "Pts Est", "Reb Est", "Ast Est", "Pts+Reb Est", "Pts+Ast Est", "Reb+Ast Est","Pts+Reb+Ast Est"]]
        masterdf = masterdf.append(df, ignore_index=True)
    
    return masterdf

sim = playerSim()
sim = sim.sort_values(by="Opponent")
sim.to_csv("Projections/{}_propsprojection.csv".format(date))