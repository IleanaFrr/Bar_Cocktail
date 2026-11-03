"""
    On va rendre le programme coopératif en :
    * modifiant clients et sa boucle while True 
    * ajoutant des await asyncio.sleep(..) pour nos trois taches  
"""

import sys, time, re
import asyncio

DUREE=0.5 

class Logable:
    """
    Classe de base pour disposer d'une méthode log
    """
    def __init__(self,name,verbose):
        self.name = name
        self.verbose = verbose

    def log(self,msg):
        if self.verbose:
            print(f"[{self.name}] {msg}", file=logf, flush=True)

class Employe(Logable):
    """
    Classe de base modélisant un employé
    """
    def __init__(self,pic,bar,clients,name,verbose):
        Logable.__init__(self,name, verbose)
        self.pic = pic
        self.bar = bar
        self.clients = clients
        self.log('prêt pour le service')

class Accessoire(asyncio.Queue, Logable):
    """
    Classe de base des accessoires (pic, bar).
    Un accessoire est une file asyncio.Queue (FIFO) : il hérite de put, get, qsize...
    get() attend qu'un élément soit disponible si la file est vide.
    """
    def __init__(self, name, verbose):
        asyncio.Queue.__init__(self)
        Logable.__init__(self,name, verbose)
        

        


class Pic(Accessoire):
    """
    Un pic contient les commandes à fabriquer.
    Il peut embrocher un post-it contenant une commande
    (une liste de consommations) par-dessus les post-it
    déjà présents et libérer le premier embroché.
    """

    async def embrocher(self,postit):
        await self.put(postit)
        self.log(f"post-it '{postit}' embrochée, {self.qsize()} post-it(s) à traiter")

    async def liberer(self):
        postit = await self.get()               #retire et renvoie le premiere élément (si le pic est vide, attend qu'il en arrive un)
        self.log(f"post-it '{postit}' libéré, {self.qsize()} post-it(s) à traiter")
        return postit


class Bar(Accessoire):
    """
    Un bar peut recevoir des commandes (composées de consommations),
    en attente d'être servies (évacuées).
    """

    async def recevoir(self,commande):
        await self.put(commande)
        self.log(f"'{commande}' posée, {self.qsize()} commande(s) à servir")
        
    async def evacuer(self):
        commande = await self.get()
        self.log(f"'{commande}' évacuée, {self.qsize()} commande(s) à servir")
        return commande


class Serveur(Employe):

    async def prendre_commande(self):
        """ Prend les commandes des clients et embroche les post-it. """
        while True:
            self.log("prêt pour prendre une nouvelle commande...'")
            commande = await self.clients.commande()
            if commande is None:
                break
            self.log(f"j'ai la commande '{commande}'")
            self.log(f"j'écris sur le post-it '{commande}'")
            await asyncio.sleep(DUREE)           #on simule le temps que le serveur prend à ecrire le post it et de l'embrocher
            await self.pic.embrocher(commande)

        await self.pic.embrocher(None)
        self.log(f"j'ai pris toutes les commandes")
    async def servir(self):
        """ Prend un plateau sur le bar. """
        while True:
            commande = await self.bar.evacuer()
            if commande is None:
                break
            self.log(f"j'apporte la commande '{commande}'")
            await asyncio.sleep(DUREE)          # Le temps de marcher jusqu'a la table  
            for conso in commande:
                self.log(f"je sers '{conso}'")
                await asyncio.sleep(DUREE)    # le temps de servir ce cocktail
        self.log("j'ai servi toutes les commandes")

    async def run(self):
        """ Serveur en action """
        await asyncio.gather(self.prendre_commande(),self.servir())


class Bariste(Employe):

    async def preparer(self):
        """ Prend un post-it, prépare la commande et la dépose sur le bar. """
        while True:
            commande = await self.pic.liberer()
            if commande is None :
                break
            self.log(f"je commence la fabrication de '{commande}'")
            for conso in commande:
                self.log(f"je prépare '{conso}'")
                await asyncio.sleep(DUREE)      # le temps de préparer ce cocktail
            await self.bar.recevoir(commande)
            self.log(f"la commande {commande} est prête")
        await self.bar.recevoir(None)
        self.log("j'ai préparé toute les commandes")

    async def run(self):
        """Bariste en action """
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

    async def commande(self):
        if len(self.commandes) > 0:
            heure_arrivee = self.commandes[-1][0]             # heure d'arrivée du prochain client
            attente = heure_arrivee - time.time()             # temps restant avant son arrivée
            if attente > 0:
                await asyncio.sleep(attente)                  # on attend en rendant la main
            return self.commandes.pop()[1]                    # le client est là : on renvoie sa commande
        else:
            return None


async def main():
    await asyncio.gather(alice.run(),bob.run())



if __name__=="__main__":
    if len(sys.argv)!=2:
        usage()
    fcommandes = sys.argv[1]

    logfile = "borabora.log"
    print(f"login in {logfile}...")
    logf = open(logfile,"w", encoding="utf-8")
    print("\n---", file=logf, flush=True)

    les_clients = Clients(fcommandes)
    le_pic = Pic(name="le_pic", verbose=True)
    le_bar = Bar(name="le_bar", verbose=True)
    bob = Bariste(le_pic, le_bar, les_clients, name="bob", verbose=True)
    alice = Serveur(le_pic, le_bar, les_clients, name="alice", verbose=True)

    asyncio.run(main())
  