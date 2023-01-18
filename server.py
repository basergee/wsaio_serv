import os

from aiohttp import web

WS_FILE = os.path.join(os.path.dirname(__file__), "index.html")


async def index_page_handler(request: web.Request):
    with open(WS_FILE, "rb") as fp:
        return web.Response(body=fp.read(), content_type="text/html")


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


# Поддерживает соединение
async def websocket_handler(request: web.Request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    try:
        # Сохраним новое соединение, чтобы была возможность рассылать новости
        request.app["sockets"].append(ws)

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
                else:
                    # Любую строку отправляем назад. Это сделано для проверки
                    # соединения между клиентом и сервером.
                    await ws.send_str(msg.data)
            elif msg.type == web.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      ws.exception())

        print('websocket connection closed')

        return ws
    finally:
        # в случае ошибки удаляем вновь добавленное соединение
        request.app["sockets"].remove(ws)


async def on_shutdown(app: web.Application):
    for ws in app["sockets"]:
        await ws.close()


def init():
    app = web.Application()
    app["sockets"] = []
    app.add_routes([web.get('/', index_page_handler),
                    web.post('/news', post_news_handler),
                    web.get("/ws", websocket_handler)])
    app.on_shutdown.append(on_shutdown)  # on_shutdown опишем позже
    return app


web.run_app(init())
