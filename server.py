from aiohttp import web, ClientSession
from scipy.spatial.distance import cdist
import mysql.connector, numpy as np, json

# API route
routes = web.RouteTableDef()

# Database
DATABASE_NAME = 'testDB' # param 
TABLE_NAME = 'testdata' # param 
db = mysql.connector.connect(
  host="localhost", # param 
  user="root", # param 
  password="localhost", # param 
  database=DATABASE_NAME
)
cursor = db.cursor()

# Extract Feature
ENDPOINT_URL = 'http://161.200.92.135/projects/faceapi/detect'

# set up code (first use)
# cursor.execute("CREATE DATABASE {}".format(DATABASE_NAME))
# cursor.execute("CREATE TABLE {} (domainName VARCHAR(255), userID VARCHAR(255), embedding JSON)".format(TABLE_NAME))

# Require image(bytes), userID(string), domainName(string), thres(float)(Optional default = 0.85)
@routes.post('/check')
async def handle_post_check(request):
    # read request data
    reader = await request.multipart()
    filedata = None
    userID = None
    domainName = None
    decisionThres = 0.85
    # read all parts
    while True:
        part = await reader.next()
        if part is None: # all parts are read
            break
        if part.name == 'image':
            filedata = await part.read()
        elif part.name == 'userID':
            userID = await part.text()
        elif part.name == 'domainName':
            domainName = await part.text()
        elif part.name == 'thres':
           decisionThres = float(await part.text())
    # check requirements
    if filedata is None or not userID or not domainName:
        return web.HTTPBadRequest(reason='Require image, userID and domainName.')
    else:
        check = "SELECT embedding FROM {} WHERE domainName = %s AND userID = %s".format(TABLE_NAME)
        cursor.execute(check, (domainName, userID))
        result = cursor.fetchone()
        # check if account already registered
        if result:
            result = np.array([json.loads(result[0])])
            async with ClientSession() as session:
                async with session.post(ENDPOINT_URL, data={'image':filedata}) as resp:
                    # check if API status_code is 200
                    if resp.status == 200: 
                        r = await resp.json()
                        # check if API can not progress
                        if r['status'] != 'OK':               
                            return web.HTTPBadRequest(reason='API Error')  
                        # check number of faces
                        elif len(r['faces']) >= 1:
                            embeddings = np.array([face['embedding'] for face in r['faces']])
                            dist2Store = cdist(embeddings, result)
                            minDist = np.min(dist2Store, axis=0)[0] # closest match
                            if minDist <= decisionThres: # atleast one face
                                return web.json_response({'result': True}) 
                            return web.json_response({'result': False}) 
                        # number of faces are not valid(0)
                        else:
                            return web.HTTPBadRequest(reason='{} faces found.'.format(len(r['faces'])))    
                    # API downed         
                    else:
                        return web.HTTPBadRequest(reason='API status : {}'.format(resp.status))  
        # domainName + userID are invalid                                                                 
        else:
            return web.HTTPNotFound()

# Require image(bytes), userID(string), domainName(string)
@routes.post('/register')
async def handle_post_register(request):
    # read request data
    reader = await request.multipart()
    filedata = None
    userID = None
    domainName = None
    # read all parts
    while True:
        part = await reader.next()
        if part is None: # all parts are read
            break
        if part.name == 'image':
            filedata = await part.read()
        elif part.name == 'userID':
            userID = await part.text()
        elif part.name == 'domainName':
            domainName = await part.text()
    # check requirements
    if filedata is None or not userID or not domainName:
        return web.HTTPBadRequest(reason='Require image, userID and domainName.')
    else:
        check = "SELECT * FROM {} WHERE domainName = %s AND userID = %s".format(TABLE_NAME)
        cursor.execute(check, (domainName, userID))
        result = cursor.fetchone()
        # check if account is not yet registered
        if not result:
            async with ClientSession() as session:
                async with session.post(ENDPOINT_URL, data={'image':filedata}) as resp:
                    # check if API status_code is 200
                    if resp.status == 200: 
                        r = await resp.json()
                        # check if API can not progress
                        if r['status'] != 'OK':
                            return web.HTTPBadRequest(reason='API Error')  
                        # check number of faces(only 1 face can be registered)
                        elif len(r['faces']) == 1:
                            embedding = r['faces'][0]['embedding']
                            sql = "INSERT INTO {} (domainName, userID, embedding) VALUES (%s, %s, %s)".format(TABLE_NAME)
                            val = (domainName, userID, json.dumps(embedding))
                            cursor.execute(sql, val)                   
                            db.commit()     
                            return web.json_response({'status': 'OK'})
                        # number of faces are not valid(not equal 1)
                        else:
                            return web.HTTPBadRequest(reason='{} faces found.'.format(len(r['faces'])))
                    # API downed 
                    else:
                        return web.HTTPBadRequest(reason='API status : {}'.format(resp.status))       
        # domainName + userID found   
        else:
            return web.HTTPBadRequest(reason='already registered')

# Require image(bytes), userID(string), domainName(string)
@routes.post('/update')
async def handle_post_update(request):
    # read request data
    reader = await request.multipart()
    filedata = None
    userID = None
    domainName = None
    # read all parts
    while True:
        part = await reader.next()
        if part is None: # all parts are read
            break
        if part.name == 'image':
            filedata = await part.read()
        elif part.name == 'userID':
            userID = await part.text()
        elif part.name == 'domainName':
            domainName = await part.text()
    # check requirements
    if filedata is None or not userID or not domainName:
        return web.HTTPBadRequest(reason='Require image, userID and domainName.')
    else:
        check = "SELECT * FROM {} WHERE domainName = %s AND userID = %s".format(TABLE_NAME)
        cursor.execute(check, (domainName, userID))
        result = cursor.fetchone()
        # check if account already registered
        if result:
            async with ClientSession() as session:
                async with session.post(ENDPOINT_URL, data={'image':filedata}) as resp:
                    # check if API status_code is 200
                    if resp.status == 200: 
                        r = await resp.json()
                        # check if API can not progress
                        if r['status'] != 'OK':
                            return web.HTTPBadRequest(reason='API Error')  
                        # check number of faces(only 1 face can be updated)
                        elif len(r['faces']) == 1:
                            embedding = r['faces'][0]['embedding']
                            sql = "UPDATE {} SET embedding = %s WHERE domainName = %s AND userID = %s".format(TABLE_NAME)
                            val = (json.dumps(embedding), domainName, userID)
                            cursor.execute(sql, val)                   
                            db.commit()     
                            return web.json_response({'status': 'OK'})
                        # number of faces are not valid(not equal 1)
                        else:
                            return web.HTTPBadRequest(reason='{} faces found.'.format(len(r['faces'])))
                    # API downed 
                    else:
                        return web.HTTPBadRequest(reason='API status : {}'.format(resp.status)) 
        # domainName + userID not found             
        else:
            return web.HTTPNotFound()

# Require json userID(string), domainName(string)
@routes.delete('/delete')
async def handle_delete(request):
    try:
        # read request data to json
        js = await request.json()
        userID = js['userID']
        domainName = js['domainName']
        check = "SELECT * FROM {} WHERE domainName = %s AND userID = %s".format(TABLE_NAME)
        cursor.execute(check, (domainName, userID))
        result = cursor.fetchone()   
        # check if account already registered 
        if result:
            sql = "DELETE FROM {} WHERE domainName = %s AND userID = %s".format(TABLE_NAME)
            val = (domainName, userID)
            cursor.execute(sql, val)                   
            db.commit()        
            return web.json_response({'status':'OK'})    
        # domainName + userID not found
        else:
            return web.HTTPNotFound()
    # error occure return error message to client
    except Exception as err:
        return web.HTTPBadRequest(reason=str(err)) 

# Require json userID(string), domainName(string)
@routes.get('/register')
async def handle_get_register(request):
    js = await request.json()
    userID = js['userID']
    domainName = js['domainName']
    check = "SELECT * FROM {} WHERE domainName = %s AND userID = %s".format(TABLE_NAME)
    cursor.execute(check, (domainName, userID))
    result = cursor.fetchone()   
    # check if account already registered 
    if result:
        return web.json_response({'status':'OK'})
    else:
        return web.json_response({'status':'Not Found'})

app = web.Application()
app.add_routes(routes)
web.run_app(app)