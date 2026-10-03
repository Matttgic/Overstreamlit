# Cotes Winamax et Betclic depuis un téléphone Android

Winamax et Betclic bloquent tous les serveurs (GitHub compris), mais pas ta connexion
(wifi ou 4G). Le téléphone télécharge donc les pages et les dépose sur le dépôt ; GitHub
fait le reste : lecture des cotes, comparaison avec la cote juste, ajout à « À jouer
maintenant » et alerte Telegram.

Deux étapes :

1. **Sonde** (fait le 03/10/2026) : le téléphone a envoyé des pages NHL de Winamax et Betclic
   pour régler la lecture des cotes.
2. **Collecte automatique** (section 6) : 4 fois par jour, le téléphone lit les cotes joueurs
   NHL (buteur, 2 buts ou +, points, passes) et envoie un petit fichier compressé.

Durée : ~15 minutes. Coût : 0 €.

## 1. Installer Termux

- Installer **F-Droid** depuis https://f-droid.org (le magasin d'applications libres),
  puis chercher **Termux** dans F-Droid et l'installer.
  (Ou télécharger l'APK sur https://github.com/termux/termux-app/releases.)
  Évitez la version du Play Store, souvent ancienne.
- Ouvrir Termux, puis copier-coller cette ligne (appui long → Coller) et valider :

```
pkg update -y && pkg install -y python
```

(Si une question s'affiche pendant l'installation, valider avec Entrée.)

## 2. Récupérer le script

```
curl -LO https://raw.githubusercontent.com/Matttgic/Overstreamlit/main/telephone/collecte_fr.py
```

Tant que la PR n'est pas fusionnée, utiliser l'adresse de la branche :

```
curl -LO https://raw.githubusercontent.com/Matttgic/Overstreamlit/ccr-db761a32-14x613/telephone/collecte_fr.py
```

## 3. Créer le jeton GitHub (accès limité à ce dépôt)

Dans le navigateur du téléphone, connecté à GitHub :

1. Ouvrir https://github.com/settings/personal-access-tokens/new
2. **Token name** : `telephone-cotes` — **Expiration** : 1 an (*Custom*).
3. **Repository access** : *Only select repositories* → choisir **Matttgic/Overstreamlit**.
4. **Permissions** → *Repository permissions* → **Contents** → *Read and write*
   (rien d'autre).
5. **Generate token**, puis **copier** le jeton (il commence par `github_pat_`).

⚠️ Ne collez jamais ce jeton dans une conversation, un message ou un site : seulement dans
Termux, comme ci-dessous. Il ne donne accès qu'à ce dépôt, et vous pouvez le supprimer à
tout moment sur la même page GitHub.

## 4. Enregistrer le jeton dans Termux

Copier-coller cette ligne, valider, **puis coller le jeton et valider** (rien ne s'affiche
pendant que vous collez : c'est normal, le jeton reste caché) :

```
read -s T && echo "$T" > ~/.overstreamlit_token && chmod 600 ~/.overstreamlit_token && unset T && echo OK
```

`OK` doit s'afficher.

## 5. Lancer la sonde

```
python collecte_fr.py sonde
```

Le script affiche une ligne par page (code, taille), par exemple `200   850 Ko  winamax_hockey`,
puis `… fichiers déposés`. Il dépose les pages (compressées) sur la branche
**cotes-telephone** du dépôt, jamais sur `main`.

Dites ensuite à Claude « sonde faite », en recopiant les lignes affichées (elles ne
contiennent pas le jeton). Si une page affiche `403`, signalez-le aussi : cela voudra dire
que le site bloque aussi le téléphone pour cette adresse.

## 6. Collecte automatique (4 fois par jour)

Mettre d'abord le script à jour (même commande qu'à l'étape 2), puis le tester à la main :

```
python collecte_fr.py
```

Il affiche par exemple :

```
  Winamax : 13 matchs NHL, 9 avec cotes joueurs, 2650 cotes
  Betclic : 13 matchs NHL, 9 avec cotes joueurs, 230 cotes
Envoyé sur GitHub.
```

(Le matin, « 0 avec cotes joueurs » est normal : les bookmakers ouvrent les buteurs le jour
du match, en général à partir de midi.)

Ensuite, programmer la collecte à 12 h, 16 h, 19 h et 22 h. Copier-coller, une ligne à la fois :

```
pkg install -y cronie termux-services
```

**Fermer complètement Termux** (notification Termux → *Exit*) et le rouvrir, puis :

```
sv-enable crond
```

```
(crontab -l 2>/dev/null; echo "5 12,16,19,22 * * * cd ~ && python collecte_fr.py >> ~/collecte.log 2>&1") | crontab -
```

```
termux-wake-lock
```

Enfin, dans les **réglages Android** : Applications → Termux → Batterie → **Non restreinte**
(sinon Android endort Termux et la collecte ne part pas). Laisser Termux ouvert en arrière-plan
(la notification « Termux » doit rester affichée).

Vérifier que tout marche (le lendemain) : `tail -20 ~/collecte.log` affiche les dernières
collectes ; le site indique aussi « Winamax et Betclic reçus du téléphone (heure) » dans la
section Buteurs NHL.

Consommation : les pages sont demandées compressées, environ 2 Mo par collecte (≈ 8 Mo par
jour, surtout en wifi à la maison).

Arrêter : `crontab -r` (supprime la programmation). Le jeton peut être supprimé à tout moment
sur https://github.com/settings/personal-access-tokens.

## En cas de souci

| Message | Que faire |
|---|---|
| `Jeton introuvable` | Refaire l'étape 4. |
| `Accès au dépôt refusé (401 ou 403)` | Jeton mal copié ou sans *Contents : Read and write* → refaire les étapes 3 et 4. |
| `command not found: python` | Refaire `pkg install -y python`. |
| Codes `0` partout | Pas de connexion internet sur le téléphone. |
| `crontab: command not found` | Refaire `pkg install -y cronie termux-services`, fermer et rouvrir Termux. |
| Pas de nouvelle ligne dans `collecte.log` | Termux endormi : batterie « Non restreinte » + `termux-wake-lock`. |
