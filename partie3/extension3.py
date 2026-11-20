"""
Bar à cocktails – Partie 3, Extension 3 : le bariste aide au service.
"""

import sys, time, re
import asyncio


class Logable:
    """
    Classe de base pour disposer d'une méthode log
    """
    def __init__(self, name, verbose):
        self.name = name
        self.verbose = verbose

    def log(self, msg):
        if self.verbose:
            print(f"[{self.name}] {msg}", file=logf, flush=True)


class Employe(Logable):
    """
    Classe de base modélisant un employé
    """
    def __init__(self, pic, bar, clients, name, verbose, productivite=0.5):
        Logable.__init__(self, name, verbose)
        self.pic = pic
        self.bar = bar
        self.clients = clients
        self.productivite = productivite
        self.verrou = asyncio.Lock()
        self.log(f"prêt pour le service (productivité : {self.productivite}s)")


class Accessoire(asyncio.Queue, Logable):
    """
    Classe de base des accessoires (pic, bar).
    Un accessoire est une file asyncio.Queue (FIFO) : il hérite de put, get, qsize...
    Il connaît aussi le nombre de serveurs qui l'utilisent (pour gérer la fin du service).
    """
    def __init__(self, name, verbose):
        asyncio.Queue.__init__(self)
        Logable.__init__(self, name, verbose)
        self.nb_serveurs = 0  #compteur des serveurs disponible

    def inscrire(self, serveur):
        """ Un serveur signale qu'il utilise cet accessoire. """
        self.nb_serveurs += 1
        self.log(f"{serveur.name} inscrit, {self.nb_serveurs} serveur(s)")


class Pic(Accessoire):
    """
    Un pic contient les commandes à fabriquer.
    Il peut embrocher un post-it contenant une commande et libérer le premier embroché.
    Un post-it None signifie qu'un serveur a terminé : le pic ne transmet la fin au
    bariste qu'une fois que TOUS les serveurs inscrits ont terminé.
    """
    def __init__(self, name, verbose):
        Accessoire.__init__(self, name, verbose)
        self.nb_fins = 0              # nombre de serveurs ayant envoyé leur None

    async def embrocher(self, postit):
        await self.put(postit)
        self.log(f"post-it '{postit}' embrochée, {self.qsize()} post-it(s) à traiter")

    async def liberer(self):
        while True:
            postit = await self.get()   #retire le premier post-it (attend si le pic est vide)
            if postit is not None:     
                self.log(f"post-it '{postit}' libéré, {self.qsize()} post-it(s) à traiter")
                return postit
            #un serveur a terminé : on le compte, sans prévenir le bariste tout de suite
            self.nb_fins += 1
            self.log(f"fin d'un serveur ({self.nb_fins}/{self.nb_serveurs})")
            if self.nb_fins == self.nb_serveurs:
                return None             #tous les serveurs ont terminé : fin du service
            #sinon, on continue : d'autres commandes peuvent encore arriver


class Bar(Accessoire):
    """
    Un bar peut recevoir des commandes (composées de consommations),
    en attente d'être servies (évacuées).
    """
    async def recevoir(self, commande):
        await self.put(commande)
        self.log(f"'{commande}' posée, {self.qsize()} commande(s) à servir")

    async def evacuer(self):
        commande = await self.get()     #retire le premier plateau (attend si le bar est vide)
        self.log(f"'{commande}' évacuée, {self.qsize()} commande(s) à servir")
        return commande

    async def fermer(self):
        """ Fin du service : un None par serveur inscrit, pour arrêter chaque tâche servir(). """
        for i in range(self.nb_serveurs):
            await self.recevoir(None)


class Serveur(Employe):

    def __init__(self, pic, bar, clients, name, verbose, productivite=0.5):
        Employe.__init__(self, pic, bar, clients, name, verbose, productivite)
        #le serveur s'inscrit sur les accessoires qu'il utilise pour connaitre le nb de serveur total
        self.pic.inscrire(self)
        self.bar.inscrire(self)

    async def prendre_commande(self):
        """ Prend les commandes des clients et embroche les post-it. """
        while True:
            self.log("prêt pour prendre une nouvelle commande...'")
            commande = await self.clients.commande()      
            if commande is None:
                break
            async with self.verrou:
                self.log(f"j'ai la commande '{commande}'")
                self.log(f"j'écris sur le post-it '{commande}'")
                await asyncio.sleep(self.productivite)                #le temps d'écrire et d'embrocher
                await self.pic.embrocher(commande)
        await self.pic.embrocher(None)                    #ce serveur a terminé
        self.log("j'ai pris toutes les commandes")

    async def servir(self):
        """ Prend un plateau sur le bar et sert chaque consommation. """
        while True:
            commande = await self.bar.evacuer()           
            if commande is None:
                break
            async with self.verrou:
                self.log(f"j'apporte la commande '{commande}'")
                await asyncio.sleep(self.productivite)                #le trajet jusqu'à la table
                for conso in commande:
                    self.log(f"je sers '{conso}'")
                    await asyncio.sleep(self.productivite)            #le temps de servir ce cocktail
        self.log("j'ai servi toutes les commandes")

    async def run(self):
        """ Serveur en action : ses deux tâches tournent en même temps """
        await asyncio.gather(self.prendre_commande(), self.servir())


class Bariste(Employe):

    async def preparer(self):
        """
        Prend un post-it, prépare la commande et la dépose sur le bar.
        Quand le pic est vide et qu'un plateau attend, sert lui-même ce plateau.
        """
        while True:
            #rien à préparer mais un plateau attend : Bob va le servir lui-même
            if self.pic.empty() and not self.bar.empty():
                commande = await self.bar.evacuer()   #le bar n'est pas vide : pas d'attente
                async with self.verrou:
                    self.log(f"j'aide et j'apporte la commande '{commande}'")
                    await asyncio.sleep(self.productivite)        #le trajet jusqu'à la table
                    for conso in commande:
                        self.log(f"je sers '{conso}'")
                        await asyncio.sleep(self.productivite)    #le temps de servir ce cocktail
                continue                                  #puis il revient voir le pic

            commande = await self.pic.liberer()   #None seulement quand TOUS les serveurs ont fini
            if commande is None:
                break
            self.log(f"je commence la fabrication de '{commande}'")
            for conso in commande:
                self.log(f"je prépare '{conso}'")
                await asyncio.sleep(self.productivite)        #le temps de préparer ce cocktail
            await self.bar.recevoir(commande)
            self.log(f"la commande {commande} est prête")
        await self.bar.fermer()                   #un None par serveur sur le bar
        self.log("j'ai préparé toutes les commandes")

    async def run(self):
        """ Bariste en action """
        await self.preparer()


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
        fmt = re.compile(r"(\d+)\s+(.*)")
        with open(fname, "r", encoding="utf-8") as f:
            for line in f:
                found = fmt.search(line)
                if found:
                    when = int(found.group(1))
                    what = found.group(2)
                    commandes.append((start + when, what.split(",")))
        self.commandes = commandes[::-1]
        self.lock_clients = asyncio.Lock()

    async def commande(self):
        async with self.lock_clients:
            if len(self.commandes) > 0:
                heure_arrivee = self.commandes[-1][0]     # heure d'arrivée du prochain client
                attente = heure_arrivee - time.time()     # temps restant avant son arrivée
                if attente > 0:
                    await asyncio.sleep(attente)          # on attend en rendant la main
                return self.commandes.pop()[1]
            else:
                return None


async def main():
    await asyncio.gather(alice.run(), charlie.run(), bob.run())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
    fcommandes = sys.argv[1]

    logfile = "borabora.log"
    print(f"login in {logfile}...")
    logf = open(logfile, "w", encoding="utf-8")
    print("\n---", file=logf, flush=True)

    les_clients = Clients(fcommandes)
    le_pic = Pic(name="le_pic", verbose=True)
    le_bar = Bar(name="le_bar", verbose=True)

    bob = Bariste(le_pic, le_bar, les_clients, name="bob", verbose=True, productivite=0.4)
    alice = Serveur(le_pic, le_bar, les_clients, name="alice", verbose=True, productivite=0.2)
    charlie = Serveur(le_pic, le_bar, les_clients, name="charlie", verbose=True, productivite=0.6)

    asyncio.run(main())