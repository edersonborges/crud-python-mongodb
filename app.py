from flask import Flask, request, jsonify, render_template
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
import datetime
from functions import insert_initial_data, is_valid_name, product_name_exists, is_valid_price, get_all_products, get_product_by_id
from flask_restx import Api, Resource, fields

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

# Configuração do flask_restx
api = Api(app, version='1.0', title='Produtos API',
    description='API para gerenciar produtos',
)

product_model = api.model('Product', {
    'name': fields.String(required=True, description='Product name'),
    'price': fields.Float(required=True, description='Product price')
})

# Endpoint de login para gerar o token JWT
@api.route('/login')
class Login(Resource):
    @api.doc(responses={200: 'Success', 401: 'Invalid credentials'})
    def post(self):
        if request.json.get("username") == "admin" and request.json.get("password") == "admin":
            access_token = create_access_token(identity={"username": "admin"})
            return jsonify(access_token=access_token), 200
        return jsonify({"error": "Invalid credentials"}), 401

# Endpoint para verificar se a API está em execução
@api.route('/')
class HealthCheck(Resource):
    @api.doc(responses={200: 'API is running!'})
    def get(self):
        return jsonify({"status": "API is running!"}), 200

# Endpoint para obter produtos
@api.route('/products')
class ProductsList(Resource):
    @jwt_required()
    @api.doc(responses={200: 'Success', 401: 'Unauthorized'})
    def get(self):
        return get_all_products(products_collection)

    @jwt_required()
    @api.expect(product_model)
    @api.doc(responses={201: 'Created', 400: 'Bad request'})
    def post(self):
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

# Endpoint para operações com um produto específico
@api.route('/products/<id>')
@api.doc(params={'id': 'The product ID'})
class Product(Resource):
    @jwt_required()
    @api.doc(responses={200: 'Success', 401: 'Unauthorized', 404: 'Not found'})
    def get(self, id):
        return get_product_by_id(products_collection, id)

    @jwt_required()
    @api.expect(product_model)
    @api.doc(responses={200: 'Updated', 400: 'Bad request', 404: 'Not found'})
    def put(self, id):
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

    @jwt_required()
    @api.doc(responses={200: 'Deleted', 400: 'Bad request', 404: 'Not found'})
    def delete(self, id):
        try:
            result = products_collection.delete_one({"_id": ObjectId(id)})
            if result.deleted_count == 0:
                return jsonify({"error": "Product not found"}), 404
            return jsonify({"message": "Product deleted successfully"}), 200
        except Exception:
            return jsonify({"error": "Invalid ID format"}), 400

@app.route('/doc')
def swagger_ui():
    return render_template("swagger_ui.html", title=api.title, specs_url="/swagger.json")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
