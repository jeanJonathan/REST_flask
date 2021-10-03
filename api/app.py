from flask import Flask, jsonify
import mariadb
app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False  # pour utiliser l'UTF-8 plutot que l'unicode

config = {
    'host': 'mariadb',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'mydatabase'
}


def execute_query(query):
    # connection for MariaDB
    conn = mariadb.connect(**config)
    # create a connection cursor
    cur = conn.cursor()
    # execute a SQL statement
    cur.execute(query)

    # serialize results into JSON
    row_headers = [x[0] for x in cur.description]
    rv = cur.fetchall()
    json_data = []
    for result in rv:
        json_data.append(dict(zip(row_headers, result)))
    return json_data


# we define the route /
@app.route('/')
def welcome():
    # return a json
    return jsonify({'status': 'api working welcome'})


@app.route('/regions')
def get_regions():
    json_data = execute_query("select * from regions")
    return jsonify(json_data)


@app.route('/departements')
def get_departements():
    json_data = execute_query("select * from departements")
    # return a json
    return jsonify(json_data)


@app.route('/villes')
def get_villes():
    # return a json
    return jsonify({'status': 'api working villes'})


if __name__ == '__main__':
    # define the localhost ip and the port that is going to be used
    app.run(host='0.0.0.0', port=5000)
