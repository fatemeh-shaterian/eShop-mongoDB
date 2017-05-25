#from celery.worker import request
from django.http import HttpResponse
from pymongo import MongoClient
import datetime
import pymongo

from django.http import HttpResponseRedirect
import math
import time
from django.template import Template, Context
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.http import Http404


client = MongoClient()
db = client.eshop

def htmlRender(html_name):
    fp = open(html_name)
    t = Template(fp.read())
    fp.close()
    html = t.render(Context())
    return HttpResponse(html)


def open_html(html_name):
    fp = open(html_name)
    t = Template(fp.read())
    fp.close()
    return t


def hello(request):
    return HttpResponse("Hello world")


@csrf_exempt
def signin(request):
    if request.method == 'POST':
        find2 = find_user(request.POST['userName'],request.POST['pass'])
        if find2 != False:
            find = str(find2['_id'])

            if is_admin(request.POST['userName']):
                request.session['is_admin'] = True
            else:
                request.session['is_admin'] = False

            request.session['member_id'] = find
            request.session['member_name'] = find2['name']
            request.session['member_uName'] = find2['username']
            return HttpResponseRedirect('/home/')
        else:
            t = open_html('template/signIn.html')
            message = HttpResponse(t.render(Context({'message': 'user name or pass is not correct!!'})))
    else:
        message = htmlRender('template/signIn.html')
    return message


@csrf_exempt
def signup(request):
    if request.method == 'POST':
        user = create_user(request.POST['name'],request.POST['userName'],request.POST['pass'])
        if user is None:
            t = open_html('template/signUp.html')
            html = t.render(Context({'message': 'User existing before!!'}))
        else:
            dbname=user['name']
           # id=user['_id']
            dbusername=user['username']
            dbpass=user['password']

            html = 'added user:  '  + dbname + " " + dbusername + " " + dbpass # just for test
            t = open_html('template/firstPage.html')
            html += t.render(Context({'message': 'Your account correctly added, for enter please sign in.'}))

    else:
        html = htmlRender('template/signUp.html')
    return HttpResponse(html)

def logout(request):
    try:
        del request.session['member_id']
        del request.session['member_name']
        del request.session['member_uName']
        del request.session['is_admin']
    except KeyError:
        return HttpResponse('error happens')
    return HttpResponseRedirect('/home/')

def date(request):
   # db = client.test_database
   now = datetime.datetime.now();
   uid=request.session.get('member_id')
   #html = "<html><body>It is now %s. </br>  %s</body></html>" % now %uid
   return HttpResponse(uid)


def home(request):
    #if request.session.get is None: #shoud be checked if session not defined
    if "member_id" not in request.session:
        fp = open('template/home.html')
        t = Template(fp.read())
        fp.close()
        html = t.render(Context({'className': 'class=behide ', 'classExit': 'class=behide ' }))
        return HttpResponse(html)
    #is customer
    name = request.session.get('member_name')
    uname = request.session.get('member_uName')
    isAdmin = request.session.get('is_admin')
    if isAdmin is False:
        fp = open('template/home.html')
        t = Template(fp.read())
        fp.close()
        html = t.render(Context({'name': name, 'username': uname , 'className': 'class=behide ' , 'notLogin': 'class=behide'}))
        return HttpResponse(html)
    #is admin
    fp = open('template/home.html')
    t = Template(fp.read())
    fp.close()
    listItem = get_all_products()

    html = t.render(Context({'name': name, 'username': uname , 'notLogin': 'class=behide', 'item_list': listItem }))
    return HttpResponse(html)


@csrf_exempt
def change_info(request):
    if request.method == 'POST':
        #new info submited
        id = request.session.get('member_id')
        name = request.POST['name']
        uname = request.session.get('member_uName')
        result = change_user_info(uname, name, request.POST['pass'])
        request.session['member_name'] = name
        html = "<html><body>It is now . %s</br> </body></html>" %result
        return HttpResponse(html)

        return HttpResponseRedirect('/home/')
    else:
        name = request.session.get('member_name')
        t = open_html('template/changeInfo.html')
        html = t.render(Context({'name':'value=%s' % name}))
    return HttpResponse(html)


@csrf_exempt
def creat_product (request):
    if request.method == 'POST':
        html = "<html><body>It is now . </br> </body></html>"
        pName = request.POST['productName']
        pType = request.POST['productType']
        pSubType = request.POST['productSubType']
        pBrand = request.POST['productBrand']
        counter = request.POST['counter']
        avaiablity = request.POST['productAvailability']
        price = request.POST['productPrice']
        num = request.POST['productNumber']
        fields = []
        i = 0
        while `i` != counter:
            fields.append({"fname":request.POST['inputName' + `(i+1)`], "fvalue" : request.POST['inputVal' + `(i+1)`]})
            i += 1
        add_product(pName,pType,pSubType,pBrand,num,price,avaiablity,fields)
        return HttpResponseRedirect('/home/')
    else:
        t = open_html('template/creat_product.html')
        html = t.render(Context())

    return HttpResponse(html)


@csrf_exempt
def simple_search_product (request):
    if request.method == 'POST':
        html = "<html><body>It is now . </br> </body></html>"
        pName = request.POST['pName']
        product = get_product(pName)
        field2 = {'hello': 'ghjkl', 'sdhfksd' : 'slkdfj'}
    return HttpResponse(product.get('name'))

@csrf_exempt
def edit_product_page (request):
    if request.method == 'POST':
        pName = request.POST['productName']
        product = get_product(pName)
        t = open_html('template/edit_product.html')
        message = HttpResponse(t.render(Context({'pname':product.get('name') , 'ptype':product.get('type') ,
                                                 'psubtype':product.get('subType'), 'pbrand':product.get('brand'),
                                                 'pnumber' : product.get('num') , 'pprice': product.get('price') ,
                                                 'fields' : product.get('fields') ,
                                                 'numberoffields': len(product.get('fields')) })))
        return HttpResponse(message)

@csrf_exempt
def edit_product(request):
    if request.method == 'POST':
        pName = request.POST['productName']
        pType = request.POST['productType']
        pSubType = request.POST['productSubType']
        pBrand = request.POST['productBrand']
        counter = request.POST['counter']
        avaiablity = request.POST['productAvailability']
        price = request.POST['productPrice']
        num = request.POST['productNumber']
        fields = []
        i = 0
        while `i` != counter:
            fields.append(
                {"fname": request.POST['inputName' + `(i + 1)`], "fvalue": request.POST['inputVal' + `(i + 1)`]})
            i += 1
        update_product(pName, pType, pSubType, pBrand, num, price, avaiablity, fields)
    return HttpResponseRedirect('/home/')



###################DATA BASE CONNECTION ###############


def create_user(nameu, usern, passw):
    lowerUserN = usern.lower()
    user = db.users.find_one({'username':lowerUserN})
    if user != None:
        return None
    db.users.insert_one({
        'name':nameu,
        'username':lowerUserN,
        'password':passw
    })
    user = db.users.find_one({'username':lowerUserN})
    return user



def find_user(enteredUserName , passw):
    lowerEn = enteredUserName.lower()

    user = db.users.find_one({'username': lowerEn, 'password' : passw })
    if user == None :
        return False
    else:
        return user
    ##RETURN USER ID OR FALSE


def is_admin(enteredUserName):
    lowerUserN = enteredUserName.lower()
    myUser = db.users.find_one({'username': lowerUserN, 'isAdmin': 'true'})

    if myUser is None:
        return False
    else:
        return True


def change_user_info(userName , name, password):

    user = db.users.find_one({'username': userName})
    user['name'] = name
    user['password'] = password
    db.users.update_one({'username': userName},{'$set': user})
    user2 = db.users.find_one({'username': userName})
    return user2['name']


def add_product(pName,pType,pSubType,pBrand,num,price,avaiablity,fields):
    db.products.insert_one({
        'name': pName,
        'type': pType,
        'subType': pSubType,
        'brand' : pBrand,
        'num' : num,
        'price' : price,
        'avaiability' : avaiablity,
        'fields' : fields
    })

def update_product(pName,pType,pSubType,pBrand,num,price,avaiablity,fields):

    product = db.products.find_one({'name': pName})
    product['type'] = pType
    product['subType'] = pSubType
    product['brand'] = pBrand
    product['num'] = num
    product['price'] = price
    product['avaiability'] = avaiablity
    product['fields'] = fields
    db.products.update_one({'name': pName}, {'$set': product})



def get_all_products():
    return db.products.find()


def get_product( name ):
    return db.products.find_one({'name': name})
