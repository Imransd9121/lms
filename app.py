from flask import Flask,flash,redirect,render_template,url_for,request,jsonify,send_file,session,abort
from flask_session import Session
import mysql.connector
from datetime import date
from datetime import datetime
from otp import genotp
from sdmail import sendmail
from tokenreset import token
from stoken1 import token1
import os
from io import BytesIO
import stripe
stripe.api_key='sk_test_51MzcVYSDVehZUuDTkwGUYe8hWu2LGN0krI8iO5QOAEqoRYXx3jgRVgkY7WzXqQmpN62oMWM59ii76NKPrRzg3Gtr005oVpiW82'
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from key import *
app=Flask(__name__)
app.secret_key='hello'
UPLOAD_FOLDER = 'static'  # Define the folder to store uploaded files
ALLOWED_EXTENSIONS = {'pdf', 'mp4','jpg'}  # Define the allowed file extensions
app.config['SESSION_TYPE'] = 'filesystem'

mydb=mysql.connector.connect(host='localhost',user='root',password='9121461636',db='learning_management_system')
Session(app)



import random
def genotp():
    u_c=[chr(i) for i in range(ord('A'),ord('Z')+1)]
    l_c=[chr(i) for i in range(ord('a'),ord('z')+1)]
    otp=''
    for i in range(2):
        otp+=random.choice(u_c)
        otp+=str(random.randint(0,9))
        otp+=random.choice(l_c)
    return otp



@app.route('/')
def index():
    cursor = mydb.cursor(buffered=True)
    cursor.execute('select * from course')


    return render_template('index.html')
#============================= Admin
@app.route('/adminiogin',methods=['GET','POST'])
def alogin():
    if session.get('admin'):
        return redirect('admindashboard')
    else:
        if request.method=='POST':
            email=request.form['email']
            code = request.form['code']
            email1="admin@codegnan.com"
            code1="admin@123"
            if email == email1: 
                if code == code1:
                    session['admin']=code1
                    return redirect('admindashboard')
            else:
                flash("unauthorized access")
                return redirect(url_for('alogin'))
        
        return render_template('adminlogin.html')

@app.route('/alogout')
def alogout():
    if session.get('admin'):
        session.pop('admin')
        flash('successfully admin log out')
        return redirect(url_for('index'))
    else:
        return redirect(url_for('alogin'))
@app.route('/admindashboard')
def admindashboard():
    if session.get('admin'):
        return render_template('admindashboard.html')
    return redirect(url_for('alogin'))

@app.route('/admin_viewstudents')
def a_students():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('''SELECT a.name AS user_name, 
       c.email AS user_email, 
       c.ph_number AS user_phone, 
       p.name AS profile_name, 
       p.specialization AS profile_specialization, 
       p.email AS profile_email,  -- Added profile email
       c.title AS course_title, 
       c.sub_topic AS course_subtopic, 
       c.course_id AS course_id
        FROM trainer t
        LEFT JOIN profile p ON a.name = a.trainer_name
        LEFT JOIN course c ON a.name = a.trainer_name;

            ''')
        adata = cursor.fetchall()
        
        return render_template('admin_viewstudents.html',a=adata)
    else:
        return redirect(url_for('alogin'))
@app.route('/admin_viewtrainers')
def a_trainers():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('''SELECT t.name AS trainer_name, 
       t.email AS trainer_email, 
       t.ph_number AS trainer_phone, 
       p.name AS profile_name, 
       p.specialization AS profile_specialization, 
       p.email AS profile_email,  -- Added profile email
       c.title AS course_title, 
       c.sub_topic AS course_subtopic, 
       c.course_id AS course_id
        FROM trainer t
        LEFT JOIN profile p ON t.name = p.trainer_name
        LEFT JOIN course c ON t.name = c.trainer_name;

            ''')
        tdata = cursor.fetchall()
        
        return render_template('admin_viewtrainers.html',t = tdata)
    return redirect(url_for('alogin'))
    
@app.route('/admin_course/<c_name>')
def acourse(c_name):
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT c.course_id, c.title, c.sub_topic, c.description, c.prerequisites, c.level, c.brochure, v.video_id, v.video, v.video_duration, v.uploaded_datetime FROM course c INNER JOIN video v ON c.course_id = v.course_id WHERE c.course_id = %s GROUP BY c.course_id, v.video_id', (c_name,))

        courses = cursor.fetchall()
        #print("======================================================",courses)
        return render_template('admin_view_uploaded_courses.html',c= courses)
    else:
        return redirect(url_for('alogin'))

@app.route('/admin_view_all_courses/<c_name>')
def aviewallcourses(c_name):
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('''select course_id,sub_topic,description,level  from course 
                       where   title=%s''',[c_name])
        data = cursor.fetchall()
        #print("========================",data)
        return render_template('admin_view_all_course.html',i = data)
    return redirect(url_for('alogin'))

@app.route('/admin_uploadfees', methods=['GET', 'POST'])
def a_fee():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select * from fees')
        fdata = cursor.fetchall()
        if request.method == "POST":
            title = request.form['title']
            amount = request.form['amount']
            # Check if a fee already exists for the given course title
            cursor.execute('SELECT * FROM fees WHERE course_title = %s', (title,))
            existing_fee = cursor.fetchone()
            if existing_fee:
                flash('A fee already exists for this course title.', 'error')
                return redirect(url_for('a_fee'))  # Redirect to the fees upload page
            else:
                cursor.execute('INSERT INTO fees (course_title, fee_amount) VALUES (%s, %s)', (title, amount))
                mydb.commit()
                flash('Fee uploaded successfully.', 'success')
                return redirect(url_for('a_fee'))  # Redirect to the fees upload page
        return render_template('fees.html',f = fdata)
    return redirect(url_for('alogin'))

@app.route('/updatefees', methods=['GET', 'POST'])
def updatefees():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)
        if request.method == "POST":
            title = request.form['title']
            amount = request.form['amount']
            cursor.execute('SELECT * FROM fees WHERE course_title = %s', (title,))
            existing_fee = cursor.fetchone()
            if existing_fee:
                cursor.execute('UPDATE fees SET fee_amount = %s WHERE course_title = %s', (amount, title))
                mydb.commit()
                flash('Fees updated successfully.', 'success')
                return redirect(url_for('a_fee'))  # Redirect to the fees upload page or any other appropriate route
            else:
                flash('Fees can not updated successfully becuase first insert fees initial then upadate the fess amount')
                return redirect(url_for('a_fee'))

        return render_template('updatefees.html')
    return redirect(url_for('alogin'))


@app.route('/uregistration',methods=['GET','POST'])
def uregistration():
  
    if request.method=="POST":
        Name = request.form['fullname']
        Mail = request.form['email']
        Pwd = request.form['password']
        cpassword = request.form['cpassword']
        
        Phone = request.form['phone']
        Place = request.form['address']
        # gender = request.form['gender']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where email=%s',[Mail])
        count = cursor.fetchone()[0]
        cursor.execute('select count(*) from users where name=%s',[Name])
        count1 = cursor.fetchone()[0]
        cursor.close()
        
        if count == 1:
            flash('Email Already In use')
            return render_template('user_registration.html')
        elif count1==1:
            flash('USER NAME ALREADY EXTSTED')
        else :
                if Pwd == cpassword:

                    otp=genotp()
                    var2={'name':Name,'mail':Mail,'ph_number':Phone,'pwd':Pwd,'add':Place,'uotp':otp}
                    subject='Email Authentication'
                    body=f"Thanks for signing up\n\nfollow this link for further steps-{otp}"
                    sendmail(to=Mail, subject=subject, body=body)
                    flash('OTP sent successfully')
                    return redirect(url_for('uotpform',uotp=token(data=var2, salt=salt)))
                else:
                    flash('password not matched')
                    return redirect(url_for('uregistration'))
    return render_template('user_registration.html')

@app.route('/uotpform/<uotp>',methods=['GET','POST'])
def uotpform(uotp):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        var2=serializer.loads(uotp,salt=salt)
    except Exception as e:
        flash('OTP expired')
        return render_template('otp.html')
    else:
        if request.method=='POST':
            otp=request.form['otp']
            if var2['uotp'] == otp :
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into users(name,email,password,phone,address) values(%s,%s,%s,%s,%s)',[var2['name'],var2['mail'],var2['pwd'],var2['ph_number'],var2['add']])
                mydb.commit()
                cursor.close()
                flash('Registration Successfull')
                return redirect(url_for('ulogin'))
            else:
                flash('Invalid OTP')
                return render_template('otp.html')
        return render_template('otp.html')
@app.route('/forgotu',methods=['GET','POST'])
def forgotu():
    if request.method=='POST':
        email=request.form['email']
        subject='RESET Link for password sent to your mail'
        body=f"Click the link to verify the reset password:{url_for('verifyforgetu',data=token(data=email,salt=salt2),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Reset Link has been sent to your mail')
        return redirect(url_for('forgotf'))
    return render_template('forgot.html')
@app.route('/verifyforgetu/<data>',methods=['GET','POST'])
def verifyforgetu(data):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(data,salt=salt2,max_age=180)
    except Exception :
        flash('Link Expired')
        return redirect(url_for('forgotf'))
    else :
        if request.method=='POST':
            npassword=request.form['npassword']
            cpassword=request.form['cpassword']
            if npassword==cpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update users set password=%s where email=%s',[npassword,data])
                mydb.commit()
                flash("PASSWORD RESET SUCCESSFULLY")
                return redirect(url_for('ulogin'))
            else:
                flash('PASSWORD NOT MATCHED')
                return redirect(url_for('verifyforgetu'))
    return render_template('newpassword.html')
@app.route('/ulogout')
def ulogout():
    if session.get('user'):
        session.pop('user')
        flash('Successfully logged out')
        return redirect(url_for('index'))
    else:
        return redirect(url_for('ulogin'))
    
# @app.route('/uconfirm/<otp>')
# def uconfirm(otp):
#     try:
#         serializer=URLSafeTimedSerializer(secret_key)
#         data=serializer.loads(token,salt=salt,max_age=180)
#     except Exception as e:
      
#         return 'Link Expired register again'
#     else:
#         cursor=mydb.cursor(buffered=True)
#         id1=data['name']
#         cursor.execute('select count(*) from users where name=%s',[id1])
#         count=cursor.fetchone()[0]
#         if count==1:
#             cursor.close()
#             flash('You are already registerterd!')
#             return redirect(url_for('ulogin'))
#         else:
#             cursor.execute('INSERT INTO users (name,email, password,phone,address) values ( %s,%s,%s,%s,%s)',[data['name'], data['mail'], data['pwd'],data['ph'],data['place']])

#             mydb.commit()
#             cursor.close()
#             flash('Details registered!')
#             return redirect(url_for('ulogin'))
@app.route('/ulogin',methods=['GET','POST'])
def ulogin():
    if session.get('user'):
        return redirect(url_for('users_dashboard'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT count(*) from users where name=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==1:
            session['user']=username
            if not session.get(username):
                session[username]={}
            return redirect(url_for("users_dashboard"))
        else:
            flash('Invalid username or password')
            return render_template('user_login.html')
    return render_template('user_login.html')
# @app.route('/uforget',methods=['GET','POST'])
# def uforgot():
#     if request.method=='POST':
#         id1=request.form['id1']
#         cursor=mydb.cursor(buffered=True)
#         cursor.execute('select count(*) from users where name=%s',[id1])
#         count=cursor.fetchone()[0]
#         cursor.close()
#         if count==1:
#             cursor=mydb.cursor(buffered=True)

#             cursor.execute('SELECT email from users where name=%s',[id1])
#             email=cursor.fetchone()[0]
#             cursor.close()
#             subject='Forget Password'
#             confirm_link=url_for('ureset',token=token1(id1,salt=salt2),_external=True)
#             body=f"Use this link to reset your password-\n\n{confirm_link}"
#             sendmail(to=email,body=body,subject=subject)
#             flash('Reset link sent check your email')
#             return redirect(url_for('ulogin'))
#         else:
#             flash('Invalid email id')
#             return render_template('forgot.html')
#     return render_template('forgot.html')


# @app.route('/ureset/<token>',methods=['GET','POST'])
# def ureset(token):
#     try:
#         serializer=URLSafeTimedSerializer(secret_key)
#         id1=serializer.loads(token,salt=salt2,max_age=180)
#     except:
#         abort(404,'Link Expired')
#     else:
#         if request.method=='POST':
#             newpassword=request.form['npassword']
#             confirmpassword=request.form['cpassword']
#             if newpassword==confirmpassword:
#                 cursor=mydb.cursor(buffered=True)
#                 cursor.execute('update users set password=%s where name=%s',[newpassword,id1])
#                 mydb.commit()
#                 flash('Reset Successful')
#                 return redirect(url_for('ulogin'))
#             else:
#                 flash('Passwords mismatched')
#                 return render_template('newpassword.html')
#         return render_template('newpassword.html')
# @app.route('/ulogout')
# def ulogout():
#     if session.get('user'):
#         session.pop('user')
#         flash('Successfully loged out')
#         return redirect(url_for('index'))
#     else:
#         return redirect(url_for('ulogin'))


@app.route('/users_dashboard')
def users_dashboard():
    if session.get('user'):
        return render_template('users_dashboard.html')
    return redirect(url_for('ulogin'))
#=============== users view course
@app.route('/scourse/<category>')
def scourse(category):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from fees where course_title=%s',[category])
    fdata = cursor.fetchone()
    cursor.execute('select * from course where title=%s',[category])
    cdata=cursor.fetchall()

    return render_template('courses.html',c=cdata,f = fdata)
@app.route('/scourse_f/<c_name>')
def scourse_f(c_name):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        #print('===================',session['user'])
        #print('===========================',c_name)
        cursor.execute('select title from course where course_id=%s',[c_name])
        title= cursor.fetchone()[0]
        cursor.execute('SELECT status FROM users_payment WHERE username = %s AND title = %s', [session['user'], title])
        status = cursor.fetchone()
        #print('=================',status)
        if status[0] == 'paid':
            cursor=mydb.cursor(buffered=True)
            cursor.execute('SELECT c.course_id, c.title, c.sub_topic, c.description, c.prerequisites, c.level,c.brochure, v.video_id, v.video, v.video_duration, v.uploaded_datetime FROM course c INNER JOIN video v ON c.course_id = v.course_id WHERE c.course_id = %s  GROUP BY c.course_id, v.video_id', (c_name,))
            courses = cursor.fetchall()
            return render_template('user_view_course.html',c=courses)
        else:
            flash('Please pay the fees to view this course.', 'error')
            return redirect(url_for('users_dashboard'))
    flash('Please login and  pay the fees to view this course.', 'error')
    return redirect(url_for('ulogin'))
   
@app.route('/pay/<id1>/<name>/<float:price>', methods=['GET'])
def pay(id1,name, price):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT * FROM users_payment WHERE username = %s AND fid = %s AND status = %s', (session['user'], id1, 'paid'))
        already_paid = cursor.fetchone()

        if already_paid:
            flash('You have already paid for this course.Ignore the purchase course button ,you can access the course', 'info')
            return redirect(url_for('scourse',category=name))  # Redirect to courses page or any other appropriate page

        total = price * 1  # Fixed quantity of 1
        checkout_session = stripe.checkout.Session.create(
            success_url=url_for('success',id1= id1, name=name, total=total, _external=True),
            line_items=[
                {
                    'price_data': {
                        'product_data': {
                            'name': name,
                        },
                        'unit_amount': int(price * 100),  # Price in cents (Stripe requires in cents)
                        'currency': 'inr',  # Assuming USD currency
                    },
                    'quantity': 1,  # Fixed quantity
                },
            ],
            mode="payment",
        )
        return redirect(checkout_session.url)
    else:
        return redirect(url_for('ulogin'))

@app.route('/success/<id1>/<name>/<total>')
def success(id1, name, total):
    if session.get('user'):
        username = session.get('user')
        payment_time = datetime.now()  # Assuming you're using datetime from the datetime module
        status = 'paid'  # Set the status to 'paid' since the payment was successful

        # Insert payment details into the users_payment table
        cursor = mydb.cursor(buffered=True)
        cursor.execute('INSERT INTO users_payment (username, payment_time, status, fid, title, amount) VALUES (%s, %s, %s, %s, %s, %s)',
                       (username, payment_time, status, id1, name, total))
        mydb.commit()
        cursor.close()

        return redirect(url_for('paymentsucess'))  # Redirect to the orders page after successful payment
    return redirect(url_for('login'))  # Redirect to login if user is not logged in
@app.route('/paymentsucess')
def paymentsucess():
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select * from users_payment where username=%s',[session['user']])
        pdata = cursor.fetchall()
        #print(pdata)
        return render_template('paymentdetails.html',p = pdata)

    return redirect(url_for('ulogin'))



#====================================Trainer Registration
@app.route('/trainer_registration',methods=['GET','POST'])
def tregistration():
    if request.method=="POST":
        Name = request.form['fullname']
        Mail = request.form['email']
        
        
        Phone = request.form['phone']
        # subject = request.form['subject']
        code = request.form['code']
        Pwd = request.form['password']
        ccode ="admin@1234"
        if ccode == code:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select count(*) from trainer where email=%s',[Mail])
            count = cursor.fetchone()[0]
      
            cursor.close()
            if count == 1:
                flash('Email Already In use')
                return render_template('trainer_registration.html')
            else :
                otp=genotp()
                var1={'name':Name,'mail':Mail,'ph_number':Phone,'pwd':Pwd,'fotp':otp}
                subject = 'Registration OTP sent to Yoyr Mail'
                body=f"Thanks for signing up\n\nfollow this link for further steps-{otp}"
                sendmail(to=Mail, subject=subject, body=body)
                flash('OTP sent successfully')
                return redirect(url_for('fotpform',fotp=token(data=var1, salt=salt)))
        else:
            flash('code is wrong!')
            return redirect(url_for('tregistration'))
        
    return render_template('trainer_registration.html')

@app.route('/fotpform/<fotp>',methods=['GET','POST'])
def fotpform(fotp):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        var1=serializer.loads(fotp,salt=salt)
    except Exception as e:
        flash('OTP expired')
        return render_template('otp.html')
    else:
        if request.method=='POST':
            otp=request.form['otp']
            if var1['fotp'] == otp :
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into trainer(name,email,ph_number,password) values(%s,%s,%s,%s)',[var1['name'],var1['mail'],var1['ph_number'],var1['pwd']])
                mydb.commit()
                cursor.close()
                flash('Registration Successfull')
                return redirect(url_for('tlogin'))
            else:
                flash('Invalid OTP')
                return render_template('otp.html')
        return render_template('otp.html')
@app.route('/forgotf',methods=['GET','POST'])
def forgotf():
    if request.method=='POST':
        email=request.form['email']
        subject='RESET Link for password for Freelancer account in TALENT-HUB'
        body=f"Click the link to verify the reset password:{url_for('verifyforgetf',data=token(data=email,salt=salt2),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Reset Link has been sent to your mail')
        return redirect(url_for('forgotf'))
    return render_template('forgot.html')
@app.route('/verifyforgetf/<data>',methods=['GET','POST'])
def verifyforgetf(data):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(data,salt=salt2,max_age=180)
    except Exception :
        flash('Link Expired')
        return redirect(url_for('forgotf'))
    else :
        if request.method=='POST':
            npassword=request.form['npassword']
            cpassword=request.form['cpassword']
            if npassword==cpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update users set password=%s where email=%s',[npassword,data])
                mydb.commit()
                flash("PASSWORD RESET SUCCESSFULLY")
                return redirect(url_for('tlogin'))
            else:
                flash('PASSWORD NOT MATCHED')
                return redirect(url_for('verifyforgetf'))
    return render_template('newpassword.html')
@app.route('/tlogout')
def tlogout():
    if session.get('user'):
        session.pop('user')
        flash('Successfully logged out')
        return redirect(url_for('index'))
    else:
        return redirect(url_for('tlogin'))
###################################################################################

@app.route('/trainer_login',methods=['GET','POST'])
def tlogin():
    if session.get('user'):
        return redirect(url_for('users_dashboard'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT count(*) from trainer where name=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==1:
            session['trainer']=username
            if not session.get(username):
                session[username]={}
            return redirect(url_for("trainer_dashboard"))
        else:
            flash('Invalid username or password')
            return render_template('trainer_login.html')
    return render_template('trainer_login.html')
# @app.route('/tforget',methods=['GET','POST'])
# def tforgot():
#     if request.method=='POST':
#         id1=request.form['email']
#         cursor=mydb.cursor(buffered=True)
#         cursor.execute('select count(*) from trainer where email=%s',[id1])

#         count=cursor.fetchone()[0]
#         cursor.close()
#         if count==1:
#             cursor=mydb.cursor(buffered=True)

#             cursor.execute('SELECT email from trainer where email=%s',[id1])
#             email=cursor.fetchone()[0]
#             cursor.close()
#             subject='Forget Password'
#             confirm_link=url_for('treset',token=token1(id1,salt=salt2),_external=True)
#             body=f"Use this link to reset your password-\n\n{confirm_link}"
#             sendmail(to=email,body=body,subject=subject)
#             flash('Reset link sent check your email')
#             return redirect(url_for('tlogin'))
#         else:
#             flash('Invalid email id')
#             return render_template('forgot.html')
#     return render_template('forgot.html')


# @app.route('/treset/<token>',methods=['GET','POST'])
# def treset(token):
#     try:
#         serializer=URLSafeTimedSerializer(secret_key)
#         id1=serializer.loads(token,salt=salt2,max_age=180)
#     except:
#         abort(404,'Link Expired')
#     else:
#         if request.method=='POST':
#             newpassword=request.form['npassword']
#             confirmpassword=request.form['cpassword']
#             if newpassword==confirmpassword:
#                 cursor=mydb.cursor(buffered=True)
#                 cursor.execute('update trainer set password=%s where name=%s',[newpassword,id1])
#                 mydb.commit()
#                 flash('Reset Successful')
#                 return redirect(url_for('tlogin'))
#             else:
#                 flash('Passwords mismatched')
#                 return render_template('newpassword.html')
#         return render_template('newpassword.html')
# @app.route('/tlogout')
# def tlogout():
#     if session.get('trainer'):
#         session.pop('trainer')
#         flash('Successfully loged out')
#         return redirect(url_for('index'))
#     else:
#         return redirect(url_for('tlogin'))

@app.route('/trainer_dashboard')
def trainer_dashboard():
    if session.get('trainer'):
        return render_template('trainer_dashboard.html')
    return redirect(url_for('tlogin')) 
@app.route('/upload_course', methods=['GET', 'POST'])
def upload_course():
    if session.get('trainer'):
        if request.method == "POST":
            title = request.form['title']
            sub_topic = request.form['sub_topic']
            description = request.form['description']
            prerequisites = request.form['prerequisites']
            level = request.form['level']
            brochure = request.files['brochure']
            video = request.files['video']
            video_duration = request.form['video_duration'].split()[0]
            file_data = brochure.read()
            audio_id = genotp()
            video_id = title + audio_id
            filename1 = secure_filename(video_id +'.mp4')
            print(filename1)
            # Ensure a secure filename
            #brochure_path = os.path.join(UPLOAD_FOLDER, secure_filename(brochure.filename))
            path = os.path.dirname(os.path.abspath(__file__))
            static_path=os.path.join(path,'static')
            video.save(os.path.join(static_path,filename1))

            cursor = mydb.cursor(buffered=True)
            cursor.execute('INSERT INTO course (title, sub_topic, description, prerequisites, level, brochure, trainer_name) VALUES (%s, %s, %s, %s, %s, %s, %s)', [title, sub_topic, description, prerequisites, level, file_data, session['trainer']])
            mydb.commit()
            course_id = cursor.lastrowid
            cursor.execute('INSERT INTO video (course_id, video, video_duration, uploaded_datetime, trainer_name) VALUES (%s, %s, %s, NOW(), %s)', [course_id, filename1, video_duration, session['trainer']])
            mydb.commit()


            flash('Course uploaded successfully!')
            return redirect(url_for('trainer_dashboard'))

        return render_template('upload_course.html')
    else:
        return redirect(url_for('tlogin'))
@app.route('/course/<c_name>')
def course(c_name):
    if session.get('trainer'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT c.course_id, c.title, c.sub_topic, c.description, c.prerequisites, c.level,c.brochure, v.video_id, v.video, v.video_duration, v.uploaded_datetime FROM course c INNER JOIN video v ON c.course_id = v.course_id WHERE c.course_id = %s AND c.trainer_name = %s GROUP BY c.course_id, v.video_id', (c_name, session['trainer']))
        courses = cursor.fetchall()
        #print("======================================================",courses)
        return render_template('view_uploaded_courses.html',c= courses)
    else:
        return redirect(url_for('tlogin'))

@app.route('/view_all_courses/<c_name>')
def viewallcourses(c_name):
    if session.get('trainer'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('''select course_id,sub_topic,description,level  from course 
                       where  trainer_name =%s and title=%s''',[session['trainer'],c_name])
        data = cursor.fetchall()
        #print("========================",data)
        return render_template('view_all_course.html',i = data)
    return redirect(url_for('tlogin'))
@app.route('/update_course/<cid>',methods=['GET','POST'])
def updatecourse(cid):
    if session.get('trainer'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('''SELECT 
                    c.course_id,
                    c.title,
                    c.sub_topic,
                    c.description,
                    c.prerequisites,
                    c.level,
                    c.brochure,
                    c.enrollment_count,
                    
                    c.trainer_name AS course_trainer,
     
                    v.video_id,
                    v.video,
                    v.video_duration,
                    v.uploaded_datetime,
                    v.trainer_name AS video_trainer
        FROM 
            course c
        LEFT JOIN 
            video v ON c.course_id = v.course_id
        WHERE 
            c.course_id = %s AND c.trainer_name = %s
        GROUP BY 
            c.course_id, v.video_id;
                       ''',[cid,session['trainer']])
        data = cursor.fetchone()
        if request.method=="POST":
            title=request.form['title']
            sub_topic = request.form['sub_topic']
            description = request.form['description']
            prerequisites = request.form['prerequisites']
            level = request.form['level']
            video_duration = request.form['video_duration']
            cursor.execute('select video_id from video where course_id=%s',[cid])
            vd = cursor.fetchone()[0]
            cursor.execute('update video set video_duration=%s where video_id=%s and trainer_name=%s',(video_duration,vd,session['trainer'],))
            cursor.execute("""
                UPDATE course
                SET title = %s,
                    sub_topic = %s,
                    description = %s,
                    prerequisites = %s,
                    level = %s
                WHERE trainer_name = %s and course_id=%s """, (title, sub_topic, description, prerequisites, level, session['trainer'],cid))
            flash(f'{title} -{sub_topic } updates sucessfully')
            return redirect(url_for('viewallcourses',c_name=title))
            


       
        return render_template('updatecourse.html',i = data)


    return redirect(url_for('tlogin'))
@app.route('/deletecourse/<cid>',methods=['GET','POST'])
def deletecourse(cid):
    if session.get('trainer'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT video FROM video WHERE course_id = %s and  trainer_name = %s', [cid,session['trainer'],])
        
        video_filename = cursor.fetchone()[0]
        if video_filename:
            cursor.execute('SELECT title,sub_topic FROM course WHERE course_id = %s and  trainer_name = %s', [cid,session['trainer'],])
            cdata= cursor.fetchone() 
            cursor.execute('delete from video where course_id=%s and trainer_name=%s',[cid,session['trainer']])
            mydb.commit()
        
            cursor.execute('delete from course where course_id=%s and trainer_name=%s',[cid,session['trainer']])
     
            path_to_video = os.path.join(UPLOAD_FOLDER, video_filename+'.mp3')
            #print("=======================================",path_to_image)
            if os.path.exists(path_to_video):
                #print('=================================,the path exists')
                os.remove(path_to_video)  # Delete the image file from the static folder
            mydb.commit()
            flash(f'{cdata[0]} of {cdata[1]} course deleted sucessfully')
            return redirect(url_for('viewallcourses',c_name=cdata[0])) 
        else:
            flash('No video found for deletion.')
            return redirect(url_for('trainer_dashboard'))

        

    return redirect(url_for('tlogin'))
@app.route('/addprofile', methods=['GET','POST'])
def addprofile():
    if session.get('trainer'):
        if request.method=="POST":
            name = request.form['name']
            specialization = request.form['specialization']
            email = request.form['email']
            experience = request.form['experience']
            profile = request.files['profile']
            profile_image = genotp()
            profile1 = name + profile_image
            cursor = mydb.cursor(buffered=True)
            cursor.execute('insert into profile (name,specialization,email,experience,profile,trainer_name) values (%s,%s,%s,%s,%s,%s)',[name,specialization,email,experience,profile1,session['trainer'],])
            mydb.commit()
   
            filename1 = secure_filename(profile1 + '.jpg')  # Ensure a secure filename
            image_path = os.path.join(UPLOAD_FOLDER, filename1)
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
           
            profile.save(image_path)
            flash('profile added sucessfully!')
            return redirect(url_for('viewprofile'))




        return render_template('addprofile.html')
    else:
        return redirect(url_for('tlogin'))
@app.route('/viewprofile')
def viewprofile():
    if session.get('trainer'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select * from profile where trainer_name=%s',[session['trainer'],])
        profile = cursor.fetchone()
       

        return render_template('viewprofile.html',p = profile)
    return redirect(url_for('tlogin'))


# @app.route('/assignmentview/<id1>')
# def assignmentview(id1):
#     if session.get('admin'):
#         #rollno=session['user']
#         cursor = mysql.connection.cursor()
        
#         cursor.execute('select id,filedata from assignment where id=%s',[id1])
#         data = cursor.fetchone()
#         cursor.close()
#         filename = str(data[0])
#         bin_file = data[1]#unicode data(binary string-data)
#         byte_data = BytesIO(bin_file)#covert binary file to bytes
#         return send_file(byte_data,download_name=filename,as_attachment=False)#arguments of send_file(1st is byte data file
#     #2.to convert the file in the given extension like(txt,pic,pdf)we need filename
#     #if we want only the pdf file we use the mime_type(explicit convertion))
#     else:
#         return redirect(url_for('alogin'))


@app.route('/addassignment',methods=['GET','POST'])
def addassignment():
    if session.get('trainer'):
        if request.method=="POST":
            title = request.form['title']
            description = request.form['description']
            deadline = request.form['deadline']
            file = request.files['file']
            filename=file.filename
            # print(filename)
            current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor = mydb.cursor(buffered=True)
            cursor.execute('insert into addassignment (title,description,deadline,uploaded_file,trainer_name,trainer_upload_datetime,filename) values (%s,%s,%s,%s,%s,%s,%s)',[title,description,deadline,file.read(),session['trainer'],current_datetime,filename])
            mydb.commit()
            flash(f'{title} assignment added sucessfully!')
            return redirect(url_for('addassignment'))



        return render_template('addassignment.html')
    return render_template('tlogin')
@app.route('/viewfile/<id1>')
def viewfile(id1):
    if session.get('trainer'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select filename,uploaded_file from addassignment where assignment_id=%s',[id1])
        data = cursor.fetchone()
        cursor.close()
        filename = str(data[0])
        bin_file = data[1]#unicode data(binary string-data)
        byte_data = BytesIO(bin_file)#covert binary file to bytes
        byte_data.seek(0)
        return send_file(byte_data,download_name=filename,as_attachment=True)#arguments of send_file(1st is byte data file
    #2.to convert the file in the given extension like(txt,pic,pdf)we need filename
    #if we want only the pdf file we use the mime_type(explicit convertion))
    else:
        return redirect(url_for('tlogin'))
#==============viewuploadassignment
@app.route('/viewassignmentdetails')
def viewassignmentdetails():
    if session.get('trainer'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select * from addassignment where trainer_name=%s',[session['trainer']])
        adata = cursor.fetchall()
        return render_template('viewassignmentdetails.html',a = adata)

    return redirect(url_for('tlogin'))

#==============update assignment
@app.route('/updateassignment/<id1>',methods=['GET','POST'])
def updateassignment(id1):
    if session.get('trainer'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select * from addassignment where assignment_id=%s',[id1])
        data = cursor.fetchone()
        if request.method=="POST":
            title = request.form['title']
            description = request.form['description']
            deadline = request.form['deadline']
            print(deadline)
            cursor.execute('''
                UPDATE addassignment
                SET title=%s, description=%s, deadline=%s, trainer_upload_datetime=%s
                WHERE assignment_id=%s and trainer_name=%s
            ''', [title, description, deadline, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id1,session['trainer']])

            mydb.commit()  # Commit the changes to the database

            # Flash message or redirect as needed
            flash('Assignment updated successfully!')
            return redirect(url_for('viewassignmentdetails'))
            


        return render_template('updateassignment.html',d = data)
    return redirect(url_for('tlogin'))
#=====================update file
@app.route('/updatefile/<id1>',methods=['GET','POST'])
def updatefile(id1):
    if session.get('trainer'):
        cursor = mydb.cursor(buffered=True)
        if request.method=="POST":
            file = request.files['file']
            cursor.execute('update addassignment set uploaded_file=%s where assignment_id=%s and trainer_name=%s',[file.read(),id1,session['trainer']])
            mydb.commit()
            flash('Assignment updated successfully!')
            return redirect(url_for('viewassignmentdetails'))
#==================delete assignment
@app.route('/deleteassignment/<id1>')
def deleteassignment(id1):
    if session.get('trainer'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('delete from addassignment where assignment_id=%s and trainer_name=%s',[id1,session['trainer']])
        mydb.commit()
        flash('assignment deleted sucessfully')
        return redirect(url_for('viewassignmentdetails'))
        

    return redirect(url_for('tlogin'))
#================users view assignment

@app.route('/uviewassignmentdetails/<title>')
def uviewassignmentdetails(title):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users_payment where username=%s and title=%s',[session['user'],title])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select * from addassignment where title=%s',[title])
            adata = cursor.fetchall()
            return render_template('userviewassignmentdetails.html',a = adata)

    return redirect(url_for('ulogin'))
@app.route('/uviewfile/<id1>')
def uviewfile(id1):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select filename,uploaded_file from addassignment where assignment_id=%s',[id1])
        data = cursor.fetchone()
        cursor.close()
        filename = str(data[0])
        bin_file = data[1]#unicode data(binary string-data)
        byte_data = BytesIO(bin_file)
         #covert binary file to bytes
        byte_data.seek(0)#covert binary file to bytes
        return send_file(byte_data,download_name=filename,as_attachment=True)#arguments of send_file(1st is byte data file
    #2.to convert the file in the given extension like(txt,pic,pdf)we need filename
    #if we want only the pdf file we use the mime_type(explicit convertion))
    else:
        return redirect(url_for('ulogin'))
    
from datetime import datetime

@app.route('/resultantfile/<id1>', methods=['GET', 'POST'])
def resultantfile(id1):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT deadline FROM addassignment WHERE assignment_id = %s', [id1])
        deadline_result = cursor.fetchone()
       
        deadline = deadline_result[0]
        if deadline and datetime.now().date() <= deadline:  # Check if today's date is before or on the deadline
            if request.method == "POST":
                file = request.files['file']
                cursor.execute('UPDATE addassignment SET resultant_file = %s, user_name = %s, user_upload_datetime = %s WHERE assignment_id = %s', [file.read(), session['user'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id1])
                mydb.commit()
                flash('Assignment uploaded successfully!')
                return redirect(url_for('users_dashboard'))
        else:
            flash('Deadline for this assignment has passed. Submission is not allowed.')
            return redirect(url_for('users_dashboard'))
    
    else:
        return redirect(url_for('ulogin'))

@app.route('/urviewfile/<id1>')
def urviewfile(id1):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select filename,resultant_file from addassignment where assignment_id=%s',[id1])
        data = cursor.fetchone()
        cursor.close()
        filename = str(data[0])
        bin_file = data[1]#unicode data(binary string-data)
        byte_data = BytesIO(bin_file)#covert binary file to bytes
        return send_file(byte_data,download_name=filename,as_attachment=True)#arguments of send_file(1st is byte data file
    #2.to convert the file in the given extension like(txt,pic,pdf)we need filename
    #if we want only the pdf file we use the mime_type(explicit convertion))
    else:
        return redirect(url_for('ulogin'))
@app.route('/userresultfile/<id1>')
def userresultfile(id1):
    if session.get('trainer'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select filename,resultant_file from addassignment where assignment_id=%s',[id1])
        data = cursor.fetchone()
        cursor.close()
        filename = str(data[0])
        bin_file = data[1]#unicode data(binary string-data)
        byte_data = BytesIO(bin_file)#covert binary file to bytes
        return send_file(byte_data,download_name=filename,as_attachment=True)#arguments of send_file(1st is byte data file
    #2.to convert the file in the given extension like(txt,pic,pdf)we need filename
    #if we want only the pdf file we use the mime_type(explicit convertion))
    else:
        return redirect(url_for('tlogin'))

@app.route('/marks/<id1>',methods=['GET','POST'])
def marks(id1):
    if session.get('trainer'):
        cursor = mydb.cursor(buffered=True)
        if request.method=="POST":
            marks = request.form['marks']
            cursor.execute('update addassignment set marks=%s where assignment_id=%s',[marks,id1])
            mydb.commit()
            flash('marks updated sucessfully')
            return redirect(url_for('viewassignmentdetails'))

    return redirect(url_for('tlogin'))
# @app.route('learnerdeatils')
# def learnersdetails():
#     if session.get('trainer'):
#         cursor = mydb.cursor(buffered=True)
@app.route('/userspayments_admin')
def userspayments():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('''SELECT u.email, u.phone, u.address, up.payment_id, up.payment_time, up.status, up.fid, up.title, up.amount
        FROM users u
        JOIN users_payment up ON u.name = up.username;
        ''')
        data = cursor.fetchall()
        return redirect(url_for('admin_userspayments.html',d = data))

    return redirect(url_for('alogin'))
        
#===
@app.route('/auserdetails')
def auserdetails():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('''SELECT
            u.name,
            u.email,
            u.phone,
            u.address,
            u.gender,
            up.payment_id,
            up.payment_time,
            up.status,
            up.fid,
            up.title,
            up.amount
        FROM
            users u
        LEFT JOIN
            users_payment up ON u.name = up.username;
        ''')
        a = cursor.fetchall()
        return render_template('admin_viewstudents.html',a = a)

    return redirect(url_for('alogin'))
        




























app.run(use_reloader='True',debug = True)
