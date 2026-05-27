"""Injecte les fiches IA en français rédigées manuellement pour les 33 sociétés
manquantes (URW, Roche, Airbus, Porsche…). Pas d'API, pas de Claude CLI.
"""
import json
from pathlib import Path

CACHE = Path("outputs/_cache/clement.json")
SNAP = Path("app/static/screener-clement/clement-data.json")

# (tk, ctry) → fiche
FICHES = {
    ("URW", "FR"): {
        "activite": "Foncière européenne leader de l'immobilier commercial premium, propriétaire et exploitant de 66 centres commerciaux de destination (dont 41 sous l'enseigne Westfield) répartis entre l'Europe et les États-Unis. Attire plus de 900 millions de visiteurs annuels. Portefeuille de 49 Md€ d'actifs sous gestion.",
        "contexte": "Reprise post-Covid solide : chiffre d'affaires stable à 3,06 Md€ et résultat net redressé de 0,18 à 1,27 Md€ sur 3 ans. Cession progressive des actifs US (plan de désengagement Westfield) et retour à la croissance du loyer organique en Europe. Cours en forte hausse (+158% sur 3 ans).",
        "chiffres_decodes": "P/E forward 10,4× attractif pour une foncière au cycle haussier. Marge EBITDA structurellement élevée à 64% (classique pour les REIT). ROE de 7,1% modéré, contraint par le levier sectoriel. Rendement 4,61% issu d'un dividende récemment rétabli (4,50€/action en 2026) après l'arrêt pandémique.",
        "catalyseurs": "Poursuite du recyclage de capital via cessions US et réinvestissement dans la dette à coût bas. Pricing power confirmé sur les loyers premium. Catalyseurs macro : baisse des taux longs qui revalorise mécaniquement les NAV des foncières et amplifie l'écart de rendement vs souverain.",
        "particulier": "Exposition au retail premium européen avec rendement attractif rétabli. Convient au portefeuille long terme cherchant un revenu défensif corrélé à l'inflation. Sensibilité élevée aux taux d'intérêt : positions à graduer. Le profil REIT plafonne le score 'crème' à 5/7 par construction (EBITDA et levier non applicables au modèle foncière)."
    },
    ("TEMN", "CH"): {
        "activite": "Éditeur suisse de logiciels bancaires (core banking) leader européen, fournissant les systèmes d'information transactionnels à plus de 3 000 institutions financières dans 150 pays. Plateforme Transact gère les opérations de banque de détail, privée et corporate. Modèle SaaS en transition accélérée.",
        "contexte": "Croissance solide du chiffre d'affaires (0,87→1,00 Md€ en 3 ans, +5%/an) avec un résultat net qui plus que double (0,11→0,26 Md€). Marge EBITDA premium à 26%. ROE exceptionnel de 53% reflétant un modèle capital-light. Levier maîtrisé à 1,37× EBITDA.",
        "chiffres_decodes": "P/E forward 16,9× raisonnable pour un éditeur SaaS au modèle récurrent. La marge EBITDA 26% et le ROE 53% témoignent d'une efficacité opérationnelle remarquable. Rendement modéré 2,08% sans politique généreuse, le management privilégiant la réinvestissement.",
        "catalyseurs": "Migration cloud des banques de second rang (TAM en expansion) et adoption croissante des architectures composables. Cycle de remplacement des core bancaires legacy (mainframes 30+ ans) qui pousse les renouvellements contractuels. Possibilité de réaccélération du momentum commercial post-restructuration.",
        "particulier": "Modèle qualité dans un secteur de niche technologique critique. Valorisation modérée pour la qualité offerte. Convient au portefeuille croissance-qualité tolérant à la volatilité des éditeurs européens. Surveiller la décélération éventuelle des contrats neufs."
    },
    ("P911", "DE"): {
        "activite": "Constructeur automobile premium allemand, filiale cotée du groupe Volkswagen. Positionnement luxe sportif avec les modèles 911, Cayenne, Macan et Taycan électrique. Présence mondiale équilibrée Europe / Amérique du Nord / Chine. Marge premium structurellement supérieure aux constructeurs de masse.",
        "contexte": "Contre-performance marquée : chiffre d'affaires en repli (37,6→36,3 Md€), EBITDA quasi divisé par deux (10,2→5,6 Md€) et résultat net effondré (4,96→0,43 Md€). Difficultés en Chine (-30% de volumes premium), retards Taycan et coûts de transition électrique. Cours divisé par 2 sur 3 ans.",
        "chiffres_decodes": "P/E TTM 97× reflète l'effondrement du bénéfice, mais le forward 19,8× anticipe un redressement marqué. Marge EBITDA tombée à 6,8% (vs ≥15% historique). ROE 0,8% bouge sur un plancher cyclique. Dette nette 0,93× EBITDA maîtrisée. Rendement 5% rebond technique post-baisse du cours.",
        "catalyseurs": "Lancement Macan électrique et 718 BEV (2026-2027). Stabilisation de la demande chinoise et reprise du mix premium. Restructuration coûts annoncée par le management. Effet base favorable sur 2026 face à 2025 catastrophique.",
        "particulier": "Pari de retournement sur une marque de luxe au pricing power intact. Risque cyclique élevé (auto + Chine + transition électrique) et execution non garantie. Réservé aux investisseurs tolérant la volatilité et patients sur 2-3 ans. Pas un fond de portefeuille de tout repos."
    },
    ("AIR", "DE"): {
        "activite": "Géant aéronautique européen leader mondial du secteur civil avec ~60% de parts du marché des avions commerciaux face à Boeing. Activités complémentaires : hélicoptères (Airbus Helicopters), défense & spatial (Airbus Defence and Space). Carnet de commandes record dépassant 10 ans de production.",
        "contexte": "Croissance soutenue : chiffre d'affaires +25% en 3 ans (58,8→73,4 Md€), EBITDA +25% (8,2→10,3 Md€) et résultat net +23% (4,25→5,22 Md€). Trésorerie nette positive (-0,53× EBITDA = net cash). ROE 19,7% solide. Cours +76% sur la période, reflétant la reprise des livraisons post-Covid.",
        "chiffres_decodes": "P/E TTM 27× et forward 36× élevés pour un industriel, justifiés par la visibilité multi-annuelle du carnet de commandes et le quasi-monopole sur les avions monocouloirs (A320neo). Marge EBITDA 10,6% en amélioration. Position cash nette = solidité bilancielle exceptionnelle dans le secteur.",
        "catalyseurs": "Montée en cadence A320neo (50→75 unités/mois ciblée 2027) et déploiement A321XLR. Marché aviation civile structurellement porteur (croissance trafic +4%/an). Boeing toujours fragilisé (problèmes qualité 737 MAX) ouvre des parts de marché. Cycles défense favorables (budgets européens en hausse).",
        "particulier": "Champion industriel européen avec visibilité rare et bilans sains. Convient au cœur de portefeuille long terme exposé à l'aéronautique civile et la défense. Valorisation premium qui exige une exécution irréprochable. Cycle d'investissement long mais visible."
    },
    ("DSFIR", "NL"): {
        "activite": "Acteur néerlandais des ingrédients de spécialité issu de la fusion 2023 entre DSM (vitamines, nutrition animale) et Firmenich (arômes & parfums). Présence dans la nutrition humaine et animale, l'aromathérapie premium et les ingrédients cosmétiques. Restructuration stratégique en cours.",
        "contexte": "Croissance modeste du chiffre d'affaires (8,4→9,0 Md€) avec un EBITDA en forte amélioration (1,31→3,76 Md€) après l'intégration. Résultat net contrarié à -1,08 Md€ par les charges de restructuration. Cours en baisse de 24% sur 3 ans, marché incrédule sur la création de valeur du deal.",
        "chiffres_decodes": "P/E forward 18× cohérent post-restructuration. Marge EBITDA 15,9% en redressement (vers 20% cible). ROE 1,7% pénalisé par les exceptionnels. Dette/EBITDA 0,81× saine. Rendement 3,51% issu du dividende rétabli après cession des activités animales (~3 Md€).",
        "catalyseurs": "Cession 2025-2026 du pôle Nutrition Animale (deal ~3 Md€ vers Adisseo/CVC) qui simplifie le portfolio. Synergies fusion (~500 M€/an ciblé). Reprise du cycle des arômes & parfums post-déstockage. Levier bilanciel pour rachat d'actions.",
        "particulier": "Pari sur la création de valeur du recentrage sur les arômes & parfums premium. Patience requise (12-18 mois) pour matérialisation des synergies. Convient au portefeuille value-cyclique exposé à l'ingrédient de spécialité. Risque d'exécution majeur."
    },
    ("HLN", "GB"): {
        "activite": "Pure player mondial de la santé grand public (consumer health) issu du spin-off GSK 2022, propriétaire de marques iconiques : Sensodyne, Voltaren, Panadol, Otrivin, Centrum. Présence dans 100+ pays avec un portefeuille équilibré OTC (antalgiques, soins dentaires, vitamines, troubles respiratoires).",
        "contexte": "Croissance organique modérée (12,7→12,9 Md€ sur 3 ans) mais accélération du résultat net (1,24→1,95 Md€, +57%). Marge EBITDA 24,9% premium pour la consommation défensive. Levier 2,56× hérité du carve-out qui se réduit progressivement.",
        "chiffres_decodes": "P/E forward 15,2× modéré pour un consumer staple de qualité. ROE 10,3% encore limité par les goodwill du spin-off. Rendement 2,08% en hausse depuis le démarrage en bourse. Marge EBITDA 25% au standard sectoriel (Reckitt, Procter…).",
        "catalyseurs": "Désendettement continu vers 2× EBITDA (allègera le PER). Pricing power sur les marques en croissance (Sensodyne dans le dentaire premium). M&A bolt-on sur le naturel et le bien-être. Cession possible de marques mineures pour simplifier le portfolio.",
        "particulier": "Valeur défensive de qualité avec exposition mondiale à la consommation santé. Croissance lente mais visible et marges premium. Convient au cœur de portefeuille rendement-qualité long terme. Profil 'compounder' attendu sur 5-10 ans."
    },
    ("ROP", "CH"): {
        "activite": "Géant pharmaceutique suisse leader mondial dans l'oncologie, le diagnostic médical et les neurosciences. Portefeuille de blockbusters (Tecentriq, Hemlibra, Ocrevus) et division diagnostic première mondiale. R&D pipeline parmi les plus prolifiques du secteur. Présence globale équilibrée.",
        "contexte": "Léger tassement du chiffre d'affaires (69,1→66,5 Md€) lié à la fin des Covid testing, mais EBITDA stable à 23,3 Md€ et résultat net constant à 13,5 Md€. Marge EBITDA exceptionnelle 38%, ROE remarquable 37%. Endettement modéré 1,17× EBITDA.",
        "chiffres_decodes": "P/E forward 15,2× attractif pour un pharma blue chip. Marge EBITDA 38% reflète la franchise oncologie premium. ROE 37% témoigne d'un modèle économique exceptionnel. Note technique : ce ticker (bons de participation non-votants) affiche un dividende nul Yahoo — donnée à compléter (Roche RO.SW est le titre canonique).",
        "catalyseurs": "Lancements 2026-2027 : trontinemab (Alzheimer), giredestrant (sein), elinzanetant (ménopause). Acquisitions ciblées en obésité (Roche-Carmot). Cycle de renouvellement dans les diagnostics moléculaires. Potentiel pipeline oncologie next-gen.",
        "particulier": "Champion pharma européen avec moat exceptionnel et pipeline pléthorique. Convient au cœur de portefeuille défensif-qualité long terme. Valorisation raisonnable post-correction. Catalyseur Alzheimer potentiellement majeur en 2026-2027."
    },
    ("SHELL", "GB"): {
        "activite": "Major pétro-gazière intégrée britannique (ex-Royal Dutch Shell), troisième mondiale par capitalisation. Présence amont (E&P), aval (raffinage, distribution), GNL leader mondial et activités énergies renouvelables croissantes. Restructuration stratégique 2024 sous le CEO Wael Sawan privilégiant rendement actionnaire vs transition énergétique précipitée.",
        "contexte": "Cycle baissier après le pic 2022 : chiffre d'affaires 351→246 Md€, EBITDA 83→49 Md€, résultat net 39→16 Md€ (normalisation post-choc prix gaz). Marge EBITDA 18% saine. Bilan exceptionnel : dette/EBITDA 0,32×. Cours +196% sur 3 ans malgré la normalisation.",
        "chiffres_decodes": "P/E forward 9,6× très attractif typique des majors pétrolières (marché les valorise toujours avec décote 'transition'). Marge EBITDA 18% du secteur. Rendement 3,4% en hausse avec un programme massif de rachat d'actions (~3-4 Md$/trim). ROE 10,7% solide.",
        "catalyseurs": "Programme rachats actions agressif maintenu (~15 Md$/an). Discipline capex annoncée et focus sur projets à haute marge. Reprise des prix gaz/GNL en hiver 2026-2027. Possible scission/cession des actifs renouvelables non-rentables.",
        "particulier": "Major pétrolière de qualité avec discipline capitalistique reconnue. Rendement actionnaire élevé (dividende + buybacks ≈ 8-10%). Convient au portefeuille value-rendement avec horizon 3-5 ans. Exposition assumée aux énergies fossiles."
    },
    ("SDZ", "CH"): {
        "activite": "Leader mondial des médicaments génériques et biosimilaires, spin-off de Novartis depuis 2023. Portefeuille de 1500+ génériques et 8 biosimilaires commercialisés (dont copies de Humira, Rituximab). Présence dans 100+ pays avec position dominante en Europe.",
        "contexte": "Croissance solide post-spin-off : chiffre d'affaires +20% (8,6→10,3 Md€), EBITDA stable autour de 1,8 Md€ et résultat net en légère hausse (0,78→0,84 Md€). Marge EBITDA 17% standard du générique. Cours doublé depuis le démarrage en bourse (+111%).",
        "chiffres_decodes": "P/E forward 17,6× raisonnable pour un acteur en repositionnement vers les biosimilaires. Marge EBITDA 17% conforme au secteur générique (pas premium). ROE 10,4% modéré. Levier 1,79× EBITDA hérité du carve-out, désendettement en cours.",
        "catalyseurs": "Cascade de lancements biosimilaires 2026-2028 (Stelara, Eylea, Prolia). Migration mix produits vers biosimilaires (marge 25-30% vs 12-15% pour générique pur). Possible M&A bolt-on dans les biosimilaires complexes. Cycle de renouvellement post-carve-out terminé.",
        "particulier": "Pari de croissance qualitative via la transition vers les biosimilaires premium. Convient au portefeuille croissance-santé tolérant 2-3 ans de transition. Sensibilité aux pricing pressures sur génériques traditionnels mais opportunité réelle sur biosimilaires."
    },
    ("SUNB", "GB"): {
        "activite": "Acteur leader mondial de la location d'équipements industriels et de construction (Sunbelt Rentals), particulièrement fort aux États-Unis (90% du chiffre d'affaires). Loue matériel BTP, levage, énergie temporaire, climatisation à 1M+ de clients via un réseau dense de 1500+ agences. Holding cotée à Londres.",
        "contexte": "Forte croissance du chiffre d'affaires (7,3→9,9 Md€, +36% en 3 ans) tirée par le boom de l'infrastructure US (IRA, CHIPS Act). EBITDA en hausse 39% (3,3→4,6 Md€) avec marge premium 42% caractéristique du modèle location. Résultat net en hausse 21% (1,15→1,39 Md€).",
        "chiffres_decodes": "P/E forward 18,6× justifié par la qualité du compounder. Marge EBITDA 42% exceptionnelle pour un industriel. ROE 18% solide pour un capital-intensive. Rendement 0% (politique de réinvestissement intégral en croissance). Levier 1,5× EBITDA maîtrisé.",
        "catalyseurs": "Mégaprojets infrastructure US (CHIPS Act, IRA, hyperscaler datacenters). Migration des entreprises vers la location pour optimiser le capex. Possible démarrage d'un programme de dividende. Rotation de la flotte plus efficace post-Covid.",
        "particulier": "Compounder industriel de qualité exposé au cycle d'infrastructure US. Convient au portefeuille croissance long terme tolérant les cycles BTP. Pas de dividende mais TRI historique remarquable (~15-20%/an sur 10 ans). Profil 'qualité-croissance' à la Ashtead."
    },
    ("GALD", "CH"): {
        "activite": "Pure player mondial de la dermatologie médicale et esthétique, ex-filiale de Nestlé spin-offée en 2024. Portefeuille équilibré : médecine esthétique (Restylane fillers, Dysport), dermatologie médicale (Soolantra acné), grand public (Cetaphil). Présence dans 80+ pays avec n°1 mondial sur les fillers dermiques.",
        "contexte": "Très forte croissance post-IPO : chiffre d'affaires +37% (3,5→4,8 Md€), EBITDA +71% (0,64→1,09 Md€) et retournement résultat net (-0,09→0,56 Md€). Cours doublé depuis l'IPO (+117% en 18 mois). Marge EBITDA en montée vers 22%.",
        "chiffres_decodes": "P/E forward 31,5× élevé reflétant la croissance et les multiples 'beauty & wellness'. Marge EBITDA 21,6% en amélioration vers le standard cosmétique premium (25%+). ROE 7,7% en montée. Levier 1,54× EBITDA correct. Rendement symbolique 0,22%.",
        "catalyseurs": "Lancement Nemluvio (urticaire chronique) Q4 2025. Cycle innovation neuro-modulators et fillers next-gen. Migration mix vers les soins anti-âge premium (marges supérieures). M&A bolt-on dans la dermatologie esthétique.",
        "particulier": "Pure play premium sur le marché dermo-esthétique en croissance structurelle. Convient au portefeuille croissance-qualité tolérant des multiples élevés. Profil défensif (consommation discrétionnaire haut de gamme résiliente) avec catalyseurs visibles."
    },
    ("UMG", "NL"): {
        "activite": "Premier label musical mondial, propriétaire de catalogues iconiques (Universal, Capitol, Def Jam, Polydor) représentant ~32% du marché de la musique enregistrée. Activités complémentaires : édition musicale (Universal Music Publishing), merchandising et marques. Spin-off de Vivendi en 2021.",
        "contexte": "Croissance solide tirée par le streaming : chiffre d'affaires +21% (10,3→12,5 Md€), EBITDA +28% (2,0→2,56 Md€) et résultat net quasi doublé (0,78→1,53 Md€). Marge EBITDA 17,9% en amélioration. ROE remarquable 33,8%. Capital relativement léger.",
        "chiffres_decodes": "P/E forward 17,7× attractif pour un compounder digital structurel. Marge EBITDA 18% en montée (cibler 22%+ à terme). ROE 33,8% reflète un modèle royalty avec faible besoin de capex. Rendement 2,57% en croissance. Levier 1,1× EBITDA confortable.",
        "catalyseurs": "Hausses tarifaires streaming (Spotify, Apple Music) qui ruissellent vers les labels. Croissance des marchés émergents (Inde, Afrique) en streaming. Monétisation IA des catalogues (deals avec OpenAI/Anthropic). Lancement de superpremium streaming tier.",
        "particulier": "Modèle royalty premium exposé à la croissance structurelle du streaming. Convient au portefeuille croissance-qualité long terme. Profil compounder avec catalogue propriétaire (moat solide). Risques modérés liés à l'IA générative musicale (à monitorer)."
    },
    ("DTG", "DE"): {
        "activite": "Constructeur mondial de poids lourds spin-off de Daimler en 2021, leader européen et top 3 mondial (Mercedes-Benz Trucks, Freightliner, Fuso, Western Star). Présent sur les segments distribution, longue distance, BTP, services et financement. Marque premium dans un secteur fragmenté.",
        "contexte": "Cycle baissier européen marqué : chiffre d'affaires en repli (51,0→45,5 Md€, -11%), EBITDA stable (4,6→4,2 Md€) mais résultat net en baisse (2,67→1,97 Md€). Marge EBITDA 8% pénalisée par la sous-charge usines. Levier élevé 4,4× lié au crédit captif (financement clients). Cours +72% malgré le creux.",
        "chiffres_decodes": "P/E forward 9,1× très bas typique des cycles bas du transport. Rendement exceptionnel 9,12% reflète un dividende massif (3,80€) sur cours déprimé. ROE 5,4% au plancher cyclique. Levier 4,42× élevé en apparence mais 80%+ correspond au financement clients (peu risqué).",
        "catalyseurs": "Reprise des commandes Europe attendue 2026 (renouvellement de flottes vieillissantes). Lancement camions électriques eActros 600 (autonomie 500km). Programme cost-down 'CO2030' avec 1 Md€ d'économies cibles. Désintermédiation possible du captif financier.",
        "particulier": "Champion cyclique à la valorisation déprimée avec rendement attractif. Convient au portefeuille value-rendement tolérant les cycles industriels. Profil très volatil — entrée à graduer selon cycle. Risque d'erreur d'allocation si la reprise tarde."
    },
    ("WISE", "GB"): {
        "activite": "Fintech britannique leader des transferts internationaux multi-devises (anciennement TransferWise). Plateforme transparente proposant des taux interbancaires sans marge cachée. Active dans 70+ pays avec ~13 millions de clients particuliers et professionnels. Modèle ultra-scalable.",
        "contexte": "Hypercroissance : chiffre d'affaires triplé en 3 ans (0,66→2,11 Md€), résultat net multiplié par 12 (0,04→0,49 Md€). Marge nette de 23% en amélioration. ROE remarquable 29,7%. Cours +157% sur la période. Modèle fintech rentable rare dans le paysage européen.",
        "chiffres_decodes": "P/E forward 24× justifié par la croissance et la qualité du modèle. ROE 29,7% reflète une économie d'échelle massive (coûts fixes amortis sur volumes croissants). Pas de dividende (réinvestissement intégral). Rendement nul mais retour total exceptionnel via le cours.",
        "catalyseurs": "Expansion B2B (Wise Business, Wise Platform) avec marges supérieures. Lancement aux États-Unis et Asie-Pacifique. Possible programme rachat d'actions une fois la croissance ralentie. Effet réseau cumulatif (>1Bn$ transferts/jour).",
        "particulier": "Fintech de qualité avec moat (taux + UX) et rentabilité prouvée — exception européenne. Convient au portefeuille croissance-tech tolérant la volatilité. Profil compounder en début de cycle de monétisation. Surveiller la pression concurrentielle (Revolut, banques traditionnelles)."
    },
    ("ACLN", "CH"): {
        "activite": "Pure player suisse de la turbocompression industrielle issu du spin-off ABB en 2022. N°1 mondial des turbo pour grands moteurs marins et stationnaires (>500kW), équipant 70% du parc mondial. Marché de niche oligopolistique avec services après-vente récurrents (50% du CA).",
        "contexte": "Croissance exceptionnelle post-IPO : chiffre d'affaires +61% (0,72→1,16 Md€), EBITDA +82% (0,17→0,31 Md€), résultat net presque doublé (0,11→0,21 Md€). Cours multiplié par 4 (+306% en 3 ans). Marge EBITDA 28% premium, ROE remarquable 57,5%.",
        "chiffres_decodes": "P/E forward 31× élevé reflétant la rareté du modèle (moat technique + parts marché dominantes). Marge EBITDA 28% en hausse. ROE 57,5% exceptionnel grâce au modèle services. Levier 0,55× EBITDA très confortable. Rendement 1,85% en hausse.",
        "catalyseurs": "Reprise du cycle de commande maritime (renouvellement flottes mondiales). Migration vers turbo bi-fuel et hydrogène (transition énergétique du shipping). Croissance services après-vente (marges 40%+). Possible M&A bolt-on sur les technologies adjacentes.",
        "particulier": "Pépite industrielle suisse avec moat technique et oligopole sectoriel. Convient au portefeuille qualité-croissance long terme tolérant les multiples élevés. Profil 'compounder caché' typique du Mittelstand suisse. Liquidité limitée à surveiller."
    },
    ("MICC", "NL"): {
        "activite": "Pure player mondial de la crème glacée issu du spin-off Unilever 2025. Propriétaire des marques Magnum, Ben & Jerry's, Wall's, Cornetto avec ~21% de parts du marché mondial. Présence dans 100+ pays, leader sur les segments premium et impulsion. Distribution multi-canaux.",
        "contexte": "Démarrage en bourse récent : chiffre d'affaires stable (7,5→7,9 Md€), EBITDA stable autour de 1,3 Md€ mais résultat net en baisse (0,51→0,29 Md€) du fait des coûts de spin-off. Marge EBITDA 14,7% standard pour la PGC alimentaire. Cours en repli post-IPO (-10%).",
        "chiffres_decodes": "P/E forward 13,2× attractif post-correction. ROE 17,9% solide. Rendement 0% (politique en construction post-IPO). Levier 2,1× EBITDA hérité du carve-out, désendettement attendu. Marge EBITDA 15% à porter vers 18% selon le management.",
        "catalyseurs": "Programme cost-down post-séparation Unilever (~200 M€ ciblés). Inflation prix maîtrisée passe en pricing. Lancement potentiel d'un dividende H2 2026. Expansion d'occupation glace artisanale haut de gamme et alternatives plant-based.",
        "particulier": "Pure play défensif sur un marché de consommation discrétionnaire récurrent. Convient au portefeuille rendement-qualité tolérant le démarrage en bourse. Pricing power réel (catégorie 'plaisir') mais pression sur les coûts laitiers à monitorer."
    },
    ("LTMC", "IT"): {
        "activite": "Leader italien des jeux d'argent et paris sportifs (anciennement Sisal + Lottomatica), opérateur historique de la loterie nationale italienne (Gratta e Vinci). Présence dans le pari sportif retail (Better, Goldbet), online (Lottomatica.it) et machines à sous (concessions VLT/AWP). Quasi-monopole sur certains segments.",
        "contexte": "Forte croissance : chiffre d'affaires +62% (1,39→2,25 Md€, intégration Sisal), EBITDA +76% (0,41→0,72 Md€), résultat net plus que doublé (0,07→0,17 Md€). Marge EBITDA 29,7% premium pour les jeux. ROE exceptionnel 39%. Cours multiplié par 2,4 sur la période.",
        "chiffres_decodes": "P/E forward 11,2× très attractif pour un compounder à marges élevées. Marge EBITDA 30% premium reflète la concession monopolistique. ROE 39% exceptionnel. Levier 2,54× EBITDA résultat du LBO d'origine, désendettement en cours.",
        "catalyseurs": "Renouvellement de la concession lotto nationale 2026 (sans surprise). Migration online (croissance 20%+/an du iGaming italien). Synergies fin d'intégration Sisal (~50 M€). Possible expansion ibérique ou européenne via M&A.",
        "particulier": "Quasi-monopole défensif sur les jeux italiens avec croissance offerte par le digital. Convient au portefeuille rendement-croissance tolérant un secteur sensible ESG (jeux d'argent). Risques réglementaires italiens à monitorer (mais concession solide jusqu'en 2030+)."
    },
    ("TPRO", "IT"): {
        "activite": "Spécialiste italien des sondes de test pour wafers semiconducteurs (probe cards). Leader mondial sur les segments mémoire (DRAM, NAND) et SoC haute densité, fournisseur des grandes fonderies (TSMC, Samsung) et fabricants mémoire (Micron, SK Hynix). Marché de niche oligopolistique.",
        "contexte": "Cycle bas semiconducteurs : chiffre d'affaires +15% sur 3 ans (0,55→0,63 Md€) mais EBITDA en repli (0,24→0,19 Md€) et résultat net en baisse (0,15→0,10 Md€). Marge EBITDA stable 30%. Cours multiplié par 4,7 (+371%) sur l'enthousiasme IA. Trésorerie nette positive (-3,55×).",
        "chiffres_decodes": "P/E TTM 214× extrême reflète l'effondrement temporaire des bénéfices, forward 52× anticipe la reprise. Marge EBITDA 30% premium pour le secteur. ROE 8% au creux cyclique. Bilan en cash net massif (-3,55× EBITDA = trésorerie supérieure à la dette de 3,5× EBITDA).",
        "catalyseurs": "Reprise du cycle mémoire 2026 (HBM pour IA en explosion). Migration vers les nœuds avancés (3nm, 2nm) qui exige des probe cards plus complexes (mix produit favorable). Croissance structurelle de la demande IA pour les semi-conducteurs HBM.",
        "particulier": "Pure play sur le cycle semi-conducteurs avec exposition IA (HBM). Convient au portefeuille croissance-tech tolérant la volatilité cyclique extrême. Profil 'play sur le cycle haut' — entrée à graduer. Trésorerie massive = solidité bilancielle exceptionnelle."
    },
    ("RNO", "FR"): {
        "activite": "Constructeur automobile français multimarque (Renault, Dacia, Alpine, Mobilize) en pleine transformation. Stratégie de remontée en gamme via Renaulution. Alliance Renault-Nissan-Mitsubishi rééquilibrée. Spécialiste de la voiture électrique européenne accessible (Renault 5, R4, Mégane E-Tech).",
        "contexte": "Croissance des volumes mais résultat net effondré : chiffre d'affaires +25% (46,3→57,9 Md€) mais perte massive en 2025 (-10,9 Md€) sur dépréciation de la participation Nissan. EBITDA stable autour de 6 Md€. Levier élevé 8,3× pénalisé par le crédit captif RCI Banque. ROE négatif -40%.",
        "chiffres_decodes": "P/E TTM impossible à calculer (résultat net négatif), forward 4,0× très bas sur la base d'un retour à la rentabilité 2026. Rendement remarquable 7,68% mais sustainability incertaine. Marge EBITDA 10% en consolidation. Levier 8,33× majoré par les actifs financiers du captif.",
        "catalyseurs": "Lancement Renault 4 E-Tech 2026 (succès en pré-commandes). Cession partielle de la participation Nissan (1,5 Md€). Plan d'économies 'EV Strategy' (3 Md€). Renormalisation de la rentabilité Dacia (cash cow). Effet base ultra favorable face à 2025 catastrophique.",
        "particulier": "Pari de retournement crédible sur le constructeur français en pleine refondation. Convient au profil value tolérant le risque industriel élevé. Dividende attractif mais à surveiller. Profil très volatil et execution-risk élevé. Pas un fond de portefeuille."
    },
    ("SYENS", "BE"): {
        "activite": "Pure player belge de la chimie de spécialité issu du spin-off Solvay 2023. Activités axées sur les composites pour aéronautique (Cytec), matériaux haute performance et solutions pour l'électronique. Concurrence Hexcel, Toray sur l'aéronautique. Présence mondiale (USA 40%, Europe 35%, Asie 25%).",
        "contexte": "Contre-performance marquée : chiffre d'affaires en repli (8,1→6,0 Md€, -26%), EBITDA en baisse (1,84→1,23 Md€), résultat net juste négatif (-0,06 Md€). Marge EBITDA 19,6% encore solide. Cours en repli (-21% sur 3 ans). Désendettement engagé (1,54× EBITDA).",
        "chiffres_decodes": "P/E forward 15,4× cohérent post-correction. Marge EBITDA 20% en consolidation. ROE quasi nul -0,8% au creux cyclique. Rendement 2,41% dividende rétabli post-spin-off. Cycle déstockage chimie passé selon le management.",
        "catalyseurs": "Reprise des volumes aéronautiques (montée cadence Airbus/Boeing). Programme cost-down (~100 M€). Lancement Sygnatur (composites recyclables). Effet base favorable 2026 face à 2025. Possible M&A bolt-on dans les composites premium.",
        "particulier": "Pari cyclique sur la chimie de spécialité aéronautique en bas de cycle. Convient au portefeuille value-cyclique 2-3 ans. Pricing power réel sur les composites mais sensibilité au cycle aéronautique. Patience requise pour matérialisation du retournement."
    },
    ("VAR", "NO"): {
        "activite": "Producteur norvégien de pétrole et gaz, filiale cotée d'Eni et HitecVision (private equity). Exploitation principalement en mer du Nord avec des coûts d'extraction parmi les plus bas du secteur. Production ~430 kbep/j. Stratégie axée sur l'extraction à pleine maturité des actifs existants.",
        "contexte": "Cycle baissier des prix : chiffre d'affaires en repli (9,0→7,3 Md€, -18%), EBITDA en baisse (7,3→6,1 Md€) mais marge EBITDA exceptionnelle 82% (typique upstream). Résultat net stable autour de 0,8 Md€. Cours doublé en 3 ans (+87%) avec rendement très élevé.",
        "chiffres_decodes": "P/E forward 11,4× attractif pour un pétrolier upstream pur. Marge EBITDA 82% reflète le faible coût d'extraction Norvège. ROE exceptionnel 97% sur des fonds propres limités. Rendement très élevé 7,69% durable selon le management. Levier 0,79× EBITDA maîtrisé.",
        "catalyseurs": "Démarrage Balder Future 2026 (production +35 kbep/j). Cycle prix favorable si OPEC+ maintient discipline. Programme buyback en complément du dividende massif. Possible cession d'actifs matures pour optimiser le portfolio.",
        "particulier": "Pure play upstream pétrolier de qualité avec rendement actionnaire élevé. Convient au portefeuille value-rendement tolérant la volatilité des prix énergétiques. Pricing risk = principal facteur de variation. Profil 'cash machine' jusqu'à la fin du cycle pétrolier."
    },
    ("R3NK", "DE"): {
        "activite": "Spécialiste allemand des engrenages de précision pour la défense (chars Leopard) et l'industrie (BTP, naval). Spin-off de KKR en 2024. Position monopolistique sur certains segments transmissions militaires en Europe. Croissance dopée par le réarmement européen.",
        "contexte": "Hypercroissance : chiffre d'affaires +61% (0,85→1,37 Md€), EBITDA +35% (0,17→0,23 Md€), résultat net triplé (0,03→0,10 Md€). Marge EBITDA 18% en amélioration. ROE remarquable 24,2%. Cours doublé en 18 mois (+98%) sur l'effet réarmement Ukraine/Europe.",
        "chiffres_decodes": "P/E forward 24× élevé reflétant la croissance forte. ROE 24% solide. Levier 1,57× EBITDA correct post-IPO. Rendement modeste 0,8% (politique réinvestissement). Marge EBITDA 18% en progression vers 22%+ ciblée selon le management.",
        "catalyseurs": "Cycle de réarmement européen (1000+ chars Leopard à produire/refit). Diversification vers les véhicules autonomes/drones terrestres. Carnet de commandes record (>3 ans de production). Possible expansion vers les marchés asiatiques (Pologne, Corée du Sud).",
        "particulier": "Pure play sur le réarmement européen avec moat technique. Convient au portefeuille croissance-thématique défense (croissance structurelle 10+ ans). Multiples élevés justifiés par la rareté du profil. Surveiller normalisation post-pic réarmement (5-7 ans)."
    },
    ("CVC", "NL"): {
        "activite": "Premier gestionnaire d'actifs alternatifs européen (private equity, dette privée, infrastructure), encours sous gestion ~190 Md€. Stratégie 'Tier 1 European' dans les LBO européens et secondary funds. IPO Amsterdam 2024. Présent en private equity, secondaries, credit, infrastructure.",
        "contexte": "Croissance soutenue : chiffre d'affaires +87% (0,99→1,85 Md€), résultat net multiplié par 4 (0,28→1,18 Md€). Marge EBITDA premium 58% typique de l'asset management. ROE exceptionnel 60,3%. Cours en correction (-22% depuis IPO) sur normalisation des multiples PE.",
        "chiffres_decodes": "P/E forward 13,4× attractif post-correction. Marge EBITDA 58% reflète le modèle GP (general partner) capital-light. ROE 60,3% exceptionnel. Rendement 3,57% en hausse via une politique de dividende régulière promise au moment de l'IPO.",
        "catalyseurs": "Closing de fonds géants 2025-2026 (>30 Md€ pour CVC Capital Partners IX). Cycle de cessions favorables avec normalisation des valorisations. Migration vers les fonds 'evergreen' (semi-liquides) plus large publique. Expansion infrastructure (~50 Md€ ciblés).",
        "particulier": "Premier asset manager européen alternatif avec retours actionnaires attractifs. Convient au portefeuille rendement-croissance avec exposition à l'industrie du PE. Profil cyclique modéré (commissions de gestion = base récurrente). Risque pricing des multiples 'à la Blackstone' à surveiller."
    },
    ("ZAB", "PL"): {
        "activite": "Leader polonais de la distribution alimentaire de proximité (10 500+ magasins Żabka), avec un modèle franchise convenience store unique en Europe. Présence dominante en Pologne avec ~95% de couverture urbaine. Marques propres premium et services digitaux (Żappka).",
        "contexte": "Très forte croissance : chiffre d'affaires +70% (3,8→6,4 Md€), EBITDA +65% (0,54→0,89 Md€), résultat net multiplié par 3 (0,09→0,26 Md€). Marge EBITDA 14% en standard du retail. ROE exceptionnel 58,8%. Cours en hausse 30% depuis l'IPO octobre 2024.",
        "chiffres_decodes": "P/E forward 16,4× cohérent pour un compounder retail. Marge EBITDA 14% à porter vers 16-18% avec digitalisation. ROE 58,8% reflète le modèle franchise capital-light. Levier 0,81× confortable. Pas de dividende (réinvestissement intégral en croissance).",
        "catalyseurs": "Expansion Roumanie 2025-2027 (~800 magasins ciblés). Croissance services digitaux (Żappka >5M users actifs). Migration mix vers marques propres premium (+marges). Possible cotation duale Varsovie+Londres pour élargir base actionnaire.",
        "particulier": "Compounder retail premium avec moat (réseau franchise dense) sur un marché en consolidation. Convient au portefeuille croissance-Europe émergente long terme. Profil Walmart polonais en accélération digitale. Risque géopolitique CEE à monitorer."
    },
    ("SUNN", "CH"): {
        "activite": "Opérateur télécom suisse (mobile, fixe, internet, TV), n°2 du marché helvétique derrière Swisscom (~30% PdM). Spin-off Liberty Global 2024 après cession de UPC Suisse. Marque grand public Sunrise et division B2B en croissance. Couverture nationale 5G/fibre.",
        "contexte": "Stabilité : chiffre d'affaires quasi stable (3,19→3,13 Md€), EBITDA stable autour de 1,2 Md€ mais résultat net dégradé (0,08→-0,12 Md€) sur amortissements post-fusion. Marge EBITDA 31% standard télécom. Levier élevé 3,47× EBITDA hérité du spin-off. Cours +26% depuis IPO.",
        "chiffres_decodes": "P/E TTM impossible (perte), forward 33× élevé reflétant les amortissements de fusion. Rendement très élevé 8,05% sur dividende de 3,42 CHF. ROE négatif -3,5% à normaliser. Marge EBITDA 31% solide. Désendettement attendu (3,47× → 2,5× cible).",
        "catalyseurs": "Programme de cost-down post-fusion (~200 M CHF annuels). Migration cash-flow vers le dividende durable (taux 60% du CF libre ciblé). Croissance B2B services managés. Possible vente d'une partie de l'infrastructure (towerco) pour réduire la dette.",
        "particulier": "Télécom de qualité défensive avec rendement très attractif. Convient au portefeuille rendement long terme tolérant la stabilité (croissance limitée). Profil 'cash machine' avec catalyseur de désendettement. Maturité concurrentielle du marché suisse comme principal risque."
    },
    ("CSG", "NL"): {
        "activite": "Fabricant néerlandais d'équipements militaires et systèmes de défense (radars, missiles, véhicules blindés). Diversification dans les composants spatiaux et l'aéronautique. Carnet de commandes alimenté par le réarmement OTAN. Marques principales : Thales Nederland, Damen Naval, Aerospace Propulsion.",
        "contexte": "Chiffre d'affaires en repli apparent (14,4→5,2 Md€ sur 2021→2024) lié à des cessions/restructurations. EBITDA stable autour de 1,5-2 Md€. Résultat net en baisse (1,23→0,55 Md€). Marge EBITDA 26% premium pour la défense. ROE remarquable 41,8% sur fonds propres maigres.",
        "chiffres_decodes": "P/E forward 13,4× attractif pour un acteur défense pure. Marge EBITDA 26% premium. ROE 41,8% reflète une efficacité capitalistique forte. Levier 1,11× EBITDA maîtrisé. Pas de dividende (réinvestissement croissance + R&D). Note : données 2024 réduites suite à reclassements comptables.",
        "catalyseurs": "Carnet de commandes OTAN record (radars, missiles courte/moyenne portée). Programme 'Defence Readiness' EU 2026-2028 (~800 Md€ déployés). Migration vers défense intelligente (capteurs, IA tactique). Possible joint-venture avec Saab, MBDA.",
        "particulier": "Pure play défense européen avec moat technologique et carnet record. Convient au portefeuille croissance-thématique défense long terme. Sensibilité ESG variable selon investisseurs. Profil pricing power exceptionnel sur les programmes critiques."
    },
    ("FDJU", "FR"): {
        "activite": "Opérateur français des jeux d'argent (loterie, paris sportifs, jeux instantanés), monopole d'État privatisé en 2019. Forte présence retail (35 000+ buralistes) et accélération digitale (FDJ.fr). Acquisition Premier Lotteries Ireland 2024. Diversification européenne en cours via FDJ United.",
        "contexte": "Forte croissance : chiffre d'affaires +50% (2,5→3,7 Md€) sous l'effet du périmètre Premier Lotteries. EBITDA +86% (0,58→1,08 Md€), résultat net en baisse (0,31→0,18 Md€) sur coûts d'acquisition. Marge EBITDA 25,6% en amélioration. Rendement spectaculaire 18% sur dividende exceptionnel.",
        "chiffres_decodes": "P/E forward 8,5× très attractif. Marge EBITDA 26% premium pour les jeux régulés. ROE 16,3% solide. Levier 1,39× EBITDA correct. Rendement TTM 18% inclut un dividende exceptionnel — rendement récurrent attendu ~6-7% à terme.",
        "catalyseurs": "Intégration Premier Lotteries Ireland (synergies 50 M€). Renouvellement de la concession française à long terme (visibilité jusqu'en 2044). Migration online (digital 30%+ du CA cible). Possibles acquisitions en Europe du Sud.",
        "particulier": "Quasi-monopole défensif avec rendement actionnaire exceptionnel. Convient au portefeuille rendement long terme tolérant le secteur jeu (sensible ESG). Profil 'monopole d'État privatisé' particulièrement résilient. Risques fiscaux/réglementaires français à monitorer."
    },
    ("IVG", "IT"): {
        "activite": "Constructeur italien de poids lourds et utilitaires (Iveco, Iveco Bus, Iveco Defence Vehicles), spin-off de CNH Industrial 2022. Position significative en Europe (~12% PdM camions) et leader des bus européens. Activités défense (véhicules tactiques Centauro, MRAP) en forte croissance.",
        "contexte": "Performance contrastée : chiffre d'affaires en repli (14,4→13,4 Md€) en raison du cycle bas truck, mais EBITDA en hausse (1,02→1,25 Md€), résultat net doublé (0,15→0,29 Md€). Marge EBITDA passable 5% (vs ~9% chez Daimler Truck). Cours triplé (+248%) sur attente OPA Tata Motors.",
        "chiffres_decodes": "P/E TTM 36,7× élevé, forward 6,2× très bas sur attente d'OPA. Rendement TTM 41,8% gonflé par un dividende exceptionnel pré-cession (5,82€). Marge EBITDA 4,9% à porter vers 7%+. Levier 2,39× EBITDA en réduction. ROE 3,1% modéré.",
        "catalyseurs": "OPA Tata Motors validée H2 2025 à 14,1€/action (prime ~25% vs cours pré-deal). Synergies attendues avec Tata Daewoo et Tata Motors. Cycle bas truck européen attendu en redressement 2026. Croissance défense (Centauro nouveaux contrats).",
        "particulier": "Pari court-terme sur le closing de l'OPA Tata Motors. Profil arbitrage avec downside limité (~14€ floor) et upside cycle truck à moyen terme. Convient aux investisseurs arbitragistes ou patients sur le rebond cyclique. Risque execution OPA principal."
    },
    ("BPT", "GB"): {
        "activite": "Gestionnaire britannique d'actifs alternatifs (private equity mid-market, secondaries, infrastructure), AUM ~70 Md€. Stratégie 'European mid-market specialist' avec 200+ investissements actifs. IPO Londres 2021 dans la mouvance CVC, EQT. Positionnement sur les buyouts 100M-2Md€.",
        "contexte": "Croissance solide des AUM mais résultat net divisé par 3 (0,14→0,05 Md€) sur normalisation des performance fees post-pic 2022. Chiffre d'affaires +83% (0,31→0,56 Md€). Marge EBITDA 51% en repli vs pic. Cours en baisse 18% sur 3 ans. ROE 4,8% au creux cyclique.",
        "chiffres_decodes": "P/E TTM 52,9× élevé, forward 9,2× attractif sur normalisation. Marge EBITDA 51% reflète le modèle GP capital-light. ROE 4,8% au creux cyclique des performance fees. Rendement 3,56% via dividende régulier. Levier maîtrisé.",
        "catalyseurs": "Closing Bridgepoint Europe VII (~9 Md€ ciblés). Normalisation des cessions PE 2025-2026 (déblocage des sorties LP). Expansion infrastructure (~5 Md€). Possible cotation US pour élargir la base d'investisseurs.",
        "particulier": "Asset manager alternatif avec rendement attractif et potentiel de retournement. Convient au portefeuille rendement-cyclique tolérant les performance fees lumpy. Profil 'mid-cap European PE' moins défensif que les leaders US (Blackstone, KKR)."
    },
    ("HIAB", "FI"): {
        "activite": "Spécialiste finlandais des équipements de levage et de manutention pour camions (grues hydrauliques, hayons, chariots embarqués Loglift, Multilift). Spin-off de Cargotec 2024. Position de leader européen sur les segments forestiers et construction. Marques : Hiab, Loglift, Moffett.",
        "contexte": "Repli temporaire post-spin-off : chiffre d'affaires -62% apparent (4,1→1,6 Md€) lié à la nouvelle scope après séparation Cargotec, EBITDA en baisse (0,41→0,27 Md€), mais résultat net en forte hausse (0,02→0,16 Md€). Marge EBITDA 13% en amélioration. Cours en hausse 34% post-spin-off.",
        "chiffres_decodes": "P/E forward 16,8× cohérent pour un cyclique industriel. Marge EBITDA 13% en montée vers 15%+ cible. ROE 13,6% solide. Levier exceptionnel 0,02× EBITDA (quasi trésorerie nette). Rendement 5,2% sur dividende rétabli post-spin-off.",
        "catalyseurs": "Cycle de remplacement des flottes BTP/forestier 2026-2027. Croissance services après-vente (~30% du CA, marges supérieures). Programme cost-down post-spin-off. M&A bolt-on possible avec bilan disponible.",
        "particulier": "Compounder industriel niche avec bilan exceptionnel et rendement attractif. Convient au portefeuille qualité-rendement tolérant la cyclicité modérée. Profil Mittelstand nordique avec moat technique. Liquidité limitée à surveiller."
    },
    ("AMV0", "DE"): {
        "activite": "Fabricant allemand d'équipements de carrosserie et systèmes électroniques pour véhicules (essuie-glaces, lave-glaces, mécanismes de portes, capteurs intelligents). Spin-off Continental 2024. Présence mondiale avec position dominante sur certains segments OEM. Transition vers les véhicules électriques et autonomes.",
        "contexte": "Stabilisation post-spin-off : chiffre d'affaires quasi stable (19,0→18,6 Md€), EBITDA quasi quadruplé (0,34→1,29 Md€) sur restructuration, perte nette en réduction (-1,01→-0,66 Md€). Marge EBITDA 7% en construction. Cours quasi stable depuis IPO. ROE négatif -6,4%.",
        "chiffres_decodes": "P/E impossible (perte), forward 7,6× très attractif sur attente de retour à la rentabilité. Marge EBITDA 7% à porter vers 10%+ cible. Levier 0,79× EBITDA confortable. Rendement 0% (politique en construction). ROE -6,4% à normaliser.",
        "catalyseurs": "Programme 'Renaissance' (~300 M€ d'économies). Migration mix vers les capteurs ADAS (marges supérieures). Effet base ultra favorable 2026 face à 2025. Possible programme rachat actions une fois la rentabilité rétablie. M&A bolt-on dans l'autonome.",
        "particulier": "Pari de retournement spéculatif sur un équipementier auto en restructuration. Réservé aux investisseurs tolérant le risque industriel élevé et l'execution risk. Pas un fond de portefeuille. Catalyseurs visibles mais exécution non garantie."
    },
    ("RO", "CH"): {
        "activite": "Géant pharmaceutique suisse leader mondial dans l'oncologie, le diagnostic médical et les neurosciences. Portefeuille de blockbusters (Tecentriq, Hemlibra, Ocrevus) et division diagnostic première mondiale. R&D pipeline parmi les plus prolifiques du secteur. Marché global équilibré.",
        "contexte": "Croissance solide : chiffre d'affaires en léger tassement (69,1→66,5 Md€) lié à la fin des Covid testing, mais EBITDA stable à 23,3 Md€ et résultat net constant à 13,5 Md€. Marge EBITDA exceptionnelle 38%. ROE remarquable 37%. Cours en hausse 17% sur 3 ans.",
        "chiffres_decodes": "P/E forward 15,3× attractif pour un pharma blue chip de la qualité de Roche. Marge EBITDA 38% reflète la franchise oncologie premium. ROE 37% exceptionnel grâce à un capital intellectuel valorisé. Rendement durable 3,22% sur un dividende croissant (9,1→10,8 CHF/action).",
        "catalyseurs": "Lancements 2026-2027 : trontinemab (Alzheimer phase 3), giredestrant (cancer sein ER+), elinzanetant (ménopause). Acquisitions ciblées en obésité (intégration Carmot). Cycle de renouvellement diagnostic moléculaire (mpox, cancer précoce). Pipeline IA-discovery prometteur.",
        "particulier": "Champion pharma européen avec moat exceptionnel et pipeline pléthorique. Convient au cœur de portefeuille défensif-qualité long terme. Valorisation raisonnable après correction. Catalyseur Alzheimer (trontinemab) potentiellement game-changer en 2026-2027."
    },
    ("SW", "IE"): {
        "activite": "Premier groupe mondial d'emballages cartonnés issu de la fusion Smurfit Kappa + WestRock en juillet 2024. Présent dans 40+ pays avec 500+ sites de production. Activités intégrées : production papier (kraftliner, testliner), conception et fabrication d'emballages, recyclage. Cotation NYSE/Dublin.",
        "contexte": "Fusion transformante : chiffre d'affaires plus que doublé (12,4→28,7 Md€) sur l'effet périmètre WestRock. EBITDA doublé (2,12→4,47 Md€) mais résultat net en repli (0,95→0,64 Md€) sur coûts d'intégration. Marge EBITDA 15% en repli temporaire. Cours en repli 16% depuis le merger.",
        "chiffres_decodes": "P/E TTM 54× élevé sur coûts exceptionnels, forward 12,4× attractif post-normalisation. Marge EBITDA 15% à reporter vers 18%+ avec synergies. ROE 2,1% au creux d'intégration. Levier 2,65× EBITDA hérité du deal, désendettement annoncé. Rendement durable 3,41%.",
        "catalyseurs": "Synergies d'intégration (~400 M$ run-rate à 18 mois). Reprise du cycle emballage (déstockage terminé). Migration vers l'emballage durable (cartonné premium remplace plastique). Possible cession d'actifs non-core post-intégration.",
        "particulier": "Champion mondial du carton avec scale exceptionnelle post-merger. Convient au portefeuille rendement-cyclique tolérant 12-18 mois d'intégration. Profil 'compounder cyclique' à la Smurfit historique avec amplification scale-up."
    },
    ("REC", "IT"): {
        "activite": "Laboratoire pharmaceutique italien spécialisé dans les médicaments rares et de niche (cardiologie, otorhinolaryngologie, troubles métaboliques). Portefeuille de marques propres premium (Zanidip, Tergyrans) et licensing-in pour Europe/Latam. Position dominante sur certains segments thérapeutiques de niche.",
        "contexte": "Croissance solide : chiffre d'affaires +40% en 4 ans, EBITDA en hausse régulière, résultat net stable. Marge EBITDA premium 38% reflète le pricing pouvoir sur les niches. ROE solide. Bilan sain avec endettement maîtrisé. Recordati est listé sous le ticker REC.MI (différent de REC).",
        "chiffres_decodes": "Pure player pharma niche avec moat thérapeutique. Marge premium typique du modèle 'orphan drug specialist'. Valorisation modérée pour la qualité offerte. Rendement croissant.",
        "catalyseurs": "Lancements 2026 (CG201 anti-tumoral). Expansion thérapeutique en cardiologie de niche. M&A bolt-on européen ou latam. Cycle de renouvellement génériques limité sur portefeuille spécialités.",
        "particulier": "Pépite pharmaceutique italienne avec moat thérapeutique. Convient au portefeuille qualité-santé long terme. Profil 'compounder pharma niche' à la Bristol-Myers historique mais en mid-cap. Liquidité moyenne à surveiller."
    },
    ("NSIS-B", "DK"): {
        "activite": "Leader mondial des enzymes industrielles et des micro-organismes (renommée de Novozymes en janvier 2024 après fusion avec Chr. Hansen). Présent dans la nutrition humaine et animale, les détergents, les biocarburants, les sciences végétales. Position oligopolistique sur les enzymes industrielles (~50% PdM mondiale).",
        "contexte": "Année de fusion : chiffre d'affaires +71% (4,1→7,0 Md DKK) sur effet périmètre Chr. Hansen. EBITDA quasi doublé. Résultat net stable autour de 1,5 Md DKK. Marge EBITDA premium 33% reflète la franchise enzyme. ROE solide ~20%. Cours en repli post-fusion sur normalisation des multiples.",
        "chiffres_decodes": "P/E forward attractif post-correction. Marge EBITDA 33% premium typique du leader enzyme. Profil capital-intensif mais ROE solide. Rendement croissant via dividende régulier. Position bilancielle saine post-fusion.",
        "catalyseurs": "Synergies d'intégration Chr. Hansen (~100 M€/an run-rate). Cycle ag-tech (renforcement durabilité agricole). Migration biocarburants 2G. Possible nouveau cycle d'innovation enzymatique pour bioéconomie.",
        "particulier": "Champion mondial des biotechnologies industrielles avec moat exceptionnel. Convient au cœur de portefeuille qualité-thématique bioéconomie long terme. Valorisation revenue à des niveaux raisonnables post-fusion. Profil compounder typique des leaders nordiques."
    },
}


def main():
    d = json.loads(CACHE.read_text())
    by_key = {(c["tk"], c["ctry"]): c for c in d["companies"]}
    added = 0
    for key, fiche in FICHES.items():
        co = by_key.get(key)
        if co is None:
            print(f"  ✗ {key} : société non trouvée dans le cache")
            continue
        for k, v in fiche.items():
            co[f"fiche_{k}"] = v
        added += 1
        print(f"  ✓ {co['name']}")

    print(f"\n{added}/{len(FICHES)} fiches injectées")
    sans = sum(1 for c in d["companies"] if not c.get("fiche_activite"))
    print(f"Reste sans fiche : {sans}")

    CACHE.write_text(json.dumps(d, ensure_ascii=False, allow_nan=False))
    SNAP.write_text(json.dumps(d, ensure_ascii=False, allow_nan=False))
    print("Cache + snapshot sauvegardés.")


if __name__ == "__main__":
    main()
