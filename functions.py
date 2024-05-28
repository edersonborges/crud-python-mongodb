from flask import jsonify
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId

def insert_initial_data(collection):
    """
    Insere dados iniciais na coleção se estiver vazia.
    """
    if collection.count_documents({}) == 0:
        initial_data = [
            {"name": "Product 1", "price": 10.99},
            {"name": "Product 2", "price": 15.49},
            {"name": "Product 3", "price": 7.99}
        ]
        collection.insert_many(initial_data)

def is_valid_name(name):
    """
    Verifica se o nome é uma string não vazia.
    """
    return name and isinstance(name, str)

def product_name_exists(collection, name):
    """
    Verifica se já existe um produto com o mesmo nome.
    """
    return collection.find_one({"name": name}) is not None

def is_valid_price(price):
    """
    Verifica se o preço é um número não negativo.
    """
    return price is not None and isinstance(price, (int, float)) and price >= 0

def get_all_products(collection):
    """
    Obtém todos os produtos.
    """
    products = list(collection.find({}))
    products_with_ids = [{"_id": str(product["_id"]), "name": product["name"], "price": product["price"]} for product in products]
    return jsonify(products_with_ids), 200

def get_product_by_id(collection, id):
    """
    Obtém um produto pelo ID.
    """
    try:
        product = collection.find_one({"_id": ObjectId(id)}, {'_id': 0})
        if not product:
            return jsonify({"error": "Product not found"}), 404
        return jsonify(product), 200
    except Exception:
        return jsonify({"error": "Invalid ID format"}), 400
