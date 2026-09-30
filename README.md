# Prédiction de consommation de médicaments

Pipeline de prévision du volume de consommation (Open Medic) : méthodes de séries temporelles, machine learning, et modèles hybrides.

## Démarrage rapide

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
# source venv/bin/activate

pip install -r requirements.txt
jupyter notebook notebooks/prediction_medicaments_complete.ipynb
```

Sans TensorFlow, la pipeline tourne quand même (LSTM désactivé par défaut). Pour l’activer : `run_pipeline(use_lstm=True)`.

## Données

Le dump `OPEN_MEDIC_2024/OPEN_MEDIC_2024.CSV` (~479 Mo) **n’est pas sur GitHub** (limite 100 Mo).

- Échantillon versionné : `data/raw/open_medic_sample.csv` (utilisé automatiquement si le dump est absent)
- Dump complet : voir `OPEN_MEDIC_2024/README.md` et [Open Medic sur data.gouv.fr](https://www.data.gouv.fr/fr/datasets/open-medic-base-complete-sur-les-depenses-de-medicaments-interregimes/)

Open Medic n’a pas de date de transaction : les lignes sont projetées sur un calendrier puis agrégées en série quotidienne (`volume_consomme`), comme dans le notebook d’origine.

## Structure

```
projet-ai/
├── src/
│   ├── data_preprocessing.py   # chargement, nettoyage, features
│   └── forecasting.py          # modèles et évaluation
├── notebooks/
│   ├── 01_exploration.ipynb
│   ├── prediction_medicaments_complete.ipynb
│   └── generate_article_visualizations.ipynb
├── data/raw/open_medic_sample.csv
├── models/                     # résultats d’expériences déjà menées
├── article_prediction_medicaments.tex
├── poster.tex
├── requirements.txt
└── LICENSE
```

Ne versionnez pas `venv/` ni le CSV complet (voir `.gitignore`).

## Pipeline

1. Chargement et nettoyage (séparateur `;`, décimales françaises)
2. Série quotidienne + interpolation
3. Features : calendrier, encodages cycliques, lags, statistiques glissantes
4. Split chronologique 70 % / 15 % / 15 % (sans mélange)
5. Modèles : moyenne mobile, LTA, SES, DES, ARIMA, régression, Random Forest, XGBoost, hybride ARIMA+XGB (LSTM optionnel)
6. Métriques : MAE, RMSE, MAPE, R² — fichiers dans `outputs/` à l’exécution

Les CSV de `models/` sont les résultats déjà produits pour l’article / le poster. Une nouvelle exécution écrit dans `outputs/` pour ne pas les écraser.

## Article et poster

- Article : `article_prediction_medicaments.tex`
- Poster : `poster.tex` — compilation : voir `README_POSTER.md`
- Figures : `notebooks/generate_article_visualizations.ipynb` (idéal après le notebook principal ; les tableaux de `models/` suffisent pour plusieurs graphiques)

## Licence

MIT — voir `LICENSE`. Les données Open Medic restent sous la licence de data.gouv.fr.
