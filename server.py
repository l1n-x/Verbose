import socket
import sqlite3
import json
# import sys, os
host = socket.gethostbyname(socket.gethostname())
port = 9090
db = sqlite3.connect('/home/l1n_x/Python/Verbose/data/server.db')
cs = db.cursor()
clients = []
s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind((host,port))
print("Сервер запущен" + "\nIP: " + host + "\nPORT: " + str(port))
quit = False
while not quit:
    try:
        data, addr = s.recvfrom(1024)
        data = json.loads(data.decode("utf-8"))
        if data['msg'] == 'Online':
            clients.append(addr)
            print('Client ' + addr[0] + ' added!')
        elif data['msg'] == 'Offline':
            clients.remove(addr)
            print('Client ' + addr[0] + ' deleted!')
        elif data['type'] == 'Message':
            print("["+addr[0]+"]:["+str(addr[1])+"]",end="")
            print(data['msg'])
            for client in clients:
                try:
                    if addr != client:
                        s.sendto(bytes(json.dumps(data),'utf-8'),client)
                except:
                    pass
        elif data['type'] == 'Registration':
            is_archiving = 0
            address = addr[0] + ':' + str(addr[1])
            cs.execute('SELECT * FROM CodeForArchiving')
            if data['tel'][2:5] in cs.fetchall():
                is_archiving = 1
            cs.execute('INSERT INTO Users(phone,password,pubkey,first_name,last_name,location,\
                born,about,is_archiving,address) VALUES(?,?,?,?,?,?,?,?,?,?)',\
                (data['Phone'],data['Password'],data['Pubkey'],data['FName'],data['LName'],\
                data['Location'],data['Born'],data['About'],is_archiving,address))
            db.commit()
            temp = {
                'type':'Registration',
                'msg': 'Done,' + str(is_archiving)
            }
            s.sendto(bytes(json.dumps(temp),'utf-8'),addr)
        elif data['type'] == 'Login':
            pass
    except:
        print("\n[ Сервер остановлен ]")
        quit = True
db.close()
s.close()