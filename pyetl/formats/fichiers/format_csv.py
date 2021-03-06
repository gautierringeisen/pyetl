# -*- coding: utf-8 -*-
# formats d'entree sortie
"""gestion des formats d'entree et de sortie.
    actuellement les formats suivants sont supportes
    asc entree et sortie
    postgis text entree (a finaliser) et sortie
    csv entree et sortie
    shape entree et sortie
"""


import os
import csv
import codecs

# from numba import jit
from .fileio import FileWriter


def csvreader(reader, rep, chemin, fichier, entete=None, separ=None):
    reader.prepare_lecture_fichier(rep, chemin, fichier)
    logger = reader.regle_ref.stock_param.logger
    if separ is None:
        separ = reader.separ
    # nom_schema, nom_groupe, nom_classe = getnoms(rep, chemin, fichier)
    nbwarn = 0
    # print(" lecture_csv, separ:", separ, "<>", reader.encoding)
    with open(
        os.path.join(rep, chemin, fichier), newline="", encoding=reader.encoding
    ) as csvfile:
        sample = csvfile.read(4094)
        dialect = csv.Sniffer().sniff(sample)
        if entete is None:
            has_header = csv.Sniffer().has_header(sample) or sample.startswith("!")
            csvfile.seek(0)
            lecteur = csv.DictReader(csvfile, dialect=dialect)
            if has_header:
                entete = [
                    i.replace(" ", "_").replace("!", "") for i in lecteur.fieldnames
                ]
            else:
                entete = ["champ_" + str(i) for i in range(len(lecteur.fieldnames))]

        if entete[-1] == "tgeom" or entete[-1] == "geometrie":
            entete[-1] = "#geom"

        lecteur = csv.DictReader(
            csvfile, fieldnames=entete, dialect=dialect, restval="", restkey="#reste"
        )
        # print("entete csv", entete)
        if reader.newschema:
            for i in entete:
                if i[0] != "#":
                    reader.schemaclasse.stocke_attribut(i, "T")
        reader.prepare_attlist(entete)
        # print("attlist", reader.attlist)
        type_geom = "-1" if entete[-1] == "#geom" else "0"
        reader.fixe["#type_geom"] = type_geom
        for attributs in lecteur:
            obj = reader.getobj(attributs=attributs)
            # print(" recup objet", obj)
            if obj is None:
                continue  # filtrage entree
            reader.process(obj)


# def decode_entetes_csv(reader, entete, separ):
#     """prepare l'entete et les noma d'un fichier csv"""

#     noms_attributs = [
#         i.strip().replace(" ", "_").replace('"', "") for i in entete.split(separ)
#     ]

#     # on verifie que les noms existent et sont uniques
#     noms = set()

#     for i, nom in enumerate(noms_attributs):
#         if not nom:
#             noms_attributs[i] = "#champs_" + str(i)
#         if nom in noms:
#             noms_attributs[i] = nom + "_" + str(i)
#         noms.add(noms_attributs[i])

#     if noms_attributs[-1] == "tgeom" or noms_attributs[-1] == "geometrie":
#         noms_attributs[-1] = "#geom"
#         # geom = True
#         # noms_attributs.pop(-1)  # on supprime la geom en attribut classique
#     if reader.newschema:
#         for i in noms_attributs:
#             if i[0] != "#":
#                 reader.schemaclasse.stocke_attribut(i, "T")
#     #    else: # on adapte le schema force pur eviter les incoherences
#     #        schemaclasse.adapte_schema_classe(noms_attributs)

#     return noms_attributs


# def _controle_nb_champs(val_attributs, controle, nbwarn, ligne, logger):
#     """ ajuste le nombre de champs lus """
#     if len(val_attributs) < controle:
#         val_attributs.extend([""] * controle)
#     else:
#         nbwarn += 1
#         if nbwarn < 10:
#             logger.warning(
#                 "format csv : nombre de valeurs incorrect %d au lieu de %d",
#                 len(val_attributs),
#                 controle,
#             )

#             print(
#                 "warning: csv  : erreur format csv : nombre de valeurs incorrect",
#                 len(val_attributs),
#                 "au lieu de",
#                 controle,
#                 ligne[:-1],
#                 val_attributs,
#             )
#     return nbwarn


# def decoupage_soigne(ligne, separ):
#     """ de coupe une ligne en respectant les " """
#     cote = False
#     bloc = ""
#     decoup = []
#     escape = False
#     precote = False
#     for i in ligne:
#         if escape:
#             bloc += i
#         elif i == '"':
#             if precote:
#                 continue
#             cote = not cote
#             bloc += i
#         elif i == separ and not cote:
#             decoup.append(bloc)
#             bloc = ""
#         else:
#             precote = i == '"'
#             if i == "\\":
#                 escape = True
#             else:
#                 bloc += i
#     if bloc:
#         decoup.append(bloc.strip('" '))
#     return decoup


# def _lire_objets_csv(reader, rep, chemin, fichier, entete=None, separ=None):
#     """lit des objets a partir d'un fichier csv"""
#     reader.prepare_lecture_fichier(rep, chemin, fichier)
#     logger = reader.regle_ref.stock_param.logger
#     if separ is None:
#         separ = reader.separ
#     # nom_schema, nom_groupe, nom_classe = getnoms(rep, chemin, fichier)
#     nbwarn = 0
#     # print(" lecture_csv, separ:", separ, "<>", reader.encoding)
#     try:
#         with open(
#             os.path.join(rep, chemin, fichier), "r", encoding=reader.encoding
#         ) as fich:
#             if not entete:
#                 entete = fich.readline()[:-1]
#                 # si l'entete n'est pas fourni on le lit dans le fichier
#             if entete[0] == "!":
#                 entete = entete[1:]
#             elif reader.regle_ref.getvar("entete_csv", "") == "1":
#                 logger.info("entete csv forcee a la premiere ligne %s", entete)
#                 # print("entete csv forcee a la premiere ligne", entete)
#                 pass
#             else:  # il faut l'inventer...
#                 logger.warning("fichier csv sans entete")
#                 logger.info("indice: pour utiliser la premiere ligne comme entete")
#                 logger.info("mettre entete_csv=1 ou demarrer la premiere ligne par !")
#                 entete = separ * len(fich.readline()[:-1].split(separ))
#                 fich.seek(0)  # on remet le fichier au debut
#             noms_attributs = decode_entetes_csv(reader, entete, separ)
#             reader.prepare_attlist(noms_attributs)
#             type_geom = "-1" if noms_attributs[-1] == "#geom" else "0"
#             controle = len(noms_attributs)
#             nlignes = 0
#             for i in fich:
#                 # nlignes = nlignes + 1
#                 if i.startswith("!"):
#                     continue
#                 val_attributs = [j.strip('" ') for j in i[:-1].split(separ)]
#                 if len(val_attributs) != controle:
#                     val_attributs = decoupage_soigne(i[:-1], separ)
#                 # liste_attributs = zip(noms_attributs, val_attributs)
#                 # print ('lecture_csv:',[i for i in liste_attributs])
#                 if len(val_attributs) != controle:

#                     nbwarn = _controle_nb_champs(
#                         val_attributs, controle, nbwarn, i, logger
#                     )
#                 obj = reader.getobj(valeurs=val_attributs)
#                 if obj is None:
#                     continue  # filtrage entree
#                 # print ('attributs:',obj.attributs['nombre_de_servitudes'])
#                 # if geom:
#                 #     obj.geom = [val_attributs[-1]]
#                 #     #                print ('geometrie',obj.geom)
#                 obj.attributs["#type_geom"] = type_geom
#                 # else:
#                 #     obj.attributs["#type_geom"] = "0"
#                 obj.attributs["#chemin"] = chemin
#                 reader.process(obj)

#     except UnicodeError:
#         logger.error(
#             "erreur encodage le fichier %s n'est pas en %s", fichier, reader.encoding
#         )
#     if nbwarn:
#         logger.warning(" %d lignes avec un nombre d'attributs incorrect", nbwarn)
#     return


class CsvWriter(FileWriter):
    """ gestionnaire des fichiers csv en sortie """

    def __init__(self, nom, schema, regle):

        super().__init__(nom, schema=schema, regle=regle)
        self.headerfonc = str
        self.classes = set()
        self.errcnt = 0
        if self.schemaclasse:
            #            print ('writer',nom, schema.schema.init, schema.info['type_geom'])
            if self.schemaclasse.info["type_geom"] == "indef":
                self.schemaclasse.info["type_geom"] = "0"
            self.type_geom = self.schemaclasse.info["type_geom"]
            self.multi = self.schemaclasse.multigeom
            self.liste_att = self.schemaclasse.get_liste_attributs()
            self.force_courbe = self.schemaclasse.info["courbe"]
        else:
            print("attention csvwriter a besoin d'un schema", self.nom)
            raise ValueError("csvwriter: schema manquant")
        self.escape = "\\" + self.separ
        self.repl = "\\" + self.escape
        if len(self.separ) != 1:
            print("attention separateur non unique", self.separ)
            self.transtable = str.maketrans({"\n": "\\" + "n", "\r": "\\" + "n"})
        else:
            self.transtable = str.maketrans(
                {"\n": "\\" + "n", "\r": "\\" + "n", self.separ: self.escape}
            )

    def header(self, init=1):
        """ preparation de l'entete du fichiersr csv"""
        # print("csvheader ", self.entete)
        entete = self.writerparms.get("entete")
        if not entete:
            #            raise
            return ""
        geom = (
            self.separ + self.headerfonc("geometrie") + "\n"
            if self.schemaclasse.info["type_geom"] != "0"
            else "\n"
        )
        return (
            ("" if entete == "csv_f" else "!")
            + self.separ.join([self.headerfonc(i) for i in self.liste_att])
            + geom
        )

    def prepare_attributs(self, obj):
        """ prepare la es attributs en fonction du format"""
        atlist = (
            str(obj.attributs.get(i, "")).translate(self.transtable)
            for i in self.liste_att
        )
        #        print ('ectriture_csv',self.schema.type_geom, obj.format_natif,
        #                obj.geomnatif, obj.type_geom)
        #        print ('orig',obj.attributs)
        attributs = self.separ.join((i if i else self.null for i in atlist))
        return attributs

    def write(self, obj):
        """ecrit un objet"""
        if obj.virtuel:
            return False  #  les objets virtuels ne sont pas sortis
        attributs = self.prepare_attributs(obj)
        if self.type_geom != "0":
            if (
                obj.format_natif == self.writerparms["geom"] and obj.geomnatif
            ):  # on a pas change la geometrie
                geom = obj.attributs["#geom"]
                if not geom:
                    geom = self.null
            #                print("sortie ewkt geom0",len(geom))
            else:
                if obj.initgeom():
                    # print ("geomwriter",self.geomwriter)
                    geom = self.geomwriter(
                        obj.geom_v, self.type_geom, self.multi, obj.erreurs
                    )
                else:
                    if not obj.attributs["#geom"]:
                        geom = self.null
                    else:
                        if self.errcnt < 10:
                            print(
                                "csv: geometrie invalide : erreur geometrique",
                                obj.ident,
                                obj.numobj,
                                "demandé:",
                                self.type_geom,
                                obj.geom_v.erreurs.errs,
                                obj.attributs["#type_geom"],
                                self.schema.info["type_geom"],
                                "->" + repr(obj.attributs["#geom"]) + "<-",
                            )
                        self.errcnt += 1
                        geom = self.null

                if obj.erreurs and obj.erreurs.actif == 2:
                    print(
                        "error: writer csv :",
                        self.extension,
                        obj.ident,
                        obj.ido,
                        "erreur geometrique: type",
                        obj.attributs["#type_geom"],
                        "demandé:",
                        obj.schema.info["type_geom"],
                        obj.erreurs.errs,
                        "->" + repr(obj.attributs["#geom"]) + "<-",
                    )
                    print("prep ligne ", attributs, "\nG:", geom)
                    print("geom initiale", obj.attributs["#geom"])
                    return False

            if not geom:
                geom = self.null
            obj.format_natif = "#ewkt"
            obj.attributs["#geom"] = geom
            obj.geomnatif = True
            ligne = attributs + self.separ + geom
        else:
            ligne = attributs
        if self.writerparms.get("nodata"):
            return False

        # print("ecriture csv", ligne, obj, self.liste_att)

        self.fichier.write(ligne)
        self.fichier.write("\n")
        return True


class SqlWriter(CsvWriter):
    """getionnaire decriture sql en fichier"""

    def __init__(self, nom, schema, regle):
        super().__init__(nom, schema, regle)
        if self.writerparms:
            self.schemaclasse.setsortie(self.output)
        self.transtable = str.maketrans(
            {"\\": r"\\", "\n": "\\" + "n", "\r": "\\" + "n", self.separ: self.escape}
        )
        self.htranstable = str.maketrans(
            {
                "\\": r"\\",
                "\n": "\\" + "n",
                "\r": "\\" + "n",
                '"': r'\\"',
                self.separ: self.escape,
            }
        )

    def __repr__(self):
        return "sqlwriter " + self.nom

    def prepare_hstore(self, val):
        """ gere le cas particulier du hstore """

    def prepare_attributs(self, obj):
        """ prepare les attributs en fonction du format"""
        if obj.hdict:
            # atlist = []
            atlist = (
                ",".join(
                    [
                        '"' + i + '"=>"' + str(j).translate(self.htranstable) + '"'
                        for i, j in sorted(obj.hdict[nom].items())
                    ]
                )
                if nom in obj.hdict
                else str(obj.attributs.get(nom, "")).translate(self.transtable)
                for nom in self.liste_att
            )

        else:
            atlist = (
                str(obj.attributs.get(i, "")).translate(self.transtable)
                for i in self.liste_att
            )

        return self.separ.join((i if i else self.null for i in atlist))

    def header(self, init=1):
        separ = ", "
        gensql = self.schema.dbsql
        if not gensql:
            print(
                "header sql: erreur generateur sql non defini",
                self.schema.nom,
                self.schemaclasse.identclasse,
                self.schema.format_sortie,
            )
            raise StopIteration(3)
        niveau, classe = self.schemaclasse.identclasse
        nouveau = self.schemaclasse.identclasse not in self.classes
        self.classes.add(self.schemaclasse.identclasse)
        gensql.regle_ref = self.regle_ref
        prefix = "SET client_encoding = 'UTF8';\n" if init else ""
        #        print ('parametres sql ', self.writerparms)
        nodata = False

        type_geom = self.schemaclasse.info["type_geom"]
        dim = self.schemaclasse.info["dimension"]

        if self.writerparms and nouveau:
            reinit = self.writerparms.get("reinit")
            #            dialecte = self.writerparms.get('dialecte', 'sql')
            nodata = self.writerparms.get("nodata")

            gensql.initschema(self.schemaclasse.schema)
            # on positionne les infos de schema pour le generateur sql

            prefix = prefix + gensql.prefix_charge(
                niveau, classe, reinit, gtyp=type_geom, dim=dim
            )

        if nodata:
            return prefix
        prefix = prefix + 'copy "' + niveau.lower() + '"."' + classe.lower() + '" ('
        end = ") FROM stdin;"

        geom = (
            separ + "geometrie" + end + "\n"
            if self.schemaclasse.info["type_geom"] != "0"
            else end + "\n"
        )
        return (
            prefix
            + separ.join([gensql.ajuste_nom_q(i.lower()) for i in self.liste_att])
            + geom
        )

    def fin_classe(self):
        """fin de classe pour remettre les sequences"""
        reinit = self.writerparms.get("reinit", "0")
        niveau, classe = self.schemaclasse.identclasse
        gensql = self.schema.dbsql
        gensql.regle_ref = self.regle_ref
        type_geom = self.schemaclasse.info["type_geom"]
        courbe = self.schemaclasse.info["courbe"]
        dim = self.schemaclasse.info["dimension"]
        if not gensql:
            print(
                "finclasse sql: erreur generateur sql non defini",
                self.schemaclasse.identclasse,
                self.schema.format_sortie,
            )
            raise StopIteration(3)
        if self.fichier.closed:
            self.reopen()
        if self.writerparms.get("nodata"):
            self.fichier.write(
                gensql.tail_charge(niveau, classe, reinit, schema=self.schemaclasse)
            )
            return
        self.fichier.write(r"\." + "\n")

        self.fichier.write(
            gensql.tail_charge(
                niveau,
                classe,
                reinit,
                gtyp=type_geom,
                dim=dim,
                courbe=courbe,
                schema=self.schemaclasse,
            )
        )

    def finalise(self):
        """ligne de fin de fichier en sql"""
        self.fin_classe()
        super().finalise()
        return 3  # on ne peut pas le reouvrir

    def changeclasse(self, schemaclasse, attributs=None):
        """ ecriture de sql multiclasse on cree des entetes intermediaires"""
        #        print( 'dans changeclasse')
        # raise
        self.fin_classe()
        self.schemaclasse = schemaclasse
        if schemaclasse.info["type_geom"] == "indef":  # pas de geometrie
            schemaclasse.info["type_geom"] = "0"
        self.type_geom = schemaclasse.info["type_geom"]
        self.multi = schemaclasse.multigeom
        self.liste_att = schemaclasse.get_liste_attributs(attributs)
        self.fichier.write(self.header(init=0))


def csvstreamer(writer, obj, regle, _):
    """ ecrit des objets csv en streaming"""
    #    sorties = regle.stock_param.sorties
    if regle.dident != obj.ident:
        regle.ressource = writer.change_ressource(obj)
        regle.dident = obj.ident

    regle.ressource.write(obj, regle.idregle)


def initwriter(self, extension, header, separ, null, writerclass=CsvWriter):
    """positionne les parametres du writer csv (sql et txt)"""
    # print ('initialisation writer', extension, header,separ,null)
    self.writerparms["separ"] = separ
    self.writerparms["extension"] = extension
    self.writerparms["entete"] = header
    self.writerparms["null"] = null
    self.writerclass = writerclass


def init_csv(self):
    """writer csv"""
    separ = self.regle.getchain(("separ_csv_out", "separ_csv"), ";")
    if separ == r"\;":
        separ = ";"
    self.regle.stock_param.logger.info(
        "init writer csv separateur: %s (%s)", separ, self.regle.getvar("separ_csv_out")
    )
    self.regle.stock_param.logger.debug(
        "init writer csv parametres: %s ", repr(self.writerparms)
    )
    headerdef = self.regle.getvar("csvheader")
    header = "csv_f" if "no!" in headerdef else "csv"
    initwriter(self, "csv", header, (";" if separ == "#std" else separ), "")
    if "up" in headerdef:
        self.headerfonc = str.upper
    elif "low" in headerdef:
        self.headerfonc = str.lower
    else:
        self.headerfonc = str
    # print("initwriter csv separateur:", separ, headerdef, header,self.headerfonc)


def init_txt(self):
    """writer txt separateur tab pour le mode copy de postgres"""
    separ = self.regle.getchain(("separ_txt_out", "separ_txt"), "\t")
    initwriter(self, "txt", False, ("\t" if separ == "#std" else separ), "")


def init_geo(self):
    """writer geo covadis"""
    initwriter(self, "geo", False, "  ", "")


def init_sql(self):
    """writer sql :  mode copy avec gestion des triggers et des sequences """
    initwriter(self, "sql", "sql", "\t", r"\N", writerclass=SqlWriter)


def lire_objets_txt(self, rep, chemin, fichier):
    """format sans entete le schema doit etre fourni par ailleurs"""
    separ = self.regle_ref.getchain(("separ_txt_in", "separ_txt"), "\t")
    schema = self.regle_ref.stock_param.schemas.get(
        self.regle_ref.getvar("schema_entree")
    )
    if schema:
        # geom = separ + "geometrie" + "\n" if schema.info["type_geom"] else "\n"
        # entete = separ.join(schema.get_liste_attributs()) + geom
        entete = schema.get_liste_attributs()
        if schema.info["type_geom"] > "0":
            entete.append("geometrie")
    else:
        entete = None
    return csvreader(self, rep, chemin, fichier, entete=entete)

    # return _lire_objets_csv(self, rep, chemin, fichier, entete, separ=separ)


def lire_objets_csv(self, rep, chemin, fichier):
    """format csv en lecture"""
    return csvreader(self, rep, chemin, fichier)


# writer, streamer, force_schema, casse, attlen, driver, fanout, geom, tmp_geom,initer)
WRITERS = {
    "csvj": ("", "", True, "low", 0, "csv", "classe", "#geojson", "#ewkt", init_csv),
    "csv": ("", "", True, "low", 0, "csv", "classe", "#ewkt", "#ewkt", init_csv),
    "txt": ("", "", True, "low", 0, "txt", "classe", "#ewkt", "#ewkt", init_txt),
    "sql": ("", "", True, "low", 0, "txt", "all", "#ewkt", "#ewkt", init_sql),
    "geo": ("", "", True, "low", 0, "txt", "classe", "#ewkt", "#ewkt", init_geo),
}

#                  reader,geom,hasschema,auxfiles,initer
READERS = {
    "csv": (lire_objets_csv, "#ewkt", True, (), None, None),
    "txt": (lire_objets_txt, "#ewkt", True, (), None, None),
}
