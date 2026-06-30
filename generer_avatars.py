from PIL import Image, ImageDraw, ImageFont
import csv
import os

def data_copy(prenom, nom, taille=500):
    """Crée une image avec les initiales sur un fond coloré"""
    # Créer une nouvelle image
    img = Image.new('RGB', (taille, taille), color='#2196F3')  # Fond bleu
    draw = ImageDraw.Draw(img)

    try:
        # Essayer de charger une police système
        font = ImageFont.truetype("arial.ttf", size=int(taille/2))
    except:
        font = ImageFont.load_default()

    # Obtenir les initiales
    initiales = (prenom[0] + nom[0]).upper()

    # Obtenir la taille du texte
    bbox = draw.textbbox((0, 0), initiales, font=font)
    largeur_text = bbox[2] - bbox[0]
    hauteur_text = bbox[3] - bbox[1]

    # Centrer le texte
    x = (taille - largeur_text) // 2
    y = (taille - hauteur_text) // 2

    # Dessiner les initiales en blanc
    draw.text((x, y), initiales, font=font, fill='white')

    return img

def generer_avatars_from_csv():
    """Génère des des images pour tous les étudiants du fichier CSV"""
    # Assurer que le dossier photos existe
    if not os.path.exists('photos'):
        os.makedirs('photos')

    # Lire le fichier CSV
    with open('etudiants.csv', 'r', encoding='utf-8') as f:
        lecteur = csv.DictReader(f)
        for etudiant in lecteur:
            nom = etudiant['nom']
            prenom = etudiant['prenom']
            nom_fichier = etudiant['nom_fichier_photo']
            
            # Créer une image data
            avatar = data_copy(prenom, nom)
            
            # Sauvegarder l'image
            chemin_fichier = os.path.join('photos', nom_fichier)
            avatar.save(chemin_fichier)
            print(f"Avatar créé pour {prenom} {nom} -> {nom_fichier}")

if __name__ == "__main__":
    print("Génération des avatars...")
    generer_avatars_from_csv()
    print("Terminé !")