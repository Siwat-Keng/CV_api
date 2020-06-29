from aiohttp import web, ClientSession
from scipy.spatial.distance import cdist
import mysql.connector, numpy as np

routes = web.RouteTableDef()
# db = mysql.connector.connect(
#   host="",
#   user="",
#   password=""
# )
# cursor = db.cursor()
ENDPOINT_URL = 'http://161.200.92.135/projects/faceapi/detect'

def computeDist(responseDict, storeEmbeddings, storeLabels, DECISION_THRES=0.85):
    responseEmbedding = np.array([face['embedding'] for face in responseDict['faces']])
    if responseEmbedding.shape[0] > 0:
        dist2Store = cdist(responseEmbedding, storeEmbeddings)
        minIdx = np.argmin(dist2Store, axis=1)
        minDist = np.min(dist2Store, axis=1)

        for distIdx, dist in enumerate(minDist): 
            if dist <= DECISION_THRES:
                responseDict['faces'][distIdx]['label'] = storeLabels[minIdx[distIdx]]
            else: 
                responseDict['faces'][distIdx]['label'] = 'unknown'

        return responseDict
    else:
        return None

@routes.post('/check')
async def handle_post_check(request):
    return web.Response(text='OK') # TODO check

@routes.post('/register')
async def handle_post_register(request):
    reader = await request.multipart()
    filedata = None
    try:
        userID = request.headers['userID']
        domainName = request.headers['domainName']
        print('userID : {}\ndomainName : {}'.format(userID, domainName))
    except KeyError:
        return web.json_response({'status': 'ERR_INVALID_REQUEST',
        'message': 'Headers require userID and domainName.'})
    while True:
        part = await reader.next()
        if part is None:
            break   
        if part.filename:
            filedata = await part.read()
    if filedata is not None:
        async with ClientSession() as session:
            async with session.post(ENDPOINT_URL, data={'image':filedata}) as resp:
                if resp.status == 200: 
                    r = await resp.json()
                    # cursor.execute("") # TODO register + check if available
                    return web.json_response({'status': r['status']})
                else:
                    return web.json_response({'status': resp.status})
    else:
        return web.json_response({'status': 'ERR_INVALID_REQUEST',
        'message': 'No image found.'})

@routes.post('/update')
async def handle_post_update(request):
    reader = await request.multipart()
    filedata = None
    try:
        userID = request.headers['userID']
        domainName = request.headers['domainName']
        print('userID : {}\ndomainName : {}'.format(userID, domainName))
    except KeyError:
        return web.json_response({'status': 'ERR_INVALID_REQUEST',
        'message': 'Headers require userID and domainName.'})
    while True:
        part = await reader.next()
        if part is None:
            break   
        if part.filename:
            filedata = await part.read()
    if filedata is not None:
        async with ClientSession() as session:
            async with session.post(ENDPOINT_URL, data={'image':filedata}) as resp:
                if resp.status == 200: 
                    r = await resp.json()
                    # cursor.execute("") # TODO update + check if not available
                    return web.json_response({'status': r['status']})
                else:
                    return web.json_response({'status': resp.status})
    else:
        return web.json_response({'status': 'ERR_INVALID_REQUEST',
        'message': 'No image found.'})

@routes.delete('/delete')
async def handle_delete(request):
    return web.Response(text='OK')

app = web.Application()
app.add_routes(routes)
web.run_app(app)