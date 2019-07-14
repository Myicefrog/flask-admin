import os
import os.path as op

from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from wtforms import fields, widgets

from sqlalchemy.event import listens_for
from jinja2 import Markup

from flask_admin import Admin, form
from flask_admin.form import rules
from flask_admin.contrib import sqla, rediscli

app = Flask(__name__, static_folder='files')
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

# Create in-memory database
app.config['DATABASE_FILE'] = 'sample_db.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE_FILE']
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

# Create directory for file fields to use
file_path = op.join(op.dirname(__file__), 'files')
try:
    os.mkdir(file_path)
except OSError:
    pass

def build_sample_db():

    db.drop_all()
    db.create_all()

    images = ["Buffalo", "Elephant", "Leopard", "Lion", "Rhino"]
    for name in images:
        image = Student()
        image.name = name
        image.photopath = name.lower() + ".jpg"
        db.session.add(image)
    db.session.commit()
    return

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    photopath = db.Column(db.Unicode(128))

    def __unicode__(self):
        return self.name

@listens_for(Student, 'after_delete')
def del_image(mapper, connection, target):
    if target.photopath:
        # Delete image
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass

        # Delete thumbnail
        try:
            os.remove(op.join(file_path,
                              form.thumbgen_filename(target.path)))
        except OSError:
            pass


class ImageView(sqla.ModelView):
    def _list_thumbnail(view, context, model, name):
        if not model.photopath:
            return ''

        return Markup('<img src="%s">' % url_for('static',
                                                 filename=form.thumbgen_filename(model.photopath)))

    column_formatters = {
        'photopath': _list_thumbnail
    }

    # Alternative way to contribute field is to override it completely.
    # In this case, Flask-Admin won't attempt to merge various parameters for the field.
    form_extra_fields = {
        'photopath': form.ImageUploadField('Image',
                                      base_path=file_path,
                                      thumbnail_size=(100, 100, True))
    }


admin = Admin(app, name='学生管理系统', template_mode='bootstrap3')
# Add administrative views here
admin.add_view(ImageView(Student, db.session,name=u'学生管理'))


if __name__ == '__main__':
    app_dir = op.realpath(os.path.dirname(__file__))
    database_path = op.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        build_sample_db()
    app.run(host='0.0.0.0', port=5010, debug=True)
