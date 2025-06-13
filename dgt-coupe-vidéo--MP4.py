import streamlit as st
import ffmpeg
import os
import tempfile

def couper_video_ffmpeg_python(chemin_video_entree, temps_debut_sec, temps_fin_sec, chemin_video_sortie):
    try:
        if not os.path.exists(chemin_video_entree):
            st.error(f"Erreur : Le fichier d'entrée '{chemin_video_entree}' n'existe pas.")
            return

        st.info(f"Lecture des métadonnées de la vidéo...")
        try:
            probe = ffmpeg.probe(chemin_video_entree)
            duree_totale = float(probe['format']['duration'])
        except ffmpeg.Error as e:
            st.error("Erreur lors de la lecture des informations de la vidéo")
            st.text(e.stderr.decode('utf8'))
            return
        except Exception as e:
            st.error(f"Impossible d'obtenir la durée de la vidéo : {e}")
            return

        if temps_debut_sec < 0 or temps_fin_sec > duree_totale or temps_debut_sec >= temps_fin_sec:
            st.error(f"Temps de coupe invalides :\nDurée vidéo = {duree_totale:.2f}s, demandé = {temps_debut_sec}-{temps_fin_sec}s")
            return

        input_stream = ffmpeg.input(chemin_video_entree, ss=temps_debut_sec)
        output_stream = ffmpeg.output(input_stream, chemin_video_sortie, to=temps_fin_sec, c='copy')

        st.info("Découpe en cours... Cela peut prendre un moment.")
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        st.success(f"Vidéo coupée avec succès !")

        return chemin_video_sortie

    except ffmpeg.Error as e:
        st.error("Erreur FFmpeg rencontrée")
        if e.stderr:
            st.text(e.stderr.decode('utf8'))
    except FileNotFoundError:
        st.error("FFmpeg n'est pas installé ou non accessible dans le PATH système.")
    except Exception as e:
        st.error(f"Erreur inattendue : {e}")


def main():
    st.title("✂️ Outil de Découpe de Vidéo MP4 (FFmpeg + Streamlit)")

    fichier_video = st.file_uploader("Téléversez votre vidéo MP4", type=["mp4"])

    if fichier_video is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
            temp_input.write(fichier_video.read())
            temp_input_path = temp_input.name

        duree_video = None
        try:
            probe = ffmpeg.probe(temp_input_path)
            duree_video = float(probe['format']['duration'])
            st.success(f"Vidéo chargée. Durée : {duree_video:.2f} secondes")
        except:
            st.error("Impossible de lire la vidéo.")

        if duree_video:
            temps_debut = st.number_input("Temps de DÉBUT (s)", min_value=0.0, max_value=duree_video, step=0.1)
            temps_fin = st.number_input("Temps de FIN (s)", min_value=0.0, max_value=duree_video, step=0.1, value=duree_video)
            nom_fichier_sortie = st.text_input("Nom du fichier de sortie", value="video_coupee.mp4")

            if st.button("Lancer la découpe"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_output:
                    chemin_sortie = couper_video_ffmpeg_python(temp_input_path, temps_debut, temps_fin, temp_output.name)
                    if chemin_sortie:
                        with open(chemin_sortie, "rb") as f:
                            st.download_button("📥 Télécharger la vidéo découpée", f, file_name=nom_fichier_sortie)

if __name__ == "__main__":
    main()
