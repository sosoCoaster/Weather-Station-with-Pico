# -*- coding: utf-8 -*-
"""
CHAREF Sohel - 5A AVM 2025-26
Programmation Microcontroleurs Python
TP 5 - Station Meteo avec la Pico" 
"""

import time
import board
import busio
import adafruit_ssd1306
import adafruit_dht

#Init DHT
dht = adafruit_dht.DHT11(board.GP21)

#Init Display
I2C_SCL = board.GP27
I2C_SDA = board.GP26
i2c = busio.I2C(I2C_SCL, I2C_SDA)
display_w = 128
display_h = 64
display = adafruit_ssd1306.SSD1306_I2C(display_w, display_h, i2c)

#Lecture DHT
def lire_capteur():
    return dht.temperature, dht.humidity

#Init comparaison pour rafraichissement seulement en cas de changement
old_tmp = 100
old_hum = 100
tmp_max, hum_max = lire_capteur()

#FIFO
N = 20; buf_temp = [None]*N; buf_hum = [None]*N; head_tmp = 0; size_tmp = 0; head_hum = 0; size_hum = 0
def push_tmp(v):
    global head_tmp, size_tmp
    buf_temp[(head_tmp + size_tmp) % N] = v
    if size_tmp < N: size_tmp += 1
    else: head_tmp = (head_tmp + 1) % N
def push_hum(v):
    global head_hum, size_hum
    buf_hum[(head_hum + size_hum) % N] = v
    if size_hum < N: size_hum += 1
    else: head_hum = (head_hum + 1) % N
def tmp_list(): # ordre ancien→récent
    return [buf_temp[(head_tmp+i)%N] for i in range(size_tmp)]
def hum_list(): # ordre ancien→récent
    return [buf_hum[(head_hum+i)%N] for i in range(size_hum)]


#Dessine une goute de 7*9 selon le point en bas a gauche
def dessine_goute(xGauche,yBas):
    #Ligne Bas
    for x in range(xGauche+3, xGauche+6):
        display.pixel(x,yBas,1)
    #Ligne Bas - 1
    for x in range(xGauche+2, xGauche+7):
        display.pixel(x,yBas-1,1)
    #Monter de la goutte
    i = 0
    for y in range(2,8):
        for x in range(xGauche+1+i,xGauche+8-i):
            display.pixel(x,yBas-y,1)
        if(y%2 == 1):
            i = i+1
    #Haut de la goutte
    display.pixel(xGauche+4,yBas-8,1)

#Dessine thermometre de 4*8 selon le point en bas a gauche
def dessine_thermo(xGauche,yBas):
    #Base du thermomettre
    for x in range(xGauche, xGauche+4):
        display.pixel(x,yBas,1)
        display.pixel(x,yBas-2,1)
    display.pixel(xGauche,yBas-1,1)
    display.pixel(xGauche+3,yBas-1,1)
    #Haut du thermometre
    for y in range(2,8):
        display.pixel(xGauche+1,yBas-y,1)
        display.pixel(xGauche+2,yBas-y,1)

#Affichage Temperature / Humiditer
def afficher_text():
    #Dessine texte
    capteur = lire_capteur()
    display.text("Temp : "+str(capteur[0])+" C",30,21,1)
    display.text("Hum : "+str(capteur[1])+" %",30,37,1)
    #Dessine goute
    dessine_goute(15,45)
    #Dessine Thermo
    dessine_thermo(18,29)
    #Dessine Rectangle
    display.rect(10, 16, 110, 34, 1)

def afficher_courbe():
    global display_h, display_w
    #Cherchons la liste
    list_tmp = tmp_list()
    list_hum = hum_list()
    #valeur max et min
    tmp_min = min(list_tmp)
    tmp_max = max(list_tmp)
    hum_min = min(list_hum)
    hum_min = min(list_hum)
    
    #Courbe temperature en haut
    for i in range(0,len(list_tmp)):
        if(tmp_max-tmp_min == 0):
            #Protection division par 0, met le graph a moitier de hauteur
            list_tmp[i] = 0.5
        else:
            #normalisation
            list_tmp[i] = float(list_tmp[i]-tmp_min)/float(tmp_max-tmp_min)
            #Anticipation pour affichage correcte (avoir le max en haut et le min en bas)
            list_tmp[i] = (list_tmp[i]-1)*(-1)
        #Dessine ligne
        if(i > 0):
            x = int(display_w)*(float(i-1)/20.0)
            y = (int(display_h)*(float(list_tmp[i-1])))/5
            x1 = int(display_w)*(float(i)/20.0)
            y1 = (int(display_h)*(float(list_tmp[i])))/5
            display.line(int(x),int(y),int(x1),int(y1),1)
            
    #Courbe humiditer en bas
    for i in range(0,len(list_hum)):
        if(hum_max-hum_min == 0):
            #Protection division par 0, met le graph a moitier de hauteur
            list_hum[i] = 0.5
        else:
            #normalisation
            list_hum[i] = float(list_hum[i]-hum_min)/float(hum_max-hum_min)
            #Anticipation pour affichage correcte (avoir le max en haut et le min en bas)
            list_hum[i] = (list_tmp[i]-1)*(-1)
        #Dessine ligne
        if(i > 0):
            x = int(display_w)*(float(i-1)/20.0)
            y = (int(display_h)*(float(list_hum[i-1])))/5+(display_h*4/5)
            x1 = int(display_w)*(float(i)/20.0)
            y1 = (int(display_h)*(float(list_hum[i])))/5+(display_h*4/5)
            display.line(int(x),int(y),int(x1),int(y1),1)

while True:
    #Rafraichissement seulement si Température ou Humiditer a changer
    if((old_tmp != dht.temperature) or (old_hum != dht.humidity)):
        display.fill(0)
        #affichage text
        afficher_text()
        #Gestion du graphique
        push_tmp(dht.temperature)
        push_hum(dht.humidity)
        afficher_courbe()
        #Stock les valeurs actuels pour prochaines comparaison
        old_tmp = dht.temperature
        old_hum = dht.humidity
        display.show()
    time.sleep(2)