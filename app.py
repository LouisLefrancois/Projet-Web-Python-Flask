from cv2 import CascadeClassifier, CASCADE_SCALE_IMAGE, COLOR_BGR2GRAY, cvtColor, imwrite, imread, rectangle
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'static/images'  # Dossier où les images seront stockés
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/') # Route par défaut - home.jinja ; lecture des infos des films à partir d'un fichier
def index():
    films = read_films_from_file()
    return render_template('home.jinja', films=films)


@app.route('/film/<int:film_id>') # Affiche les détails d'un film spécifique en utilisant son id ; détecte les visages dans l'image du film (si disponible) et génère une page HTML pour afficher les détails
def film_details(film_id):
    film = get_film_by_id(film_id)

    # Détection des visages dans l'image du film
    if film is not None:
        detect_faces(film)

    return render_template('film_detail.jinja', film=film)

@app.route('/film/add', methods=['GET', 'POST']) # Permet à l'utilisateur d'ajouter un film à partir d'un form ; redirection vers le film nouvellement ajouté
def create_film(): # fonction gère les requêtes GET et POST 
    if request.method == 'POST':
        film_data = {
            'image': '',
            'titre': request.form['titre'],
            'description': request.form['description'],
            'annee': int(request.form['annee']),
            'acteurs': request.form['acteurs'],
            'realisation': request.form['realisation']
        }

        if 'image' in request.files:
            image = request.files['image']
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            film_data['image'] = filename

        create_film_in_file(film_data)
        return redirect(url_for('film_details', film_id=film_data['id']))

    return render_template('film_ajout.jinja')


@app.route('/film/edit/<int:film_id>', methods=['GET', 'POST']) # Permet la modification d'un film ; redirection vers la page des détails du film modifié
def update_film(film_id):
    film = get_film_by_id_from_file(film_id)
    if request.method == 'POST':
        film['image'] = request.form['image']
        film['titre'] = request.form['titre']
        film['description'] = request.form['description']
        film['annee'] = int(request.form['annee'])
        film['acteurs'] = request.form['acteurs']
        film['realisation'] = request.form['realisation']
        update_film_in_file(film_id, film)
        return redirect(url_for('film_details', film_id=film_id))

    return render_template('film_modif.jinja', film=film)


@app.route('/film/delete/<int:film_id>', methods=['POST']) # Supprime le film choisi
def delete_film(film_id):
    delete_film_from_file(film_id)
    return redirect(url_for('index'))


def read_films_from_file(): # Fonction qui lit les informations des films à partir du fichier "mesfilms.txt" 
    films = []
    with open('mesfilms.txt', 'r') as file:
        for line in file:
            film_data = line.strip().split(';')
            film = {
                'id': int(film_data[0]),
                'image': film_data[1],
                'titre': film_data[2],
                'description': film_data[3],
                'annee': int(film_data[4]),
                'acteurs': film_data[5],
                'realisation': film_data[6]
            }
            films.append(film)
    return films


def get_film_by_id(film_id): # Fonction qui permet d'obtenir les infos d'un film spécifique en utilisant son id
    films = read_films_from_file()
    for film in films:
        if film['id'] == film_id:
            return film
    return None


def get_film_by_id_from_file(film_id): # Fonction qui permet d'obtenir les informations d'un film spécifique en utilisant son id en lisant le fichier "mesfilms.txt"
    with open('mesfilms.txt', 'r') as file:
        for line in file:
            film_data = line.strip().split(';')
            if int(film_data[0]) == film_id:
                film = {
                    'id': int(film_data[0]),
                    'image': film_data[1],
                    'titre': film_data[2],
                    'description': film_data[3],
                    'annee': int(film_data[4]),
                    'acteurs': film_data[5],
                    'realisation': film_data[6]
                }
                return film
    return None


def write_films_to_file(films): # Prend la liste des films en entrée et écrit les informations de chaque film dans le fichier "mesfilms.txt"
    with open('mesfilms.txt', 'w') as file:
        for film in films:
            file.write(f"{film['id']};{film['image']};{film['titre']};{film['description']};{film['annee']};{film['acteurs']};{film['realisation']}\n")


def get_next_film_id(films): # Fonction qui permet d'obtenir l'id qui sera attribué au prochain film à ajouter dans la liste.
    if films:
        return max(film['id'] for film in films) + 1
    else:
        return 1


def create_film_in_file(film_data): # Ajoute un nouveau film dans le fichier "mesfilms.txt"
    films = read_films_from_file()
    film_data['id'] = get_next_film_id(films)
    films.append(film_data)
    write_films_to_file(films)


def update_film_in_file(film_id, updated_film): # Update les infos dans le fichier "mesfilms.txt"
    films = read_films_from_file()
    for film in films:
        if film['id'] == film_id:
            film.update(updated_film)
            break
    write_films_to_file(films)


def delete_film_from_file(film_id): # Supprime un nouveau film dans le fichier "mesfilms.txt"
    films = read_films_from_file()
    for film in films:
        if film['id'] == film_id:
            # Supprimer l'image associée dans le dossier
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], film['image'])
            if os.path.exists(image_path):
                os.remove(image_path)
            break

    films = [film for film in films if film['id'] != film_id]
    write_films_to_file(films)


def detect_faces(film): # utilise l'algo de détéction des visages
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], film['image'])
    image = imread(image_path)
    gray = cvtColor(image, COLOR_BGR2GRAY)

    cascPath = './haarcascade_frontalface_default.xml'
    faceCascade = CascadeClassifier(cascPath)

    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(30, 30),
        flags=CASCADE_SCALE_IMAGE
    )

    print('Found {} faces!'.format(len(faces))) # Print dans la console

    for (x, y, w, h) in faces:
        rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 5)

    output_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'faces_' + film['image'])
    imwrite(output_image_path, image)
    film['faces_image'] = 'faces_' + film['image']

    film['num_faces'] = len(faces)
    

if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'static/images'
    app.run(debug=True)
