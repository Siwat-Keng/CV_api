from aiohttp import web, MultipartReader, ClientSession
from scipy.spatial.distance import cdist
import mysql.connector, numpy as np, json

routes = web.RouteTableDef()
DATABASE_NAME = 'testDB' # param 
TABLE_NAME = 'testdata' # param 
db = mysql.connector.connect(
  host="localhost", # param 
  user="root", # param 
  password="localhost", # param 
  database=DATABASE_NAME
)
cursor = db.cursor()
ENDPOINT_URL = 'http://161.200.92.135/projects/faceapi/detect'

# set up code (first use)
# cursor.execute("CREATE DATABASE {}".format(DATABASE_NAME))
# cursor.execute("CREATE TABLE {} (domainName VARCHAR(255), userID VARCHAR(255), embedding JSON)".format(TABLE_NAME))

@routes.post('/check')
async def handle_post_check(request):
    reader = await request.multipart()
    filedata = None
    userID = None
    domainName = None
    decisionThres = 0.85
    while True:
        part = await reader.next()
        if part is None:
            break
        if part.name == 'image':
            filedata = await part.read()
        elif part.name == 'userID':
            userID = await part.text()
        elif part.name == 'domainName':
            domainName = await part.text()
        elif part.name == 'thres':
           decisionThres = int(await part.text())
    if filedata is None or not userID or not domainName:
        return web.HTTPBadRequest(reason='Require image, userID and domainName.')
    else:
        regCheck = "SELECT embedding FROM {} WHERE domainName = %s AND userID = %s".format(TABLE_NAME)
        cursor.execute(regCheck, (domainName, userID))
        result = cursor.fetchone()
        if result:
            result = np.array([json.loads(result[0])])
            async with ClientSession() as session:
                async with session.post(ENDPOINT_URL, data={'image':filedata}) as resp:
                    if resp.status == 200: 
                        r = await resp.json()
                        if r['status'] != 'OK':               
                            return web.HTTPBadRequest(reason='API Error')  
                        elif len(r['faces']) == 1:
                            embedding = np.array([r['faces'][0]['embedding']])
                            return web.json_response({'result': str(np.min(cdist(embedding, result), axis=1)[0] <= decisionThres)})    
                        else:
                            return web.HTTPBadRequest(reason='{} faces found.'.format(len(r['faces'])))             
                    else:
                        return web.HTTPBadRequest(reason='API status : {}'.format(resp.status))                                                                   
        else:
            return web.HTTPNotFound()

@routes.post('/register')
async def handle_post_register(request):
    reader = await request.multipart()
    filedata = None
    userID = None
    domainName = None
    while True:
        part = await reader.next()
        if part is None:
            break
        if part.name == 'image':
            filedata = await part.read()
        elif part.name == 'userID':
            userID = await part.text()
        elif part.name == 'domainName':
            domainName = await part.text()
    if filedata is None or not userID or not domainName:
        return web.HTTPBadRequest(reason='Require image, userID and domainName.')
    else:
        regCheck = "SELECT * FROM {} WHERE domainName = %s AND userID = %s".format(TABLE_NAME)
        cursor.execute(regCheck, (domainName, userID))
        result = cursor.fetchone()
        if not result:
            async with ClientSession() as session:
                async with session.post(ENDPOINT_URL, data={'image':filedata}) as resp:
                    if resp.status == 200: 
                        r = await resp.json()
                        if r['status'] != 'OK':
                            return web.HTTPBadRequest(reason='API Error')  
                        elif len(r['faces']) == 1:
                            embedding = r['faces'][0]['embedding']
                            sql = "INSERT INTO {} (domainName, userID, embedding) VALUES (%s, %s, %s)".format(TABLE_NAME)
                            val = (domainName, userID, json.dumps(embedding))
                            cursor.execute(sql, val)                   
                            db.commit()     
                            return web.json_response({'status': r['status']})
                        else:
                            return web.HTTPBadRequest(reason='{} faces found.'.format(len(r['faces'])))
                    else:
                        return web.HTTPBadRequest(reason='API status : {}'.format(resp.status))           
        else:
            return web.HTTPBadRequest(reason='already registered')


@routes.post('/update')
async def handle_post_update(request):
    reader = await request.multipart()
    filedata = None
    userID = None
    domainName = None
    while True:
        part = await reader.next()
        if part is None:
            break
        if part.name == 'image':
            filedata = await part.read()
        elif part.name == 'userID':
            userID = await part.text()
        elif part.name == 'domainName':
            domainName = await part.text()
    if filedata is None or not userID or not domainName:
        return web.json_response({'status': 'ERR_INVALID_REQUEST',
        'message': 'Require image, userID and domainName.'})
    else:
        async with ClientSession() as session:
            async with session.post(ENDPOINT_URL, data={'image':filedata}) as resp:
                if resp.status == 200: 
                    r = await resp.json()
                    # cursor.execute("") # TODO update + check if not available
                    return web.json_response({'status': r['status']})
                else:
                    return web.json_response({'status': resp.status})

@routes.delete('/delete')
async def handle_delete(request):
    return web.Response(text='OK')

app = web.Application()
app.add_routes(routes)
web.run_app(app)