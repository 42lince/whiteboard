from flask import Flask, g, render_template, request, redirect
import sqlite3
from datetime import datetime
from price import Price
import json
# -- leave these lines intact --
app = Flask(__name__)


def get_db():
    if not hasattr(g, 'sqlite_db'):
        db_name = app.config.get('DATABASE', 'data.db')
        g.sqlite_db = sqlite3.connect(db_name)

    return g.sqlite_db


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'sqlite_db', None)
    if db is not None:
        db.close()
# ------------------------------


@app.route('/')
def root():
    conn = get_db()
    c = conn.cursor()
    s = "SELECT * from prices order by tenor"
    c.execute(s)
    allrows = c.fetchall()
    d = dict()
    for row in allrows:
        tenor = row[1]
        broker = row[0]
        p = row[2]
        direction = row[3]
        qty = row[4]
        firm_price = row[5]
        client = row[6]

        price = Price(tenor, broker, direction, p, firm_price, qty, client)

        if tenor in d.keys():
            d[tenor][direction].append(price)
        else:
            d[tenor] = {'sell':[], 'buy':[]}
            d[tenor][direction].append(price)
    

    tablerows = []
    for key in d.keys():
        d[key]['buy'].sort(key=lambda x: x.p, reverse=True)
        d[key]['sell'].sort(key=lambda x : x.p, reverse=True)
        i = 0
        j = 0
        while i < len(d[key]['buy']) or j < len(d[key]['sell']):
            if i == len(d[key]['buy']):
                sell_p = d[key]['sell'][j]
                tablerows.append([sell_p.tenor, '', '', '', '', sell_p.p, sell_p.qty, sell_p.client, sell_p.broker])
                j = j + 1
            elif j == len(d[key]['sell']):
                buy_p = d[key]['buy'][i]
                tablerows.append([buy_p.tenor, buy_p.broker, buy_p.client, buy_p.qty, buy_p.p, '','','',''])
                i = i + 1
            else:
                sell_p = d[key]['sell'][j]
                buy_p = d[key]['buy'][i]
                tablerows.append([buy_p.tenor, buy_p.broker, buy_p.client, buy_p.qty, buy_p.p, sell_p.p, sell_p.qty, sell_p.client, sell_p.broker])
                i = i + 1
                j = j + 1

    return render_template('index.html', pricetable=tablerows)

@app.route('/update',methods=['POST'])
def update():
    tabledata = request.form['tabledata']
    #print(tabledata)
    conn = get_db()
    c = conn.cursor()
    time = str(datetime.now())
    s = 'DELETE from prices'
    c.execute(s)
    conn.commit()
    print('records removed')
    table_json = json.loads(tabledata)
    for item in table_json:
        tenor = item['tenor']
        broker = item['broker']
        if 'bid' in item:
            p = float(item['bid'])
            direction = 'buy'
        else:
            p = float(item['ask'])
            direction = 'sell'
        qty = int(item['qty'])
        firm_price = 'True'
        client = item['client']
        s = 'INSERT INTO prices VALUES ("{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}")'.format(broker, tenor, p, direction, qty, firm_price, client, str(datetime.now()))
        c.execute(s)
    
    conn.commit()
    conn.close()
    return redirect('/')
    #return "hello world"

if __name__ == '__main__':
    app.run(debug=True)
