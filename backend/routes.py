from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok"}

@app.route('/count', methods=['GET'])
def count():
    return {"count": len(songs_list)}

@app.route('/song', methods=['GET'])
def song():
    songs = db.songs.find({})
    return {"songs": parse_json(songs)}

@app.route('/song/<int:id>', methods=['GET'])
def get_song_by(id):
    song = db.songs.find_one({"id": id})
    if not song:
        return {"message": "song with id not found"}, 404
    return parse_json(song)

@app.route('/song', methods=['POST'])
def create_song():
    data = request.json
    if db.songs.find_one({"id": data["id"]}):
        return {"Message": "song with id {} already present".format(data['id'])}, 302
    db.songs.insert_one(data)
    return {"inserted id": data["id"]}, 201

@app.route('/song/<int:id>', methods=['PUT'])
def update_song(id):
    data = request.json
    song = db.songs.find_one({"id": id})
    if not song:
        return {"message": "song not found"}, 404
    db.songs.update_one({"id": id}, {"$set": data})
    return parse_json(db.songs.find_one({"id": id}))

@app.route('/song/<int:id>', methods=['DELETE'])
def detele_song(id):
    deleted = db.songs.delete_one({"id": id})
    if deleted.deleted_count == 0:
        return {"message": "song not found"}, 404
    return {}, 204