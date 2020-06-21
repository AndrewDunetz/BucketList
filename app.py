from flask import Flask, render_template, json, request, redirect, session, jsonify
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import os
import traceback

app = Flask(__name__)
mysql = MySQL()
app.secret_key = 'why would I tell you my secret key?'
 
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Digpink01'
app.config['MYSQL_DATABASE_DB'] = 'BucketList'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()

# Default setting
pageLimit = 5

@app.route("/")
def main():
    return render_template('index.html')

@app.route('/showSignUp')
def showSignUp():
    return render_template('signup.html')

@app.route('/showSignin')
def showSignin():
    return render_template('signin.html')

@app.route('/showDashboard')
def showDashboard():
    return render_template('dashboard.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        extension = os.path.splitext(file.filename)[1]
        f_name = str(uuid.uuid4()) + extension
        app.config['UPLOAD_FOLDER'] = 'static/Uploads'
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], f_name))
        return json.dumps({'filename':f_name})

@app.route('/userHome')
def userHome():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('error.html',error = 'Unauthorized Access')

@app.route('/showAddWish')
def showAddWish():
    return render_template('addWish.html')

# DONE
@app.route('/signUp',methods=['POST','GET'])
def signUp():
 
    # read the posted values from the UI
    _name = request.form['inputName']
    _email = request.form['inputEmail']
    _password = request.form['inputPassword']
 
    # validate the received values
    if _name and _email and _password:
        _hashed_password = generate_password_hash(_password)
        sql = "select * from tbl_user where user_username = '" + _email + "'"
        cursor.execute(sql)
        #cursor.callproc('sp_createUser',(_name,_email,_hashed_password))
        data = cursor.fetchall()
 
        if len(data) == 0:
            sql = "insert into tbl_user(user_name, user_username, user_password) values('" + _name + "','" + _email + "','" + _hashed_password + "');"
            cursor.execute(sql)
            conn.commit()
            return json.dumps({'message':'User created successfully !'})
        else:
            return json.dumps({'error':str(data[0])})
    else:
        return json.dumps({'html':'<span>Enter the required fields</span>'})

# DONE
@app.route('/validateLogin',methods=['POST'])
def validateLogin():
    try:
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']

        # connect to mysql
        conn = mysql.connect()
        cursor = conn.cursor()
        sql = "select * from tbl_user where user_username = '" + _username + "'"
        cursor.execute(sql)
        #cursor.callproc('sp_validateLogin',(_username,))
        data = cursor.fetchall()

        if len(data) > 0:
            if check_password_hash(str(data[0][3]),_password):
                session['user'] = data[0][0]
                return redirect('/showDashboard')
            else:
                return render_template('error.html',error = 'Wrong Email address or Password.')
        else:
            return render_template('error.html',error = 'Wrong Email address or Password.')
 
    except Exception as e:
        return render_template('error.html',error = str(e))

@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/')

# DONE
@app.route('/getWish',methods=['POST'])
def getWish():
    try:
        if session.get('user'):
            _user = session.get('user')
            _limit = pageLimit
            _offset = request.form['offset']
            #_total_records = 0

            con = mysql.connect()
            cursor = con.cursor()
            sql = "select count(*) from tbl_wish where wish_user_id = '" + str(_user) + "'"
            cursor.execute(sql)
            #cursor.callproc('sp_GetWishByUser',(_user,_limit,_offset,_total_records))
            result = cursor.fetchall()
            _total_records = result[0][0]
            sql = "select * from tbl_wish where wish_user_id = " + str(_user) + " order by wish_date desc limit " + str(_limit) + " offset " + str(_offset) + ""
 
            cursor.execute(sql)
 
            wishes = cursor.fetchall()
 
            response = []
            wishes_dict = []
 
            for wish in wishes:
                wish_dict = {
                    'Id': wish[0],
                    'Title': wish[1],
                    'Description': wish[2],
                    'Date': wish[4]}
                wishes_dict.append(wish_dict)
     
            response.append(wishes_dict)
            response.append({'total':_total_records}) 
 
            return json.dumps(response)
        else:
            return render_template('error.html', error = 'Unauthorized Access')
    except Exception as e:
        return render_template('error.html', error = str(e))

# DONE
def getSum(p_wish_id):
    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select sum(wish_like) from tbl_likes where wish_id = " + str(p_wish_id) + ""
    cursor.execute(sql)
    result = cursor.fetchall()
    print(result[0][0])
    return result[0][0]

# DONE
def hasLiked(p_wish, p_user):
    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select wish_like from tbl_likes where wish_id = " + str(p_wish) + " and user_id = " + str(p_user) + ""
    cursor.execute(sql)
    result = cursor.fetchall()
    if result:
        return result[0][0]
    else:
        return 0

# DONE
@app.route('/getAllWishes')
def getAllWishes():
    try:
        if session.get('user'):
            _user = session.get('user')
            conn = mysql.connect()
            cursor = conn.cursor()
            sql = "select wish_id,wish_title,wish_description,wish_file_path from tbl_wish where wish_private = 0"
            cursor.execute(sql)
            #cursor.callproc('sp_GetAllWishes',(_user,))
            result = cursor.fetchall()

            wishes_dict = []
            for wish in result:
                sumNum = getSum(wish[0])
                #print(str(sumNum) + "HI")
                if sumNum is None:
                    sumNum = 0
                wish_dict = {
                        'Id': wish[0],
                        'Title': wish[1],
                        'Description': wish[2],
                        'FilePath': wish[3],
                        'Like': int(sumNum),
                        'HasLiked': hasLiked(wish[0], _user)}
                #print(wish_dict)
                # print(getSum(wish[0]))
                        #'Like': wish[4],
                        #'HasLiked': wish[5]}
                wishes_dict.append(wish_dict)       
 
            return json.dumps(wishes_dict)
        else:
            return render_template('error.html', error = 'Unauthorized Access')
    except Exception as e:
        #return render_template('error.html',error = str(e))
        print(e)
        traceback.print_exc()

# DONE
@app.route('/addWish',methods=['POST'])
def addWish():
    try:
        if session.get('user'):
            _title = request.form['inputTitle']
            _description = request.form['inputDescription']
            _user = session.get('user')
            if request.form.get('filePath') is None:
                _filePath = ''
            else:
                _filePath = request.form.get('filePath')
            if request.form.get('private') is None:
                _private = 0
            else:
                _private = 1
            if request.form.get('done') is None:
                _done = 0
            else:
                _done = 1

            conn = mysql.connect()
            cursor = conn.cursor()
            sql = "insert into tbl_wish(wish_title,wish_description,wish_user_id,wish_date,wish_file_path,wish_accomplished,wish_private)values('"+_title+"','"+_description+"',"+str(_user)+",NOW(),'"+_filePath+"',"+str(_done)+","+str(_private)+")"
            cursor.execute(sql)
            conn.commit()
            sql = "select LAST_INSERT_ID()"
            cursor.execute(sql)
            result = cursor.fetchall()
            last_id = result[0][0]
            print(last_id)
            sql = "insert into tbl_likes(wish_id,user_id,wish_like)values(" + str(last_id) + "," + str(_user) + ",0)"
            cursor.execute(sql)
            conn.commit()
            #cursor.callproc('sp_addWish',(_title,_description,_user,_filePath,_private,_done))
            data = cursor.fetchall()
 
            if len(data) == 0:
                conn.commit()
                return redirect('/userHome')
            else:
                return render_template('error.html',error = 'An error occurred!')
 
        else:
            return render_template('error.html',error = 'Unauthorized Access')
    except Exception as e:
        return render_template('error.html',error = str(e))
    finally:
        cursor.close()
        conn.close()

# DONE
@app.route('/addUpdateLike',methods=['POST'])
def addUpdateLike():
    try:
        if session.get('user'):
            _wishId = request.form['wish']
            _like = request.form['like']
            _user = session.get('user')
            
            conn = mysql.connect()
            cursor = conn.cursor()
            sql = "select 1 from tbl_likes where wish_id = " + str(_wishId) + " and user_id = " + str(_user)  + ""
            cursor.execute(sql)
            result = cursor.fetchall()

            if len(result) != 0:
                sql = "select wish_like from tbl_likes where wish_id = " + str(_wishId) + " and user_id = " + str(_user)  + ""
                cursor.execute(sql)
                wish_like = cursor.fetchall()

                if wish_like[0][0] == 0:
                    sql = "update tbl_likes set wish_like = 1 where wish_id = " + str(_wishId) + " and user_id = " + str(_user)  + ""
                    cursor.execute(sql)
                    conn.commit()

                    wish_sum = getSum(_wishId)
                    liked = hasLiked(_wishId, _user)
                    print(str(wish_sum))
                    print(str(liked))
                    return json.dumps({'status':'OK','total':int(wish_sum),'likeStatus':liked})
                    # sql = "select '" + getSum(_wishId) + "','" + hasLiked(_wishId, _user)"'"
                    # cursor.execute(sql)

                    # result = cursor.fetchall()

                    #return json.dumps({'status':'OK','total':result[0][0],'likeStatus':result[0][1]})
                else:
                    sql = "update tbl_likes set wish_like = 0 where wish_id = " + str(_wishId) + " and user_id = " + str(_user)  + ""
                    cursor.execute(sql)
                    conn.commit()

                    wish_sum = getSum(_wishId)
                    liked = hasLiked(_wishId, _user)
                    return json.dumps({'status':'OK','total':int(wish_sum),'likeStatus':liked})
            else:
                sql = "insert into tbl_likes(wish_id,user_id,wish_like)values(" + str(_wishId) + "," + str(_user) + "," + str(_like) + ")"
                cursor.execute(sql)
                conn.commit()
                return render_template('error.html',error = 'Unauthorized Access')

            # cursor.callproc('sp_AddUpdateLikes',(_wishId,_user,_like))
            # data = cursor.fetchall()
 
        #     if len(data) == 0:
        #         conn.commit()
        #         cursor.close()
        #         conn.close()

        #         conn = mysql.connect()
        #         cursor = conn.cursor()
        #         #sql = "select '" + getSum(_wishId ) + "','" + hasLiked(_wishId, _user)"'"
        #         #cursor.execute(sql)
        #         cursor.callproc('sp_getLikeStatus',(_wishId,_user))
                
        #         result = cursor.fetchall()

        #         return json.dumps({'status':'OK','total':result[0][0],'likeStatus':result[0][1]})
        #     else:
        #         return render_template('error.html',error = 'An error occurred!')
 
        # else:
        #     return render_template('error.html',error = 'Unauthorized Access')
    except Exception as e:
        traceback.print_exc()
        #return render_template('error.html',error = str(e))
    finally:
        cursor.close()
        conn.close()

# DONE
@app.route('/getWishById',methods=['POST'])
def getWishById():
    try:
        if session.get('user'):
 
            conn = mysql.connect()
            cursor = conn.cursor()
            _id = request.form['id']
            _user = session.get('user')
            print(_id)

            sql = "select wish_id,wish_title,wish_description,wish_file_path,wish_accomplished,wish_private from tbl_wish where wish_id = " + str(_id) + " and wish_user_id = " + str(_user) + ""
            cursor.execute(sql)
            #cursor.callproc('sp_GetWishById',(_id,_user))
            result = cursor.fetchall()
            print(result)
 
            wish = []
            wish.append({'Id':result[0][0],'Title':result[0][1],'Description':result[0][2],'FilePath':result[0][3],'Done':result[0][4],'Private':result[0][5]})
 
            return json.dumps(wish)
        else:
            return render_template('error.html', error = 'Unauthorized Access')
    except Exception as e:
        traceback.print_exc()

#STILL HAVE TO UPDATE
@app.route('/updateWish', methods=['POST'])
def updateWish():
    try:
        if session.get('user'):
            _user = session.get('user')
            _title = request.form['title']
            _description = request.form['description']
            _wish_id = request.form['id']
            _filePath = request.form['filePath']
            _isPrivate = request.form['isPrivate']
            _isDone = request.form['isDone']
 
            conn = mysql.connect()
            cursor = conn.cursor()
            sql = "update tbl_wish set wish_title = '" + _title + "',wish_description = '" + _description + "',wish_file_path = '" + _filePath + "',wish_accomplished = " + str(_isDone) + ",wish_private = " + str(_isPrivate) + " where wish_id = " + str(_wish_id) + " and wish_user_id = " + str(_user) + ""
            cursor.execute(sql)
            #cursor.callproc('sp_updateWish',(_title,_description,_wish_id,_user,_filePath,_isPrivate,_isDone)) 
            data = cursor.fetchall()
 
            if len(data) == 0:
                conn.commit()
                return json.dumps({'status':'OK'})
            else:
                return json.dumps({'status':'ERROR'})
    except Exception as e:
        traceback.print_exc()
        return json.dumps({'status':'Unauthorized access'})
    finally:
        cursor.close()
        conn.close()

# DONE
@app.route('/deleteWish',methods=['POST'])
def deleteWish():
    try:
        if session.get('user'):
            _id = request.form['id']
            _user = session.get('user')
 
            conn = mysql.connect()
            cursor = conn.cursor()
            sql = "delete from tbl_wish where wish_id = '" + str(_id) + "' and wish_user_id = '" + str(_user) + "'"
            cursor.execute(sql)
            #cursor.callproc('sp_deleteWish',(_id,_user))
            result = cursor.fetchall()
 
            if len(result) == 0:
                conn.commit()
                return json.dumps({'status':'OK'})
            else:
                return json.dumps({'status':'An Error occured'})
        else:
            return render_template('error.html',error = 'Unauthorized Access')
    except Exception as e:
        return json.dumps({'status':str(e)})
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run()