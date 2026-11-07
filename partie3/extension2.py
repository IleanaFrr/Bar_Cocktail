"""
extension 2: pas la même productivité
"""

import sys, time, re
import asyncio

class Logable:
    def __init__(self, name, verbose):
        self.name = name
        self.verbose = verbose

    def log(self, msg):
        if self.verbose:
            print(f"[{self.name}] {msg}", file=logf, flush=True)

class Employe(Logable):
    def __init__(self, pic, bar, clients, name, verbose, productivite=0.5):
        Logable.__init__(self, name, verbose)
        self.pic = pic
        self.bar = bar
        self.clients = clients
        self.productivite = productivite 
        self.log(f"prêt pour le service (productivité: {self.productivite}s)")
        self.verrou = asyncio.Lock()   

class Accessoire(asyncio.Queue, Logable):
    def __init__(self, name, verbose):
        asyncio.Queue.__init__(self)
        Logable.__init__(self, name, verbose)

class Pic(Accessoire):
    async def embrocher(self, postit):
        await self.put(postit)
        self.log(f"post-it '{postit}' embrochée, {self.qsize()} post-it(s) à traiter")
        
    async def liberer(self):
        postit = await self.get()
        self.log(f"post-it '{postit}' libéré, {self.qsize()} post-it(s) à traiter")
        return postit

class Bar(Accessoire):
    async def recevoir(self, commande):
        await self.put(commande)
        self.log(f"'{commande}' posée, {self.qsize()} commande(s) à servir")
        
    async def evacuer(self):
        commande = await self.get()
        self.log(f"'{commande}' évacuée, {self.qsize()} commande(s) à servir")
        return commande

class Serveur(Employe):
    async def prendre_commande(self):
        while True:
            self.log("prêt pour prendre une nouvelle commande...'")
            commande = await self.clients.commande()
            if commande is None:
                break
            async with self.verrou:
                self.log(f"j'ai la commande '{commande}'")
                self.log(f"j'écris sur le post-it '{commande}'")
                await asyncio.sleep(self.productivite) # Utilisation de sa productivité
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
                await asyncio.sleep(self.productivite)  
                for conso in commande:
                    self.log(f"je sers '{conso}'")
                    await asyncio.sleep(self.productivite)
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
                await asyncio.sleep(self.productivite) # Utilisation de sa productivité
            await self.bar.recevoir(commande)
            self.log(f"la commande {commande} est prête")
            
        await self.bar.recevoir(None)
        await self.bar.recevoir(None)
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
    bob = Bariste(le_pic, le_bar, les_clients, name="bob", verbose=True, productivite=0.4)
    alice = Serveur(le_pic, le_bar, les_clients, name="alice", verbose=True, productivite=0.2)
    charlie = Serveur(le_pic, le_bar, les_clients, name="charlie", verbose=True, productivite=0.6)

    asyncio.run(main())