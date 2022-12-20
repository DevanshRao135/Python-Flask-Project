from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
from werkzeug.utils import secure_filename
import json
import os, math
from werkzeug.middleware.proxy_fix import ProxyFix


with open('config.json','r') as c:
    parameters = json.load(c)["parameters"]
local_server = parameters["local_server"]

app = Flask(__name__)
app.secret_key = 'super-secret-key' # for creating sessions
app.config['UPLOAD_FOLDER'] = parameters['upload_location']
app.config.update(MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = parameters['gmail-user'],
    MAIL_PASSWORD = parameters['gmail-password']
                  )
app.wsgi_app = ProxyFix(app.wsgi_app)
mail = Mail(app)

if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = parameters['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = parameters['production_uri']

db = SQLAlchemy(app)

class Contact(db.Model):
    Sno = db.Column(db.Integer, primary_key = True)
    Name = db.Column(db.String(80), nullable = False)
    Email = db.Column(db.String(30), nullable = False)
    PhoneNum = db.Column(db.String(12), nullable = False)
    Message = db.Column(db.String(120), nullable = False)
    Date = db.Column(db.String(12), nullable = True)

class Posts(db.Model):
    Sno = db.Column(db.Integer, primary_key = True)
    Title = db.Column(db.String(80), nullable = False)
    Tagline = db.Column(db.String(50), nullable = False)
    Slug = db.Column(db.String(30), nullable = False)
    Content = db.Column(db.String(300), nullable = False)
    Img_file = db.Column(db.String(25), nullable = False)
    Date = db.Column(db.String(12), nullable = True)

@app.route("/logout")
def logout():
    session.pop('username')
    return redirect('/login.html')

@app.route("/login.html", methods =['GET', 'POST'])
def login():
    posts = Posts.query.all()

    if ('username' in session and session['username']== parameters['username']):
        return render_template('dashboard.html', parameters = parameters, posts =posts)

    if request.method =='POST':
        # return root() # Redirect to admin Page
        username = request.form.get('username')
        userpass = request.form.get('password')
        if (username==parameters['username'] and userpass == parameters['password']):
            session['username'] = username
            return render_template('dashboard.html', parameters = parameters)
        else:
            print("wrong password")
            return render_template("login.html")
    else:
        return render_template("login.html")

@app.route("/")
def root():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts) / int(parameters['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(parameters['no_of_posts']):(page - 1) * int(parameters['no_of_posts']) + int(
    parameters['no_of_posts'])]
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', parameters=parameters, posts=posts, prev=prev, next=next)
#
# @app.route("/index.html")
# def index():
#     page = request.args.get('page', 1, type=int)
#     posts = Posts.query.paginate(page=page, per_page=parameters['no_of_posts'])
#     return render_template("index.html", parameters = parameters, posts = posts)

@app.route("/about.html")
def about():
    return render_template("about.html", parameters = parameters)

@app.route("/post.html/<string:post_slug>", methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(Slug=post_slug).first() #fetching post
    return render_template("post.html", parameters = parameters, post = post) #post = post access post in html

@app.route("/edit/<string:Sno>", methods=['GET', 'POST'])
def edit(Sno):
    if "username" in session and session['username'] == parameters['username']:
        if request.method == "POST":
            box_title = request.form.get('Title')
            Tagline = request.form.get('Tagline')
            Slug = request.form.get('Slug')
            Content = request.form.get('Content')
            Img_file = request.form.get('Img_file')
            Date = datetime.now()

            if Sno == '0':
                posts = Posts(Title=box_title, Slug=Slug, Content=Content, Tagline=Tagline, Img_file=Img_file, Date=Date)
                db.session.add(posts)
                db.session.commit()
            else:
                posts = Posts.query.filter_by(Sno=Sno).first()
                posts.Title = box_title
                posts.Tagline = Tagline
                posts.Slug = Slug
                posts.Content = Content
                posts.Img_file = Img_file
                posts.Date = Date
                db.session.commit()
                return redirect('/edit/' + Sno)

    posts = Posts.query.filter_by(Sno=Sno).first()
    return render_template('edit.html', parameters=parameters, posts=posts, Sno=Sno)


@app.route("/delete/<string:Sno>", methods=['GET', 'POST'])
def delete(Sno):
    if "username" in session and session['username'] == parameters['username']:
        post = Posts.query.filter_by(Sno=Sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/login.html')

@app.route("/uploader", methods = ['GET', "POST"])
def uploader():
    if "username" in session and session['username'] == parameters['username']:
        if(request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "UPLOADED SUCCESSFULLY."

@app.route("/contact.html", methods = ['GET', "POST"])
def contact():
    if (request.method == "POST"):
        name = request.form.get('name')         
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(Name = name, PhoneNum = phone, Date=datetime.now(), Email= email, Message = message )
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[parameters['gmail-user']],
                          body=message + "\n" + phone
                          )
    return render_template("contact.html", parameters = parameters)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port= 5000)