# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 14:34:04 2015

@author: 89965
fonctions de chargement web up/download http et ftp + acces web services
"""
import logging
import os
import io
import requests
import ftplib
import csv
import json

try:
    import pysftp

    SFTP = True
except ImportError:
    SFTP = False
import time

LOGGER = logging.getLogger(__name__)


def geocode_traite_stock(regle, final=True):
    """libere les objets geocodes """
    if regle.nbstock == 0:
        return
    flist = list(regle.filtres.values())
    adlist = regle.params.att_entree.liste
    prefix = regle.params.cmp1.val
    outcols = 2 + len(flist)
    header = []
    suite = regle.branchements.brch["end"]
    fail = regle.branchements.brch["fail"]
    traite = regle.stock_param.moteur.traite_objet
    geocodeur = regle.getvar("url_geocodeur")
    data = {"columns": "_adresse"}.update(regle.filtres)
    buffer = (
        ";".join(["ident", "_adresse"] + flist)
        + "\n"
        + "\n".join(
            [
                str(n)
                + ";"
                + " ".join(
                    [
                        obj.attributs.get(i, "").replace("\n", " ").replace('"', "")
                        for i in adlist
                    ]
                )
                + (
                    (
                        ";"
                        + ";".join(
                            [
                                obj.attributs.get(i, "")
                                .replace("\n", " ")
                                .replace('"', "")
                                for i in flist
                            ]
                        )
                    )
                    if flist
                    else ""
                )
                for n, obj in enumerate(regle.tmpstore)
            ]
        )
    ).encode("utf-8")

    # print('geocodage', regle.nbstock, adlist,flist, data)

    files = {"data": io.BytesIO(buffer)}
    try:
        res = requests.post(geocodeur, files=files, data=data)
    except requests.RequestException as prob:
        print("url geocodeur defectueuse", geocodeur)
        print("exception levee", prob)

        raise StopIteration(2)
    # print ('retour', res.text)

    #        print ('retour ',buf)
    for row in csv.reader(res.text.split("\n"), delimiter=";"):
        attributs = row
        if not attributs:
            continue

        if attributs[0].isnumeric():
            numero = int(attributs[0])
            obj = regle.tmpstore[numero]
            obj.attributs.update(
                [(nom, contenu) for nom, contenu in zip(header, attributs[outcols:])]
            )
            # print ('retour',obj)
            score = obj.attributs.get("result_score", "")
            if not score:
                print("erreur geocodage", attributs)
            traite(obj, suite if score else fail)
        elif not header:
            header = [prefix + i for i in attributs[outcols:]]
            # print ('calcul header', header)
            obj = regle.tmpstore[0]
            if obj.schema:
                # print ('geocodage action schema',regle.action_schema, header)
                obj.schema.force_modif(regle)
                regle.liste_atts = header
                regle.action_schema(regle, obj)
                # print ('schema :', obj.schema)
        else:
            if not final:
                print("geocodeur: recu truc etrange ", attributs)
                # print("retry")
                # geocode_traite_stock(regle, final=True)
                return

    # and regle in obj.schema.regles_modif
    regle.traite += regle.nbstock
    regle.nbstock = 0
    if not regle.getvar("_testmode"):
        print(
            "geocodage %d objets en %d secondes (%d obj/sec)"
            % (
                regle.traite,
                int(time.time() - regle.tinit),
                regle.traite / (time.time() - regle.tinit),
            )
        )
    regle.tmpstore = []


def h_geocode(regle):
    """ prepare les espaces de stockage et charge le geocodeur addok choisi"""
    if not regle.getvar("_testmode"):
        LOGGER.info("geocodeur utilise  %s", regle.getvar("url_geocodeur"))
        # print("geocodeur utilise ", regle.getvar("url_geocodeur"))
        LOGGER.info("liste_filtres demandes %s", regle.params.cmp2.val)
        # print("liste_filtres demandes", regle.params.cmp2.liste)
    regle.blocksize = int(regle.getvar("geocodeur_blocks", 1000))
    regle.store = True
    regle.nbstock = 0
    regle.traite = 0
    regle.traite_stock = geocode_traite_stock
    regle.tmpstore = []
    regle.liste_atts = []
    regle.scoremin = 0
    regle.filtres = dict(i.split(":") for i in regle.params.cmp2.liste)
    #    regle.ageocoder = dict()
    regle.tinit = time.time()
    return True


def f_geocode(regle, obj):
    """#aide||geocode des objets en les envoyant au gecocodeur addict
    #aide_spec||en entree clef et liste des champs adresse a geocoder score min pour un succes
    #parametres||liste attributs adresse;;confiance mini;liste filtres
    #pattern||;;L;geocode;?C;?LC
    #schema||ajout_att_from_liste
    #req_test||url_geocodeur
    #test||obj||^X;1 parc de l'etoile Strasbourg;;set||^;;X;geocode;;||atv:result_housenumber:1
    """
    #    clef = obj.attributs.get(regle.params.cmp1.val)
    #    print("avant geocodeur", regle.nbstock)
    regle.tmpstore.append(obj)
    #    regle.ageocoder[clef] = ";".join([obj.attributs.get(i,"")
    #                                      for i in regle.params.att_entree.liste])
    #    print("geocodeur", regle.nbstock)
    regle.nbstock += 1
    if regle.nbstock >= regle.blocksize:
        regle.traite_stock(regle, final=False)
    return True


def h_ftpupload(regle):
    """prepare les parametres ftp"""
    if regle.params.pattern == "1":
        regle.chargeur = True
    codeftp = regle.params.cmp1.val
    regle.ftp = None
    if codeftp:
        serveur = regle.context.getvar("server_" + codeftp, "")
        servertyp = regle.context.getvar("ftptyp_" + codeftp, "")
        user = regle.context.getvar("user_" + codeftp, "")
        passwd = regle.context.getvar("passwd_" + codeftp, regle.params.cmp2.val)
        regle.setlocal("acces_ftp", (codeftp, serveur, servertyp, user, passwd))
        regle.servertyp = servertyp
        regle.destdir = regle.params.cmp2.val
    else:  # connection complete dans l'url
        regle.servertyp = "direct"
        # regle.destdir = getftpinfo(regle, regle.params.cmp2.val)


def getftpinfo(regle, fichier):
    """extrait l'info ftp de l'url"""
    if fichier.startswith("ftp://"):
        servertyp = "ftp"
        fichier = fichier[6:]
    elif fichier.startswith("sftp://"):
        servertyp = "sftp"
        fichier = fichier[7:]
    else:
        print("service FTP inconnu", fichier, regle)
        raise ftplib.error_perm
    acces, elem = fichier.split("@", 1)
    user, passwd = acces.split(":", 1)
    serveur, fich = elem.split("/", 1)
    codeftp = "tmp"
    regle.setlocal("acces_ftp", (codeftp, serveur, servertyp, user, passwd))
    return fich


def ftpconnect(regle):
    """connection ftp"""
    _, serveur, servertyp, user, passwd = regle.getvar("acces_ftp")
    if regle.debug:
        print("ouverture acces ", regle.getvar("acces_ftp"))
    try:
        if servertyp == "tls":
            regle.ftp = ftplib.FTP_TLS(host=serveur, user=user, passwd=passwd)
            return True
        elif servertyp == "ftp":
            regle.ftp = ftplib.FTP(host=serveur, user=user, passwd=passwd)
            return True
    except ftplib.error_perm as err:
        print("!!!!! erreur ftp: acces non autorisé", serveur, servertyp, user, passwd)
        print("retour_erreur", err)
        return False
    if servertyp == "sftp" and SFTP:
        try:
            cno = pysftp.CnOpts()
            cno.hostkeys = None
            regle.ftp = pysftp.Connection(
                serveur, username=user, password=passwd, cnopts=cno
            )
            return True
        except pysftp.ConnectionException as err:
            print(
                "!!!!! erreur ftp: acces non autorisé", serveur, servertyp, user, passwd
            )
            print("retour_erreur", err)
            return False
    else:
        print("mode ftp non disponible", servertyp)
        return False


def f_ftpupload(regle, obj):
    """#aide||charge un fichier sur ftp
    #aide_spec||;nom fichier; (attribut contenant le nom);ftp_upload;ident ftp;chemin ftp
      #pattern1||;?C;?A;ftp_upload;?C;?C
      #pattern2||;=#att;A;ftp_upload;?C;C
         #test||notest
    """
    filename = regle.getval_entree(obj)
    destname = regle.destdir + "/" + str(os.path.basename(filename))

    # destname = regle.destdir
    if not regle.ftp:
        retour = ftpconnect(regle)
        if not retour:
            return False
        if regle.debug:
            print("connection ftp etablie")

    try:
        # print ('envoi fichier',filename,'->',destname)
        if regle.servertyp == "sftp":
            regle.ftp.cwd(regle.destdir)
            regle.ftp.put(filename)
            if regle.debug:
                print("transfert effectue", filename, "->", destname)
        else:
            if regle.params.pattern == "2":
                input = io.BytesIO()
                input = obj.attributs[regle.params.att_entree.val].encode("utf8")
                regle.ftp.storbinary("STOR " + destname, input.read)
                input.close()
            else:
                localfile = open(filename, "rb")
                regle.ftp.storbinary("STOR " + destname, localfile)
                localfile.close()
            if regle.debug:
                print("transfert effectue", filename, "->", destname)
        return True

    except ftplib.all_errors as err:
        print("!!!!! erreur ftp:", err)
        LOGGER.error(
            "ftp upload error: Houston, we have a %s", "major problem", exc_info=True
        )
        return False


def f_ftpdownload(regle, obj):
    """#aide||charge un fichier sur ftp
    #aide_spec||;nom fichier; (attribut contenant le nom);ftp_download;ident ftp;repertoire
     #pattern1||;?C;?A;ftp_download;C;?C
     #pattern2||;?C;?A;ftp_download;;
     #pattern3||A;?C;?A;ftp_download;;
     #pattern4||A;?C;?A;ftp_download;C;?C
       #helper||ftpupload
         #test||notest
    """
    filename = regle.getval_entree(obj)
    if regle.servertyp == "direct":
        filename = getftpinfo(regle, regle.getval_entree(obj))
    if not regle.ftp:
        retour = ftpconnect(regle)
        if not retour:
            return False
        if regle.debug:
            print("connection ftp etablie")
    if not regle.params.att_sortie.val:
        localdir = regle.getvar("localdir", os.path.join(regle.getvar("_sortie", ".")))
        localname = os.path.join(localdir, filename)
        os.makedirs(os.path.dirname(localname), exist_ok=True)
        if regle.debug:
            print("creation repertoire", os.path.dirname(localname))
    else:
        localname = "[" + regle.params.att_sortie.val + "]"
        localdir = "."

    try:
        if regle.servertyp == "sftp":
            if regle.debug:
                print("choix repertoire", regle.destdir)
            regle.ftp.cwd(regle.destdir)
            if filename == "*":
                regle.ftp.get_d(".", localdir, preserve_mtime=True)
            elif filename == "*/*":
                regle.ftp.get_r(".", localdir, preserve_mtime=True)
            else:
                regle.ftp.get(filename, localpath=localname, preserve_mtime=True)
        else:
            if regle.params.att_sortie.val:
                output = io.BytesIO()
                regle.ftp.retrbinary("RETR " + filename, output.write)
                obj.attributs[regle.params.att_sortie.val] = output.getvalue().decode(
                    "utf8"
                )
                output.close()
            else:
                localfile = open(localname, "wb")
                regle.ftp.retrbinary("RETR " + filename, localfile.write)
                localfile.close()
        if regle.debug:
            print("transfert effectue", filename, "->", localname)
        return True

    except ftplib.all_errors as err:
        print("!!!!! erreur ftp:", err)
        LOGGER.error(
            "ftp download error: Houston, we have a %s", "major problem", exc_info=True
        )
        return False


def _to_dict(parms):
    """transforme un texte de type aa:yy,tt:vv en dictionnaire"""
    if not parms:
        return dict()
    if "'" in parms:
        # il y a des cotes
        cot=False
        groups=[]
        group=""
        for i in parms:
            if i=="'":
                cot=not cot
            elif i=="," and not cot:
                groups.append(group)
                group=""
            else:
                group+=i
        if group:
            groups.append(group)
        return dict([k.split(":", 1) for k in groups  ] )
    return dict([k.split(":", 1) for k in parms.split(",")])


def h_httpdownload(regle):
    """prepare les parametres http"""
    regle.chargeur = True
    path = regle.params.cmp1.val if regle.params.cmp1.val else regle.getvar("_sortie")
    if path:
        os.makedirs(path, exist_ok=True)
    regle.path = path
    if regle.params.cmp2.val:
        name = os.path.join(path, regle.params.cmp2.val)
        regle.fichier = name
    else:
        regle.fichier = None

    regle.httparams = _to_dict(regle.getvar("http_params"))
    regle.httheaders = _to_dict(regle.getvar("http_header"))
    # print("preparation parametres", regle.httparams, regle.httheaders)
    regle.valide=True
    return True

def _jsonsplitter(regle,obj,jsonbloc):
    """decoupe une collection json en objets"""
    struct=json.loads(jsonbloc)
    for elem in struct:
        if isinstance(elem,dict):
            obj2=obj.dupplique()
            obj2.virtuel=False
            for att,val in elem.items():
                if isinstance(val,str):
                    obj2.attributs[att]=val
                elif isinstance(val,dict):
                    hdict={i:json.dumps(j,separators=(',', ':')) for i,j in val.items()}
                    obj2.sethtext(att, dic=hdict)
                elif isinstance(val,list):
                    jlist=[json.dumps(j,separators=(',', ':')) for j in val]
                    obj2.setmultiple(att,liste=jlist)
            regle.stock_param.moteur.traite_objet(obj2, regle.branchements.brch["gen"])
        else:
            print ("element incompatible", elem)



def f_httpdownload(regle, obj):
    """aide||telecharge un fichier via http
    #aide_spec||; url; (attribut contenant l'url);http_download;racine;nom
      #pattern1||;?C;?A;download;?C;?C
      #pattern2||A;?C;?A;download
      #pattern3||;?C;?A;download;=#B||cmp1
      #pattern4||;?C;?A;download;=#json||cmp1
         #test||notest
    """
    url = regle.getval_entree(obj)

    # if regle.httparams:
    retour = None
    try:
        retour = requests.get(
            url,
            stream=regle.params.pattern == "1",
            params=regle.httparams,
            headers=regle.httheaders,
        )
    except:
        LOGGER.error("connection impossible %s", retour.url if retour else url)
        return False

    # else:
    #     retour = requests.get(url, stream=regle.params.pattern == "1")
    if regle.debug:
        print("telechargement", url, retour.url if retour else url)
        print("info", retour.headers)
    obj.sethtext("#http_header", dic=retour.headers)
    taille = int(retour.headers.get("Content-Length", 0))

    if regle.params.pattern == "2":  # retour dans un attribut
        if regle.getvar("http_encoding"):
            retour.encoding = regle.getvar("http_encoding")

        regle.setval_sortie(obj, retour.text)
        # if obj.virtuel and obj.attributs["#classe"] == "_chargement":  # mode chargement
        #     regle.stock_param.moteur.traite_objet(obj, regle.branchements.brch["gen"])
        # print("retour requests", retour.encoding)
        return True
    elif regle.params.pattern=="3":
        regle.setval_sortie(obj, retour.content)
        return True
    elif regle.params.pattern=="4":
        _jsonsplitter(regle,obj,retour.text)
        return True
    if regle.fichier is None:
        fichier = os.path.join(regle.path, os.path.basename(url))
    else:
        fichier = regle.fichier

    decile = taille / 10 if taille else 100000
    recup = 0
    bloc = 4096
    nb_pts = 0
    nblocs = 0
    debut = time.time()
    if retour.status_code == 200:
        with open(fichier, "wb") as fich:
            for chunk in retour.iter_content(bloc):
                nblocs+=1
                recup += bloc  # ca c'est la deco avec des petits points ....
                if recup > decile:
                    recup = recup - decile
                    nb_pts += 1
                    print(".", end="", flush=True)
                fich.write(chunk)
        if nblocs*bloc>taille:
            taille=nblocs*bloc
        print(
            "    ",
            taille,
            "octets télecharges en ",
            int(time.time() - debut),
            "secondes",
        )
        return True
    LOGGER.error("erreur requete %s", retour.url )
    LOGGER.error("headers %s", str(retour.request.headers) )
    # print ("==========erreur requete==========")
    # print ("request url", retour.url)
    # print ("request headers", retour.request.headers)
    LOGGER.error("retour statut %s", retour.status_code )
    LOGGER.error("headers %s", str(retour.headers) )
    LOGGER.error("text %s", str(retour.text) )

    # print ("============retour================")
    # print ("statuscode", retour.status_code)
    # print ("headers", retour.headers)
    # print ("text", retour.text)
    return False


def h_wfsdownload(regle):
    """prepare les parametres http"""
    regle.chargeur = True
    regle.path = None
    if regle.params.pattern == "1":
        path = regle.params.att_sortie.val
        if not os.path.isabs(path):
            path = os.path.join(regle.getvar("_sortie"), path)
        regle.path = path

    regle.wfsparams = {"SERVICE": "WFS"}
    regle.wfsparams["OUTPUTFORMAT"] = "text/xml"
    if regle.params.cmp2.val == "json":
        regle.wfsparams["OUTPUTFORMAT"] = "json"


def f_wfsdownload(regle, obj):
    """aide||recupere une couche wfs
    #aide_spec||; classe;  attribut contenant la classe;wfs;url;format
      #pattern1||F;?C;?A;wfsload;C;?C
      #pattern2||A;?C;?A;wfsload;C;?C
         #test||notest
    """
    # https://data.strasbourg.eu/api/wfs?
    # TYPENAME=ods%3Asections_cadastrales&REQUEST=GetFeature
    # &RESULTTYPE =RESULTS
    # &OUTPUTFORMAT=text%2Fxml%3B+suntype%3Dgml%2F3.1.1
    # &VESRION=1.1&SERVICE=WFS
    url = regle.params.cmp1.val
    params = regle.wfsparams
    params["TYPENAME"] = regle.getval_entree(obj)
    print("wfs", url, params)
    retour = requests.get(url, params, stream=regle.params.pattern == "1")
    print("info", retour.headers)
    obj.sethtext("#wfs_header", dic=retour.headers)
    taille = int(retour.headers["Content-Length"])

    if regle.params.pattern == "2":  # retour dans un attribut
        regle.setval_sortie(obj, retour.text)
        if obj.virtuel and obj.attributs["#classe"] == "_chargement":  # mode chargement
            regle.stock_param.moteur.traite_objet(obj, regle.branchements.brch["gen"])
        # print("apres", obj)
        return True
    if regle.fichier is None:
        fichier = os.path.join(regle.path, os.path.basename(url))
    else:
        fichier = regle.fichier

    decile = taille / 10
    recup = 0
    bloc = 4096
    nb_pts = 0
    debut = time.time()
    if retour.status_code == 200:
        with open(fichier, "wb") as fich:
            for chunk in retour.iter_content(bloc):
                recup += bloc  # ca c'est la deco avec des petits points ....
                if recup > decile:
                    recup = recup - decile
                    nb_pts += 1
                    print(".", end="", flush=True)
                fich.write(chunk)
        print(
            "    ",
            taille,
            "octets télecharges en ",
            int(time.time() - debut),
            "secondes",
        )
        return True
    return False
