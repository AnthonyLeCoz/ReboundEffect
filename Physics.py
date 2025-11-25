""" File defining the schematic functions """

import numpy as np

"""
    Catégorie de population:
        - urbain, Pop = ?, Pouvoir d'achat: 10000 
        - rural,  Pop = ?, Pouvoir d'achat: 9000 

    Besoins:
        - ["Prix de revient ($/km)", "km en ville", "km hors ville"]
            =>  Burbain_i = [0.2, 150, 50]
                Brural_i = [0.13, 50, 220]

    Vecteur de design x:
        - ["Vmax (km/h)", "Autonomie (kWh)", "mass (kg)"]
     => Service rendu:
        - ["Rendement (kW/km)", "Distance max (km)"]

    Vecteur de l'état:
        - ["Prix energie ($/kW)", "Subvention ($/voiture)"]

    Autre moyen de transport:
        - ["$ en bus", "$ en train"]

    Coût d'entretient :
        - Révision annuelle (check complet, diagnostic batterie, niveaux fluides)	Tous les 12 mois ou 10 000 km	De 120 € à 180 €
        - Remplacement des pneus (4 roues en 14″)	Tous les 20 000 à 30 000 km	De 180 € à 240 €
        - Freins avant/arrière (kit plaquettes tambours)	Tous les 15 000 à 25 000 km	De 100 € à 160 €
        - Amortisseurs (usure normale sur routes urbaines)	Tous les 40 000 à 60 000 km	De 250 € à 350 €
        - Essuie-glaces / Lave-glace / Ampoules	Selon usure saisonnière	De 20 € à 50 €
        - Pare-brise (remplacement complet)	Si fissure ou impact majeur	Environ 250 €
        - Recharge du liquide de frein et purge circuit	Tous les 2 ans	De 50 € à 70 €
        - Remplacement batterie auxiliaire 12V (si équipée)	Tous les 5 à 6 ans	De 90 € à 130 €
"""

mass_i = 485

# Vitesse et masse au rendement maximal
vmax_optimal = 40
mass_optimal = 400

eff_i = 7.3/100 # rendement initial kW/km
autonomie_i = 75*eff_i
autonomie_optimal = autonomie_i
x_i = [45, autonomie_i, 485] # design initial

p_i = 7990 # Initial price
prodCost_i = 7990*0.5 # Initial production price

dlife = 100000 # Distance (km) sur la vie de la voiture
savMax = 500 # Côut maximal de sav au bout de dlife

""" Impact Carbone """
GESkWh = 0.014 # Coût carbone par kgCo2e/kWh en France
GESprod = 3700 # Coût carbone de production en kgCo2e
GESkmAutreMobilite = np.array([0.113, 0.016]) # Emission carbone par km des autres mobilités (bus, train)
GESautreDepenseParEUR = 1000/250 # Emission GES par euro dépensé. Paris newYork Avion -> 1 Tonne Co2, ~250$

""" Ménages """
prixKwh = 0.14
subvention_i = 150
loi_i = [prixKwh, 150] # Prix energie, subvention voiture
Pi_urbain = 8000# pop urbaine
Pi_rural = 5000# pop rurale
ptransport_i = 8000 # Prix initial mis dans les transport
# ["Prix de revient ($/km)", "km en ville / Recharge", "km hors ville / recharge"]
Burbain_i = [1.5*prixKwh*eff_i, 50, 10]
Brural_i = [1.1*prixKwh*eff_i, 20, 60]
# Pondération des besoins
pondrural_i = [0.5, 0.05, 0.45]
pondurbain_i = [0.5, 0.45, 0.05]


""" Report modal """
CostKmBus   = 2/10 # coût par km de bus (~10km 91.06, 2$)
CostKmTrain = 70/1000 # cout par km de train (marseille lille, 1000km, 70$)

import numpy as np

# constants unchanged …

def savCost(distance):
    return savMax * (1 - np.exp(-3 * distance / dlife))

def maintenance(distance):
    cost  = 150 * int(distance/10000)
    cost += 200 * int(distance/25000)
    cost += 150 * int(distance/20000)
    cost += 300 * int(distance/50000)
    cost += 40  * int(distance/5000)
    return cost

def modele_ingénerie(x):
    vmax, autonomie, mass = x
    eff = eff_i/(np.exp(-np.abs(-0.8*(vmax-vmax_optimal)/vmax_optimal))
                 * np.exp(-np.abs(-0.3*(mass-mass_optimal)/mass_optimal))
                 * np.exp(min(0, -np.abs(-0.5*(autonomie/autonomie_optimal-1)))))
    dmax = autonomie/eff
    return [[eff, dmax]]

def benefice_economique(Q, p, D):
    CA = Q*p
    Davg = D/Q
    prodCost = Q*prodCost_i + savCost(Davg)*Q
    return [CA - prodCost]

def impact_voiture(Q, D, SR):
    eff = SR[0]
    kwh = eff*D
    return [GESkWh*kwh + GESprod*Q]

def impact_autre_transports(EURr, Dr):
    return [GESkmAutreMobilite[0]*Dr[0] + GESkmAutreMobilite[1]*Dr[1]]

def impact_redirection_dépense(EUR):
    return [EUR * GESautreDepenseParEUR]

def prix_efficace(p, loi):
    return [p - loi[1]]

def satisfaction_pop(B, PA, peff, SR, loi, pond):
    eff, dmax = SR
    pkm = eff*loi[0]
    kmville = dmax
    kmautre = dmax*0.8

    fb = np.array([pkm, kmville, kmautre])

    def dsat(a, b):
        return np.where(a < b, 1, np.exp(-3*(a-b)/a))

    def d(a, b):
        return np.array([dsat(b[0], a[0])*pond[0],
                         dsat(a[1], b[1])*pond[1],
                         dsat(a[2], b[2])*pond[2]])

    S = d(B, fb) * dsat(peff, PA)
    return [S]

def distance_avec_satisfaction(S, B, pop):
    return [B[1+pop] * np.linalg.norm(S) * dlife]

def distance_avec_report_modal(R, B):
    return [np.array([B[1]*np.linalg.norm(R)*dlife,
                      B[2]*np.linalg.norm(R)*dlife])]

def cout_report_modal(Dr):
    return [np.array([Dr[0]*CostKmBus, Dr[1]*CostKmTrain])]

def bien_etre(CostV, CostR, pop, S):
    return [(Pi_rural*pop+Pi_urbain*(1-pop))* np.linalg.norm(S) / (CostV + CostR)]

def cout_user_voiture(Q, peff, D, loi, SR):
    kmCost = loi[0]*SR[0]
    return [Q*peff + maintenance(D/Q)*Q + kmCost*D, D/Q]

def autre_depenses(ptransport):
    return [ptransport_i - ptransport]
