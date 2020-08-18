from aiohttp import web, ClientSession
from scipy.spatial.distance import cdist
from aiohttp_tokenauth import token_auth_middleware
from asyncio import get_event_loop
from aiomysql import connect
import numpy as np, json, jwt

# API route
routes = web.RouteTableDef()

# Database
DATABASE_NAME = 'testDB'
TABLE_NAME = 'testdata'
HOST = 'localhost'
USER = 'root'
PASSWORD = 'localhost'
PORT = 3306
SECRET = 'secret'

# Extract Feature
ENDPOINT_URL = 'http://161.200.92.135/projects/faceapi/detect'

# set up code
# cursor.execute("CREATE DATABASE {}".format(DATABASE_NAME))
# cursor.execute("CREATE TABLE {} (domainName VARCHAR(255), userID VARCHAR(255), embedding JSON)".format(TABLE_NAME))

async def init(loop):
    conn = await connect(host=HOST, port=PORT,
    user=USER, password=PASSWORD,
    db=DATABASE_NAME, loop=loop
    )

    # Require image(bytes), userID(string), domainName(string), thres(float)(Optional default = 0.85)
    @routes.post('/check')
    async def handle_post_check(request):
        # read request data
        reader = await request.multipart()
        filedata = None
        userID = None
        domainName = None
        decisionThres = 1.1
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
            if userID != request['user']['userID'] or domainName != request['user']['domainName']:
                return web.HTTPForbidden(text='Invalid Token')     
            async with conn.cursor() as cursor:
                stmt = 'SELECT embedding FROM {} WHERE domainName = %s AND userID = %s'.format(TABLE_NAME)
                value = (domainName, userID)
                await cursor.execute(stmt, value)
                result = await cursor.fetchone()
                await cursor.close() 
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
            if userID != request['user']['userID'] or domainName != request['user']['domainName']:
                return web.HTTPForbidden(text='Invalid Token') 
            async with conn.cursor() as cursor:       
                stmt = 'SELECT * FROM {} WHERE domainName = %s AND userID = %s'.format(TABLE_NAME)
                value = (domainName, userID)
                await cursor.execute(stmt, value)
                result = await cursor.fetchone()
                await cursor.close() 
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
                                    async with conn.cursor() as cursor:
                                        stmt = 'INSERT INTO {} (domainName, userID, embedding) VALUES (%s, %s, %s)'.format(TABLE_NAME)
                                        value = (domainName, userID, json.dumps(embedding))
                                        await cursor.execute(stmt, value)                   
                                        await conn.commit()  
                                        await cursor.close()
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
            if userID != request['user']['userID'] or domainName != request['user']['domainName']:
                return web.HTTPForbidden(text='Invalid Token')
            async with conn.cursor() as cursor:
                stmt = 'SELECT * FROM {} WHERE domainName = %s AND userID = %s'.format(TABLE_NAME)
                value = (domainName, userID)
                await cursor.execute(stmt, value)
                result = await cursor.fetchone()
                await cursor.close()
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
                                    async with conn.cursor() as cursor:
                                        stmt = 'UPDATE {} SET embedding = %s WHERE domainName = %s AND userID = %s'.format(TABLE_NAME)
                                        value = (json.dumps(embedding), domainName, userID)
                                        await cursor.execute(stmt, value)                   
                                        await conn.commit()   
                                        await cursor.close()  
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
            if userID != request['user']['userID'] or domainName != request['user']['domainName']:
                return web.HTTPForbidden(text='Invalid Token')
            async with conn.cursor() as cursor:
                stmt = 'SELECT * FROM {} WHERE domainName = %s AND userID = %s'.format(TABLE_NAME)
                value = (domainName, userID)
                await cursor.execute(stmt, value)
                result = await cursor.fetchone()  
                await cursor.close() 
                # check if account already registered 
                if result:
                    async with conn.cursor() as cursor:
                        stmt = 'DELETE FROM {} WHERE domainName = %s AND userID = %s'.format(TABLE_NAME)
                        value = (domainName, userID)
                        await cursor.execute(stmt, value)                   
                        await conn.commit()   
                        await cursor.close()     
                        return web.json_response({'status':'OK'})    
                # domainName + userID not found
                else:
                    return web.HTTPNotFound()
            # error occure return error message to client
        except Exception as err:
            return web.HTTPBadRequest(reason=str(err)) 


    async def user_loader(token: str):
        try:
            user = { k:v for k, v in jwt.decode(token, SECRET, algorithms=['HS256']).items() if k in ('userID', 'domainName') }
            if 'userID' not in user or 'domainName' not in user:
                user = None
        except:
            user = None
        finally:
            return user

    app = web.Application(middlewares=[token_auth_middleware(user_loader)])
    app.add_routes(routes)
    return app

if __name__ == '__main__':
    loop = get_event_loop()
    web.run_app(loop.run_until_complete(init(loop)))