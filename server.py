import os

from aiohttp import web

WS_FILE = os.path.join(os.path.dirname(__file__), "websocket.html")


async def wshandler(request: web.Request):
    resp = web.WebSocketResponse()
    available = resp.can_prepare(request)
    if not available:
        with open(WS_FILE, "rb") as fp:
            return web.Response(body=fp.read(), content_type="text/html")

    await resp.prepare(request)

    await resp.send_str("Welcome!!!")

    try:
        print("Someone joined.")
        for ws in request.app["sockets"]:
            await ws.send_str("Someone joined")
        request.app["sockets"].append(resp)

        async for msg in resp:
            if msg.type == web.WSMsgType.TEXT:
                for ws in request.app["sockets"]:
                    if ws is not resp:
                        await ws.send_str(msg.data)
            else:
                return resp
        return resp

    finally:
        request.app["sockets"].remove(resp)
        print("Someone disconnected.")
        for ws in request.app["sockets"]:
            await ws.send_str("Someone disconnected.")


# Принимает POST-запрос на создание новости и рассылает текст новости всем
# подключенным по websocket клиентам
async def post_news_handler(request: web.Request):
    data = await request.post()
    print("Received POST request: ")
    print(data['newstext'])

    # Рассылаем текст новости всем подключенным клиентам
    for ws in request.app["sockets"]:
        await ws.send_str(data['newstext'])

    return web.Response(text=data['newstext'])


async def on_shutdown(app: web.Application):
    for ws in app["sockets"]:
        await ws.close()


def init():
    app = web.Application()
    app["sockets"] = []
    app.add_routes([web.get('/', wshandler),
                    web.post('/news', post_news_handler)])
    app.on_shutdown.append(on_shutdown)  # on_shutdown опишем позже
    return app


web.run_app(init())
