from flask import Flask, render_template, request

name = 'Sejong'
app = Flask(name)
@app.route('/')
def student():
   return render_template('student.html')


@app.route('/result',methods = ['POST', 'GET'])
def result():
   if request.method == 'POST':
      result = request.form
      return render_template("result.html",result = result)


if name == 'main':
   app.run(debug = True)