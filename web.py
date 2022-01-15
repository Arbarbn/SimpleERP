from flask import Flask, render_template, request, redirect, url_for, session, json
from flask_mysqldb import MySQL
import MySQLdb.cursors
import pandas as pd
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = '13jHkdyThs89l'

# Enter your database connection details below
conn = MySQLdb.connect("localhost","root","18agustus98","erp")

# Intialize MySQL
mysql = MySQL(app)
@app.route('/cuslogin/', methods=['GET', 'POST'])
def cuslogin():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form:
        # Create variables for easy access
        name = request.form['name']
        password_ent = request.form['password']

        # Check if account exists using MySQL
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `customer_manager` WHERE name= %s ', [name])
        account = cursor.fetchone()
        # Fetch one record and return result
        if account:
            password = account['password']
            # If account exists in accounts table in out database
            if bcrypt.check_password_hash(password.encode('utf-8'), password_ent.encode('utf-8')):
                # Create session data, we can access this data in other routes
                app.logger.info('Password Matched')
                session['loggedin'] = True
                session['id'] = account['customerID']
                session['name'] = account['name']

                # Redirect to home page
                return redirect(url_for('cushome'))
            else:
                # Account doesnt exist or username/password incorrect
                msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)

@app.route('/cusregister/', methods=['GET', 'POST'])
def cusregister():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form :
        # Create variables for easy access
        name = request.form['name']
        password = request.form['password']

        hashed = bcrypt.generate_password_hash(password)
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM customer_manager WHERE name = %s', (name,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO customer_manager (name,password) VALUES (%s, %s)', (name, hashed,))
            conn.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

@app.route('/cushome/')
def cushome():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('cushome.html', name=session['name'])
    # User is not loggedin redirect to login page
    return redirect(url_for('cuslogin'))

@app.route('/custore/')
def custore():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM store_manager")
        data = cursor.fetchall()  # data from database
        return render_template('custore.html', value=data)
    # User is not loggedin redirect to login page
    return redirect(url_for('cuslogin'))

@app.route('/updatecustore', methods=["POST"])
def updatecustore():
    id = request.form['id']
    title = request.form['title']
    price = request.form['price']
    newstock = request.form['newstock']

    cursor = conn.cursor()
    cursor.execute('UPDATE `store_manager` SET sales=sales+%s, in_stock=in_stock-%s WHERE storeID=%s',(newstock, newstock, id))
    cursor.execute('INSERT INTO `sales_manager` (buyer, title, purchase, price) VALUES (%s, %s, %s, %s)', (session['name'], title, newstock, price ))
    cursor.execute('UPDATE `sales_manager` SET Total=purchase*price')
    conn.commit()
    return redirect(url_for('custore'))

@app.route('/profile/')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM customer_manager WHERE customerID = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('cuslogin'))

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password_ent = request.form['password']

        # Check if account exists using MySQL
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `login` WHERE username= %s ', [username])
        account = cursor.fetchone()
        # Fetch one record and return result
        if account:
            password = account['password']
            # If account exists in accounts table in out database
            if bcrypt.check_password_hash(password.encode('utf-8'),password_ent.encode('utf-8')):
                # Create session data, we can access this data in other routes
                app.logger.info('Password Matched')
                session['loggedin'] = True
                session['username'] = account['username']

                # Redirect to home page
                return redirect(url_for('home'))
            else:
                # Account doesnt exist or username/password incorrect
                msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)

@app.route('/home/')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        cursor = conn.cursor()
        cursor.execute("SELECT title, sales FROM store_manager ORDER BY sales DESC LIMIT 4")
        data = cursor.fetchall()

        cursor.execute("SELECT SUM(Total) FROM sales_manager")
        pendapatan = cursor.fetchall()

        cursor.execute("SELECT Count(id_karyawan) FROM karyawan")
        karyawan = cursor.fetchall()

        cursor.execute("SELECT COUNT(customerID) FROM customer_manager")
        customer = cursor.fetchall()
        return render_template("in_home.html", value=data, values=pendapatan, value1=karyawan, value2=customer)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/logout/')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('username', None)
   session.pop('password', None)
   # Redirect to login page
   return redirect(url_for('login'))

@app.route('/sales/')
def sales():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sales_manager")
        data = cursor.fetchall()  # data from database
        return render_template('sales.html', value=data)
    # User is not loggedin redirect to login page
    else :
        return redirect(url_for('login'))

@app.route('/data/')
def data():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM karyawan")
        data = cursor.fetchall()  # data from database
        return render_template('data.html', value=data)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/simpandata',methods=["POST"])
def simpandata():
    if 'loggedin' in session:
        nama = request.form['nama']
        posisi = request.form['posisi']
        umur = request.form['umur']
        gaji = request.form['gaji']

        cursor = conn.cursor()
        cursor.execute('INSERT INTO `karyawan` (nama, posisi, umur, gaji) VALUES (%s, %s, %s, %s)',(nama, posisi, umur, gaji))
        conn.commit()
        return redirect(url_for('data'))
    else:
        return redirect(url_for('login'))

@app.route('/updatedata', methods=["POST"])
def updatedata():
    id = request.form['id']
    nama = request.form['nama']
    posisi = request.form['posisi']
    umur = request.form['umur']
    gaji = request.form['gaji']

    cur = conn.cursor()
    cur.execute("UPDATE karyawan SET nama=%s, posisi=%s, umur=%s, gaji=%s WHERE id_karyawan=%s", (nama,posisi,umur,gaji,id))
    conn.commit()
    return redirect(url_for('data'))

@app.route('/hapusdata/<string:id_data>', methods=["GET"])
def hapusdata(id_data):
    cur = conn.cursor()
    cur.execute("DELETE FROM karyawan WHERE id_karyawan=%s", (id_data,))
    conn.commit()
    return redirect(url_for('data'))

@app.route('/store/')
def store():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM store_manager")
        data = cursor.fetchall()  # data from database
        return render_template('store.html', value=data)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/simpanstore',methods=["POST"])
def simpanstore():
    if 'loggedin' in session:
        title = request.form['title']
        manufacture = request.form['manufacture']
        price = request.form['price']
        stock = request.form['stock']

        cursor = conn.cursor()
        cursor.execute('INSERT INTO `store_manager` (title, manufacture, price, in_stock) VALUES (%s, %s, %s, %s)',(title, manufacture, price, stock))
        conn.commit()
        return redirect(url_for('store'))
    else:
        return redirect(url_for('login'))

@app.route('/updatestore', methods=["POST"])
def updatestore():
    msg=''
    id = request.form['id']
    title = request.form['title']
    price = request.form['price']
    newstock = request.form['newstock']
    buyer = 'Budi'

    cursor = conn.cursor()
    cursor.execute('UPDATE `store_manager` SET sales=sales+%s, in_stock=in_stock-%s WHERE storeID=%s',(newstock, newstock, id))
    cursor.execute('INSERT INTO `sales_manager` (buyer, title, purchase, price) VALUES (%s, %s, %s, %s)', (buyer, title, newstock, price ))
    cursor.execute('UPDATE `sales_manager` SET Total=purchase*price')
    conn.commit()
    return redirect(url_for('store'))

@app.route('/crm/')
def crm():
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customer_manager")
        data = cursor.fetchall()  # data from database
        return render_template('crm.html', value=data )
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/hapuscrm/<string:id_data>', methods=["GET"])
def hapuscrm(id_data):
    cur = conn.cursor()
    cur.execute("DELETE FROM customer_manager WHERE customerID=%s", (id_data,))
    conn.commit()
    return redirect(url_for('crm'))

@app.route('/invoice/')
def invoice():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('in_home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/logistic/')
def logistic():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('in_home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
