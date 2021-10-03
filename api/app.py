from flask import Flask, jsonify
app = Flask(__name__)


# we define the route /
@app.route('/')
def welcome():
    # return a json
    return jsonify({'status': 'api working welcome'})


@app.route('/regions')
def get_regions():
    # return a json
    return jsonify({'status': 'api working regions'})


@app.route('/departements')
def get_departements():
    # return a json
    return jsonify({'status': 'api working departements'})


@app.route('/villes')
def get_villes():
    # return a json
    return jsonify({'status': 'api working villes'})


if __name__ == '__main__':
    # define the localhost ip and the port that is going to be used
    app.run(host='0.0.0.0', port=5000)
