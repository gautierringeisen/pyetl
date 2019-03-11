# -*- coding: utf-8 -*-
'''moteur de traitement principal : gere l'enchainement des regles '''
import logging
from pyetl.formats.interne.objet import Objet  # objets et outils de gestiion
from .fonctions.outils import printexception
#import pyetl.schema.schema_io as SC
#import pyetl.schema.fonctions_schema as FSC

LOGGER = logging.getLogger('pyetl')


class Moteur(object):
    '''gestionnaire de traitements '''
    def __init__(self, mapper, regles, debug=0):
        self.regles = regles
        self.mapper = mapper
        self.debug = debug
        self.ident_courant = ''
        self.regle_debut = 0
        self.dupcnt = 0
        self.ncnt = 0
        self.suppcnt = 0

    @property
    def regle_sortir(self):
        ''' retourne la regle finale'''
        return self.regles[-1]


    def traitement_virtuel(self, unique=0):
        ''' cree un objet virtuel et le traite pour toutes les classes non utilisees '''

#        if self.debug != 0:
#        print("moteur: traitement virtuel", unique)
        LOGGER.info("traitement virtuel"+ str(unique))
#        for i in self.regles:
#            print (i.chargeur, i)
        if unique: # on lance un virtuel unique pour les traitements sans entree
            # on lance un virtuel unique puis on verifie toutes les regles de chargement
            self.traite_regles_chargement()
        else:
            for sch in list(self.mapper.schemas.values()):

                if sch.origine in 'LB' and not sch.nom.startswith('#'):
                    print('moteur: traitement schema', sch.nom, sch.origine, len(sch.classes))
                    LOGGER.info("traitement schema"+ sch.nom+' '+sch.origine)

                #(on ne traite que les schemas d'entree')
                    for schemaclasse in list(sch.classes.values()):
                        if schemaclasse.utilise:
#                            print ('traitement virtuel classe ignoree',schemaclasse.identclasse)
                            continue
#                        print('traitement objet virtuel ', schemaclasse.identclasse)
                        groupe, classe = schemaclasse.identclasse
                        obj = Objet(groupe, classe, conversion='virtuel', schema=schemaclasse)
                        obj.attributs['#categorie'] = 'traitement_virtuel'
#                        obj = Objet(groupe, classe)
#                        obj.virtuel = True
#                        obj.setschema(schemaclasse)
#                        obj.initattr()
                        obj.attributs['#type_geom'] = schemaclasse.info["type_geom"]
#                        print ('traitement obj',obj)
                        self.traite_objet(obj, self.regles[0])



    def traite_regles_chargement(self):
        ''' declenche les regles de chargement pour les traitements sans entree'''
#        if self.debug:
#        print('moteur: regles de chargement pour un traitement sans entree', self.regles[0].mode)
        self.regles[0].chargeur = True # on force la premiere
#        if self.regles[0].mode == "start": #on prends la main dans le script
#            self.regles[0].fonc(self.regles[0], None)
#            return
        for i in self.regles:
#            print ('-------------------------------traite_charge ', i.declenchee ,i.chargeur,i )
            if not i.declenchee and i.chargeur:
                if i.mode == "start": #on prends la main dans le script
                    i.fonc(i, None)
                obj = Objet('_declencheur', '_chargement', format_natif='interne',
                            conversion='virtuel')
                i.mode_chargeur = True
                self.traite_objet(obj, i)
                i.mode_chargeur = False



    def traite_objet(self, obj, regle):
        '''traitement basique toutes les regles sont testees '''
        while regle:
            last = regle
            regle.declenchee = True
            self.ncnt += 1
            try:
                if regle.selstd is None or regle.selstd(obj):
#                    print ('moteur:select', regle.numero, obj.ident, regle.fonc)
                    if regle.copy:
#                        print ('moteur: copie', regle.numero, regle.branchements.brch["copy"],
#                               regle.branchements.brch["fail"])
                        if not obj.virtuel:
                            self.traite_objet(obj.dupplique(),
                                              regle.branchements.brch["copy"])
                        # on envoie une copie dans le circuit qui ne passe pas la regle
                            self.dupcnt += 1
                        #print "apres copie ", obj.schema
    #                print("traitement regle",regle)
                    resultat = regle.fonc(regle, obj)
    #                print ('params:action schema',regle.params.att_sortie.liste,
#                           resultat,obj.schema,regle.action_schema)

                    if resultat:
                        if obj.schema is not None:
                            if regle.action_schema:
#                                print ('action schema',regle.action_schema)
#                                print ('schema avant',obj.schema)
                                regle.action_schema(regle, obj)
#                                print ('schema apres',obj.schema)
                            if regle.changeclasse:
                                regle.changeclasse(regle, obj)
                        if regle.changeschema:
                            regle.changeschema(regle, obj)

                    obj.is_ok = resultat

                    if regle.mode_chargeur: # la on fait des monocoups
                        regle = None
                    else:
                        if obj.redirect and obj.redirect in regle.branchements.brch:
                            regle = regle.branchements.brch[obj.redirect]
                            obj.redirect = None
                        else:
                            regle = regle.branchements.brch["ok"] if resultat\
                                    else regle.branchements.brch["fail"]

                else:
                    if regle.debug and '+' in regle.v_nommees['debug']:
                        regle.affiche('--non executee--->')
                        print('suite', regle.branchements.liens_num()["sinon"])
                    regle = regle.branchements.brch["sinon"]
            except StopIteration as abort:
#                print ('stopiteration', ab.args)
                if abort.args[0] == '1': # arret de traitement de l'objet
                    return
                raise # on la passe au niveau au dessus
            except NotADirectoryError as exc:
                print('==========erreur de traitement repertoire inconnu', exc)
                print('====regle courante:', regle)
#                printexception()
                raise StopIteration(3)

            except NotImplementedError as exc:
                print('==========erreur de traitement fonction inexistante', exc)
                print('====regle courante:', regle)
                raise StopIteration(3)

            except Exception as exc:
                print('==========erreur de traitement non gérée')
                print('====regle courante:', regle)
                printexception()
                if regle.getvar('debuglevel', '0') != "0":
                    print('==========environnement d\'execution')
                    print('====pyetl :', regle.stock_param.nompyetl, regle.stock_param.idpyetl)
                    print('====objet courant :', obj)
                    print("====parametres\n", regle.params)
                    print(regle.context)
                    if regle.getvar('debuglevel', '0') > '1':
                        print('========================= variables globales==========',
                              regle.stock_param.context)
                    print('========== fin erreur de traitement')

                raise StopIteration(3)
#                raise
        if not last.store:
            if last.filter or last.supobj:
                self.suppcnt += 1
            if obj.schema: # c est un objet qui a ete jete par une regle filtrante
                obj.schema.objcnt -= 1
#            print ('fin de l objet ', last.affiche(), obj.schema.schema.nom,
#                   obj.schema.identclasse, obj.schema.objcnt)



class Macro(object):
    """ structure de gestion des macros"""
    def __init__(self, nom, file=''):
        self.nom = nom
        self.file = file
        self.commandes_macro = dict()
        self.help = ''
        self.help_detaillee = []
        self.vpos = []

    def add_command(self, ligne, numero):
        ''' ajoute une commande a la liste'''
        if ligne.startswith('#!help'):
            self.help = ligne[6:]
            return
        if ligne.startswith('#!desc'):
            self.help_detaillee.append(ligne[6:])
            return
        self.commandes_macro[numero] = ligne


    def bind(self, liste):
        '''mappe les variables locales et retourne un dictionnaire'''
        return {nom:bind for nom, bind in zip(self.vpos, liste) if bind}


    def get_commands(self):
        """recupere les commandes de la macro"""
        return [(i, self.commandes_macro[i]) for i in sorted(self.commandes_macro)]

    def __repr__(self):
        """affichage lisible de la macro"""
        header = '&&#def;'+self.nom
        return '\n'.join([header]+[self.help]+self.help_detaillee+
                         [self.commandes_macro[i] for i in sorted(self.commandes_macro)])



class Context(object):
    """contexte de stockage d es variables"""
    def __init__(self, ref=None, parent=None):
        self.ref = self if ref is None else ref
        self.parent = parent
        self.vloc = dict()
        self.search = [self.vloc]
        if parent is not None:
            self.search.extend(parent.search)


    def getmacroenv(self):
        '''fournit un contexte ephemere lia au contexte de reference'''
        return Context(ref=self.ref, parent=self)

    def getcontext(self):
        '''fournit un nouveau contexte de reference empilé'''
        return Context(ref=None, parent=self)


    def getvar(self, nom, defaut=''):
        '''fournit la valeur d'un parametre selon des contextes standardises'''
#        if nom == 'nbaffich':
#            print ('chemin de recherche ',self.search)
        for c in self.search:
#            print ('getvar recherche', nom,' dans ', c)
            if nom in c:
                return c[nom]
        return defaut

    def getlocal(self, nom, defaut=''):
        '''fournit la valeur d'un parametre selon des contextes standardises'''
        return self.vloc.get(nom, defaut)


    def getgroup(self, prefix):
        '''fournit une liste de variables respectant un prefixe'''
        return {i:j for i, j in self.ref.vloc.items() if i.startswith(prefix)}


    def setvar(self, nom, valeur):
        """positionne une variable du contexte de reference"""
        self.ref.vloc[nom] = valeur


    def exists(self, nom):
        return nom in self.ref.vloc


    def update(self, valeurs):
        '''affectation en masse'''
        self.vloc.update(valeurs)


    def setlocal(self, nom, valeur):
        """positionne une variable locale du contexte"""
        self.ref.vloc[nom] = valeur

    def __repr__(self):
        return '==============================variables locales========\n' +\
                 '\n\t'+'\n\t'.join([i+':'+str(j) for i, j in sorted(self.vloc.items())])+\
                 '========================= variables globales==========\n'+\
                 '\n\t'+'\n\t'.join([i+':'+str(j) for i, j in sorted(self.ref.vloc.items())])

