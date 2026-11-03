
"""
 Partie 1, Étape 2
 à lancer avec python partie1_etape2.py commandes/lundi
"""
import sys, time, re


class Accessoire(list):
    """
    Classe de base des accessoires (pic, bar).
    Un accessoire est une liste : il hérite de append, pop, len...

    """


class Pic(Accessoire):
    """
    Un pic contient les commandes à fabriquer.
    Il peut embrocher un post-it contenant une commande
    (une liste de consommations) par-dessus les post-it
    déjà présents et libérer le premier embroché.
    """

    def embrocher(self, postit):
        self.append(postit)

    def liberer(self):
        if len(self) > 0:
            postit = self.pop()
            return postit
        else:
            return None


class Bar(Accessoire):
    """
    Un bar peut recevoir des commandes (composées de consommations),
    en attente d'être servies (évacuées).
    """

    def recevoir(self, commande):
        self.append(commande)

    def evacuer(self):
        if len(self) > 0:
            commande = self.pop()
            return commande
        else:
            return None


class Employe:
    """
    Classe de base modélisant un employé.
    """

    def __init__(self, pic, bar, clients):
        self.pic = pic
        self.bar = bar
        self.clients = clients
        self.step = 0
        print(f"{self.__class__.__name__}: prêt pour le service")


class Serveur(Employe):

    def prendre_commande(self):
        """ Prend les commandes des clients et embroche les post-it. """
        while True:
            print(f"{self.__class__.__name__}: prêt pour prendre une nouvelle commande...'")
            commande = self.clients.commande()
            if commande is None:
                break
            print(f"{self.__class__.__name__}: j'ai la commande '{commande}'")
            print(f"{self.__class__.__name__}: j'écris sur le post-it '{commande}'")
            self.pic.embrocher(commande)

    def servir(self):
        """ Prend un plateau sur le bar. """
        while True:
            commande = self.bar.evacuer()
            if not commande:
                break
            print(f"{self.__class__.__name__}: j'apporte la commande '{commande}'")
            for conso in commande:
                print(f"{self.__class__.__name__}: je sers '{conso}'")

    def run(self):
        """ Serveur en action """
        if self.step == 0:
            self.step += 1
            self.prendre_commande()
        elif self.step == 1:
            self.step += 1
            self.servir()


class Bariste(Employe):

    def preparer(self):
        """ Prend un post-it, prépare la commande et la dépose sur le bar. """
        while True:
            commande = self.pic.liberer()
            if not commande:
                break
            print(f"{self.__class__.__name__}: je commence la fabrication de '{commande}'")
            for conso in commande:
                print(f"{self.__class__.__name__}: je prépare '{conso}'")
            self.bar.recevoir(commande)
            print(f"{self.__class__.__name__}: la commande {commande} est prête")

    def run(self):
        """ Bariste en action """
        self.preparer()


def usage():
    print(f"usage: {sys.argv[0]} fichier")
    exit(1)


class Clients:
    """
    Simule les clients : lit les commandes dans un fichier et les renvoie
    une par une, en respectant le délai indiqué sur chaque ligne.
    """

    def __init__(self, fname):
        commandes = []
        start = time.time()
        fmt = re.compile(r"(\d+)\s+(.*)") # sépare le délai (groupe 1) du reste de la ligne (groupe 2)
        with open(fname, "r", encoding="utf-8") as f:
            for line in f:
                found = fmt.search(line)
                if found:
                    when = int(found.group(1))
                    what = found.group(2) #c'est la commande entière encore sous forme de texte : "bloody mary,moscow mule"
                    commandes.append((start + when, what.split(","))) # on met le couple (heure d'arrivée du client, liste des consommations)
        self.commandes = commandes[::-1] #pour avoir un fifo

    def commande(self):
        if len(self.commandes) > 0:
            while True:
                if time.time() > self.commandes[-1][0]:
                    return self.commandes.pop()[1]
        else:
            return None


def main():
    alice.run()
    bob.run()
    alice.run()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
    fcommandes = sys.argv[1]

    le_pic = Pic()
    le_bar = Bar()
    les_clients = Clients(fcommandes)
    bob = Bariste(le_pic, le_bar, les_clients)
    alice = Serveur(le_pic, le_bar, les_clients)
    main()