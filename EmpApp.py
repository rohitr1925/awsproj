from flask import Flask,render_template,request,url_for,session,redirect
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)
app.secret_key = 'robin1925'

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)

output = {}
table = 'employee'


@app.route("/login")
def login():
    return render_template('Login.html')

@app.route("/goget")
def goget():
    return render_template('GetEmp.html')


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

@app.route("/getemp",methods=['Get','POST'])
def getemp():
    return render_template("GetEmp.html")

@app.route("/admin_page", methods=['GET', 'POST'])
def admin_page():
    if request.method == 'POST':
        user_name = request.form.get('username')
        passw = request.form.get('pass')
        if user_name == admin_name and passw == admin_pass:
            user = {
                'user': user_name,
                'Password': passw
            }
            session['user'] = user
            return redirect('/protected')
    return f"Access Denied"

@app.route("/protected")
def protected():
    try:
        user = session.get('user')
        if user:
            return render_template("AddEmp.html")
        else:
            return "Access denied."
    except Exception as e:
        return str(e)

@app.route("/fetchdata",methods=['Get','POST'])
def fetchdata():
         id=request.form['emp_id']
         query = "SELECT * FROM employee WHERE empid=%s"
         cursor=db_conn.cursor()
         cursor.execute(query,id )
         result = cursor.fetchone()
         return render_template("GetEmpOutput.html",id=result[0],fname=result[1],lname=result[2],interest=result[3],location=result[4],image_url=result[5])

@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            response = s3.put_object(
        Bucket=custombucket,
        Key=emp_image_file_name_in_s3,
            Body=emp_image_file,
            ACL='public-read'
        )
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)
            cursor.execute(insert_sql, (emp_id, first_name, last_name,  pri_skill, location, object_url))
            db_conn.commit()
        except Exception as e:
            return str(e)

    finally:
        cursor.close()
    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
