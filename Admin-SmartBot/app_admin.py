from flask import Flask, render_template, url_for, request, session, redirect, flash
from flask_pymongo import PyMongo
from flask import send_from_directory
from json.decoder import JSONDecoder
import bcrypt
import os
import json
import pymongo
import bson
import base64
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from pymongo import cursor
from bson import json_util
from flask import jsonify
import pprint

ALLOWED_EXTENSIONS = {'json'}

app=Flask(__name__)

app.config['MONGO_DBNAME'] = 'smartbot_chatbot'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/smartbot_chatbot'

mongo = PyMongo(app)
client = pymongo.MongoClient('localhost',27017)
db = client['smartbot_chatbot']
collection = db['botreview']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    if 'username' in session:
        return redirect(url_for('upload'))

    return render_template("Login.html")

@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.adminuser
    login_user = users.find_one({'name' : request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            # return redirect(url_for('index'))
        else:
            flash('Invalid Username/Password Combination')
    else:
        flash('Invalid Username/Password Comibination')
    
    return redirect(url_for('index'))

@app.route('/logout', methods=['POST'])
def logout():
    if 'username' in session:
        session.pop('username', None)
    return redirect(url_for('index'))

@app.route("/upload")
def upload():
    return render_template("Upload.html",username=session['username'])

@app.route('/create', methods=['POST'])
def create():
    if request.method == 'POST':
        if 'choosefile' not in request.files:
            flash('No file part')
            return redirect(url_for('upload'))
            
        file=(request.files['choosefile'])
        if file.filename=='':
            flash('No selected files')
            return redirect(url_for('upload'))

        if allowed_file(file.filename)==False:
            flash('Upload Error. Sorry, this extention is not allowed.')
            return redirect(url_for('upload'))

        if file and allowed_file(file.filename):
            filename=secure_filename(file.filename)
            base64_message=file.read()
            message = base64_message.decode('ascii')
            msg=eval(message)
            mongo.db.botreview.insert(msg)
            flash('File Uploaded')

    return redirect(url_for('upload'))

@app.route('/uploaded-data', methods=['GET'])
def uploaded_data():
    if request.method == 'GET':
        cursor = mongo.db.botreview.find()

        response = []
        for document in cursor:
            document['_id'] = str(document['_id'])
            response.append(document)
        msg=json.dumps(response, indent=4, separators=(',',':'), default=json_util.default)
        open("review_intents.json","w").write(msg)
        res = str(msg)[1:-1]
        return render_template('Show-Data.html', uploaded=res)

@app.route('/show_data')
def show_data():
    return render_template('Show-Data.html',username=session['username'])

@app.route('/delete')
def delete():
    return render_template('Delete.html',username=session['username'])

@app.route('/object', methods=['POST'])
def object():
    if request.method == 'POST':
        if request.form['objectid']=='':
            flash('Please Enter ObjectId')
            return redirect(url_for('delete'))
        else:
            object_id=request.form['objectid']
            mongo.db.botreview.remove({"_id": ObjectId(object_id)});
            # mongo.db.adminusers.delete({'_id':ObjectId(object_id)});
            flash('Data Deleted')

    return redirect(url_for('delete'))

@app.route('/profile')
def profile():
    users = mongo.db.adminuser
    username=session['username']
    login_user = users.find_one({'name' : username})
    name=login_user['name']
    password=login_user['password']
    mobile=login_user['mobile']
    city=login_user['city']

    return render_template('Profile.html',username=session['username'],name=login_user['name'],password=login_user['password'],mobile=login_user['mobile'],city=login_user['city'])

@app.route('/profile_update', methods=['POST'])
def profile_update():    
        name=request.form['name']
        password=request.form['pswd']
        mobile=request.form['mobile']
        city=request.form['city']
        username=session['username']

        hashpass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users=mongo.db.adminuser
        users.update({'name' : username},{'name' : name,'password' :hashpass,'mobile': mobile,'city': city});
        flash('Data Updated Successfully')
        return redirect(url_for('profile'))

@app.route('/records')
def records():
    data_result=mongo.db.req_res.find({},{"user_msg":1,"bot_response":1,'_id':0})
    data_user=mongo.db.req_res.find({},{"user_msg":1,'_id':0})
    data_bot=mongo.db.req_res.find({},{"bot_response":1,'_id':0})

    result_user=[]
    result_bot=[]
    final_result=[]
    for i in data_user:
        user_data=i['user_msg']
        # content_user=user_data.replace('\n','<br>')
        result_user.append("User:"+user_data)

    for j in data_bot:
        bot_data=j['bot_response']
        # content_bot=bot_data.replace('\n','<br>')
        result_bot.append("SmartBot:"+bot_data)

    for i,j in zip(result_user, result_bot):
        final_result.append(i)
        final_result.append(j)

    # paras="Hello \n SmartBot"
    # paras_result=paras.replace('\n','<br>')

    return render_template('Records.html',message=final_result, len=len(final_result))
    
if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True, port=5001)