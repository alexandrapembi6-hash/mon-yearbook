# Documentation technique

## Architecture generale

Le projet est centre sur [main1.py](/c:/Users/Administrator/OneDrive/Desktop/mon%20yearbook/PROJET-PYTHON/main1.py).

Les sous-programmes sont regroupes par responsabilite :

- `parse_args` et `YearbookOptions` gerent les options globales du yearbook : orientation, citations, couleur/noir et blanc, chemins d'entree et PDF de sortie.
- `read_students`, `discover_photo`, `read_quote` lisent les donnees et construisent une liste d'objets `Student`.
- `resize_nearest`, `resize_interpolated`, `resize_manual` implementent le redimensionnement manuel.
- `box_blur_manual` applique un flou de type box blur.
- `create_cover_page`, `create_class_photo_page`, `create_student_pages` produisent les differentes pages.
- `save_pdf` assemble les pages dans un PDF A4.
- `main` orchestre la validation, la generation et la sauvegarde.

## Format des donnees

Le programme accepte :

- Le format du sujet : `id`, `prenom`, `nom`, `role`, `flouter`.
- Le format deja present dans le projet : `nom`, `prenom`, `promo`, `citation`, `nom_fichier_photo`.

Les citations peuvent venir :

- Soit d'un dossier de fichiers texte nommes par identifiant etudiant.
- Soit directement d'une colonne `citation` dans le CSV.

## Algorithme de redimensionnement

Le sujet demandait un algorithme manuel :

- Pour un agrandissement, `resize_nearest` applique la methode du plus proche voisin. Chaque pixel de destination recopie le pixel source le plus proche.
- Pour une reduction, `resize_interpolated` utilise une interpolation bilineaire. Pour chaque pixel de destination, on calcule une position reelle dans l'image source puis une moyenne ponderee des 4 pixels voisins.
- `resize_manual` choisit automatiquement la strategie adaptee selon que l'image est agrandie ou reduite.

Interet :

- Le plus proche voisin est simple et rapide pour l'agrandissement.
- L'interpolation bilineaire produit une reduction plus propre que la simple copie de pixels.

## Algorithme de floutage

`box_blur_manual` implemente un box blur :

- On parcourt chaque pixel.
- On considere une fenetre carree de rayon `radius` autour de ce pixel.
- On additionne les composantes rouge, verte et bleue des voisins.
- On remplace le pixel par la moyenne des couleurs de cette fenetre.

Le flou est applique uniquement aux etudiants marques comme floutes dans le CSV.

## Mise en page

Le programme respecte la structure demandee :

- Page de garde avec logo et nom de promotion.
- Page avec photo de classe.
- Pages etudiants.

Disposition des etudiants :

- Paysage sans citation : `3 x 5`.
- Portrait sans citation : `5 x 3`.
- Paysage avec citation : `2 x 5`.
- Portrait avec citation : `3 x 3`.

Les badges sont ajoutes sur la photo :

- `1` : delegue.
- `2` : suppleant.

Une trame simple est appliquee avec un bandeau haut, un pied de page et des cartes pour chaque etudiant.

## Commandes Pillow utilisees

Principales operations Pillow visibles dans le projet :

- `Image.open(...)` pour charger les images.
- `Image.new(...)` pour creer une page vide.
- `image.convert(...)` pour basculer en RGB ou noir et blanc.
- `image.crop(...)` pour recadrer.
- `image.paste(...)` pour coller logo et photos sur les pages.
- `ImageDraw.Draw(...)` pour dessiner textes, rectangles, cadres et badges.
- `draw.text(...)` et `draw.textbbox(...)` pour l'affichage et le calcul des zones de texte.
- `ImageFont.truetype(...)` pour charger une police.
- `image.save(..., save_all=True, append_images=...)` pour exporter le PDF.

## Lancement

Depuis le dossier `PROJET-PYTHON` :

```powershell
python main1.py
```

Exemple avec options :

```powershell
python main1.py --orientation portrait --quotes non --color nb --output yearbook_nb.pdf
```

## Tests

Le fichier [test_yearbook.py](/c:/Users/Administrator/OneDrive/Desktop/mon%20yearbook/PROJET-PYTHON/test_yearbook.py) contient des tests simples sur :

- Les dimensions du redimensionnement.
- La conservation de taille apres flou.
- Les dimensions A4.
- Une generation complete minimale de 3 pages.
