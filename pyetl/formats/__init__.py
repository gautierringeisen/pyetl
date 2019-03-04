# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 10:14:31 2019

@author: 89965

gestionaire de formats de traitements
les formats sont enregistres en les mettant dans des fichiers python qui
commencent par format_

"""
from types import MethodType
from .db import DATABASES
from .fichiers import READERS, WRITERS
from .geometrie import GEOMDEF
'''
geomdef = namedtuple("geomdef", ("reader", "converter"))

rdef = namedtuple("reader", ("reader", "geom", "has_schema", "auxfiles", "converter"))
wdef = namedtuple("writer", ("writer", "streamer",  "force_schema", "casse",
                                 "attlen", "driver", "fanout", "geom", "tmp_geom",
                                 "geomwriter", "tmpgeomwriter"))

'''
# assemblage avec les geometries
for nom in WRITERS:
    tmp = WRITERS[nom]
    WRITERS[nom] = tmp._replace(geomwriter=GEOMDEF[tmp.geom].writer,
                               tmpgeomwriter=GEOMDEF[tmp.tmp_geom].writer)

for nom in READERS:
    tmp = READERS[nom]
    READERS[nom] = tmp._replace(converter=GEOMDEF[tmp.geom].converter)




class Reader(object):
    '''wrappers d'entree génériques'''
    databases = DATABASES
    lecteurs = READERS
    geomdef = GEOMDEF
    @staticmethod
    def get_formats():
        return Reader.lecteurs
#    auxiliaires = AUXILIAIRES
#    auxiliaires = {a:AUXILIAIRES.get(a) for a in LECTEURS}


    def __init__(self, nom, regle, regle_start, debug=0):
        self.nom_format = nom
        self.debug = debug
        self.regle = regle # on separe la regle de lecture de la regle de demarrage
        self.regle_start = regle_start
        stock_param = regle_start.stock_param
        self.traite_objets = stock_param.moteur.traite_objet
        self.set_format_entree(nom)
        if self.debug:
            print("debug:format: instance de reader ", nom)

    def set_format_entree(self, nom):
        '''#positionne un format d'entree'''
        nom = nom.replace('.', '').lower()
        if nom in self.lecteurs:
#            lire, converter, cree_schema, auxiliaires = self.lecteurs[nom]
            descr = self.lecteurs[nom]
            self.lire_objets = MethodType(descr.reader, self)
            self.nom_format = nom
            self.cree_schema = descr.has_schema
            self.auxiliaires = descr.auxfiles
            self.conv_geom = self.get_converter(nom)
            if self.debug:
                print("debug:format: lecture format "+ nom, self.conv_geom)
        else:
            print("error:format: format entree inconnu", nom)
            raise KeyError

    def get_info(self):
        ''' affichage du format courant : debug '''
        print('info :format: format courant :', self.nom_format)

    def get_converter(self, format_natif=None):
        '''retourne la fonction de conversion geometrique'''
        if format_natif is None:
            return self.conv_geom
        fgeom = Reader.lecteurs.get(format_natif, Reader.lecteurs['interne']).geom
        return Reader.geomdef[fgeom].converter





class Writer(object):
    '''wrappers de sortie génériques'''
    databases = DATABASES
    sorties = WRITERS
    geomdef = GEOMDEF



    def __init__(self, nom, debug=0):
#        print ('dans writer', nom)

        self.dialecte = None
        destination = ''
        dialecte = ''
        if ':' in nom:
            defs = nom.split(':')
#            print ('decoupage writer', nom, defs,nom.split(':'))
            nom = defs[0]
            dialecte = defs[1]
            destination = defs[2] if len(defs) > 2 else ''
            fich = defs[3] if len(defs) > 3 else ''
        self.nom_format = nom
#        self.destination = destination
        self.regle = None
        self.debug = debug
        self.writerparms = dict() # parametres specifique au format
        '''#positionne un format de sortie'''
        nom = nom.replace('.', '').lower()
        if nom in self.sorties:
            self.def_sortie = self.sorties[nom]
#            ecrire, stream, tmpgeo, schema, casse, taille, driver, fanoutmax,\
#            nom_format = self.sorties[nom]
        else:
            print("format sortie inconnu '"+nom+"'", self.sorties.keys())
            self.def_sortie = self.sorties["#poubelle"]

#            ecrire, stream, tmpgeo, schema, casse, taille, driver, fanoutmax, nom_format =\
#                    self.sorties['#poubelle']
        if nom == 'sql':

            if dialecte == '':
                dialecte = 'natif'
            else:
                dialecte = dialecte if dialecte in self.databases else 'sql'
                self.writerparms['dialecte'] = self.databases[dialecte]
                self.writerparms['base_dest'] = destination
                self.writerparms['destination'] = fich
        else:
            self.writerparms['destination'] = destination
        self.dialecte = dialecte
#        self.conv_geom = self.geomdef[self.def_sortie.geom].converter

        self.ecrire_objets = self.def_sortie.writer
        self.ecrire_objets_stream = self.def_sortie.streamer
        self.tmp_geom = self.def_sortie.tmp_geom
        self.nom_fgeo = self.def_sortie.geom
        self.calcule_schema = self.def_sortie.force_schema
        self.minmaj = self.def_sortie.casse # determine si les attributs passent en min ou en maj
        self.driver = self.def_sortie.driver
        self.nom = nom
        self.l_max = self.def_sortie.attlen
        self.ext = '.'+nom
        self.multiclasse = self.def_sortie.fanout != 'classe'
        self.fanoutmax = self.def_sortie.fanout
#        print('writer : positionnement dialecte',nom, self.nom_format, self.writerparms)

    def get_info(self):
        ''' affichage du format courant : debug '''
        print('error:format: format courant :', self.nom_format)

    def get_geomwriter(self, format_natif=None):
        '''retourne la fonction de conversion geometrique'''
        if format_natif is None:
            return self.geomdef[self.nom].writer
        fgeom = self.sorties.get(format_natif, Writer.sorties['interne']).geom
        return self.geomdef[fgeom].writer
