import asyncio

port = 5554
ip = '127.0.0.1'

async def processar_mensagem(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    print(f"Recebido {message} de {addr}")
    print(f"Enviando resposta para {addr}")
    writer.write(data)
    await writer.drain()
    print("Fechando a conexão")
    writer.close()

async def iniciar_socket_middleware():
    server = await asyncio.start_server(processar_mensagem, ip, port)

    async with server:
        await server.serve_forever()



asyncio.run(iniciar_socket_middleware())