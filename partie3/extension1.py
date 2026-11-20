"""
extension 1: on ajoute un deuxième serveur
"""

import sys, time, re
import asyncio

DUREE = 0.5 

class Logable:
    def __init__(self, name, verbose):
        self.name = name
        self.verbose = verbose

    def log(self, msg):
        if self.verbose:
            print(f"[{self.name}] {msg}", file=logf, flush=True)

class Employe(Logable):
    def __init__(self, pic, bar, clients, name, verbose):
        Logable.__init__(self, name, verbose)
        self.pic = pic
        self.bar = bar
        self.clients = clients
        self.log('prêt pour le service')
        self.verrou = asyncio.Lock()   

class Accessoire(asyncio.Queue, Logable):
    def __init__(self, name, verbose):
        asyncio.Queue.__init__(self)
        Logable.__init__(self, name, verbose)
        self.nb_serveurs = 0          #nombre de serveurs pour cet accesoire 

    def inscrire(self, serveur):
        """ Un serveur signale qu'il utilise cet accessoire. """
        self.nb_serveurs += 1
        self.log(f"{serveur.name} inscrit, {self.nb_serveurs} serveur(s)")

class Pic(Accessoire):
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
            # un serveur a terminé : on le compte, sans prévenir le bariste tout de suite (attendre tous les serveurs avant de retourner None qui signale la fin)
            self.nb_fins += 1
            self.log(f"fin d'un serveur ({self.nb_fins}/{self.nb_serveurs})")
            if self.nb_fins == self.nb_serveurs:
                return None             # tous les serveurs ont terminé : fin du service
            # sinon, on continue : d'autres commandes peuvent encore arriver

class Bar(Accessoire):
    async def recevoir(self, commande):
        await self.put(commande)
        self.log(f"'{commande}' posée, {self.qsize()} commande(s) à servir")
        
    async def evacuer(self):
        commande = await self.get()
        self.log(f"'{commande}' évacuée, {self.qsize()} commande(s) à servir")
        return commande
        
    async def fermer(self):
        """ Fin du service : un None par serveur inscrit, pour arrêter chaque tâche servir(). """
        for i in range(self.nb_serveurs):
            await self.recevoir(None)
            
class Serveur(Employe):
    def __init__(self, pic, bar, clients, name, verbose):
        Employe.__init__(self, pic, bar, clients, name, verbose)
        self.pic.inscrire(self)
        self.bar.inscrire(self)
    async def prendre_commande(self):
        while True:
            self.log("prêt pour prendre une nouvelle commande...'")
            commande = await self.clients.commande()
            if commande is None:
                break
            async with self.verrou:
                self.log(f"j'ai la commande '{commande}'")
                self.log(f"j'écris sur le post-it '{commande}'")
                await asyncio.sleep(DUREE)
                await self.pic.embrocher(commande)

        await self.pic.embrocher(None)
        self.log(f"j'ai pris toutes les commandes")

    async def servir(self):
        while True:
            commande = await self.bar.evacuer()
            if commande is None:
                break
            async with self.verrou:
                self.log(f"j'apporte la commande '{commande}'")
                await asyncio.sleep(DUREE)  
                for conso in commande:
                    self.log(f"je sers '{conso}'")
                    await asyncio.sleep(DUREE)
        self.log("j'ai servi toutes les commandes")

    async def run(self):
        await asyncio.gather(self.prendre_commande(), self.servir())


class Bariste(Employe):
    async def preparer(self):
        while True:
            commande = await self.pic.liberer()
            if commande is None :
                break
            self.log(f"je commence la fabrication de '{commande}'")
            for conso in commande:
                self.log(f"je prépare '{conso}'")
                await asyncio.sleep(DUREE)
            await self.bar.recevoir(commande)
            self.log(f"la commande {commande} est prête")
            
        await self.bar.fermer()      
        self.log("j'ai préparé toute les commandes")

    async def run(self):
        await self.preparer()

def usage():
    print(f"usage: {sys.argv[0]} fichier")
    exit(1)


class Clients:
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
                heure_arrivee = self.commandes[-1][0]
                attente = heure_arrivee - time.time()
                if attente > 0:
                    await asyncio.sleep(attente)
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
    
    bob = Bariste(le_pic, le_bar, les_clients, name="bob", verbose=True)
    alice = Serveur(le_pic, le_bar, les_clients, name="alice", verbose=True)
    charlie = Serveur(le_pic, le_bar, les_clients, name="charlie", verbose=True)

    asyncio.run(main())
