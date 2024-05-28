# app.py

from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
import datetime
from functions import insert_initial_data, is_valid_name, product_name_exists, is_valid_price, get_all_products, get_product_by_id

app = Flask(__name__)

# Configuração do JWT
app.config['JWT_SECRET_KEY'] = 'CRUD'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)
jwt = JWTManager(app)

# Conexão com o MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client.get_database("app-produtos")
products_collection = db.get_collection("produtos")

insert_initial_data(products_collection)

# Endpoint de login para gerar o token JWT
@app.route('/login', methods=['POST'])
def login():
    if request.json.get("username") == "admin" and request.json.get("password") == "admin":
        access_token = create_access_token(identity={"username": "admin"})
        return jsonify(access_token=access_token), 200
    return jsonify({"error": "Invalid credentials"}), 401

# Endpoint para verificar se a API está em execução
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "API is running!"}), 200

# Endpoint para obter produtos
@app.route('/products', methods=['GET'])
@app.route('/products/<id>', methods=['GET'])
@jwt_required()
def get_products(id=None):
    if id:
        return get_product_by_id(products_collection, id)
    else:
        return get_all_products(products_collection)

# Endpoint para criar um novo produto
@app.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    data = request.json

    if not is_valid_name(data.get("name")):
        return jsonify({"error": "Name must be a non-empty string"}), 400

    if product_name_exists(products_collection, data["name"]):
        return jsonify({"error": "A product with the same name already exists"}), 400

    if not is_valid_price(data.get("price")):
        return jsonify({"error": "Price must be a non-empty, non-negative number"}), 400
    
    product = {
        "name": data["name"],
        "price": data["price"]
    }
    
    try:
        products_collection.insert_one(product)
        return jsonify(product), 201
    except DuplicateKeyError:
        return jsonify({"error": "Product with this ID already exists"}), 400

# Endpoint para atualizar um produto pelo ID
@app.route('/products/<id>', methods=['PUT'])
@jwt_required()
def update_product(id):
    data = request.json

    if not is_valid_name(data.get("name")):
        return jsonify({"error": "Name must be a non-empty string"}), 400

    if not is_valid_price(data.get("price")):
        return jsonify({"error": "Price must be a non-empty, non-negative number"}), 400
    
    update_data = {
        "name": data["name"],
        "price": data["price"]
    }

    try:
        result = products_collection.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        if result.matched_count == 0:
            return jsonify({"error": "Product not found"}), 404
        return jsonify({"message": "Product updated successfully"}), 200
    except Exception:
        return jsonify({"error": "Invalid ID format"}), 400

# Endpoint para deletar um produto pelo ID
@app.route('/products/<id>', methods=['DELETE'])
@jwt_required()
def delete_product(id):
    try:
        result = products_collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Product not found"}), 404
        return jsonify({"message": "Product deleted successfully"}), 200
    except Exception:
        return jsonify({"error": "Invalid ID format"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
