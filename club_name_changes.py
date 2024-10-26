import pandas as pd

# changes the names of clubs in the original elo ratings
elo_name_changes = {'Brighton': 'Brighton & Hove Albion', 'Leeds': 'Leeds United', 'Leicester': 'Leicester City',
                    'Man City': 'Manchester City', 'Man United': 'Manchester United', 'Newcastle': 'Newcastle United',
                    'Norwich': 'Norwich City', 'Tottenham': 'Tottenham Hotspur', 'West Ham': 'West Ham United',
                    'Wolves': 'Wolverhampton Wanderers', 'Luton': 'Luton Town', 'Stoke': 'Stoke City',
                    'Swansea': 'Swansea City', 'Cardiff': 'Cardiff City', 'Forest': 'Nottingham Forest',
                    'Birmingham': 'Birmingham City', 'Ipswich': 'Ipswich Town', "Hull": "Hull City",
                    'Derby': 'Derby County', 'Blackburn': 'Blackburn Rovers', 'Coventry': 'Coventry City',
                    'West Brom': 'West Bromwich Albion', 'Huddersfield': 'Huddersfield Town',
                    'Preston': 'Preston North End', 'QPR': 'Queens Park Rangers', 'Rotherham': 'Rotherham United',
                    'Plymouth': 'Plymouth Argyle', 'Sheffield Weds': 'Sheffield Wednesday', 'Dundee': 'Dundee United',
                    'Atlético': 'Atlético Madrid', 'Atletico': 'Atlético Madrid', 'Betis': 'Real Betis',
                    'Sociedad': 'Real Sociedad', 'Bilbao': 'Athletic Bilbao', 'Celta': 'Celta Vigo', 'Cadiz': 'Cádiz',
                    'Alaves': 'Alavés', 'Leganes': 'Leganés', 'Depor': 'Deportivo La Coruña', 'Malaga': 'Málaga',
                    'Almeria': 'Almería', 'Petrocub': 'Petrocub Hîncești',
                    'Augsburg': 'FC Augsburg', 'Hertha': 'Hertha BSC', 'Bielefeld': 'Arminia Bielefeld',
                    'Bochum': 'VfL Bochum', 'Dortmund': 'Borussia Dortmund', 'Frankfurt': 'Eintracht Frankfurt',
                    'Freiburg': 'SC Freiburg', 'Fürth': 'Greuther Fürth', 'Fuerth': 'Greuther Fürth',
                    'Hoffenheim': 'TSG Hoffenheim', 'Köln': '1. FC Köln', 'Koeln': '1. FC Köln',
                    'Leverkusen': 'Bayer Leverkusen', 'Mainz': 'Mainz 05', 'Gladbach': 'Borussia Mönchengladbach',
                    'Bayern': 'Bayern Munich', 'Stuttgart': 'VfB Stuttgart', 'Wolfsburg': 'VfL Wolfsburg',
                    'Darmstadt': 'Darmstadt 98', 'Heidenheim': '1. FC Heidenheim', 'Hamburg': 'Hamburger SV',
                    'Hannover': 'Hannover 96', 'Werder': 'Werder Bremen', 'Schalke': 'Schalke 04',
                    'Duesseldorf': 'Fortuna Düsseldorf', 'Nuernberg': '1. FC Nürnberg', 'Paderborn': 'SC Paderborn',
                    'Inter': 'Inter Milan', 'Internazionale': 'Inter Milan', 'Milan': 'AC Milan', 'Spal': 'SPAL',
                    'Verona': 'Hellas Verona', 'Mlada Boleslav': 'Mladá Boleslav', 'Paphos': 'Pafos',
                    'Saint-Etienne': 'Saint-Étienne', 'Paris SG': 'Paris Saint-Germain', 'Nimes': 'Nîmes',
                    'Brugge': 'Club Brugge',
                    'Sporting': 'Sporting CP', 'Salzburg': 'RB Salzburg',
                    'Shakhtar': 'Shakhtar Donetsk', 'FC Kobenhavn': 'Copenhagen', 'Viktoria Plzen': 'Viktoria Plzeň',
                    'Olympiakos': 'Olympiacos', 'Besiktas': 'Beşiktaş', 'Spartak Moskva': 'Spartak Moscow',
                    'CSKA Moskva': 'CSKA Moscow', 'Karabakh Agdam': 'Qarabağ', 'Crvena Zvezda': 'Red Star Belgrade',
                    'AEK': 'AEK Athens', 'Lok Moskva': 'Lokomotiv Moscow', 'Slavia Praha': 'Slavia Prague',
                    'Bueyueksehir': 'İstanbul Başakşehir', 'FC Krasnodar': 'Krasnodar', 'Ferencvaros': 'Ferencváros',
                    'Malmoe': 'Malmö FF', 'Steaua': 'FCSB', 'Beer-Sheva': "Hapoel Be'er Sheva",
                    'Zorya': 'Zorya Luhansk', 'Apollon Lemesos': 'Apollon Limassol', 'Tescoma Zlin': 'Zlín',
                    'FK Astana': 'Astana', 'Razgrad': 'Ludogorets Razgrad', 'M Tel Aviv': 'Maccabi Tel Aviv',
                    'Ostersund': 'Östersunds FK', 'Skenderbeu': 'Skënderbeu', 'BATE': 'BATE Borisov',
                    'Setubal': 'Vitória de Setúbal', 'Den Haag': 'ADO Den Haag', 'Maritimo': 'Marítimo',
                    'Alkmaar': 'AZ', 'Venlo': 'VVV-Venlo', 'Breda': 'NAC Breda',
                    'Belenenses': 'B-SAD', 'Fenerbahce': 'Fenerbahçe', 'Akhisar': 'Akhisarspor',
                    'Dudelange': 'F91 Dudelange', 'Videoton': 'Fehérvár', 'Larnaca': 'AEK Larnaca',
                    'Standard': 'Standard Liège', 'Zuerich': 'Zürich', 'Sarpsborg': 'Sarpsborg 08',
                    'Vorskla': 'Vorskla Poltava', 'Pacos Ferreira': 'Paços de Ferreira', 'Olexandriya': 'Oleksandriya',
                    'Wolfsberg': 'Wolfsberger AC', 'Lech': 'Lech Poznań', 'Sparta Praha': 'Sparta Prague',
                    'Lincoln': 'Lincoln Red Imps', 'HJK Helsinki': 'HJK', 'Flora Tallinn': 'Flora',
                    'Brondby': 'Brøndby', 'Legia': 'Legia Warsaw', 'Slovacko': 'Slovácko',
                    'Shamrock': 'Shamrock Rovers',
                    'Zalgiris Vilnius': 'Žalgiris', 'Djurgarden': 'Djurgårdens IF', 'Guimaraes': 'Vitória de Guimarães',
                    'Lustenau': 'Austria Lustenau', 'Sittard': 'Fortuna Sittard',
                    'Almere': 'Almere City', 'Famalicao': 'Famalicão', 'Lausanne': 'Lausanne-Sport',
                    'Cukaricki': 'Čukarički', 'Levski': 'Levski Sofia', 'CSKA 1948 Sofia': 'CSKA 1948',
                    'St Gillis': 'Union SG', 'Leuven': 'OH Leuven', 'Haecken': 'BK Häcken', 'Goeteborg': 'IFK Göteborg',
                    'Viitorul': 'Farul Constanța', 'Rapid Bucuresti': 'Rapid București',
                    'Craiova': 'Universitatea Craiova', 'Sepsi': 'Sepsi OSK', 'Grasshoppers': 'Grasshopper',
                    'Bodoe Glimt': 'Bodø/Glimt', 'Valerenga': 'Vålerenga', 'Rackow': 'Raków Częstochowa',
                    'Lubin': 'Zagłębie Lubin', 'Odense': 'OB', 'Hajduk': 'Hajduk Split', 'Dnipro': 'Dnipro-1',
                    'Hearts': 'Heart of Midlothian', 'StGallen': 'St. Gallen', 'Rakow': 'Raków Częstochowa',
                    'Estrela Amadora': 'Estrela da Amadora', 'Nijmegen': 'NEC', 'Zwolle':
                    'PEC Zwolle', 'Waalwijk': 'RKC Waalwijk', 'Backa Topola': 'TSC', 'Dunajska': 'DAC Dunajská Streda',
                    'Klaksvik': 'KÍ', 'Breidablik': 'Breiðablik', 'Nordsjaelland': 'Nordsjælland',
                    'Pogon': 'Pogoń Szczecin', 'Lillestrom': 'Lillestrøm', 'Oxford': 'Oxford United',
                    'AVS Futebol': 'AVS', 'Holstein': 'Holstein Kiel', 'St. Pauli': 'FC St. Pauli',
                    'St Pauli': 'FC St. Pauli', 'Heracles': 'Heracles Almelo', 'PSV': 'PSV Eindhoven',
                    'Víkingur': 'Víkingur Reykjavík'
                    }

# changes the name of clubs from the Football Transfers website
football_transfers_name_changes = {'Milan': 'AC Milan', 'Atlético de Madrid': 'Atlético Madrid',
                                   'Bayer 04 Leverkusen': 'Bayer Leverkusen', 'Stade Rennais': 'Rennes',
                                   'Real Betis Balompié': 'Real Betis', 'Olympique Marseille': 'Marseille',
                                   'LOSC Lille': 'Lille', 'Ajax Amsterdam': 'Ajax',
                                   '1.FC Union Berlin': 'Union Berlin', 'Celta de Vigo': 'Celta Vigo',
                                   'Olympique Lyon': 'Lyon', 'Bologna FC 1909': 'Bologna', 'Augsburg': 'FC Augsburg',
                                   'Udinese Calcio': 'Udinese', 'Freiburg': 'SC Freiburg', '1.FSV Mainz 05': 'Mainz 05',
                                   'Stade Reims': 'Reims', 'Feyenoord Rotterdam': 'Feyenoord',
                                   'Red Bull Salzburg': 'RB Salzburg', '1.FC Köln': '1. FC Köln',
                                   'Salernitana 1919': 'Salernitana', 'Strasbourg Alsace': 'Strasbourg',
                                   'Stade Brestois 29': 'Brest', 'Clermont Foot 63': 'Clermont',
                                   'Vitória Guimarães': 'Vitória de Guimarães', 'Deportivo Alavés': 'Alavés',
                                   'Cagliari Calcio': 'Cagliari', 'Vitesse Arnhem': 'Vitesse',
                                   'Frosinone Calcio': 'Frosinone', '1.FC Heidenheim 1846': '1. FC Heidenheim',
                                   'Estoril Praia': 'Estoril', 'Excelsior Rotterdam': 'Excelsior',
                                   'Royal Antwerp': 'Antwerp', 'Olympiacos Piraeus': 'Olympiacos',
                                   'Panathinaikos Athens': 'Panathinaikos', 'PAOK Thessaloniki': 'PAOK',
                                   'Royale Union Saint Gilloise': 'Union SG', 'Malmö': 'Malmö FF',
                                   'Ferencvárosi': 'Ferencváros', 'Basel 1893': 'Basel',
                                   'Partizan Belgrade': 'Partizan', 'Häcken': 'BK Häcken',
                                   'St. Gallen 1879': 'St. Gallen', 'Djurgårdens': 'Djurgårdens IF',
                                   'CSKA-Sofia': 'CSKA Sofia', 'Grasshopper Club Zurich': 'Grasshopper',
                                   'Göteborg': 'IFK Göteborg', 'Solna': 'AIK',
                                   '1904 Dunajská Streda': 'DAC Dunajská Streda', 'TSC Backa Topola': 'TSC',
                                   'Sint-Truidense': 'Sint-Truiden', 'Norrköping': 'IFK Norrköping',
                                   'Budapest': 'MTK', 'Crete': 'OFI', 'Atromitos Athens': 'Atromitos',
                                   'Bröndby': 'Brøndby', 'Rakow Czestochowa': 'Raków Częstochowa',
                                   'Oud-Heverlee Leuven': 'OH Leuven', 'Lech Poznan': 'Lech Poznań',
                                   'Farul Constanta': 'Farul Constanța', 'Viktoria Plzen': 'Viktoria Plzeň',
                                   'Rapid 1923': 'Rapid București', 'Legia Warszawa': 'Legia Warsaw',
                                   'Zorya Lugansk': 'Zorya Luhansk', 'Vålerenga Fotball': 'Vålerenga',
                                   'Rapid Vienna': 'Rapid Wien', 'Sepsi OSK Sf. Gheorghe': 'Sepsi OSK',
                                   'Zaglebie Lubin': 'Zagłębie Lubin', 'Odense Boldklub': 'OB', 'AZ Alkmaar': 'AZ',
                                   'Nijmegen': 'NEC', 'Zwolle': 'PEC Zwolle',
                                   'Waalwijk': 'RKC Waalwijk', 'Nordsjaelland': 'Nordsjælland',
                                   'Pogon Szczecin': 'Pogoń Szczecin', '1899 Hoffenheim': 'TSG Hoffenheim',
                                   'Tottenham': 'Tottenham Hotspur', 'Wolves': 'Wolverhampton Wanderers',
                                   "Gladbach": 'Borussia Mönchengladbach', 'Preston': 'Preston North End',
                                   'Sheff Wed': 'Sheffield Wednesday', 'SM Caen': 'Caen', 'Parma Calcio 1913': 'Parma',
                                   'Oxford': 'Oxford United', 'AVS Futebol SAD': 'AVS', 'Holstein': 'Holstein Kiel',
                                    'St. Pauli': 'FC St. Pauli', 'Como 1907': 'Como', 'Sheff Utd': 'Sheffield United',
                                   'Espanyol Barcelona': 'Espanyol', 'AJ Auxerre': 'Auxerre', 'CD Leganés': 'Leganés',
                                   'UC Sampdoria': 'Sampdoria', 'Angers SCO': 'Angers',
                                   'Deportivo de La Coruña': 'Deportivo La Coruña', 'Levante UD': 'Levante',
                                   'CD Santa Clara': 'Santa Clara', "1.FC Nürnberg": "1. FC Nürnberg",
                                   "Real Valladolid": 'Valladolid', 'Real Zaragoza': 'Zaragoza',
                                   'Real Oviedo': 'Oviedo', 'Spezia Calcio': 'Specia', 'Heracles': 'Heracles Almelo'
                                   }
# changes the name of Clubs on the WikiTable
wiki_name_changes = {'Paris SG': 'Paris Saint-Germain', 'PSV': 'PSV Eindhoven', 'Milan': 'AC Milan'}

# changes the name of clubs on the Football Reference website
fbref_name_changes = {'Paris S-G': 'Paris Saint-Germain', 'Brighton': 'Brighton & Hove Albion',
                      'Newcastle Utd': 'Newcastle United', 'Manchester Utd': 'Manchester United',
                      'Wolfsburg': 'VfL Wolfsburg', 'Hoffenheim': 'TSG Hoffenheim', 'Inter': 'Inter Milan',
                      'Freiburg': 'SC Freiburg', "M'Gladbach": 'Borussia Mönchengladbach',
                      'La Coruña': 'Deportivo La Coruña', 'Athletic Club': 'Athletic Bilbao',
                      'Tottenham': 'Tottenham Hotspur', 'Köln': '1. FC Köln', 'Betis': 'Real Betis',
                      'Eint Frankfurt': 'Eintracht Frankfurt', 'Stuttgart': 'VfB Stuttgart', 'Augsburg': 'FC Augsburg',
                      'Dortmund': 'Borussia Dortmund', 'Leverkusen': 'Bayer Leverkusen', 'Milan': 'AC Milan',
                      'West Ham': 'West Ham United', 'NK Maribor': 'Maribor', 'Shakhtar': 'Shakhtar Donetsk',
                      'APOEL FC': 'APOEL', 'Qarabağ FK': 'Qarabağ', 'Wolves': 'Wolverhampton Wanderers',
                      'Düsseldorf': 'Fortuna Düsseldorf', 'Red Star': 'Red Star Belgrade',
                      'Loko Moscow': 'Lokomotiv Moscow', 'Sheffield Utd': 'Sheffield United',
                      'Paderborn 07': 'SC Paderborn', 'Arminia': 'Arminia Bielefeld',
                      'Başakşehir': 'İstanbul Başakşehir', 'Clermont Foot': 'Clermont', 'Bochum': 'VfL Bochum',
                      'Malmö': 'Malmö FF', "Nott'ham Forest": 'Nottingham Forest', 'FC Copenhagen': 'Copenhagen',
                      'Vitória': 'Vitória de Guimarães', 'FK Vardar': 'Vardar', "Be'er Sheva": "Hapoel Be'er Sheva",
                      'Fastav Zlín': 'Zlín', 'FC Astana': 'Astana', 'Astana FK': 'Astana',
                      'Ludogorets': 'Ludogorets Razgrad', 'Östersund': 'Östersunds FK',
                      'Skënderbeu Korçë': 'Skënderbeu', 'Rotherham Utd': 'Rotherham United',
                      'Charlton Ath': 'Charlton Athletic', "P'borough Utd": 'Peterborough United',
                      'Vitória Setúbal': 'Vitória de Setúbal', 'AÉK Lárnaka': 'AEK Larnaca', 'Qarabağ Ağdam': 'Qarabağ',
                      'Apollon': 'Apollon Limassol', "Sparta R'dam": 'Sparta Rotterdam',
                      'Gil Vicente FC': 'Gil Vicente', 'Paços': 'Paços de Ferreira', 'FC Oleksandriya': 'Oleksandriya',
                      'Wycombe': 'Wycombe Wanderers', 'Go Ahead Eag': "Go Ahead Eagles", 'NŠ Mura': 'Mura',
                      'Red Imps': 'Lincoln Red Imps', 'Qaırat Almaty': 'Kairat', 'SK Dnipro-1': 'Dnipro-1',
                      'Shamrock Rov': 'Shamrock Rovers', 'KF Ballkani Therandë': 'Ballkani', 'FK Rīgas FS': 'RFS',
                      'Djurgården': 'Djurgårdens IF', 'Blackburn': 'Blackburn Rovers', 'Pafos FC': 'Pafos',
                      'Huddersfield': 'Huddersfield Town', 'West Brom': 'West Bromwich Albion',
                      'Preston': 'Preston North End', 'Sheffield Weds': 'Sheffield Wednesday',
                      'QPR': 'Queens Park Rangers', 'Hearts': 'Heart of Midlothian', 'Vidi': 'Fehérvár',
                      'Estrela': 'Estrela da Amadora', 'Heidenheim': '1. FC Heidenheim', 'AZ Alkmaar': 'AZ',
                      'NEC Nijmegen': 'NEC', 'Zwolle': 'PEC Zwolle', 'Waalwijk': 'RKC Waalwijk',
                      'Olimpija': 'Olimpija Ljubljana', 'TSC Bačka Top': 'TSC',
                      'Aris Limassol FC': 'Aris Limassol', 'Häcken': 'BK Häcken', 'Servette FC': 'Servette',
                      'RKS Raków': 'Raków Częstochowa', 'AVS Futebol': 'AVS', 'Petrocub': 'Petrocub Hîncești',
                      'Gladbach': 'Borussia Mönchengladbach', 'St. Pauli': 'FC St. Pauli',
                      "Nürnberg": '1. FC Nürnberg', 'NK Celje': 'Celje', 'FC Noah': 'Noah', 'Larne FC': 'Larne',
                      'KV': 'Víkingur Reykjavík'
                      }

# These are lists that contain data for clubs that were not able to be found in the Elo Ratings from 8/1/2017
xg_missing_club_names = ['Mallorca', 'SC Paderborn', 'Lecce', 'Elche', 'Monza', 'Wigan Athletic', 'Blackburn Rovers',
                         'Luton Town', 'Coventry City', 'Wycombe Wanderers', 'Rotterham United', 'Charlton Athletic',
                         'Blackpool', 'Famalicão', 'Casa Pia', 'Gil Vicente', 'Vizela', 'Go Ahead Eagles',
                         'RKC Waalwijk', 'Arouca', 'Farense', 'NEC', 'Nacional', 'Emmen', 'AC Omonia',
                         'Cambuur', 'Mura', 'Volendam', 'Spartak Trnava', 'Ballkani', 'Anorthosis', 'Fortuna Sittard',
                         'De Graafschap', 'Santa Clara', 'Bodø/Glimt', 'RFS', 'Dnipro-1', 'Union SG',
                         'Peterborough United', 'Plymouth Argyle', 'Estrela da Amadora', 'Almere City', 'TSC',
                         'Dunajska', 'KÍ', 'Breiðablik', 'Servette', 'Aris Limassol', 'Raków Częstochowa',
                         'Oxford United', 'Portsmouth', 'AVS', 'Como', 'Cercle Brugge', 'Westerlo', 'Rotherham United',
                         'Polissya Zhytomyr', 'OH Leuven', 'Rapid București', 'Larne', 'Noah', 'Borac Banja Luka',
                         'Víkingur Reykjavík', 'Petrocub Hîncești', 'Pafos']

xg_missing_club_countries = ['ESP', 'GER', 'ITA', 'ESP', 'ITA', 'ENG', 'ENG', 'ENG', 'ENG', 'ENG', 'ENG', 'ENG', 'ENG',
                             'POR', 'POR', 'POR', 'POR', 'NED', 'NED', 'POR', 'POR', 'NED', 'POR', 'NED', 'CYP', 'NED',
                             'SVN', 'NED', 'SLK', 'KOS', 'CYP', 'NED', 'NED', 'POR', 'NOR', 'LAT', 'UKR', 'BEL', 'ENG',
                             'ENG', 'POR', 'NED', 'SRB', 'SLK', 'FAR', 'ISL', 'SUI', 'CYP', 'POL', 'ENG', 'ENG', 'POR',
                             'ITA', 'BEL', 'BEL', 'ENG', 'UKR', 'BEL', 'ROM', 'NIR', 'ARM', 'BIH', 'ISL', 'MOL', 'CYP']

# These Elo Ratings were determined by looking at the closest Rating to when the Club's Rating is in use
xg_missing_club_elo_ratings = [1501.40551758, 1357.40759277, 1373.2545166, 1470.01879883, 1386.21459961, 1374.68078613,
                               1374.68078613, 1418.29626465, 1356.68652344, 1356.68652344, 1374.68078613, 1418.28491211,
                               1443.22253418, 1382.99597168, 1399.82580566, 1382.99597168, 1359.59082031, 1295.49084473,
                               1320.58068848, 1359.26000977, 1351.43603516, 1295.49084473, 1360.27355957, 1275.10205078,
                               1459.00878906, 1295.49084473, 1161.25476074, 1380.20788574, 1384.20422363, 1014.16369629,
                               1445.86584473, 1275.10205078, 1275.10205078, 1360.27355957, 1180.12976074, 1128.54516602,
                               1350.01940918, 1315.92456055, 1443.22253418, 1423.65393066, 1405.84973145, 1404.53405762,
                               1131.38134766, 1344.78076172, 910.591674805, 1162.21923828, 1358.60681152, 1395.20166016,
                               1222.75012207, 1514, 1383, 1382, 1366.520874, 1360.163, 1315.925, 1374.681, 1261.217,
                               1367, 1209.880737, 1046.7, 1098, 1264.19, 1154.97, 1207, 1450.38
]

xg_missing_club_df = pd.DataFrame({"Rank": 'None', "Club": xg_missing_club_names, "Country": xg_missing_club_countries,
                                   "Level": "None", "Elo": xg_missing_club_elo_ratings, "From": '2017-08-01',
                                   "To": '2017-08-01'})
