"""Schematic of the rebound effect"""

from Utils import *
from Physics import *
import numpy as np
import matplotlib.pyplot as plt

netlist = Netlist()


# Legends (alpha removed)
netlist.addLegend("x", ["Vmax (km/h)", "Autonomie (kWh)", "mass (kg)"])
netlist.addLegend("loi", ["Prix energie ($/km)", "Subvention ($/voiture)"])
netlist.addLegend("SR", ["Rendement (kW/km)", "Distance max (km)"])
netlist.addLegend("$r", ["$ en bus", "$ en train"])
netlist.addLegend("Dr", ["km en bus", "km en train"])

netlist.addLegend("Burbain", ["Prix de revient ($/km)", "km en ville", "km hors ville"])
netlist.addLegend("Brural", ["Prix de revient ($/km)", "km en ville", "km hors ville"])

netlist.addLegend("Srural", ["S1", "S2", "S3"])
netlist.addLegend("Surbain", ["S1", "S2", "S3"])

netlist.addLegend("Drrural", ["km bus", "km train"])
netlist.addLegend("Drurbain", ["km bus", "km train"])

netlist.addLegend("$rrural", ["$ bus", "$ train"])
netlist.addLegend("$rurbain", ["$ bus", "$ train"])

# bounds (unchanged)
netlist.addBounds("b", 0, 1)
netlist.addBounds("x", [30, 0.3*autonomie_i, 0.5*mass_i],
                       [140, 3*autonomie_i, 2*mass_i])
netlist.addBounds("loi", [prixKwh*0.5, 0],
                         [prixKwh*8, subvention_i*2])
netlist.addBounds("p", p_i*0.5, p_i*2)

# Constants
PAurbain_i = 10000
PArural_i = 9000

netlist.add(Constant("Choix Techniques", "x", x_i))
netlist.add(Constant("Prix", "p", p_i))
netlist.add(Constant("Politique publique", "loi", loi_i))
netlist.add(Constant("Pondération Rural", "pondrural", pondrural_i))
netlist.add(Constant("Pondération Urbain", "pondurbain", pondurbain_i))

# alpha removed → no Pop.Visée block

# Engineering model
netlist.add(Block("Modèle d'ingénérie", modele_ingénerie, ["x"], ["SR"]))

# Economics & impacts
netlist.add(Block("Bénéfice economique", benefice_economique, ["Q", "p", "D"], ["$"]))
netlist.add(Block("Impact de la voiture", impact_voiture, ["Q", "D", "SR"], ["iv"]))
netlist.add(Block("Impact des autres transports", impact_autre_transports, ["$R", "Dr"], ["iav"]))
netlist.add(Block("Impact redirection des dépenses", impact_redirection_dépense, ["$autre"], ["ia"]))

netlist.add(Block("Somme", lambda a, b, c: [a + b + c], ["iv", "ia", "iav"], ["itot"]))

# Household blocks (alpha removed everywhere)
netlist.add(Constant("Besoins Urbain", "Burbain", Burbain_i))
netlist.add(Constant("Besoins Rural", "Brural", Brural_i))

netlist.add(Constant("PA Urbain", "PAurbain", PAurbain_i))
netlist.add(Constant("PA Rural", "PArural", PArural_i))

netlist.add(Block("Prix efficace", prix_efficace, ["p", "loi"], ["peff"]))

netlist.add(Block("Satisfaction Urbaine",
                  satisfaction_pop,
                  ["Burbain", "PAurbain", "peff", "SR", "loi", "pondurbain"],
                  ["Surbain"]))

netlist.add(Block("Satisfaction Rurale",
                  satisfaction_pop,
                  ["Brural", "PArural", "peff", "SR", "loi", "pondrural"],
                  ["Srural"]))

# Sales (Qrural, Qurbain) now depend only on satisfaction
netlist.add(Block("Ventes Rurale", lambda S: [np.linalg.norm(S) * Pi_rural], ["Srural"], ["Qrural"]))
netlist.add(Block("Ventes Urbaine", lambda S: [np.linalg.norm(S) * Pi_urbain], ["Surbain"], ["Qurbain"]))

# Distances without alpha
netlist.add(Block("Distance Rurale", lambda S, B: distance_avec_satisfaction(S, B, 1),
                  ["Srural", "Brural"], ["Drural"]))

netlist.add(Block("Distance Urbaine", lambda S, B: distance_avec_satisfaction(S, B, 0),
                  ["Surbain", "Burbain"], ["Durbain"]))

# Welfare (alpha removed)
netlist.add(Block("BE rural",
                  lambda CostR, CostRM, S: bien_etre(CostR, CostRM, 1, S),
                  ["$rural", "$rrural", "Srural"], ["BErural"]))

netlist.add(Block("BE urbain",
                  lambda CostU, CostUM, S: bien_etre(CostU, CostUM, 0, S),
                  ["$urbain", "$rurbain", "Surbain"], ["BEurbain"]))

netlist.add(Block("BE pondéré", lambda a, b: [a + b], ["BErural", "BEurbain"], ["BE"]))

# Costs
netlist.add(Block("Coût rural", cout_user_voiture,
                  ["Qrural", "peff", "Drural", "loi", "SR"], ["$rural", "Davg"]))

netlist.add(Block("Coût urbain", cout_user_voiture,
                  ["Qurbain", "peff", "Durbain", "loi", "SR"], ["$urbain", "Davg"]))

netlist.add(Block("Coût voiture total", lambda cu, cr: [cu + cr],
                  ["$urbain", "$rural"], ["$voiture"]))

# Modal shift
netlist.add(Block("Coût Report Modal Rural", cout_report_modal, ["Drrural"], ["$rrural"]))
netlist.add(Block("Coût Report Modal Urbain", cout_report_modal, ["Drurbain"], ["$rurbain"]))

netlist.add(Block("Distance Report Modal Rural", distance_avec_report_modal,
                  ["Rrural", "Brural"], ["Drrural"]))

netlist.add(Block("Distance Report Modal Urbain", distance_avec_report_modal,
                  ["Rurbain", "Burbain"], ["Drurbain"]))

netlist.add(Block("Coût Report Modal Total", lambda cu, cr: [cu + cr],
                  ["$rurbain", "$rrural"], ["$R"]))

netlist.add(Block("Distance Report Modal Total", lambda du, dr: [du + dr],
                  ["Drurbain", "Drrural"], ["Dr"]))

netlist.add(Block("$Transport", lambda R, V: [R[0] + R[1] + V],
                  ["$R", "$voiture"], ["$transport"]))

netlist.add(Block("Autre dépenses", autre_depenses, ["$transport"], ["$autre"]))

netlist.add(Block("Ventes totales", lambda a, b: [a + b], ["Qrural", "Qurbain"], ["Q"]))
netlist.add(Block("Distance totales", lambda a, b: [a + b], ["Drural", "Durbain"], ["D"]))

netlist.add(Block("Report Modal Rural", lambda S: [1 - np.linalg.norm(S)], ["Srural"], ["Rrural"]))
netlist.add(Block("Report Modal Urbain", lambda S: [1 - np.linalg.norm(S)], ["Surbain"], ["Rurbain"]))

traces = postProdNetlist(netlist)
