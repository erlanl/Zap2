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
import rdt3 as rdt

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
        self.canva.configure(background='#252331')

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
        thread_get_message_rdt = threading.Thread(target=self.get_message_rdt, args=(), daemon=True)
        thread_get_message_rdt.start()

    def createWidgets(self):
        #Declarando os widgets do chat
        self.txt_chat = ScrolledText(self.canva, border = 1, state=DISABLED)
        self.txt_chat.pack()
        self.txt_field = Entry(self.canva, width = 92, border = 1, bg = '#252331')
        self.send_button = Button(self.canva, text = "Enviar", width=14, command = self.send, background="#494758", foreground='white')
        self.clean_button = Button(self.canva, text = "Limpar", width=14, command = self.clean, background="#494758", foreground='white')
        self.upload_button = Button(self.canva, text = "Arquivo", width=14, command = self.upload, background="#494758", foreground='white')
        self.window.bind('<Return>', self.send)
        
        
        #Posicionando os Widgets
        self.txt_chat.config(background = "#252331", foreground='white')
        self.txt_chat.grid(column = 0, row = 0, columnspan = 3)
        self.txt_field.config(background = "#1e1d26", foreground='white')
        self.txt_field.grid(column = 0, row = 2)
        self.send_button.grid(column = 2, row = 1)
        self.clean_button.grid(column = 2, row = 2)
        self.upload_button.grid(column = 2, row = 3)
    
    def playSong(self):
        pygame.mixer.music.load(self.window.filename)
        pygame.mixer.music.play(loops=0)

    def stopSong(self):
        pygame.mixer.music.stop()

    def playVideo(self):
        print(self.window.filename)
        video = VideoFileClip(self.window.filename)
        video.preview()
        pygame.quit() 
    
    def upload(self):
        global imagem
        global play_button
        global play_video_button

        self.window.filename = filedialog.askopenfilename(filetypes= (("png files",".png"), 
                                                        ("jpg files", ".jpg"), ("svg files", ".svg"), 
                                                        ("bmp files", ".bmp"), ("mp3 files", ".mp3"), 
                                                        ("mp4 files", ".mp4"), ("wav files", ".wav"), 
                                                        ("mkv files", ".mkv"), ("gif files", "*.gif")))

        print(self.window.filename)
        #Separando o nome do arquivo em relação ao '.' e pegar o último elemento que é o tipo do arquivo
        nome_arquivo = self.window.filename.split('.')
        tipo_arquivo = nome_arquivo[len(nome_arquivo) - 1]

        #Pritando mensagem de arquivo enviado
        if(self.window.filename != ""):
            self.txt_chat.configure(state=NORMAL)

            #Mensagem com data, hora e nome de quem enviou
            current_time = "<" + datetime.now().strftime('%d/%m/%Y %H:%M') + "h" + "> "
            self.txt_chat.insert(END, current_time + self.name + ": " + '\n')

            #Colocando arquivo na tela
            self.show_archive(tipo_arquivo)

            self.txt_chat.configure(state=DISABLED)

            #Enviando tipo de arquivo para o outro cliente
            rdt.rdt_send(self.socket_udp_msg, self.addr_msg, tipo_arquivo.encode('utf-8'))

            #Lendo o arquivo e enviando bytes do arquivo para o outro cliente
            with open(self.window.filename, 'rb') as file:
                for data in file.readlines():
                    rdt.rdt_send(self.socket_udp_msg, self.addr_msg, data)
                    #time.sleep(0.03)
                    #self.socket_udp_msg.sendto(data, self.addr_msg)

            #Confirmandoo que o arquivo foi enviado 
            #self.socket_udp_msg.sendto("Envio Terminado".encode('utf-8'), self.addr_msg)
            rdt.rdt_send(self.socket_udp_msg, self.addr_msg, "Envio Terminado".encode('utf-8'))


    def show_archive(self, tipo_arquivo):
        #Caso o anexo seja uma imagem
        if(tipo_arquivo in ['jpg', 'png', 'svg', 'bmp']):

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
            self.txt_chat.window_create(END, window=Button(self.window, text="Stop Song", padx = 40, command=self.stopSong))
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

        #Socket para enviar mensagens e receber acks
        self.socket_udp_msg = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.socket_udp_msg.sendto("Mensagens".encode('utf-8'), self.server_port_udp)
        time.sleep(0.03)
        #Socket para enviar acks e receber mensagens
        self.socket_udp_acks = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.socket_udp_acks.sendto("ACKS".encode('utf-8'), self.server_port_udp)

        #RECEBE DO SERVER OS DADOS DO OUTRO CLIENTE
        self.name_p2p = self.client_server.recv(1024).decode('utf-8')
        self.host_p2p = self.client_server.recv(1024).decode('utf-8')
        self.port_p2p = int(self.client_server.recv(1024).decode('utf-8'))
        #Endereço para enviar acks
        addr_acks_1 = int(self.client_server.recv(1024).decode('utf-8'))
        self.addr_acks = ('localhost', addr_acks_1)
        #Endereço para enviar mensagens
        addr_msg_1 = int(self.client_server.recv(1024).decode('utf-8'))
        self.addr_msg = ('localhost', addr_msg_1)

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
    
    def get_message_rdt(self):
        #Recenbendo o tipo de anexo e criando ele
        archive_type = rdt.rdt_recv(self.socket_udp_acks, self.addr_acks, rdt.PAYLOAD)
        archive_name = f"ZapZap2 - {self.name_p2p} {self.receive_n}.{archive_type.decode('utf-8')}"

        #Loop para receber e escrever o anexo, para quando recebe o aviso que o envio foi enviado completamente
        with open(archive_name, 'wb') as file:
            while True:
                msg_received = rdt.rdt_recv(self.socket_udp_acks, self.addr_acks, rdt.PAYLOAD)

                if msg_received == bytes("Envio Terminado", 'utf-8'):
                    break
                else:
                    file.write(msg_received)

            file.close()

        self.window.filename = archive_name
        self.receive_n += 1

        #Pritando o anexo e a mensagem de anexo enviado
        self.txt_chat.configure(state=NORMAL)
        current_time = "<" + datetime.now().strftime('%d/%m/%Y %H:%M') + "h" + "> "
        self.txt_chat.insert(END, current_time + self.name_p2p + ": " + '\n')

        self.show_archive(archive_type.decode('utf-8'))

        self.txt_chat.configure(state=DISABLED)

        #Chamando a funcao para poder pegar o proximo anexo
        self.get_message_rdt()

    def start(self):
        self.window.mainloop()

class Login:

    def __init__(self, largura, altura):
        #Declarando as informações da janela
        self.window = Tk()
        self.window.title("Zap 2")
        self.canva = Canvas(self.window, width = largura, height = altura)
        self.canva.configure(background='#1e1d26')
        self.canva.grid(columnspan = 3)
        self.createWidgets()

        self.text_nome = ""
        self.text_porta = ""

    def createWidgets(self):

        #Labels de nome e porta
        self.label1 = Label(self.canva, text="Nome: ", anchor = W, width = 8, background="#1e1d26", foreground='white')
        self.label2 = Label(self.canva, text="Porta TCP: ", anchor = W, width = 8, background="#1e1d26", foreground='white')
        self.label3 = Label(self.canva, text="IP: ", anchor = W, width = 8, background="#1e1d26", foreground='white')

        #Declarando as áreas de Texto
        self.txt_name = Entry(self.canva, width = 75, border = 1, bg = '#252331', foreground='white')
        self.txt_port_tcp = Entry(self.canva, width = 75, border = 1, bg = '#252331', foreground='white')
        self.txt_port_udp = Entry(self.canva, width = 75, border = 1, bg = '#252331', foreground='white')
        self.txt_ip = Entry(self.canva, width = 75, border = 1, bg = '#252331', foreground='white')   
   
        #Declarando o Botão
        self.send_button = Button(self.canva, text = "Enviar", width=10, command = self.send, background="#494758", foreground='white')  
        self.window.bind('<Return>', self.send)      
        
        #Posicionando os Widgets
        self.label1.grid(column = 0, row = 1, columnspan = 1)
        self.label2.grid(column = 0, row = 5, columnspan = 1)
        self.label3.grid(column = 0, row = 6, columnspan = 1)
        self.txt_name.grid(column = 1 , row = 1, columnspan = 3)
        self.txt_port_tcp.grid(column = 1, row = 5, columnspan = 3)
        self.txt_ip.grid(column = 1, row = 6, columnspan = 3)

        self.send_button.grid(column = 5, row = 5)

    def send(self, event = None):
        #Pegando as infromações de nome e porta e fechando a janela
        self.text_nome = self.txt_name.get()
        self.text_porta_tcp = int(self.txt_port_tcp.get())
        self.window.destroy()

    def start(self):
        self.window.mainloop()
        return self.text_nome, self.text_porta_tcp