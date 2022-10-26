from tkinter import *
from classes import *


if __name__ == '__main__':
    nome, porta = Login(1024, 768).start()
    interface = Chat(1024, 768, nome, porta).start()

