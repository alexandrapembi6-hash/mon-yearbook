import zipfile
import os
import shutil

def extraire_photos_zip():
    # Chercher le fichier zip qui contient 'data' dans le nom
    dossier_courant = os.path.dirname(os.path.abspath(__file__))
    fichiers = os.listdir(dossier_courant)
    fichier_zip = None
    
    for fichier in fichiers:
        if fichier.endswith('.zip') and 'data' in fichier.lower():
            fichier_zip = fichier
            break
    
    if not fichier_zip:
        print("Aucun fichier  contenant 'data' a été trouvé.")
        return
    
    # Créer/nettoyer le dossier photos
    if os.path.exists('photos'):
        # Sauvegarder le logo de l'université s'il existe
        logo_path = os.path.join('photos', 'logo de l\'universite.png')
        if os.path.exists(logo_path):
            temp_logo = 'temp_logo.png'
            shutil.copy2(logo_path, temp_logo)
        
        # Supprimer l'ancien contenu
        shutil.rmtree('photos')
    
    os.makedirs('photos', exist_ok=True)
    
    # Restaurer le logo si sauvegardé
    if os.path.exists('temp_logo.png'):
        shutil.move('temp_logo.png', logo_path)
    
    # Extraire le contenu du zip
    print(f"Extraction de {fichier_zip}...")
    with zipfile.ZipFile(fichier_zip, 'r') as zip_ref:
        zip_ref.extractall('photos')
    
    print("Photos extraites avec succès !")

if __name__ == "__main__":
    extraire_photos_zip()