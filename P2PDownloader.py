import socket
import threading
import sys
import time

from numpy import number
if(len(sys.argv) != 4):
    print("Need 4 arguments")
    sys.exit()
timestart = time.time()
num_blocks, file_size, ip1, port1, ip2, port2 = 0,0,0,0,0,0
def getMetadata(lastCall):
    if time.time() - lastCall < 1.25:
        global num_blocks, file_size, ip1, port1, ip2, port2
        return num_blocks, file_size, ip1, port1, ip2, port2
    print("sent datagram")
    serverName = sys.argv[2]
    serverPort = int(sys.argv[3])
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    getMessage = f"GET {sys.argv[1]}.torrent\n"
    clientSocket.sendto(getMessage.encode(), (serverName, serverPort))
    metaMessage, metaServer = clientSocket.recvfrom(2048)
    metaMessage = metaMessage.decode()
    arr = metaMessage.splitlines()
    num_blocks = int(arr[0][12:])
    file_size = int(arr[1][11:])
    ip1 = arr[2][5:]
    port1 = int(arr[3][7:])
    ip2 = arr[4][5:]
    port2 = int(arr[5][7:])
    return num_blocks, file_size, ip1, port1, ip2, port2
lastUdpCall = time.time()
num_blocks, file_size, ip1, port1, ip2, port2 = getMetadata(0)
print(num_blocks)



bytesread = [b""] * 6
def thread(ip, port, block_range, id):
    global bytesread
    print(block_range)
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpSocket.settimeout(2)
    tcpSocket.connect((ip, port))
    for block in range(block_range[0], block_range[1] + 1):
        print(f"Getting Block {block} on {id}")
        message = f"GET {sys.argv[1]}:{block}\n"
        tcpSocket.send(message.encode())
        header = ""
        while True:
            # try:
            if(len(header) > 6 and header.find("200 OK") == -1):
                print(header)
            response = tcpSocket.recv(1)
            # except:
            #     print("Timeout")
            #     header = ""
            #     tcpSocket.close()
            #     _,_,ip1,port1,ip2,port2 = getMetadata()
            #     tcpSocket.connect((ip1, port1)) if id == 1 else tcpSocket.connect((ip2, port2))
            #     response = tcpSocket.recv(1)

            header += response.decode()
            if(len(header) > 1 and response.decode() == "\n" and header[-2] == "\n"):
                    break
        lines = header.splitlines()
        if(not str.startswith(lines[0], "200")):
            tcpSocket.close()
            sys.exit()
        offset = int(lines[1][26:])
        length = int(lines[2][18:])
        # print("here")
        # print(id)
        # print(header)
        i = 0
        while i < length:
            try:
                bytesread[id-1] += tcpSocket.recv(1)
            except Exception as e: 
                print(e)
                print("timeout", id)
                tcpSocket.close()
                _,_,ip1,port1,ip2,port2 = getMetadata(time.time())
                tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if id == 1:
                    print(ip1, port1)
                    tcpSocket.connect((ip1, port1))
                else:
                    print(ip2, port2)
                    tcpSocket.connect((ip2, port2))
                tcpSocket.recv(i-1) if i > 0 else ()
            i += 1
        print(f"Finished {block} on {id}")
    tcpSocket.close()
    print(f"\033[1mTHREAD {id} DONE\033[0m")
    sys.exit()
thread1 = threading.Thread(target=thread, args=[ip1, port1, (0, int(num_blocks/5)), 1])
thread2 = threading.Thread(target=thread, args=[ip2, port2, (int(num_blocks/5)+1, int(2*num_blocks/5)), 2])

thread1.start()
thread2.start()

_,_,ip3,port3,ip4,port4 = getMetadata(lastUdpCall)

thread3 = threading.Thread(target=thread, args=[ip3, port3, (int(2*num_blocks/5)+1, int(3*num_blocks/5)), 3])
thread4 = threading.Thread(target=thread, args=[ip4, port4, (int(3*num_blocks/5)+1, int(4*num_blocks/5)), 4])

thread3.start()
thread4.start()

_,_,ip5,port5,ip6,port6 = getMetadata(lastUdpCall)

thread5 = threading.Thread(target=thread, args=[ip5, port5, (int(4*num_blocks/5)+1, int(num_blocks-1)), 5])
# thread6 = threading.Thread(target=thread, args=[ip6, port6, (int(5*num_blocks/6)+1, num_blocks-1), 6])

thread5.start()
# thread6.start()


thread1.join()
thread2.join()
thread3.join()
thread4.join()
thread5.join()
# thread6.join()
print("writing image")
image = open(sys.argv[1], "wb")
result = b""
for byte in bytesread:
    result += byte
image.write(result)
image.close()
print("Time Elapsed:", time.time() - timestart)
print(port1, port2, port3, port4, port5)