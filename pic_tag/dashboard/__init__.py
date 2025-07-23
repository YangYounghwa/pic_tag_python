from flask import Flask
app = Flask(__name__)
app.config['DaATABASE'] = '../data/my_database.db'