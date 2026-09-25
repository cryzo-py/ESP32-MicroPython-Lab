# Documentation des Entrées Numériques (Digital Input)

Le simulateur ESP32 MicroPython Lab modélise les entrées numériques (`machine.Pin.IN`) de manière topologique. Le comportement des GPIOs ne dépend pas directement de l'état UI du bouton (enfoncé ou relâché) mais du réseau électrique virtuel (netlist).

## Architecture

Le modèle suit une approche Backend-first (Pull-based) :
1. **Composants physiques (ButtonModel)** : L'interaction utilisateur met à jour un booléen `pressed` dans le modèle de données du composant. 
2. **Topologie (ElectricalNetResolver)** : À chaque événement `topology_updated`, le composant (par exemple un bouton poussoir) ouvre ou ferme un pont électrique interne dans le graphe.
3. **GPIOManager** : Lorsque le code MicroPython effectue une lecture via `Pin.value()`, le `GPIOManager` demande au résolveur la liste des nœuds connectés au GPIO actuel.

## Résolution d'état logique

Lorsque `GPIOManager.read(pin)` est appelé pour une broche configurée en entrée, la séquence de détermination d'état est la suivante :

1. **Recherche de VCC / GND** :
   Le résolveur électrique traverse le circuit pour voir si le GPIO touche une source d'alimentation VCC (`3V3`, `5V`, `VIN`, `VCC`) ou la masse (`GND`). Les composants passifs sans résistance (comme les interrupteurs fermés, ou les fils) propagent le réseau. Les résistances laissent actuellement passer le signal logique (elles agissent comme pont transparent pour la résolution binaire de l'état "HIGH/LOW").

2. **Résolution des cas (Déterministe)** :
   * **Connexion au VCC exclusif** (`vcc and not gnd`) -> **Retourne 1 (HIGH)**
   * **Connexion au GND exclusif** (`gnd and not vcc`) -> **Retourne 0 (LOW)**
   * **Connexion simultanée VCC et GND** (`vcc and gnd`) -> Cas de conflit/court-circuit. Pour éviter les comportements aléatoires, le système documente ce cas (`CONFLICT`) et **retourne systématiquement 0**. (Dans l'avenir, une simulation SPICE pourrait affiner ce calcul selon les résistances).
   * **Flottant** (`not vcc and not gnd`) -> Passe à l'étape suivante.

3. **Traitement Flottant (PULL Resistors)** :
   Si le GPIO est physiquement en l'air (ou si le circuit est ouvert, par ex. un bouton relâché sans pull externe) :
   * Si la broche est configurée avec `Pin.PULL_UP` -> **Retourne 1 (HIGH)**
   * Si la broche est configurée avec `Pin.PULL_DOWN` -> **Retourne 0 (LOW)**
   * Par défaut (pas de Pull) -> **Retourne 0 (LOW)**. Le simulateur évite l'aléatoire pour faciliter la reproductibilité.

## Exemple : Bouton Poussoir

Un `ButtonGraphicsItem` a un layout standard (4 broches) :
* `pin1` et `pin2` sont reliés en interne en permanence (Côté A).
* `pin3` et `pin4` sont reliés en interne en permanence (Côté B).
* Une pression physique ferme le contact entre Côté A et Côté B.

### Scénario PULL_UP

* **Configuration** : `bouton = Pin(27, Pin.IN, Pin.PULL_UP)`
* **Câblage** : Côté A connecté au `GPIO27`, Côté B connecté à `GND`.
* **Bouton relâché** : Le GPIO27 ne touche pas GND. Le résolveur ne trouve ni VCC ni GND. L'état tombe dans le traitement Flottant. Le `PULL_UP` interne force un retour de `1`.
* **Bouton enfoncé** : Le pont se ferme. Le GPIO27 touche GND. L'état logique est résolu sur GND exclusif. Retour de `0`.

### Scénario PULL_DOWN Externe

* **Configuration** : `bouton = Pin(4, Pin.IN)`
* **Câblage** : Côté A connecté à `3V3`, Côté B connecté au `GPIO4`. De plus, une résistance relie physiquement `GPIO4` à `GND`.
* **Bouton relâché** : Le GPIO4 touche GND à travers la résistance. Il retourne `0`.
* **Bouton enfoncé** : Le GPIO4 touche 3V3 et GND simultanément. Dans la topologie simplifiée actuelle, ceci déclenche l'état de conflit, retournant 0. (La résolution des conflits de résistances pull externes nécessitera le modèle SPICE complet).
