from flask import Flask, render_template, request, redirect , url_for, flash , session ,jsonify
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from flask import abort
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from forms import RegisterForm,LoginForm, AddItemForm
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
import paypalrestsdk
from paypalrestsdk import Payment
from datetime import datetime
from flask.json import JSONEncoder
import json
import hashlib
from flask_gravatar import Gravatar



class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, OrderItem):
            return {'id': obj.id, 'item_id': obj.item_id, 'quantity': obj.quantity}
        return super().default(obj)



app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///betting_predictions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json_encoder = CustomJSONEncoder
Bootstrap(app)
db = SQLAlchemy(app)

app.app_context().push()

login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(app, size=50, rating='g', default='retro',
 force_default=False, force_lower=False, use_ssl=False, base_url=None)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    cart_items = db.relationship('CartItem', backref='user', lazy='dynamic')
    orders = db.relationship('Order', backref='user', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    items = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)   

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=True)
    description = db.Column(db.String(256), nullable=True)
    odds = db.Column(db.String(256),nullable=True)
    price = db.Column(db.Float, nullable=True)
    detailed_description = db.Column(db.String(1000))
    img_url = db.Column(db.String(1000),nullable=True)
    cart_items = db.relationship('CartItem', backref='item', lazy='dynamic')
    
    
class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)



def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin():
    users = User.query.all()
 
    return render_template('admin.html', title='Admin', users=users)

@app.route('/create_admin', methods=['POST'])
def create_admin():
    # Get the form data from the request
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    # Create a new user with admin privileges
    user = User(username=username, email=email, password=password, is_admin=True)
    db.session.add(user)
    db.session.commit()

    return redirect(url_for('admin'))

@app.route('/')
def index():
    items = Item.query.all()
    return render_template('index.html', items=items)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("logged in successfully",'success')
            return redirect(url_for('index'))
          
    return render_template("login.html", form=form)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            username=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Successfully registered!! ')
  
        
        return redirect(url_for("login"))

    return render_template("register.html", form=form)

@app.route('/items')
def item_list():
    items = Item.query.all()
    return render_template('item_list.html', items=items)

@app.route('/add_to_cart', methods=["GET", "POST"])
def add_to_cart():
    if not current_user.is_authenticated:
        flash('Login or register to start buying.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        item_id = request.form['item_id']
        quantity = request.form['quantity']
        item = Item.query.filter_by(id=item_id).first()
        if not item:
            flash('Item not found.', 'error')
            return redirect(url_for('index'))

    # Check if the user already has this item in their cart
    existing_cart_item = CartItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if existing_cart_item:
        existing_cart_item.quantity += int(quantity)
        db.session.commit()
        flash('Item added to cart!', 'success')
        return redirect(url_for('index'))

    # Otherwise, create a new cart item for the user
    new_cart_item = CartItem(user_id=current_user.id, item_id=item_id, quantity=quantity)
    db.session.add(new_cart_item)
    db.session.commit()
    flash('Item added to cart!', 'success')
    return redirect(url_for('index'))

@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = 0
    for cart_item in cart_items:
        item = Item.query.filter_by(id=cart_item.item_id).first()
        cart_item.total_price = cart_item.quantity * item.price
        db.session.commit()
        total += cart_item.total_price

    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
@admin_required
def add_item():
    form = AddItemForm()
    if form.validate_on_submit():
        item = Item(name=form.name.data,
                    description=form.description.data,
                    price=form.price.data,odds=form.odds.data,detailed_description=form.detailed_description.data
                    ,img_url=form.img_url.data)
        db.session.add(item)
        db.session.commit()
        flash('Item added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_item.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/remove_from_cart', methods=['POST'])
@login_required
def remove_from_cart():
    item_id = request.form['item_id']
    cart_item = CartItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)
        db.session.commit()
    flash('item removed successfully','success')
    return redirect(url_for('cart'))


@app.route('/get_cart_items_count')
def get_cart_items_count():
    count = 0
    if current_user.is_authenticated:
        count = current_user.cart_items.count()
    return jsonify({'count': count})

@app.route('/save-order', methods=['POST'])
@login_required
def save_order():
    # Fetch items from cart using the user_id
    user_cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    # Create a list to hold the order details
    order_items = []
    
    # Loop through the cart items and create OrderItems for each item
    for cart_item in user_cart_items:
        order_item = OrderItem(
            item_id=cart_item.item_id,
            quantity=cart_item.quantity,
            price=cart_item.item.price
        )
        order_items.append(order_item)
    
    # Create a new Order and add the OrderItems to it
    order = Order(
        user_id=current_user.id,
        total=0,
        items=json.dumps(order_items,cls=CustomJSONEncoder),
        date_created=datetime.now()
    )
    
    # Save the order to the database
    db.session.add(order)
    db.session.commit()
    
    # Clear the cart by deleting all cart items for the user
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    # Display the order details on the success page
    return redirect(url_for('payment_success'))

@app.route('/success')
def payment_success():
    return render_template("payment_success.html")


@app.route('/profile')
def profile():
    order_list = []
    user = current_user
    orders = Order.query.filter_by(user_id=user.id).all()
    for order in orders:
        order_items_json = order.items
        order_items = json.loads(order_items_json)

# Get the item details for each order item
        for item in order_items:
            item_id = item['item_id']
            item_details = Item.query.get(item_id)
            order_list.append(item_details)

# Do something with the item details

    return render_template('profile.html',orders = order_list, user=user)

if __name__ == '__main__':
    app.run(debug=True)
