"""
    on va modéliser les Accesoir avec asyncio.Queue au lieu d'une liste 
"""

import sys, time, re
import asyncio
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
        self.step = 0
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
        self.log(f"post-it '{postit}' embrochée, {self.qsize()} post-it(s) à traiter")
        await self.put(postit)

    async def liberer(self):
        postit = await self.get() #retire et renvoie le premiere élément (si le pic est vide, attend qu'il en arrive un)
        self.log(f"post-it '{postit}' libéré, {self.qsize()} post-it(s) à traiter")
        return postit


class Bar(Accessoire):
    """
    Un bar peut recevoir des commandes (composées de consommations),
    en attente d'être servies (évacuées).
    """

    async def recevoir(self,commande):
        self.log(f"'{commande}' posée, {self.qsize()} commande(s) à servir")
        await self.put(commande)

    async def evacuer(self):
        commande = await self.get()
        self.log(f"'{commande}' évacuée, {self.qsize()} commande(s) à servir")
        return commande


class Serveur(Employe):

    async def prendre_commande(self):
        """ Prend les commandes des clients et embroche les post-it. """
        while True:
            self.log("prêt pour prendre une nouvelle commande...'")
            commande = self.clients.commande()
            if commande is None:
                break
            self.log(f"j'ai la commande '{commande}'")
            self.log(f"j'écris sur le post-it '{commande}'")
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
            for conso in commande:
                self.log(f"je sers '{conso}'")

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
            await self.bar.recevoir(commande)
            self.log(f"la commande {commande} est prête")
        await self.bar.recevoir(None)
        self.log(f"j'ai préparé toute les commandes")

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

    def commande(self):
        if len(self.commandes) > 0:
            while True:
                if time.time() > self.commandes[-1][0]:
                    return self.commandes.pop()[1]
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
  