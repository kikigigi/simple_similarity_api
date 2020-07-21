from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SimilarityDB
users = db["Users"]

class Register(Resource):
    # Step 1 - get posted data
    # Step 2 - verify username
    # Step 3 - encode password
    # Step 4 - store username and password to db

    def post(self):
        # Step 1
        data = request.get_json()
        # Step 2
        username = data['username']
        if userExist(username):
            return jsonify({'message': 'Invalid username!',
                             'status': 301})

        password = data['password']
        # Step 3
        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
        # Step 4
        users.insert({'Username': username,
                      'Password': hashed_pw,
                      'Tokens': 6})

        return jsonify({'message': 'User successfully created!',
                        'status': 200})


def userExist(username):
    if users.count_documents({'Username': username}) == 0:
        return False
    return True


class Detect(Resource):
    # Step 1 - get the posted data
    # Step 2 - verify user
    # Step 3 - check tokens
    # Step 4 - check similarity

    def post(self):
        # Step 1
        data = request.get_json()
        username = data['username']

        # Step 2
        if not userExist(username):
            return jsonify({'message': 'Invalid username!',
                           'status': 301})

        password = data['password']
        if not correctPassword(username, password):
            return jsonify({'message': 'Invalid password!',
                            'status': 302})
        # Step 3
        num_tokens = countTokens(username)
        if num_tokens == 0:
            return jsonify({'message': 'You are out of tokens. Please refill tokens!',
                            'status': 303})

        # Step 4
        text1 = data['text1']
        text2 = data['text2']

        nlp = spacy.load('en_core_web_sm')
        text1 = nlp(text1)
        text2 = nlp(text2)

        similarity = text1.similarity(text2)

        users.update({'Username':username},
                     {'$set':{'Tokens': num_tokens - 1}

        })

        return jsonify({'message': 'Similarity of two documents is {}'.format(similarity),
                        'status': 200})


def correctPassword(username, password):
    hashed_pw = users.find({'Username': username})[0]['Password']
    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    return False

def countTokens(username):
    return users.find({'Username':username})[0]['Tokens']

class Refill(Resource):
    def post(self):
        # Step 1 - verify username
        # Step 2 - verify admin password
        # Step 3 - add tokens

        # Step 1
        data = request.get_json()
        username = data['username']

        if not userExist(username):
            return jsonify({'message': 'Invalid username',
                            'status': 301})
        # Step 2
        password = data['admin_pw']
        correct_pw = "abc123"
        if password != correct_pw:
            return jsonify({'message': 'Invalid admin password',
                            'status': 304})

        # Step 3
        num_tokens = data['refill']
        current_tokens = countTokens(username)
        total = current_tokens + num_tokens
        users.update({'Username':username},
                     {'$set':{'Tokens':total}})
        return jsonify({'message': 'Tokens added successfully. Total tokens are {}'.format(total),
                        'status': 200})


api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')

if __name__ == "__main__":
    app.run(host="0.0.0.0")
