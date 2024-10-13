from flask import Flask, jsonify, abort, request
import mariadb
import urllib.parse

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False  # pour utiliser l'UTF-8 plutot que l'unicode


def execute_query(query, data=()):
    config = {
        'host': 'mariadb',
        'port': 3306,
        'user': 'root',
        'password': 'root',
        'database': 'mydatabase'
    }
    """Execute une requete SQL avec les param associés"""
    # connection for MariaDB
    conn = mariadb.connect(**config)
    # create a connection cursor
    cur = conn.cursor()
    # execute a SQL statement
    cur.execute(query, data)

    if cur.description:
        # serialize results into JSON
        row_headers = [x[0] for x in cur.description]
        rv = cur.fetchall()
        list_result = []
        for result in rv:
            list_result.append(dict(zip(row_headers, result)))
        return list_result
    else:
        conn.commit()
        return cur.lastrowid


# we define the route /
@app.route('/')
def welcome():
    liens = [{}]
    liens[0]["_links"] = [{
        "href": "/departements",
        "rel": "departements"
    }, {
        "href": "/regions",
        "rel": "regions"
    },
    {
        "href": "/villes",
        "rel": "villes"
    },
    {
        "href": "/pays",
        "rel": "pays"
    }]
    return jsonify(liens), 200


""" ################## REGIONS ##################
    #############################################"""


@app.route('/regions')
def get_regions():
    """recupère la liste des regions"""
    regions = execute_query("select code, nom from regions")
    # ajout de _links à chaque dico région
    for i in range(len(regions)):
        regions[i]["_links"] = [
            {
                "href": "/regions/" + urllib.parse.quote(regions[i]["nom"]),
                "rel": "self"
            },
            {
                "href": "/regions/" + urllib.parse.quote(regions[i]["nom"]) + "/departements",
                "rel": "departements"
            }
        ]
    return jsonify(regions), 200


@app.route('/regions/<string:nom>')
def get_region(nom):
    """"Récupère les infos d'une région en paramètre"""
    regions = execute_query("select code, nom from regions where nom=?", (nom,))
    # ajout de _links à la région 
    regions[0]["_links"] = [{
        "href": "/regions/" + urllib.parse.quote(regions[0]["nom"]) + "/departements",
        "rel": "departements"
    }]
    return jsonify(regions), 200



@app.route('/regions', methods=['POST'])
def post_region():
    """"Ajoute une région"""
    code = int(request.args.get("code"))
    nom = request.args.get("nom")
    execute_query("insert into regions (code, nom) values (?,?)", (code, nom))
    # on renvoi le lien de la région que l'on vient de créer
    reponse_json = jsonify({
        "_links": [{
            "href": "/regions/" + urllib.parse.quote(nom),
            "rel": "self"
        }]
    })
    return reponse_json, 201  # created

@app.route('/regions/<string:nom>', methods=['DELETE'])
def delete_region(nom):
    """supprimer une région"""
    execute_query("delete from regions where nom=?", (nom, ))
    return "", 204  # no data

""" ################## DEPARTEMENTS ##################
    #############################################"""


@app.route('/departements')
def get_departements():
    """récupère les départements"""
    departements = execute_query("select * from departements")
    for i in range(len(departements)):
        departements[i]["_links"] = [{
            "href": "/departements/" + departements[i]["code"],
            "rel": "self"
        }, {
            "href": "/departements/" + departements[i]["code"] + "/villes",
            "rel": "villes"
        }]
    return jsonify(departements), 200


@app.route('/departements/<string:code>')
def get_departement(code):
    """Récupère les infos d'un département en envoyant une requete HTTP
       Si le dpt n'existe pas renvoi 404
    """
    departements = execute_query("select code, nom from departements where code = ?", (code,))
    if departements == []:
        abort(404, "Ce département n'existe pas")
    departements[0]["_links"] = [{
        "href": "/departements/" + departements[0]["code"] + "/villes",
        "rel": "villes"
    }]
    return jsonify(departements), 200


@app.route('/departements/<string:code_dpt>', methods=['DELETE'])
def delete_departement(code_dpt):
    """supprimer un département"""
    execute_query("delete from departements where code=?", (code_dpt, ))
    return "", 204

#On doit bien les placé dans departement ces deux methodes
@app.route('/regions/<string:nom>/departements')
def get_departements_for_region(nom: str):
    """Récupère les département d'une région"""
    departements = execute_query("""select departements.nom, departements.code
                                    from departements
                                    join regions on departements.region_id = regions.id
                                    where lower(regions.nom) = ?""", (urllib.parse.unquote(nom.lower()),))
    if departements == []:
        abort(404, "Aucuns départements dans cette région")
    # ajout de _links à chaque dico département
    for i in range(len(departements)):
        departements[i]["_links"] = [{
            "href": "/departements/" + departements[i]["code"],
            "rel": "self"
        }]
    return jsonify(departements), 200

@app.route('/regions/<string:nom_region>/departements', methods=['POST'])
def post_departement_for_region(nom_region):
    """créé un département"""
    code_dpt = request.args.get("code")
    nom_dpt = request.args.get("nom")
    execute_query("insert into departements (code, nom, region_id) values (?, ?, (select id from regions where nom = ?))", (code_dpt, nom_dpt, nom_region))
    # on renvoi le lien du département  que l'on vient de créer
    reponse_json = jsonify({
        "_links": [{
            "href": "/departements/" + code_dpt,
            "rel": "self"
        }]
    })
    return reponse_json, 201  # created


""" ################## VILLES ##################
    #############################################"""

#Obtenir la liste de toutes les villes 
@app.route('/villes', methods=['GET'])
def get_villes():
    """Récupère la liste de toutes les villes avec leur département_id""" 
    # Requête SQL simple pour récupérer toutes les villes
    villes = execute_query("SELECT * FROM villes")
    # Ajout des liens _links pour chaque ville
    for i in range(len(villes)):
        villes[i]["_links"] = [{
            "href": f"/villes/{villes[i]['code_postal']}",
            "rel": "self"
        }, {
            "href": f"/departements/{villes[i]['departement_id']}",
            "rel": "departement"
        }]  
    # Retourne la liste des villes en format JSON avec un code HTTP 200 (OK)
    return jsonify(villes), 200

#Obtenir les details d'une ville specifique à partir du code postal
@app.route('/villes/<string:code_postal>', methods=['GET'])
def get_ville_by_code_postal(code_postal):
    """Récupère les détails d'une ville spécifique via son code postal"""
    # Requête SQL pour obtenir la ville avec le code postal donné
    ville = execute_query("SELECT * FROM villes WHERE code_postal = ?", (code_postal,))   
    # Vérifie si la ville existe
    if not ville:
        abort(404, description="Ville non trouvée") 
    # Ajout des liens _links pour la ville trouvée
    ville[0]["_links"] = [{
        "href": f"/villes/{ville[0]['code_postal']}",
        "rel": "self"
    }, {
        "href": f"/departements/{ville[0]['departement_id']}",
        "rel": "departement"
    }]
    
    # Retourne les détails de la ville avec un code HTTP 200
    return jsonify(ville[0]), 200

#Supprimer une ville 
@app.route('/villes/<string:code_postal>', methods=['DELETE'])
def delete_ville(code_postal):
    """supprimer une ville"""
    execute_query("delete from villes where code_postal=?", (code_postal, ))
    return "", 204

#Ajouter une ville specifique (en incluant donc le depart clé etrangere)
@app.route('/departements/<string:nom_departement>/villes', methods=['POST'])
def post_ville_for_departement(nom_departement):
    """Crée une ville dans un département spécifié par son nom"""
    nom_ville = request.args.get("nom")
    code_postal = request.args.get("code_postal")
    execute_query("INSERT INTO villes (nom, code_postal, departement_id) VALUES (?, ?, (SELECT id FROM departements WHERE nom = ?))", (nom_ville, code_postal, nom_departement))
    # On renvoie le lien de la ville que l'on vient de créer
    reponse_json = jsonify({
        "_links": [{
            "href": "/villes/" + code_postal,
            "rel": "self"
        }]
    })
    return reponse_json, 201  # Created

#Obtenir la liste de toutes les villes d'un departement 
@app.route('/departements/<string:nom>/villes')
def get_villes_for_departements(nom: str):
    """Récupère les villes d'un département"""
    villes = execute_query("""select villes.nom, villes.code_postal
                                    from villes
                                    join departements on villes.departement_id = departements.id
                                    where lower(departements.nom) = ?""", (urllib.parse.unquote(nom.lower()),))
    if villes == []:
        abort(404, "Aucune ville dans cet departement")
    # ajout de _links à chaque dico département
    for i in range(len(villes)):
        villes[i]["_links"] = [{
            "href": "/villes/" + villes[i]["code_postal"],
            "rel": "self"
        }]
    return jsonify(villes), 200
"""
# Importation des modules nécessaires
from flask import Flask, request, jsonify, abort

# Création d'une instance de l'application Flask
app = Flask(__name__)

# Définition de la route pour créer une ville dans un département spécifique, avec une méthode POST
@app.route('/departements/<string:nom_departement>/villes', methods=['POST'])
def post_ville_for_departement(nom_departement):

    Créer une ville dans un département spécifié par son nom.
    
    :param nom_departement: Nom du département où la ville sera ajoutée
    :type nom_departement: str

    # Récupération des paramètres 'code_postal' et 'nom' de la ville à partir de la requête
    code_postal = request.args.get("code_postal")
    nom_ville = request.args.get("nom")
    
    # Vérification de la présence des paramètres 'code_postal' et 'nom'. S'ils manquent, renvoie une erreur 400.
    if not code_postal or not nom_ville:
        abort(400, description="Le code postal et le nom de la ville sont requis.")
    
    # Exécution d'une requête SQL pour trouver l'ID du département basé sur le nom fourni
    departement = execute_query("SELECT id FROM departements WHERE nom = ?", (nom_departement,))
    
    # Vérification de l'existence du département. Si non trouvé, renvoie une erreur 404.
    if not departement:
        abort(404, description="Département non trouvé.")
    
    # Extraction de l'ID du département à partir du résultat de la requête
    departement_id = departement[0]['id']
    
    # Insertion de la nouvelle ville dans la base de données avec les informations fournies
    execute_query("INSERT INTO villes (code_postal, nom, departement_id) VALUES (?, ?, ?)", 
                  (code_postal, nom_ville, departement_id))
    
    # Création d'une réponse JSON contenant un lien vers la ville nouvellement créée
    reponse_json = jsonify({
        "_links": [{
            "href": "/villes/" + code_postal,
            "rel": "self"
        }]
    })
    
    # Renvoie la réponse JSON avec un code de statut HTTP 201 (Created), indiquant que la ville a été créée
    return reponse_json, 201


"""

#Obtenir la liste de toutes les villes d'une region
@app.route('/regions/<string:nom>/villes', methods=['GET'])
def get_villes_for_region(nom: str):
    """Récupère les villes d'une région spécifique"""
    villes = execute_query("""select villes.nom, villes.code_postal
                              from villes
                              join departements on villes.departement_id = departements.id
                              join regions on departements.region_id = regions.id
                              where lower(regions.nom) = ?""", (urllib.parse.unquote(nom.lower()),))
    if not villes:
        abort(404, "Aucune ville trouvée dans cette région")
    
    # ajout de _links à chaque dictionnaire de ville
    for i in range(len(villes)):
        villes[i]["_links"] = [{
            "href": "/villes/" + villes[i]["code_postal"],
            "rel": "self"
        }]
    
    return jsonify(villes), 200


""" ################## PAYS ##################
    #############################################"""

@app.route('/pays', methods=['GET'])
def get_all_pays():
    pays = execute_query("SELECT * FROM pays")
    for p in pays:
        p["_links"] = [{"href": f"/pays/{p['id']}", "rel": "self"}]
    return jsonify(pays), 200

@app.route('/pays', methods=['POST'])
def add_pays():
    # Récupération des paramètres 'code' et 'nom' du pays à partir de la requête
    code = request.args.get('code')
    nom = request.args.get('nom')
    if not code or not nom:
        abort(400, description="Les champs 'code' et 'nom' sont requis.")

    # Insertion du pays dans la base de données
    execute_query("INSERT INTO pays (code, nom) VALUES (?, ?)", (code, nom))

    # Création d'une réponse JSON contenant un lien vers le pays créé
    reponse_json = jsonify({
        "_links": [{
            "href": "/pays?code=" + urllib.parse.quote(code),
            "rel": "self"
        }]
    })
    return reponse_json, 201  # Code HTTP pour "Created"

@app.route('/pays/<string:nom>', methods=['GET'])
def get_pays(nom):
    """ Récupère les détails d'un pays spécifique par son nom """
    pays = execute_query("SELECT * FROM pays WHERE nom = ?", (nom,))
    if not pays:
        abort(404, description="Pays non trouvé")
    # Ajout des liens _links pour le pays trouvé
    pays[0]["_links"] = [{
        "href": f"/pays/{pays[0]['nom']}",
        "rel": "self"
    }]
    return jsonify(pays[0]), 200

@app.route('/pays/<string:code>', methods=['DELETE'])
def delete_pays(code):
    execute_query("DELETE FROM pays WHERE code = ?", (code,))
    return '', 204

@app.route('/pays/<string:code>', methods=['PUT'])
def update_pays(code):
    """ Met à jour un pays spécifié par son code """
    new_code = request.args.get('code')
    new_nom = request.args.get('nom')
    if not new_nom or not new_code:
        abort(400, "Les champs 'new_code' et 'nom' sont requis pour la mise à jour.")
    result = execute_query("UPDATE pays SET code=?, nom=? WHERE code=?", (new_code, new_nom, code))
    if result == 0:
        abort(404, "Pays non trouvé")

    # Création d'une réponse JSON contenant un lien vers le pays mis à jour
    reponse_json = jsonify({
        "_links": [{
            "href": f"/pays/{new_code}",
            "rel": "self"
        }]
    })
    return reponse_json, 200


"""
Attention pour ce code ci on utilise via postman le corps corps de la requête JSON au lieu des paramètres de la requête (query parameters)
@app.route('/pays', methods=['POST'])
def add_pays():
    data = request.get_json()
    code = data.get('code')
    nom = data.get('nom')
    if not code or not nom:
        abort(400, description="Les champs 'code' et 'nom' sont requis.")
    execute_query("INSERT INTO pays (code, nom) VALUES (?, ?)", (code, nom))
    pays_id = cur.lastrowid
    reponse_json = jsonify({
        "_links": [{
            "href": f"/pays/{pays_id}",
            "rel": "self"
        }]
    })
    return reponse_json, 201
"""

if __name__ == '__main__':
    # define the localhost ip and the port that is going to be used
    app.run(host='0.0.0.0', port=5000)
