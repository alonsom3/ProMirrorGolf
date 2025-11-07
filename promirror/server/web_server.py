"""
Local Web Server for 3D Viewer
"""
from aiohttp import web
import aiofiles
import logging

logger = logging.getLogger(__name__)


async def handle_index(request):
    async with aiofiles.open('./viewer/index.html', 'r') as f:
        content = await f.read()
    return web.Response(text=content, content_type='text/html')


async def handle_css(request):
    async with aiofiles.open('./viewer/css/styles.css', 'r') as f:
        content = await f.read()
    return web.Response(text=content, content_type='text/css')


async def handle_js(request):
    filename = request.match_info['filename']
    async with aiofiles.open(f'./viewer/js/{filename}', 'r') as f:
        content = await f.read()
    return web.Response(text=content, content_type='application/javascript')


async def start_server(port=8080):
    app = web.Application()
    
    app.router.add_get('/', handle_index)
    app.router.add_get('/css/styles.css', handle_css)
    app.router.add_get('/js/{filename}', handle_js)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, 'localhost', port)
    await site.start()
    
    logger.info(f"Web server started: http://localhost:{port}")