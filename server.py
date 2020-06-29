from aiohttp import web
import aiohttp, mysql.connector

routes = web.RouteTableDef()
# db = mysql.connector.connect(
#   host="",
#   user="",
#   password=""
# )
# cursor = db.cursor()
ENDPOINT_URL = 'http://161.200.92.135/projects/faceapi/detect'

@routes.post('/check')
async def handle_post_check(request):
    return web.Response(text='OK') # TODO check

@routes.post('/register')
async def handle_post_register(request):
    reader = await request.multipart()
    filedata = None
    userID = request.headers['userID']
    domainName = request.headers['domainName']
    print('userID : {}\ndomainName : {}'.format(userID, domainName))
    while True:
        part = await reader.next()
        if part is None:
            break   
        if part.filename:
            filedata = await part.read()
    if filedata is not None:
        async with aiohttp.ClientSession() as session:
            async with session.post(ENDPOINT_URL, data={'image':filedata}) as resp:    
                r = await resp.json()
                # cursor.execute("")
                return web.json_response(r) # TODO register 
    else:
        return web.Response(text='Input Error')

@routes.post('/update')
async def handle_post_update(request):
    return web.Response(text='OK') # TODO update      

@routes.delete('/delete')
async def handle_delete(request):
    return web.Response(text='OK')

app = web.Application()
app.add_routes(routes)
web.run_app(app)