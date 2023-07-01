from flask import *
import sqlite3, hashlib, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'random string'
UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
  
def getLogindetails():
    with sqlite3.connect('database.db') as data:
        connection = data.cursor()
        if 'email' not in session:
            loggedIn = False
            first_name = ""
        else:
            try:
                details = connection.execute("Select * from users where email='"+session['email']+"'") 
                p = details.fetchone()
                first_name = p[3]
                loggedIn = True
            except:
                loggedIn = False
                first_name = ""
                session.pop('email')
    return (loggedIn, first_name)    
       
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def valid(email,password):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("select email, password from users where email='"+email+"'")
    user = cur.fetchall()
    try:
        for i in user:
            if email == i[0] and password == i[1]:
                return True
    except:
        return False
@app.route("/")
def root():
    loggedIn, first_name = getLogindetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()        
        cur.execute('SELECT * FROM categories')            
        categoryData = cur.fetchall()              
    return render_template('index.html', loggedIn = loggedIn, first_name = first_name, categoryData=categoryData)
  
@app.route('/about us')
def Info():
    return "That page will be avialabe soon"

@app.route('/login')
def loginform():
    if request.args.get('email'):
        email = request.args.get('email')
        password = request.args.get('password')
        if valid(email,password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            flash("Invalid credentials")
            return render_template('login.html' )
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('email')
    return redirect(url_for('root')) 

@app.route('/register',methods=['POST','GET'])   
def register():
    print(app.config['UPLOAD_FOLDER'])
    if request.method == 'GET':
        return render_template('register.html')  
    elif request.method == 'POST':
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']
        password = request.form['password'] 
        a = "Insert into users (password,email,firstname,lastName) values('{}','{}','{}','{}')".format(password,email,firstName,lastName)    

        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            print(a)
            try:                
                cur.execute(a)
                con.commit()
                return redirect('/login')
            except:
                con.rollback()
                flash("Something Went wrong")
                print(flash)
                return redirect(url_for('register'))
    
        
       

@app.route('/profile')
def profile():
    loggedIn, first_name = getLogindetails()
    if loggedIn == False:
        return redirect(url_for('loginform'))
    with sqlite3.connect('database.db') as con:
        cur = con.cursor()
        cur.execute("select * from users where email='{}'".format(session['email']))  
        user_info = cur.fetchone()
    return render_template('profile.html',loggedIn= loggedIn, first_name=first_name, user_info=user_info)

@app.route('/profile/update',methods=['POST','GET'])
def edit_profile():
    if request.method == "GET":
        loggedIn, first_name = getLogindetails()
        if loggedIn == False:
            return redirect(url_for('loginform'))
        else:
            with sqlite3.connect('database.db') as c:
                conn = c.cursor()
                conn.execute("select * from users where email='{}'".format(session['email']))
                user_info = conn.fetchone()        
            return render_template('update_profile.html',user_info=user_info, loggedIn=loggedIn, first_name=first_name)
    elif request.method == "POST":
        firstName = request.form['firstName']
        lastName = request.form['lastName']        
        update = "update users set firstname='{}',lastName='{}'where email='{}'".format(firstName,lastName,session['email'])
        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            print(update)
            try:
                cur.execute(update)
                con.commit()  
                flash("update succesfull")
                return redirect(url_for('edit_profile'))              
            except:
                flash("Something Went wrong")
                return redirect(url_for('edit_profile'))  
    else:
        return "something went wrong"
             
        

@app.route('/passwordchange')
def Password_change():
    return render_template("password_change.html")

@app.route("/product", methods=['GET','POST'])
def product():
    if request.method == "GET":
        loggedIn, first_name = getLogindetails()
        product_name = request.args.get('product') 
        with sqlite3.connect('database.db') as c:
            conn = c.cursor()
            conn.execute("select * from products where name='{}'".format(product_name))
            product_info = conn.fetchone()
        
        return render_template('product_description.html', loggedIn=loggedIn, first_name=first_name, product_info=product_info)
    elif request.method == "POST":
        loggedIn, first_name = getLogindetails()
        if not loggedIn:
            return redirect(url_for('loginform'))
        else:
            Product_name = request.args.get('product')
            quantity = request.form['quantity']
            with sqlite3.connect('database.db') as c:
                conn = c.cursor()
                conn.execute("select userId from users where email='{}'".format(session['email']))
                userId = conn.fetchone()
                conn.execute("select productId from products where name='{}'".format(Product_name))
                productId = conn.fetchone()
                conn.execute("insert into kart values('{}','{}','{}')".format(userId[0],productId[0],quantity))
                c.commit()
                conn.execute("select * from kart")
                a = conn.fetchall()
                print(a)
            return redirect(url_for('root'))
                     

@app.route('/cart')
def cart():
    loggedin, name = getLogindetails()
    if not loggedin:
        return redirect(url_for('loginform'))
    
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        # Fetch cart items for the logged-in user
        c.execute("""
            SELECT p.name, p.price, k.quantity , k.productId
            FROM kart k
            JOIN products p ON p.productId = k.productId
            JOIN users u ON u.userId = k.userId
            WHERE u.email = ?
        """, (session['email'],))
        cart_items = c.fetchall()

    return render_template('cart.html', loggedIn=loggedin, first_name=name, cart_items=cart_items)

@app.route('/remove-from-cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    loggedin, name = getLogindetails()
    if not loggedin:
        return redirect(url_for('form'))

    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        # Remove the product from the kart for the logged-in user
        c.execute("""
            DELETE FROM kart
            WHERE userId = (
                SELECT userId
                FROM users
                WHERE email = ?
            ) AND productId = ?
        """, (session['email'], product_id))

        conn.commit()

    return redirect(url_for('cart'))



@app.route('/shop_by_category')
def category():
    loggedIn, first_name = getLogindetails()
    category = request.args.get('category')
    print(category)
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("select products.*, categories.name from products, categories where products.categoryId=categories.categoryId and categories.name='{}'".format(category))
        products = cur.fetchall()
        print(products)
    return render_template('category.html', category = category,loggedIn=loggedIn, first_name=first_name, products=products)



if __name__ == "__main__":
    app.run(debug=True,port=4000)