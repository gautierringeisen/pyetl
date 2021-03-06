# -*- coding: utf-8 -*-
"""creation d un zip pourinstallation ( evite les fichiers .git .pyc)"""
import zipfile
import os
import re

re.match(".*(?!(git))", ".git")
dirp = "(?!(git)||(__pycache__))"
dirp = ".*(?!(git))"
start = os.path.dirname(__file__)


def scandirs(rep_depart, chemin):
    """parcours recursif d'un repertoire."""
    exclude = {".git", ".vscode", "__pycache__"}

    path = os.path.join(rep_depart, chemin)
    # print("recherche", path)
    if os.path.isfile(path):
        chemin = os.path.dirname(chemin)
        yield (str(os.path.basename(path)), str(chemin))
        return
    if os.path.exists(path):
        for element in os.listdir(path):
            #        for element in glob.glob(path):
            if os.path.isdir(os.path.join(path, element)) and element in exclude:
                continue
            yield from scandirs(rep_depart, os.path.join(chemin, element))
    else:
        raise NotADirectoryError(str(path))

def update_build(build="BUILD =", file="vglobales.py",orig=start):
    for (fichier, chemin) in scandirs(orig, ""):
            # print(fichier, chemin)
        if file and fichier!=file:
            # print ("ignore ",fichier)
            continue
        # print ("analyse ",fichier)
        with open(os.path.join(orig, chemin, fichier),"r", encoding="utf8") as vglob:
            for contenu in vglob:
            # contenu=str(vglob.read())
                if build in contenu:
                    # print ("build trouve dans ", fichier)
                    found=True
                    break
            else:
                print ("non trouve",build)
                found=False
        if found:
            with open(os.path.join(orig, chemin, fichier),"r", encoding="utf8") as vglob:
                fich_orig=vglob.readlines()
            resultat=[]
            for contenu in fich_orig:
            # contenu=str(vglob.read())
                if build in contenu:
                    tmp,nv=contenu.split("=")
                    nv1=" "+str(int(nv)+1)+"\n"
                    resultat.append(contenu.replace(nv,nv1))
                else:
                    resultat.append(contenu)
            with open(os.path.join(orig, chemin, fichier),"w", encoding="utf8") as vglob:
                vglob.writelines(resultat)
            return int(nv)+1
    return None





def zipall(orig=start,nv=""):
    name="mapper"+nv+".zip"
    with zipfile.ZipFile(
        name, "w", compression=zipfile.ZIP_BZIP2
    ) as zip:
        os.chdir(orig)
        for (fichier, chemin) in scandirs(".", ""):
            # print(fichier, chemin)
            zip.write(os.path.join(chemin, fichier))


def _main():
    """ mode autonome """
    print("preparation version")
    zipall()


if __name__ == "__main__":
    # execute only if run as a script
    _main()
