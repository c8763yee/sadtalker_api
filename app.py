import os
from shutil import rmtree

from flask import send_from_directory

from flask_app import create_app
from model import Status, db

app = create_app()


def init() -> None:
    db.init_app(app)
    with app.app_context():
        if os.path.exists("data.sqlite3") is False:
            db.create_all()
        else:
            Status.delete_table()
    rmtree("upload", ignore_errors=True)
    rmtree("output", ignore_errors=True)


@app.route('/')
def index():
    return 'ok'


@app.route('/download/<task_id>')
def download(task_id):
    return send_from_directory('output', f'{task_id}.mp4', as_attachment=True)


init()
if __name__ == '__main__':
    app.run(debug=True)
