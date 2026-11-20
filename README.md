# Bar à cocktails

Projet réalisé dans le cadre du M2 Data Science par **Ileana Ferry** et **Aïcha Ben Salah**.

Le programme simule le fonctionnement d'un bar à cocktails à travers le travail de ses employés :

- un **serveur** prend les commandes des clients et les écrit sur des post-it qu'il embroche sur un **pic** ;
- un **bariste** récupère les post-it, prépare les cocktails et pose les plateaux sur le **bar** ;
- le serveur prend les plateaux sur le bar et sert les clients.

Toutes les actions sont enregistrées dans un journal (`borabora.log`). Le projet part d'une version
séquentielle (Partie 1), la rend concurrente avec `asyncio` (Partie 2), puis l'enrichit avec plusieurs
extensions (Partie 3).

---

## Résumé des étapes

### Partie 1 – Version séquentielle
Le serveur prend **toutes** les commandes, puis le bariste les prépare **toutes**, puis le serveur les
sert **toutes**. Le programme fonctionne, mais chacun attend que l'autre ait complètement fini.

### Partie 2 – Version concurrente
1. **Coroutines et `gather()`** : les trois tâches (prendre les commandes, préparer, servir) sont lancées
   ensemble. Problème : le bariste trouve le pic vide au démarrage et s'arrête.
2. **`asyncio.Queue`** : une tâche qui trouve une file vide **attend** au lieu d'abandonner. La fin du
   service est signalée par une **sentinelle** (`None`), transmise du serveur au pic, puis du bariste au bar.
3. **Coopération** : des `await asyncio.sleep(...)` simulent la durée des actions et rendent la main aux
   autres tâches ; l'attente active de `Clients` est supprimée. Le serveur et le bariste travaillent
   enfin en même temps, mais le serveur « zappe » d'une tâche à l'autre.
4. **Un verrou par employé** (`asyncio.Lock`) : un employé termine une tâche avant d'en commencer une autre,
   sans bloquer les autres employés.

### Partie 3 – Extensions
1. **Un second serveur** : un verrou protège l'accès aux clients. Chaque serveur s'inscrit auprès du pic
   et du bar ; le pic ne signale la fin au bariste qu'une fois reçue la sentinelle de **tous** les
   serveurs, et le bar pose une sentinelle par serveur (`fermer()`).
2. **Productivité propre à chaque employé** : l'attribut `productivite` (durée d'une action, en secondes)
   remplace la durée commune.
3. **Le bariste aide au service** : après chaque préparation, s'il n'a plus rien à préparer et qu'un
   plateau attend encore (les serveurs sont occupés), il le sert lui-même. Avec `mardi`, il n'aide pas ;
   avec `mercredi`, il sert la dernière commande.

---

## Arborescence

```
Bar_a_cocktails/
├── README.md
├── .gitignore
├── commandes/
│   ├── lundi
│   ├── mardi
│   └── mercredi
├── partie1/
│   ├── etape1.py
│   ├── etape2.py
│   └── etape3.py
├── partie2/
│   ├── etape1.py
│   ├── etape2.py
│   ├── etape3.py
│   └── etape4.py
└── partie3/
    ├── extension1.py
    ├── extension2.py
    └── extension3.py
```

---

## Exécution

Toutes les commandes se lancent **depuis la racine du projet**.

Sous Windows (PowerShell) :

```powershell
py partie1/etape1.py                          # Partie 1, étape 1 : saisie au clavier
py partie1/etape2.py commandes/lundi          # à partir de l'étape 2 : un fichier de commandes
py partie2/etape4.py commandes/mardi
py partie3/extension3.py commandes/mercredi
```

Sous Linux / macOS, remplacer `py` par `python3`.

À l'étape 1, taper les commandes une par une (cocktails séparés par des virgules), puis valider une
ligne vide pour terminer :

```
planteur,piña colada
tequila sunrise,margarita
```

### Suivre le journal

À partir de l'étape 3 de la Partie 1, les messages ne s'affichent plus dans le terminal (seul
`login in borabora.log...` apparaît) : ils sont écrits dans `borabora.log`, à la racine du projet.
Le fichier est réécrit à chaque exécution.

Pour suivre le journal en direct, ouvrir un **second terminal** :

```powershell
Get-Content borabora.log -Wait -Encoding UTF8     # Windows (PowerShell)
```
```bash
tail -f borabora.log                              # Linux / macOS
```

### Choisir qui écrit dans le journal

Chaque objet (employé, pic, bar) possède un attribut `verbose`. Pour n'écouter que certains d'entre
eux, modifier leur création dans le bloc `if __name__ == "__main__":`, par exemple :

```python
bob = Bariste(le_pic, le_bar, les_clients, name="bob", verbose=True)
alice = Serveur(le_pic, le_bar, les_clients, name="alice", verbose=False)
```

---

## Auteurs

- Ileana Ferry
- Aïcha Ben Salah
