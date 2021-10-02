from flask import Flask, jsonify
app = Flask(__name__)


# we define the route /
@app.route('/')
def welcome():
    # return a json
    return jsonify({'status': 'api working'})


if __name__ == '__main__':
    # define the localhost ip and the port that is going to be used
    app.run(host='0.0.0.0', port=5000)
