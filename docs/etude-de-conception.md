# Étude de conception : MaintAI et CantineAI

---

## 1. Utilisateur principal

| MaintAI | CantineAI |
|---|---|
| Le responsable de l'équipe de maintenance de l'usine | Le gestionnaire de la cantine du lycée |

## 2. Décision et fréquence

| MaintAI | CantineAI |
|---|---|
| Choisir les machines à inspecter, **chaque matin** | Commander à la cuisine le nombre de repas du lendemain, **chaque jour à 10 h** |

## 2. Coût d'une erreur

| | MaintAI | CantineAI |
|---|---|---|
| **Erreur 1** | **Panne manquée** : une ligne de production arrêtée pendant une journée (coût pour l'usine) | **Repas en trop** : environ 15 DH de matière première jetés par repas, et du gaspillage alimentaire (coût pour la cantine) |
| **Erreur 2** | **Fausse alerte** : une heure d'inspection perdue (coût pour l'équipe de maintenance) | **Repas manquant** : un élève sans déjeuner ou un sandwich acheté en urgence, et des plaintes des parents (coût pour les élèves et les familles) |
| **Erreur la plus grave** | La panne manquée | Le repas manquant, mais les deux comptent |

## 3. Approche

| MaintAI | CantineAI |
|---|---|
| **ML, classification.** Des règles à seuil fixe (« si température > X ») ne capturent pas les combinaisons de capteurs (température, vibration, charge, heures). Le deep learning ou un LLM seraient inutiles pour des données tabulaires de cette taille. | **ML, régression.** La règle actuelle (« même jour la semaine précédente ») ignore le menu, les examens, les sorties et les veilles de vacances. Un modèle simple suffit avec 340 lignes ; le deep learning ou un LLM seraient disproportionnés. |

## 4. Données

| | MaintAI | CantineAI |
|---|---|---|
| **Fichier** | `data/exemple_pannes.csv` | `data/cantine_repas.csv` |
| **Source et licence** | Données synthétiques fournies pour le cours | Données synthétiques générées pour le cours |
| **Volume** | 5 000 relevés de capteurs, 17,6 % de pannes (colonne `failure`) | 340 jours d'école (septembre 2024 à juin 2026), une ligne par jour |
| **Données personnelles** | Aucune | Aucune (seulement des totaux par jour, aucun élève identifié) |
| **Remarque** | Classes déséquilibrées | 60 valeurs vides dans `repas_semaine_precedente` (premières semaines après les vacances) |

## 5. Baseline

| MaintAI | CantineAI |
|---|---|
| Toujours prédire « pas de panne » (classe majoritaire) | Reprendre le nombre de repas du même jour de la semaine précédente (`repas_semaine_precedente`), comme le fait le gestionnaire aujourd'hui |

## 5. Métrique principale

| MaintAI | CantineAI |
|---|---|
| **Recall** : part des vraies pannes détectées. Une panne manquée coûte bien plus cher qu'une fausse alerte, donc on veut en rater le moins possible. | **MAE** (erreur absolue moyenne) : elle s'exprime directement en nombre de repas, donc se traduit en dirhams perdus et en élèves sans repas. |

## 5. Critère d'acceptation

| MaintAI | CantineAI |
|---|---|
| Recall **≥ 0,80** sur le **jeu de test**, avec une precision **≥ 0,40** | MAE **≤ 40 repas** sur le **jeu de test (les 20 % de jours les plus récents)**, et **meilleure que la baseline** |

---

## Réglages de `config.py`

| Réglage | MaintAI | CantineAI |
|---|---|---|
| `DATA_PATH` | `data/exemple_pannes.csv` | `data/cantine_repas.csv` |
| `TARGET` | `failure` | `repas_servis` |
| `TASK` | `classification` | `regression` |
| `MAIN_METRIC` | `recall` | `mae` |
| `SPLIT` | `random` | `chronologique` |
| `TIME_COLUMN` | `None` | `date` |

---

## Questions finales

**MaintAI : un modèle qui ne prédit jamais de panne aurait quelle accuracy ? Pourquoi cette métrique ne convient-elle pas ?**

Il aurait une accuracy d'environ **82,4 %**, car 82,4 % des relevés ne sont pas des pannes. Pourtant, il ne détecterait **aucune** panne : son recall serait de 0. L'accuracy ne convient pas parce que les classes sont déséquilibrées et qu'une panne manquée coûte beaucoup plus cher qu'une fausse alerte.

**CantineAI : pourquoi ne faut-il pas tirer les jours de test au hasard ?**

C'est une série temporelle. Si on tire les jours au hasard, le modèle apprend sur des jours **futurs** pour prédire des jours **passés** : c'est une fuite d'information, et le score obtenu est trop optimiste. Dans la réalité, le gestionnaire ne connaît que le passé. On teste donc sur les jours les plus récents, avec un découpage chronologique.

---

## Résultats obtenus

| Prototype | Meilleur modèle | Résultat | Baseline | Critère |
|---|---|---|---|---|
| MaintAI | Régression logistique | Recall = 0,847, precision = 0,527 | Recall = 0 | **Atteint** |
| CantineAI | Régression linéaire | MAE = 22,2 repas | MAE ≈ 79 repas | **Atteint** |