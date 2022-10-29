from distutils.command.upload import upload
from re import U
from tkinter import *
import socket
import time
import threading
from datetime import datetime
from tkinter import filedialog
from tkinter.filedialog import *
from tkinter.scrolledtext import ScrolledText
from turtle import up
from PIL import Image, ImageTk
import pygame
from moviepy.editor import *

class Chat:

    def __init__(self, largura, altura):
        #Informações do usuário
        self.name, self.port_tcp = Login(1024, 768).start()
        self.server_port_tcp = 50000
        self.server_port_udp = ('localhost', 50001)
        self.receive_n = 0
        self.ackseq =-1
        self.req = 0

        #Declarando as informações da janela
        self.window = Tk()
        self.window.title(f"Chat P2P de {self.name}")
        self.canva = Canvas(self.window, width = largura, height = altura)
        self.canva.grid(columnspan = 3)
        self.listImages = []
        self.createWidgets()

        #Conectando com o server
        self.connect_server()
        #Conectando com o outro usuário
        self.connect_p2p()

        #Thread para receber mensagens
        thread_get_message = threading.Thread(target=self.get_message, args=(), daemon=True)
        thread_get_message.start()

        #Thread UDP
        thread_get_message_udp = threading.Thread(target=self.get_message_udp, args=(), daemon=True)
        thread_get_message_udp.start()

    def createWidgets(self):
        #Declarando os widgets do chat
        self.txt_chat = ScrolledText(self.canva, border = 1, state=DISABLED)
        self.txt_chat.pack()
        self.txt_field = Entry(self.canva, width = 90, border = 1, bg = 'white')
        self.send_button = Button(self.canva, text = "Enviar", padx = 39, command = self.send)
        self.clean_button = Button(self.canva, text = "Limpar", padx = 38, command = self.clean)
        self.upload_button = Button(self.canva, text = "Arquivo", padx = 35, command = self.upload)
        self.window.bind('<Return>', self.send)
        
        
        #Posicionando os Widgets
        self.txt_chat.config(background = "#363636", foreground='white')
        self.txt_chat.grid(column = 0, row = 0, columnspan = 3)
        self.txt_field.grid(column = 0, row = 2, columnspan = 2)
        self.send_button.grid(column = 2, row = 1)
        self.clean_button.grid(column = 2, row = 2)
        self.upload_button.grid(column = 2, row = 3)
    
    def playSong(self):
        pygame.mixer.music.load(self.window.filename)
        pygame.mixer.music.play(loops=0)

    def playVideo(self):
        print(self.window.filename)
        video = VideoFileClip(self.window.filename)
        video.preview()
        pygame.quit() 
    
    def upload(self):
        global imagem
        global play_button
        global play_video_button

        self.window.filename = filedialog.askopenfilename(filetypes= (("png file",".png"), ("jpg file", ".jpg"),
                                                        ("svg file", ".svg"), ("bmp file", ".bmp"),
                                                        ("mp3 file", ".mp3"), ("mp4 file", ".mp4"),
                                                        ("wav file", ".wav"), ("mkv file", ".mkv"), 
                                                        ("gif file", "*.gif")))
        print(self.window.filename)
        nome_arquivo = self.window.filename.split('.')
        tipo_arquivo = nome_arquivo[len(nome_arquivo) - 1]

        #Pritando mensagem de arquivo enviado
        self.txt_chat.configure(state=NORMAL)
        current_time = "<" + datetime.now().strftime('%d/%m/%Y %H:%M') + "h" + "> "
        self.txt_chat.insert(END, current_time + self.name + ": " + '\n')
        self.show_archive(tipo_arquivo)

        self.txt_chat.configure(state=DISABLED)
     
        self.socket_udp.sendto(tipo_arquivo.encode('utf-8'), self.addr)

        #Enviando arquivos para o outro cliente
        with open(self.window.filename, 'rb') as file:
            data = file.read(1024)
            while data:
                self.socket_udp.sendto(data, self.addr)
                data = file.read(1024)    

        time.sleep(0.03)
        self.socket_udp.sendto("Envio Terminado".encode('utf-8'), self.addr)

    def show_archive(self, tipo_arquivo):
        #Caso o anexo seja uma imagem
        if(tipo_arquivo in ['jpg', 'jpeg', 'png', 'svg', 'bmp']):
            print("passei aqui")

            #Reduzindo o tamanho da imagem, caso necessario
            size = (self.txt_chat.winfo_width(), self.txt_chat.winfo_width())
            imagem = Image.open(self.window.filename)
            if(imagem.width > size[0]//2 or imagem.height > size[1]//2):
                nu = (imagem.width//(size[0]//2) if imagem.width//(size[0]//2) > imagem.height//(size[1]//2) else imagem.height//(size[1]//2))
                imagem = imagem.resize((imagem.width//nu,imagem.height//nu))
            
            #Printando a imagem na tela
            imagem = ImageTk.PhotoImage(imagem)
            self.txt_chat.image_create(END, image=imagem)
            self.txt_chat.insert(END, '\n')
            self.listImages.append(imagem)
        
        elif (tipo_arquivo in ['mp3', 'wav']):
            pygame.mixer.init()               
                    
            self.txt_chat.window_create(END, window=Button(self.window, text="Play Song", padx = 40, command=self.playSong))
            self.txt_chat.insert(END, '\n')

        elif (tipo_arquivo in ['mp4', 'mkv', 'gif']):
            
            pygame.init()

            self.txt_chat.window_create(END, window=Button(self.window, text="Play Video", padx = 40, command=self.playVideo))
            self.txt_chat.insert(END, '\n')
            print(tipo_arquivo)
        

    def clean(self):
        #Limpando tela de mensagens
        self.txt_chat.configure(state=NORMAL)
        self.txt_chat.delete("1.0", "end")
        self.txt_chat.configure(state=DISABLED)

    def send(self, event = None):
        self.text = self.txt_field.get()
        text_aux = self.text.replace(' ', '')

        #Impedindo o envio de mensagens vazias
        if text_aux != "":
            current_time = "<" + datetime.now().strftime('%d/%m/%Y %H:%M') + "h" + "> "
            self.txt_chat.configure(state=NORMAL)
            self.txt_chat.insert(END, current_time + self.name + ": " + self.text + '\n')
            self.txt_field.delete(0, END)
            self.txt_chat.configure(state=DISABLED)

            #Enviando a mensagem para o outro usuário
            try:
                self.client_p2p.send(self.text.encode('utf-8'))
            except:
                pass

    def receive(self, text):
        self.text_received = text + "\n"
        current_time = "<" + datetime.now().strftime('%d/%m/%Y %H:%M') + "h" + "> "
        self.txt_chat.configure(state=NORMAL)
        self.txt_chat.insert(END, current_time + self.text_received)
        self.txt_chat.configure(state=DISABLED)

    def connect_server(self):
        #Abrindo conexão com o server
        self.client_server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.client_server.bind(('localhost', self.port_tcp))
        self.client_server.connect(('localhost', self.server_port_tcp))
        self.client_server.send(self.name.encode('utf-8'))
        time.sleep(0.03)
        self.socket_udp = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.socket_udp.sendto("OI".encode('utf-8'), self.server_port_udp)

        #RECEBE DO SERVER OS DADOS DO OUTRO CLIENTE
        self.name_p2p = self.client_server.recv(1024).decode('utf-8')
        self.host_p2p = self.client_server.recv(1024).decode('utf-8')
        self.port_p2p = int(self.client_server.recv(1024).decode('utf-8'))
        addr_1 = int(self.client_server.recv(1024).decode('utf-8'))
        self.addr = ('localhost', addr_1)

        #Fechando conexão com o server
        self.client_server.close()

    def connect_p2p(self):
        #Abrindo uma conexão P2P com o outro cliente
        self.client_p2p = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.client_p2p.bind(('localhost', self.port_tcp))
        self.client_p2p.connect((self.host_p2p, self.port_p2p))
                
    def get_message(self):
        while True:
            try:
                #Recebendo mensagem
                self.msg_received = self.client_p2p.recv(1024).decode('utf-8')
                #print(self.name_p2p + ": " + self.msg_received)
                self.receive(self.name_p2p + ": " + self.msg_received)
            except:
                pass
    
    def get_message_udp(self):
        #Recenbendo o tipo de anexo e criando ele
        archive_type = self.socket_udp.recvfrom(1024)
        archive_name = f"ZapZap2 - {self.name_p2p} {self.receive_n}.{archive_type[0].decode('utf-8')}"

        #Loop para receber e escrever o anexo
        with open(archive_name, 'wb') as file:
            while True:
                msg_received = self.socket_udp.recvfrom(1024)

                if msg_received[0] != bytes("Envio Terminado", 'utf-8'):
                    file.write(msg_received[0])
                    self.ackseq=-1
                    self.req=0
                    messg=''
                    continue
                else:
                    break

                message=message.split('/r')
                checksumm = []
                checksumm.append(list(self.calculate_checksum(message[0].split())))
                checksumm.append(list(message[1]))
                sum = self.summ(checksumm)
                if ('0' not in sum) and (req==int(message[2])):
                    if self.req==0:
                        self.req=1
                        self.ackseq=0
                    else :
                        self.req=0
                        self.ackseq=1
                    messg+=message[0]
                    modifiedMessage = 'AK'+'/r'+'1011111010110100'+'/r'+message[2]
                    self.socket_udp.sendto(modifiedMessage.encode('utf-8'), self.addr)
                elif ('0' in sum) or (req!=int(message[2])):
                    modifiedMessage = 'AK'+'/r'+'1011111010110100'+'/r'+str(ackseq)
                    self.socket_udp.sendto(modifiedMessage.encode('utf-8'), self.addr)
            
            file.close()

        self.window.filename = archive_name
        self.receive_n += 1
        
        #Pritando o anexo e a mensagem de anexo enviado
        self.txt_chat.configure(state=NORMAL)
        current_time = "<" + datetime.now().strftime('%d/%m/%Y %H:%M') + "h" + "> "
        self.txt_chat.insert(END, current_time + self.name_p2p + ": " + '\n')

        self.show_archive(archive_type[0].decode('utf-8'))
    
        self.txt_chat.configure(state=DISABLED)

        #Chamando a funcao para poder pegar o proximo anexo
        self.get_message_udp()

    def start(self):
        self.window.mainloop()

    ##Implemation RDT3.0

    def binary_sum(self, f):  # To find sum of 16 bit words of a packet
        carry=0
        ss=[]
        for i in range(0,16,1):
            s=int(f[0][i])+int(f[1][i])+carry
            if s==0:
                ss.append('0')
            elif s==1:
                ss.append('1')
                if carry==1:
                    carry=0
            elif s==2:
                ss.append('0')
                carry=1
            elif s==3:
                ss.append('1')
                carry=1
        while(carry!=0):
            for i in range(0,16,1):
                s=int(ss[i])+carry
                if s==int(ss[i]):
                    break
                if s==1:
                    ss[i]='1'
                    if carry==1:
                        carry=0
                if s==2:
                    ss[i]='0'
                    carry=1
        return ss

    def packet_division(data, packet_size):  #Divide message into packets
        try:
            packets=[]
            reminder=int(len(data) % packet_size)
            number_of_packets=int(len(data)/packet_size)
            for i in range(number_of_packets):
                packets.append(list(data[(i*packet_size):(packet_size+(packet_size*i))]))
            rem = list(data[(number_of_packets*packet_size):(reminder+(packet_size*number_of_packets))])
            for i in range((5-len(rem))):
                rem.append(' ')
            packets.append(rem)
            return packets
        except Exception as e:
            print("Cant create packets")
            return []

    def firstcom(s):  #Find first complement
        for i in range(len(s)):
            if s[i]=='0':
                s[i]='1'
            elif s[i]=='1':
                s[i]='0'
        return s

    def calculate_checksum(self, f):   # Main function to find checksum of a packet
        sum=[['0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0']]
        count=0
        for  i in f:
            if len(i)==2:
                sum.append(self.Convert_to_bits(i))
                count+=1
        if count==2:
            s=list(sum[1:3])
            s = self.summ(s)
            s = self.firstcom(s)
            s=''.join(s)
            return(s)
        elif count==1:
            return(''.join(self.firstcom(sum[1])))
        else:
            return(''.join(self.firstcom(sum[0])))


    def packets_checksum(self, packets):  #start of checksum calculation
        try:
            s=[]
            Convert_to_bits=[]
            for i in range(len(packets)):
                    f=''.join(packets[i])
                    s.append(f.split())
                    Convert_to_bits.append(self.calculate_checksum(f.split()))
            return(Convert_to_bits)
        except Exception as e:
            print('cant do it')

    def create_packet(packet,Convert_to_bits,seq):
        f = ''.join(packet)+'/r'+Convert_to_bits+'/r'+str(seq)
        return(f)

    def rdt_send(self, data):
        packet_size=5
        packetss = self.packet_division(data,packet_size)
        print("Number of packets made",int(len(packetss)))
        Convert_to_bits=self.packets_checksum(packetss)
        sequence_number=0
        for i in range(len(packetss)):
            count=1
            timeoutflag=0
            message = self.create_packet(packetss[i],Convert_to_bits[i],sequence_number)
            print("Sending packet",i,"with checksum",str(Convert_to_bits[i]),"and sequence number",sequence_number)
            if sequence_number==1:
                sequence_number=0
            else:
                sequence_number=1
            self.socket_udp.sendto(message.encode(),self.addr)
            while True:
                try:
                    modifiedMessage, serverAddress = self.socket_udp.recvfrom(2048)
                    break
                except Exception as aa:
                    count+=1
                    if count==100000:
                        print("Timeout")
                        timeoutflag=1
                        break
            if timeoutflag==1:
                i-=1
                if sequence_number==1:
                    sequence_number=0
                else:
                    sequence_number=1
                continue
            modifiedMessage=modifiedMessage.decode()
            modifiedMessage= modifiedMessage.split('/r')
            s=[]
            s.append(list(str(modifiedMessage[1])))
            s.append(list('0100000101001011'))
            ff = self.summ(s)
            if ('0'  in ff) or (sequence_number==int(modifiedMessage[2])):
                i-=1
                if sequence_number==1:
                    sequence_number=0
                else:
                    sequence_number=1
            else:
                print("Acknowledgement of packet with sequence number",modifiedMessage[2],"received")
        message="/r/r"
        self.socket_udp.sendto(message.encode(),self.addr)
        return

class Login:

    def __init__(self, largura, altura):
        #Declarando as informações da janela
        self.window = Tk()
        self.window.title("Zap 2")
        self.canva = Canvas(self.window, width = largura, height = altura)
        self.canva.grid(columnspan = 3)
        self.createWidgets()

        self.text_nome = ""
        self.text_porta = ""

    def createWidgets(self):

        #Labels de nome e porta
        self.label1 = Label(self.canva, text="Nome: ", anchor = W)
        self.label2 = Label(self.canva, text="Porta TCP: ", anchor = W)
        #self.label4 = Label(self.canva, text="IP: ", anchor = W)

        #Declarando as áreas de Texto
        self.txt_name = Entry(self.canva, width = 85, border = 1, bg = 'white')
        self.txt_port_tcp = Entry(self.canva, width = 85, border = 1, bg = 'white')
        self.txt_port_udp = Entry(self.canva, width = 85, border = 1, bg = 'white')
        #self.txt_ip = Entry(self.canva, width = 85, border = 1, bg = 'white')   
   
        #Declarando o Botão
        self.send_button = Button(self.canva, text = "Enviar", padx = 40, command = self.send)  
        self.window.bind('<Return>', self.send)      
        
        #Posicionando os Widgets
        self.label1.grid(column = 0, row = 1, columnspan = 1)
        self.label2.grid(column = 0, row = 5, columnspan = 1)
        #self.label4.grid(column = 0, row = 7, columnspan = 1)
        self.txt_name.grid(column = 1 , row = 1, columnspan = 3)
        self.txt_port_tcp.grid(column = 1, row = 5, columnspan = 3)
        #self.txt_ip.grid(column = 1, row = 7, columnspan = 3)

        self.send_button.grid(column = 5, row = 1)

    def send(self, event = None):
        #Pegando as infromações de nome e porta e fechando a janela
        self.text_nome = self.txt_name.get()
        self.text_porta_tcp = int(self.txt_port_tcp.get())
        self.window.destroy()

    def start(self):
        self.window.mainloop()
        return self.text_nome, self.text_porta_tcp

class Server:
    def __init__(self):
        #Porta do server
        self.port_tcp = 50000
        self.port_udp = 50001

        #Criando socket TCP do server
        self.server_tcp = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.server_tcp.bind(('localhost', self.port_tcp))

        #Criando socket UDP do server
        self.server_udp = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.server_udp.bind(('localhost', self.port_udp))

        #Inicia o server
        self.start()

    #Aceita a conexão do cliente e recebe seus dados
    def accept_client(self):
        client, addr = self.server_tcp.accept()
        name = client.recv(1024).decode('utf-8')
        print("Nome: " + name)

        addr_pair = self.server_udp.recvfrom(1024)
        print("Addr: " + str(addr_pair[1]))
        command = addr_pair[0].decode('utf-8')
        address = addr_pair[1]

        client_list = [client, addr[0], addr[1], name, address[1]]

        return client_list

    #Envia os dados de um cliente ao outro
    def send_data(self, client_sender, client_reciever):
        client_reciever[0].sendall(client_sender[3].encode('utf-8'))
        time.sleep(0.03)
        client_reciever[0].sendall(client_sender[1].encode('utf-8'))
        time.sleep(0.03)
        client_reciever[0].sendall(str(client_sender[2]).encode('utf-8'))
        time.sleep(0.03)
        client_reciever[0].sendall(str(client_sender[4]).encode('utf-8'))
        print("Troca Concluída")

    def start(self):
        self.server_tcp.listen(2)
        self.client1 = self.accept_client()
        self.client2 = self.accept_client()

        #Troca os dados entre os clientes
        self.send_data(self.client1, self.client2)
        self.send_data(self.client2, self.client1)

        #Fecha a conexão do server
        self.server_tcp.close()
        self.server_udp.close()