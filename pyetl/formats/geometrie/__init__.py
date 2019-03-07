# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 13:22:59 2019

@author: 89965
"""
import os
from collections import namedtuple
from importlib import import_module

def loadmodules():
    '''lit toutes les descriptions de format depuis le repertoire courant
    et enregistre les readers et writers'''
    geomdef = namedtuple("geomdef", ("writer", "converter"))
    geomlist = dict()
    for fich_module in os.listdir(os.path.dirname(__file__)):
        if fich_module.startswith("format_"):
            module = "."+os.path.splitext(fich_module)[0]
            try:
                format_def = import_module(module, package=__package__)
                for nom, description in getattr(format_def, 'GEOMDEF').items():
#                    print('chargement geomdef', nom, description)
                    if nom in geomlist:
                        print('attention : redefinition du format de sortie', nom)
                    geomlist[nom] = geomdef(*description)

            except ImportError:
                print('module', module, 'non disponible')

    return geomlist


GEOMDEF = loadmodules()
