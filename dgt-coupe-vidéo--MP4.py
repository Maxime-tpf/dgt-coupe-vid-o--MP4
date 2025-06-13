import streamlit as st
import ffmpeg
import os
import tempfile # Pour gérer les fichiers temporaires de manière sécurisée

def couper_video_ffmpeg_python(chemin_video_entree, temps_debut_sec, temps_fin_sec, chemin_video_sortie):
    """
    Coupe un segment d'une vidéo MP4 en utilisant ffmpeg-python et l'enregistre comme un nouveau fichier.

    Args:
        chemin_video_entree (str): Le chemin complet vers le fichier vidéo MP4 d'entrée.
        temps_debut_sec (float): Le temps de début de la coupe en secondes.
        temps_fin_sec (float): Le temps de fin de la coupe en secondes.
        chemin_video_sortie (str): Le chemin complet où la vidéo coupée sera enregistrée.
    """
    try:
        # Streamlit affiche déjà le message d'erreur si le fichier n'est pas uploadé
        if not os.path.exists(chemin_video_entree):
            st.error(f"Erreur : Le fichier d'entrée '{chemin_video_entree}' est introuvable sur le serveur.")
            return False

        st.info(f"Préparation de la découpe de : {os.path.basename(chemin_video_entree)} de {temps_debut_sec:.2f}s à {temps_fin_sec:.2f}s...")

        # Utilisation de ffmpeg.probe pour obtenir la durée de la vidéo
        try:
            probe = ffmpeg.probe(chemin_video_entree)
            duree_totale = float(probe['format']['duration'])
        except ffmpeg.Error as e:
            st.error(f"Erreur lors de la lecture des informations de la vidéo : {e.stderr.decode('utf8')}")
            return False
        except Exception as e:
            st.error(f"Impossible d'obtenir la durée de la vidéo. Erreur : {e}")
            return False

        # Valider les temps de coupe
        if temps_debut_sec < 0 or temps_fin_sec > duree_totale or temps_debut_sec >= temps_fin_sec:
            st.error(f"Erreur : Temps de coupe invalides. La durée totale est de {duree_totale:.2f}s.")
            st.error(f"Vous avez demandé de couper de {temps_debut_sec:.2f}s à {temps_fin_sec:.2f}s.")
            st.error("Veuillez vous assurer que 0 <= début < fin <= durée_totale.")
            return False

        # Construire le flux d'entrée avec les options de découpe
        input_stream = ffmpeg.input(chemin_video_entree, ss=temps_debut_sec)

        # Utilisation de '-to' pour la fin absolue dans la commande de sortie.
        output_stream = ffmpeg.output(input_stream, chemin_video_sortie, to=temps_fin_sec, c='copy')

        # Exécuter la commande FFmpeg
        st.info(f"Exécution de la découpe... Veuillez patienter.")
        # Utiliser un placeholder pour afficher la progression en temps réel si Streamlit le permet avec des logs
        # Pour des applications simples, le message "En cours..." est suffisant.
        
        ffmpeg.run(output_stream, overwrite_output=True, quiet=False) # quiet=False pour voir les logs dans le terminal de l'app Streamlit

        st.success(f"Vidéo coupée avec succès ! Enregistrée sous '{os.path.basename(chemin_video_sortie)}'")
        return True

    except ffmpeg.Error as e:
        st.error(f"Une erreur FFmpeg s'est produite :")
        st.error(f"Code d'erreur : {e.returncode}")
        if e.stdout:
            st.code(f"Stdout: {e.stdout.decode('utf8')}")
        if e.stderr:
            st.code(f"Stderr: {e.stderr.decode('utf8')}")
        st.warning("Conseil : Vérifiez les chemins d'accès et les temps de coupe. Assurez-vous que FFmpeg est à jour et correctement installé.")
        return False
    except FileNotFoundError:
        st.error("Erreur : La commande 'ffmpeg' n'a pas été trouvée.")
        st.error("Veuillez vous assurer que FFmpeg est installé et que son exécutable est dans votre PATH système sur la machine où Streamlit est exécuté.")
        return False
    except Exception as e:
        st.error(f"Une erreur inattendue s'est produite : {e}")
        st.warning("Veuillez vérifier les chemins et permissions des fichiers.")
        return False

# --- Interface Streamlit ---
st.set_page_config(page_title="Découpeur Vidéo MP4", layout="centered")

st.title("✂️ Découpeur Vidéo MP4 (avec FFmpeg-Python)")
st.write("Uploadez une vidéo MP4, spécifiez les temps de début et de fin, et découpez un segment.")

st.warning("**IMPORTANT :** Ce programme nécessite que **FFmpeg** soit installé sur votre système (et ajouté à votre PATH).")

uploaded_file = st.file_uploader("Choisissez un fichier MP4", type=["mp4"])

if uploaded_file is not None:
    # Pour Streamlit, nous devons enregistrer le fichier uploadé temporairement
    # afin que FFmpeg puisse y accéder via son chemin.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
        tmp_file.write(uploaded_file.read())
        chemin_entree = tmp_file.name
    
    st.video(chemin_entree) # Afficher un aperçu de la vidéo uploadée

    col1, col2 = st.columns(2)

    with col1:
        temps_debut = st.number_input("Temps de début (secondes)", min_value=0.0, value=0.0, step=0.1)
    
    with col2:
        temps_fin = st.number_input("Temps de fin (secondes)", min_value=0.0, value=10.0, step=0.1)

    nom_sortie = st.text_input("Nom du fichier de sortie (ex: ma_video_coupee.mp4)", "video_coupee.mp4")
    if not nom_sortie.lower().endswith(".mp4"):
        nom_sortie += ".mp4"

    if st.button("Découper la vidéo"):
        # Créer un chemin temporaire pour le fichier de sortie avant le téléchargement
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as output_tmp_file:
            chemin_sortie = output_tmp_file.name

        with st.spinner("Découpe en cours..."):
            success = couper_video_ffmpeg_python(chemin_entree, temps_debut, temps_fin, chemin_sortie)

        if success:
            st.download_button(
                label="Télécharger la vidéo coupée",
                data=open(chemin_sortie, "rb").read(),
                file_name=nom_sortie,
                mime="video/mp4"
            )
            # Afficher la vidéo coupée pour prévisualisation
            st.video(chemin_sortie)
        
        # Nettoyer les fichiers temporaires après utilisation
        if os.path.exists(chemin_entree):
            os.remove(chemin_entree)
        if os.path.exists(chemin_sortie):
            os.remove(chemin_sortie)
