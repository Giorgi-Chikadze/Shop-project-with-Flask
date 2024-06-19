import os
from flask import Flask, render_template, redirect, request, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from utilis import check_in_session, protected
from sqlalchemy import or_ 

app = Flask(__name__) 
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///post.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "12345"
db = SQLAlchemy(app) 

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    price = db.Column(db.Integer)
    image = db.Column(db.String(500))
    phonenumber = db.Column(db.Integer)
    postname = db.Column(db.String(30))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post_ref', lazy=True)
    ratings = db.relationship('Rating', backref='post_ref', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30))
    username = db.Column(db.String(30))
    password = db.Column(db.String(30))
    Money = db.Column(db.Integer)
    confirmpassword = db.Column(db.String(30))
    posts = db.relationship('Post', backref='user_ref', lazy=True)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user = db.relationship('User', backref='Purchases')
    post = db.relationship('Post', backref='Purchases')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    content = db.Column(db.Text, nullable=False)
    user = db.relationship('User', backref='Comments')
    post = db.relationship('Post', backref='Comments')

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    score = db.Column(db.Integer, nullable=False)
    user = db.relationship('User', backref='Ratings')
    post = db.relationship('Post', backref='Ratings')


def __repr__(self):
    return f"Post('{self.postname}', '{self.description}', '{self.price}', '{self.phonenumber}', '{self.image}')"

@app.route("/")
def home(): 
    return render_template("add_post.html")

@app.route("/register")
def show_register():
    return render_template("register.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == 'POST':
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirmpassword = request.form["confirmpassword"]
        user = User(username=username, email=email, confirmpassword=confirmpassword, password=password, Money=100000)
        if user.password == user.confirmpassword:
            db.session.add(user)
            db.session.commit()
        else:
            return render_template("register.html")
    return redirect(url_for("login"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    email = request.form["email"]
    password = request.form["password"]
    user = User.query.filter_by(email=email, password=password).first()
    if user and user.password == password:
        session['user'] = {'id': user.id} 
        session.modified = True
        return redirect(url_for("show_posts"))
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    del session["user"]
    session.modified = True
    return redirect(url_for("home"))

@app.route("/posts", methods=["POST"])
def add_posts():
    if 'user' not in session:
        flash('You must be logged in to add a post.', 'error')
        return redirect(url_for('login'))

    postname = request.form["postname"]
    description = request.form["description"]
    price = request.form["price"]
    image = request.files["image"]

    if image.filename == "":
        flash('No selected file for image.', 'error')
        return redirect(request.url)

    filename = "".join(image.filename.split())
    image.save(os.path.join("static", filename))
    full_path = os.path.join("static", filename)

    user_id = session['user']['id']  # Assuming session['user'] contains the current user's data
    post = Post(postname=postname, price=price, description=description, image=full_path, user_id=user_id)

    db.session.add(post)
    db.session.commit()

    flash('Post added successfully!', 'success')
    return redirect(url_for("show_posts"))


@app.route("/posts")
def show_posts(): 
    id = session.get('user')
    user = User.query.get(id)
    posts = Post.query.all()
    return render_template("add_post.html", posts=posts, user = user)

@app.route("/favourites")
@protected
def favourites():
    if 'posts' not in session:
        return 'No posts found'
    ids = session.get("posts")
    posts = Post.query.filter(Post.id.in_(ids)).all()
    return render_template("favourite.html", queryset=posts)

@app.route("/add_to_favourite/<int:id>")
def add_to_favourite(id):
    if "posts" not in session:
        session["posts"] = []
    if not check_in_session(id):
        session["posts"].append(id)
        session.modified = True
    return redirect(url_for("show_posts"))

@app.route("/remove_from_favourite/<int:id>")
def remove_from_favourite(id):
    if check_in_session(id):
        session["posts"].remove(id)
        session.modified = True
    return redirect(url_for("show_posts"))


@app.route('/delete_post/<int:id>', methods=['POST'])
def delete_post(id):
    if 'user' in session:
        post = Post.query.get(id)
        if post:
            current_user_id = session['user']['id']  # Assuming session['user'] contains the current logged-in user's data
            if post.user_id == current_user_id:
                db.session.delete(post)
                db.session.commit()

                if 'posts' in session and id in session['posts']:
                    session['posts'].remove(id)
                    session.modified = True
            else:
                flash('You are not authorized to delete this post.')
    return redirect(url_for('home'))

    

@app.route("/buy_product/<int:id>", methods=["GET", "POST"])
def buy_product(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    user = User.query.get(user_id)
    post = Post.query.get(id)
    
    if user.Money >= post.price:
        user.Money -= post.price
        purchase = Purchase(user_id=user.id, post_id=post.id)
        db.session.add(purchase)
        db.session.commit()
        flash('Purchase successful!', 'success')
    else:
        flash('Not enough money!', 'danger')
    
    return redirect(url_for('show_posts'))

@app.route("/search_Product", methods=["GET"])
def search_Product():
    query = request.args.get("query")
    if query:
        posts = Post.query.filter(
            or_(
                Post.description.ilike(f"%{query}%"),
                Post.price.ilike(f"%{query}%"),
                Post.postname.ilike(f"%{query}%")
            )
        ).all()
        if posts:
            return render_template("search_results.html", posts=posts, query=query)
        else:
            flash("No products found matching your search.")
            return redirect(url_for("home"))
    else:
        flash("Please provide a search query.")
        return redirect(url_for("home"))


@app.route("/profile")
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    user = User.query.get(user_id)
    purchases = Purchase.query.filter_by(user_id=user_id).all()
    purchased_posts = [purchase.post for purchase in purchases]

    return render_template("profile.html", user=user, purchased_posts=purchased_posts)

@app.route('/review/<int:id>')
def review(id):
    post = Post.query.get(id)
    if not post:
        return redirect(url_for('home'))
    return render_template('review.html', post=post)

@app.route('/comment/<int:id>', methods=['POST'])
def comment_product(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    content = request.form['comment']
    comment = Comment(user_id=user_id, post_id=id, content=content)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('review', id=id))

@app.route('/rate/<int:id>', methods=['POST'])
def rate_product(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    score = int(request.form['rating'])
    rating = Rating(user_id=user_id, post_id=id, score=score)
    db.session.add(rating)
    db.session.commit()
    return redirect(url_for('review', id=id))

if "__main__" == __name__:
    with app.app_context():
        db.create_all()
    app.run(debug=True)
