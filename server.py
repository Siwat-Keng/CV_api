from aiohttp import web
import numpy as np
import cv2, aiohttp, json

routes = web.RouteTableDef()

@routes.post('/check')
async def handle_post_check(request):
    reader = await request.multipart()
    metadata = None
    filedata = None
    while True:
        part = await reader.next()
        if part is None:
            break   
        if part.filename is not None:
            filedata = cv2.imdecode(np.frombuffer(await part.read(), np.uint8), cv2.IMREAD_COLOR)
        else:
            metadata = await part.text()
    return web.Response(text='OK') # TODO check

@routes.post('/register')
async def handle_post_register(request):
    reader = await request.multipart()
    filedata = None
    while True:
        part = await reader.next()
        if part is None:
            break   
        if part.filename is not None:
            filedata = cv2.imdecode(np.frombuffer(await part.read(), np.uint8), cv2.IMREAD_COLOR)
    return web.Response(text='OK') # TODO register   

app = web.Application()
app.add_routes(routes)
web.run_app(app)