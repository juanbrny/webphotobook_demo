#!/usr/bin/env python
# Small gallery image webapp.
# It is insecure and has bugs on purpose (some may not be on purpose :) )
#
# Author/s:
#   Raul Mahiques <raul.mahiques@suse.com>
#


from flask import Flask, render_template, request, url_for, flash, redirect, send_from_directory, Blueprint
import sqlite3
from flask_restful import Resource, Api
from flask_basicauth import BasicAuth
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
import random
import yaml
import json
import os


app = Flask(__name__)

num = str(random.random())


config_settings= ['ADMIN_USER','IMAGES_LOCATION','APP_NAME','DB_FILE']

# read the config file
if 'CONFIG_FILE' in os.environ:
  config_file = os.environ['CONFIG_FILE']
else:
  config_file = 'myconf.yml'

app.config.from_file(config_file, load=yaml.safe_load)

with open(config_file, 'r') as file:
  cfg = yaml.safe_load(file)

api_bp = Blueprint('api', __name__)
api = Api(api_bp)
basic_auth = BasicAuth(app)

def allowed_file(filename):
  return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def connect_db():
    conn = sqlite3.connect(app.config['DB_FILE'])
    conn.row_factory = sqlite3.Row
    return conn

class Photo(Resource):
  def get_photo(photo_id):
    conn = connect_db()
    photo = conn.execute('SELECT * FROM ' + app.config['DB_TABLE_NAME'] + ' WHERE id = ?',(photo_id,)).fetchone()
    conn.close()
    if photo is None:
  	  abort(404)
    return photo

  def edit_entry(id, title, description, image=None):
    conn = connect_db()
    # Write the image file/s to a directory
    if image.filename != '' and allowed_file(image.filename):
      image_path = num + '_' + secure_filename(image.filename)
      image.save( app.config['IMAGES_LOCATION'] + image_path )      
      conn.execute('UPDATE ' + app.config['DB_TABLE_NAME'] + ' SET title = ?, description = ?, url = ?'
                ' WHERE id = ?',
                (title, description, image_path, id))
    else:
      conn.execute('UPDATE ' + app.config['DB_TABLE_NAME'] + ' SET title = ?, description = ?'
                ' WHERE id = ?',
                (title, description, id))      
    conn.commit()
    conn.close()
    return id, 201

  def del_entry(id):
    photo = Photo.get_photo(id)
    if photo['url'] is not None:
      os.remove(app.config['IMAGES_LOCATION'] + photo['url'])
    conn = connect_db()
    conn.execute('DELETE FROM ' + app.config['DB_TABLE_NAME'] + ' WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return '', 204
    
  def get(self, id):
    return get_photo(id)

class Photos(Resource):    
  # Returns a list of photos
  def get_photos():
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    photos = c.execute('SELECT * FROM ' + app.config['DB_TABLE_NAME']).fetchall()
    conn.close()
    return photos

  # Inserts an entry in the DB
  def insert_entry(title, description, image=None):
  	# Establish connection to DB
    conn = connect_db()
    # Save the image file/s to a directory
    if image !=None and image.filename != '' and allowed_file(image.filename):
      image_path = num + '_' + secure_filename(image.filename)
      image.save( app.config['IMAGES_LOCATION'] + image_path )      
      conn.execute('INSERT INTO ' + app.config['DB_TABLE_NAME'] + ' (title, description, url) VALUES (?, ?, ?)',
                        (title, description, image_path ))
    else:
      conn.execute('INSERT INTO ' + app.config['DB_TABLE_NAME'] + ' (title, description) VALUES (?, ?)',
                        (title, description ))
    conn.commit()
    conn.close()
    return '', 201

  def get(self):
    a=[]
    for u in Photos.get_photos():
      for i in u:
        a.append(i)
    return a

class Settings(Resource):
  def get(self):
    cfg = {}
    with open(config_file, 'r') as file:
      for i in yaml.safe_load(file).items():
        if i[0] in config_settings:
          cfg[i[0]] = i[1] 
    return cfg
  def post(self):
    with open(config_file, 'r') as file:
      cfg = yaml.safe_load(file)
    for i in request.form:
      if i in config_settings:
        cfg[i] = request.form[i]
        app.config[i] = request.form[i]
    with open(config_file, 'w') as file:
      yaml.dump(cfg,file)
    

#########################################################################################################
api.add_resource(Photo, '/api/photo/<photo_id>')
api.add_resource(Photos, '/api/photos')
api.add_resource(Settings, '/api/settings')
app.register_blueprint(api_bp)


@app.route('/')
def index():
  photos = Photos.get_photos()
  return render_template('index.html', photos=photos, app_name=app.config['APP_NAME'], images_location=app.config['IMAGES_LOCATION'])

@app.route('/settings', methods=('GET', 'POST'))
@basic_auth.required
def settings():
  with open(config_file, 'r') as file:
    cfg = yaml.safe_load(file)
  if request.method == 'POST':
    for i in config_settings:
      cfg[i] = request.form[i]    
      app.config[i] = request.form[i] 
    with open(config_file, 'w') as file:
      yaml.dump(cfg,file)
  return render_template('settings.html', cfg=cfg, config_settings=config_settings )

@app.route('/about')
def about():
  return render_template('about.html')

@app.route('/<int:photo_id>')
def photo(photo_id):
  photo = Photo.get_photo(photo_id)
  return render_template('photo.html', photo=photo, images_location=app.config['IMAGES_LOCATION'])

@app.route('/create', methods=('GET', 'POST'))
def create():
  if request.method == 'POST':
    title = request.form['title']
    description = request.form['description']
    image = request.files['image']
    if not title:
      flash('Title is required!')
    else:
      Photos.insert_entry(title, description, image)      
      return redirect(url_for('index'))
  return render_template('create.html')
 
@app.route('/<int:id>/edit', methods=('GET', 'POST')) 
def edit(id):
  photo = Photo.get_photo(id)
  if request.method == 'POST':
    title = request.form['title']
    description = request.form['description']
    image = request.files['image']   
    if not title:
      flash('Title is required!')
    else:
      conn = connect_db()
      Photo.edit_entry(id, title, description, image)
      return redirect(url_for('index'))

  return render_template('edit.html', photo=photo, images_location=app.config['IMAGES_LOCATION'] )  
  
@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    photo = Photo.get_photo(id)
    Photo.del_entry(id)
    flash('"{}" was successfully deleted!'.format(photo['title']))
    return redirect(url_for('index'))



@app.route( '/' + app.config['IMAGES_LOCATION'] + '<filename>')
def upload(filename):
    return send_from_directory(app.config['IMAGES_LOCATION'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

  