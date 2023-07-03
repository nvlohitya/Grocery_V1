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

@app.route('/')
def root():
    loggedin, name = getLogindetails()
    admin_loggedin = 'admin' in session
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM categories')
        category_data = cur.fetchall()
    
    return render_template('index.html', loggedIn=loggedin, admin_loggedin=admin_loggedin, first_name=name, categoryData=category_data)

  
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
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM products WHERE name=?", (product_name,))
            product_info = c.fetchone()
            stock = product_info[5]
        
        return render_template('product_description.html', loggedIn=loggedIn, first_name=first_name, product_info=product_info, stock=stock)
    elif request.method == "POST":
        loggedIn, first_name = getLogindetails()
        if not loggedIn:
            return redirect(url_for('loginform'))
        else:
            product_name = request.args.get('product')
            quantity = int(request.form['quantity'])
            with sqlite3.connect('database.db') as conn:
                c = conn.cursor()
                c.execute("SELECT productId, stock FROM products WHERE name=?", (product_name,))
                product = c.fetchone()
                if product:
                    product_id, stock = product
                    if quantity <= stock:
                        # Insert into kart table
                        c.execute("SELECT userId FROM users WHERE email=?", (session['email'],))
                        user_id = c.fetchone()[0]
                        c.execute("INSERT INTO kart (userId, productId, quantity) VALUES (?, ?, ?)",
                                  (user_id, product_id, quantity))
                        conn.commit()

                        # Update the stock in the products table
                        new_stock = stock - quantity
                        c.execute("UPDATE products SET stock=? WHERE productId=?", (new_stock, product_id))
                        conn.commit()
                    else:
                        flash("Quantity exceeds available stock")
                else:
                    flash("Product not found")

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
    
        total = sum(item[1] * item[2] for item in cart_items)

    return render_template('cart.html', loggedIn=loggedin, first_name=name, cart_items=cart_items,total=total)

@app.route('/remove-from-cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    loggedin, name = getLogindetails()
    if not loggedin:
        return redirect(url_for('form'))

    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        # Retrieve the quantity being removed
        c.execute("""
            SELECT quantity
            FROM kart
            WHERE userId = (
                SELECT userId
                FROM users
                WHERE email = ?
            ) AND productId = ?
        """, (session['email'], product_id))
        removed_quantity = c.fetchone()[0]

        # Remove the product from the kart for the logged-in user
        c.execute("""
            DELETE FROM kart
            WHERE userId = (
                SELECT userId
                FROM users
                WHERE email = ?
            ) AND productId = ?
        """, (session['email'], product_id))

        # Update the stock in the products table by adding the removed quantity
        c.execute("""
            UPDATE products
            SET stock = stock + ?
            WHERE productId = ?
        """, (removed_quantity, product_id))

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

@app.route('/admin_login',methods = ['GET','POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if valid(email, password):
            session['admin'] = email
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials")
            return render_template('admin_login.html')
    else:
        return render_template('admin_login.html')

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'GET':
        return render_template('admin_register.html')
    elif request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        
        # Perform validation and registration logic for admin
        
        # Example: Insert admin data into the database
        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            query = "INSERT INTO admins (password , email , firstname, lastName) VALUES (?, ?, ?, ?)"
            try:
                cur.execute(query, (password , email, firstname, lastname))
                con.commit()
                return redirect('/admin_login')
            except:
                con.rollback()
                flash('Error occurred during admin registration.')
                return redirect(url_for('admin_register'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    conn.close()

    return render_template('admin_dashboard.html', categories=categories)

@app.route('/admin_view_products/<int:category_id>')
def admin_view_products(category_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get the category name
    cursor.execute("SELECT name FROM categories WHERE categoryId=?", (category_id,))
    category_name = cursor.fetchone()[0]
    
    # Get the products for the category
    cursor.execute("SELECT * FROM products WHERE categoryId=?", (category_id,))
    products = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_view_products.html', category_id=category_id, category_name=category_name, products=products)



@app.route('/add_product/<int:category_id>', methods=['GET', 'POST'])
def add_product(category_id):
    if request.method == 'POST':
        # Retrieve form data
        product_name = request.form.get('product_name')
        product_price = request.form.get('product_price')
        product_description = request.form.get('product_description')
        stock = request.form.get('stock')
        
        # Perform validation and add the product to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, price, description,stock,categoryId) VALUES (?, ?, ?, ?,?)",
                       (product_name, product_price, product_description,stock,category_id))
        conn.commit()
        conn.close()
        
        # Redirect to the admin_view_products page for the respective category
        return redirect(url_for('admin_view_products', category_id=category_id))
    
    # If it's a GET request, render the add_product.html template
    return render_template('add_product.html', category_id=category_id)

@app.route('/modify_product/<int:product_id>', methods=['GET', 'POST'])
def modify_product(product_id):
    if request.method == 'POST':
        new_name = request.form.get('new_name')

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Get the category ID for the product
        cursor.execute("SELECT categoryId FROM products WHERE productId = ?", (product_id,))
        result = cursor.fetchone()
        category_id = result[0] if result else None

        if category_id:
            # Update the product name in the database based on the product_id
            cursor.execute("UPDATE products SET name = ? WHERE productId = ?", (new_name, product_id))
            conn.commit()

            flash("Product name updated successfully")

        conn.close()

        return redirect(url_for('admin_view_products', category_id=category_id))

    return render_template('modify_product.html', product_id=product_id)


@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    # Check if the user is logged in as admin
    if 'admin' not in session:
        flash('Please log in as admin to delete products')
        return redirect(url_for('admin_login'))
    
    # Delete the product from the database
    # conn = sqlite3.connect('database.db')
    # cursor = conn.cursor()
    # cursor.execute('DELETE FROM products WHERE productId = ?', (product_id,))
    # conn.commit()

    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM products WHERE productId = ?", (product_id,))
        product = c.fetchone()

        if product:
            # Delete the product from the category
            c.execute("DELETE FROM products WHERE productId = ?", (product_id,))
            conn.commit()

            # Delete the product from the cart database if it is present
            c.execute("DELETE FROM kart WHERE productId = ?", (product_id,))
            conn.commit()
    
    flash('Product deleted successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        name = request.form['name']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()

        conn.close()

        flash("Category added successfully!")
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_category.html')

@app.route('/modify_category/<int:category_id>', methods=['GET','POST'])
def modify_category(category_id):
    if request.method == 'POST':
        new_name = request.form.get('new_name')

        # Update the category name in the database based on the category_id
        conn = sqlite3.connect('database.db')
        conn.execute("UPDATE categories SET name = ? WHERE categoryId = ?", (new_name, category_id))
        conn.commit()
        conn.close()

        flash("Category name updated successfully")
        return redirect(url_for('admin_dashboard'))
    
    return render_template('category_modify.html',category_id=category_id)



@app.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Check if the category exists
    cursor.execute("SELECT * FROM categories WHERE categoryId=?", (category_id,))
    category = cursor.fetchone()
    
    if category is None:
        flash("Category not found")
    else:
        # Delete the category and its associated products
        cursor.execute("DELETE FROM categories WHERE categoryId=?", (category_id,))
        cursor.execute("DELETE FROM products WHERE categoryId=?", (category_id,))
        conn.commit()
        flash("Category deleted successfully")
    
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/search')
def search():
    query = request.args.get('query')
    products = []

    if query:
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM products WHERE name LIKE ? OR price = ?", ('%' + query + '%', query))
            products = c.fetchall()

    return render_template('search_results.html', products=products, query=query)


@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


if __name__ == "__main__":
    app.run(debug=True,port=4000)