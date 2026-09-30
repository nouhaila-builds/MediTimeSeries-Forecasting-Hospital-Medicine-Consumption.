# Poster LaTeX - Hospital Medicine Consumption Forecasting

## Description
Ce fichier LaTeX génère un poster scientifique au format A0 (portrait) pour présenter le projet de prédiction de consommation de médicaments hospitaliers.

## Prérequis

### Packages LaTeX nécessaires
- `tikzposter` : Classe principale pour créer le poster
- `tikz` : Pour les graphiques (inclus avec tikzposter)
- `amsmath`, `amssymb`, `amsfonts` : Pour les formules mathématiques
- `booktabs` : Pour les tableaux professionnels
- `graphicx` : Pour insérer les images
- `adjustbox` : Pour ajuster les images
- `enumitem` : Pour les listes personnalisées
- `xcolor` : Pour les couleurs

### Installation des packages

**Sur Linux (TeX Live):**
```bash
sudo apt-get install texlive-latex-extra texlive-pictures texlive-latex-recommended
```

**Sur Windows (MiKTeX):**
Les packages seront installés automatiquement lors de la première compilation.

**Sur macOS (MacTeX):**
```bash
brew install --cask mactex
```

## Compilation

### Méthode 1 : Compilation directe
```bash
pdflatex poster.tex
```

### Méthode 2 : Avec bibliographie (si nécessaire)
```bash
pdflatex poster.tex
bibtex poster
pdflatex poster.tex
pdflatex poster.tex
```

## Format du poster

- **Format** : A0 (841mm × 1189mm) - Portrait
- **Marges** : 0mm (marges internes de 15mm)
- **Espacement** : 15mm entre les colonnes, 8mm entre sous-colonnes

## Structure du poster

Le poster contient les sections suivantes :

1. **Background** - Contexte et problématique
2. **Proposed Workflow** - Pipeline de données proposé
3. **Aims and Objectives** - Objectifs de la recherche
4. **Experimental Setup** - Configuration expérimentale
5. **Related Works** - Travaux connexes
6. **Results** - Résultats et comparaisons
7. **Conclusion & Future Works** - Conclusion et travaux futurs
8. **References** - Références bibliographiques
9. **Acknowledgment** - Remerciements

## Images à insérer

Le poster contient des placeholders pour les images suivantes :

1. **Image 1 (Background)** : Graphique montrant l'impact des ruptures de stock vs surstockage
2. **Image 2 (Workflow)** : Diagramme de flux complet du pipeline
3. **Image 3 (Objectives)** : Diagramme visuel des objectifs avec icônes
4. **Image 4 (Experimental Setup)** : Tableau récapitulatif des configurations OU architecture LSTM
5. **Image 5 (Related Works)** : Timeline ou tableau comparatif des travaux précédents
6. **Image 6a (Results)** : Graphique en barres comparant les MAPE de tous les modèles
7. **Image 6b (Results)** : Courbes de prédiction vs valeurs réelles
8. **Image 6c (Results)** : SHAP summary plot
9. **Image 6d (Results)** : Graphique d'analyse des pics
10. **Image 7 (Conclusion)** : Diagramme des contributions OU timeline des travaux futurs

## Comment insérer les images

Pour remplacer un placeholder par une vraie image, remplacez le bloc `\fbox{...}` par :

```latex
\begin{center}
\includegraphics[width=0.9\textwidth]{nom_de_votre_image.png}
\captionof{figure}{Description de l'image}
\end{center}
```

Ou pour une image avec une taille spécifique :

```latex
\begin{center}
\includegraphics[width=0.8\textwidth, height=0.3\textheight, keepaspectratio]{nom_de_votre_image.png}
\end{center}
```

## Personnalisation

### Changer les couleurs
Modifiez les définitions de couleurs dans le préambule :
```latex
\definecolor{primaryblue}{RGB}{0,51,102}
\definecolor{secondaryblue}{RGB}{0,102,204}
```

### Changer le thème
Remplacez `\usetheme{Default}` par :
- `\usetheme{Basic}`
- `\usetheme{Simple}`
- `\usetheme{Envelope}`
- `\usetheme{Wave}`
- `\usetheme{Board}`
- `\usetheme{Autumn}`
- `\usetheme{Desert}`

### Changer le style de couleur
Remplacez `\usecolorstyle{Default}` par :
- `\usecolorstyle{Australia}`
- `\usecolorstyle{Britain}`
- `\usecolorstyle{Sweden}`
- `\usecolorstyle{Spain}`
- `\usecolorstyle{Russia}`
- `\usecolorstyle{Denmark}`
- `\usecolorstyle{Germany}`

## Notes importantes

1. **Taille des polices** : Le poster utilise une taille de base de 25pt. Les sections utilisent des tailles automatiques basées sur le thème.

2. **Tableaux** : Le tableau des résultats utilise `booktabs` pour un style professionnel. Assurez-vous que le package est installé.

3. **Listes** : Les listes utilisent `enumitem` pour un contrôle précis de l'indentation.

4. **Espacement** : Les espacements entre les blocs sont contrôlés par `blockverticalspace=15mm` dans les options de classe.

## Dépannage

### Erreur : "tikzposter.sty not found"
Installez le package tikzposter :
```bash
# Linux
sudo apt-get install texlive-pictures

# Ou via tlmgr (TeX Live)
tlmgr install tikzposter
```

### Erreur : "File ended while scanning use of \@xverbatim"
Vérifiez que tous les environnements `verbatim` ou `lstlisting` sont correctement fermés.

### Le poster est trop grand pour l'écran
C'est normal ! Le poster A0 est très grand. Utilisez un visualiseur PDF avec zoom (comme Adobe Reader) ou compilez directement en PDF pour l'impression.

## Support

Pour toute question ou problème, consultez la documentation de tikzposter :
- Documentation : https://ctan.org/pkg/tikzposter
- Exemples : https://www.overleaf.com/latex/templates/tikzposter-poster-template/yzqgqjqjqjqj

