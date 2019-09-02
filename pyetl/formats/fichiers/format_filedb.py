# -*- coding: utf-8 -*-
"""
Created on Fri Oct 21 13:20:44 2016

@author: 89965
vrapper virtuel permettant d'acceder a des bases monofichier
type access, sqlite... en envoyant un objet virtuel a un lecteur de base de donnees

"""
import os

# from .db import DATABASES
# types de bases fichier connues


def lire_objets_fdb(self, rep, chemin, fichier):
    """ prepare l objet virtuel declencheur pour la lecture en base access ou sqlite"""
    #    type_base = {".mdb":"access",
    #                 ".sqlite":"sqlite"}
    type_base = {
        self.databases[i].fileext: i
        for i in self.databases
        if self.databases[i].svtyp == "file"
    }
    #    regle = stock_param.regles[0]
    base, ext = os.path.splitext(fichier)
    #    stock_param.parms["serveur_"+base]=chemin
    self.setidententree("__filedb", base)
    obj = self.getobj()
    obj.attributs["#racine"] = rep
    obj.attributs["#chemin"] = chemin
    obj.attributs["#nombase"] = base
    obj.attributs["#base"] = os.path.join(rep, chemin, fichier)
    force = self.regle_ref.getvar("F_entree")
    type_base_demande = "." + force if force else ext
    type_base_trouve = type_base.get(type_base_demande)
    if type_base_trouve:
        obj.attributs["#type_base"] = type_base_trouve
        #        obj.debug("filedb:virtuel")
        obj.virtuel = True
        #        print ('traitement filedb: ', obj.attributs["base"])
        self.process(obj)
        return 1
    print("error: fildb: type_base inconnu", type_base_demande)
    return 0


READERS = {
    "mdb": (lire_objets_fdb, "", True, (), None),
    "accdb": (lire_objets_fdb, "", True, (), None),
    "sqlite": (lire_objets_fdb, "", True, (), None),
    "spatialite": (lire_objets_fdb, "#ewkt", True, (), None),
}

WRITERS = {}
