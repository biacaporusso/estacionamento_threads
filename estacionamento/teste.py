import asyncio


vagas = '[(0, "abc"), (1, "def"), (2, None), (3, "jkl"), (4, "mno"), (5, "pqr"), (6, "stu"), (7, "vwx"), (8, "yz")]'

# AE 1
# total_vagas = 3
# vagas = [ (0, None), (1, None), (2, None) ]
# RV 1
# vagas = [ (0, "abc"), (1, None), (2, None) ]

vagas_livres = 0
temp = vagas.replace("[", "").replace("]", "").split(")")
for i in temp:
    if not i:
        continue
    var = i.replace("(", "").replace(",", "").split()
    #print(var)
    print(var[0], var[1])


# print(temp)

# for vaga in vagas:
#     if vaga[1] is None:
#         vagas_livres += 1
#     print(vaga)
# print(vagas_livres)


# port = 5554
# ip = '127.0.0.1'

# async def processar_mensagem(reader, writer):
#     data = await reader.read(100)
#     message = data.decode()
#     addr = writer.get_extra_info('peername')
#     print(f"Recebido {message} de {addr}")
#     print(f"Enviando resposta para {addr}")
#     writer.write(data)
#     await writer.drain()
#     print("Fechando a conexão")
#     writer.close()

# async def iniciar_socket_middleware():
#     server = await asyncio.start_server(processar_mensagem, ip, port)

#     async with server:
#         await server.serve_forever()



# asyncio.run(iniciar_socket_middleware())