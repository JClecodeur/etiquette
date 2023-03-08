from fpdf import FPDF
import streamlit as st
import os
from PIL import Image
from datetime import datetime
from pdf2image import convert_from_bytes, convert_from_path
import pandas as pd
import csv

class PDF(FPDF):
    def redimAuto(self, image, centreX, centreY, wMax = 1000, hMax = 1000, redim = 0):
        try:
            r = (100+redim)/100
            with Image.open(image) as im:
                wImage, hImage = (im.size)
            X = (wMax / wImage) * r
            if X*hImage > hMax:
                X = (hMax / hImage) * r
            self.image(image, x = centreX - (wImage*X)/2, y = centreY - (hImage*X)/2, w = wImage*X)
            return (wImage*X, hImage*X)
        except Exception as e:
            print(e)
            return
    
def hex_to_rgb(hex):
  return tuple(int(hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))



#### Début de la page streamlit

# Configuration
st.set_page_config(
    page_title="Outil de création d'étiquettes",
    page_icon="🏷️",
    layout='wide',
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "App created by Jean CHABANOL-SEROUDE for MediaGraphic Group"
    }
)

st.title("Création d'étiquettes pour livraison conteneur")
st.write("-"*10)

cols = st.columns((10,1,7,1,6,1,6,1,6,1,8))

def load_products():
    global products
    # products = pd.read_csv("product.csv", header=None)[0].to_list()

    with open('product.csv', newline='') as f:
        reader = csv.reader(f)
        products = [i[0] for i in list(reader)]
    return

def update_products():
    global products
    with open("product.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows([[i] for i in products + [product]])

if 'products' not in globals():
    load_products()

with cols[0]:
    product = st.multiselect("Nom du produit :", options=['Autre'] + sorted(products), max_selections=1, default=(st.session_state['product'] if 'product' in st.session_state else 'Pure Banner 330 DG'))
    if product:
        product = product[0]
        if 'product' in st.session_state and product!='Autre':
                st.success("Produit ajouté à la liste !")
        if product=='Autre':
            product = st.text_input("Préciser :")
            disabled_product_button = (False if product else True)
            if st.button("Ajouter **définitivement** ce produit à la liste", disabled=disabled_product_button):
                if product not in products:
                    update_products()
                    load_products()
                    st.session_state['product'] = product
                    st.experimental_rerun()
                else:
                    st.warning("Produit déjà dans la liste !")
    else:
        product = ''

condit_options = [
    "0m90 x 5m",
    "1m60 x 50m",
    "2m50 x 50m",
    "3m20 x 50m",
    "5m00 x 50m",
    "Autre"
]
with cols[2]:
    laize = st.selectbox("Conditionnement :", options=condit_options, index=len(condit_options)-2)
    if laize=='Autre':
        laize = st.text_input("Préciser en respectant ce format :", placeholder="1m20 x 25m")
        # disabled_laize_button = (False if product else True)                
        # if st.button("Ajouter ces dimensions à la liste", disabled=disabled_laize_button):
        #     print("MAJ")

fire_options = [
    "Aucun",
    "Bs1-d0",
    "Bs2-d0",
    "M1",
    "M2",
    "Autre"
]
with cols[4]:
    fire = st.selectbox("Traitement feu :", options=fire_options, index=1)
    if fire=='Aucun':
        fire = None
    if fire=='Autre':
        fire = st.text_input("Préciser :", placeholder="Classé")

with cols[6]:
    date = st.date_input("Date d'arrivage :")
    container = st.text_input("Numéro de conteneur :", placeholder="C021")

with cols[8]:
    label_limit = st.number_input("Nombre d'étiquettes nécessaires :", value = 21)

company_options = ["MediaVision Blanc", "MediaPrint Blanc", "MediaFix Blanc", "MediaVision Noir", "MediaPrint Noir", "MediaFix Noir"]
with cols[10]:
    company = st.selectbox("Logo :", options=sorted(company_options, reverse=True)).lower().replace(" ", "_")
    background_color = hex_to_rgb(st.color_picker("Couleur de fond :", '#FFFFFF', label_visibility="visible"))

for i in range(1, 11, 2):
    with cols[i]:
        st.write("|")
        st.write("|")
        st.write("|")
        st.write("|")

label_text = "\n".join([i for i in [product, laize, fire, (f"{container} - " if container!="" else "") + date.strftime("%d/%m/%Y")] if i!=None and i!=""])

def create_label():
    global label_text
    global background_color
    global company
    global label_limit
    pdf = PDF(orientation='P', unit='mm', format='A4')
    #pdf.set_page_background(background_color)
    #pdf.set_fill_color(background_color)
    exec(f"pdf.set_fill_color{background_color}")
    pdf.add_page()
    pdf.set_font('Helvetica')
    pdf.set_margins(0,0)
    pdf.set_auto_page_break(True, margin=0)
    cell_height = 297/7
    cell_width = 210/3
    image_height = cell_height/3

    line_number = label_text.count("\n")+1

    pdf.set_xy(0,0)
    i = 0
    label_count = 0
    while label_count<label_limit:
        if pdf.get_y() > 230:
            pdf.add_page()
            i = 0
            pdf.set_xy(0,0)
        
        y = cell_height*i
        
        for j in range(3):
            x = cell_width*j
            pdf.rect(x=x, y=y,w=210/3, h=297/7, style='FD')
            pdf.redimAuto(f"logo/{company}.png", centreX=x+210/6, centreY=y+image_height/2, wMax = 210/3, hMax = 1000, redim = 0)
            pdf.set_xy(x=x, y=y+image_height)
            pdf.multi_cell(txt=label_text, w=(210/3), h=(cell_height-image_height)/line_number, border=False, new_x='RIGHT', new_y='TOP', align='C')
            label_count += 1
            if label_count >= label_limit:
                break
        i+=1
        
    return bytes(pdf.output())

# Mono étiquette en guise d'aperçu
def show_one_label():
    global label_text
    global background_color
    global company
    pdf = PDF(orientation='P', unit='mm', format=(210/3, 297/7))
    pdf.set_auto_page_break(False, margin=0)
    pdf.set_page_background(background_color)
    pdf.add_page()
    pdf.set_font('Helvetica')
    pdf.set_margins(0,0)
    cell_height = 297/7
    cell_width = 210/3
    image_height = cell_height/3
    pdf.set_xy(0,0)
    line_number = label_text.count("\n")+1
    pdf.redimAuto(f"logo/{company}.png", centreX=210/6, centreY=image_height/2, wMax = 210/3, hMax = 1000, redim = 0)
    pdf.set_xy(x=0, y=image_height)
    pdf.multi_cell(txt=label_text, w=(210/3), h=(cell_height-image_height)/line_number, border=False, align='C')
    st.image(convert_from_bytes(bytes(pdf.output())), width=350)


st.write("-"*10)

col1, col2, col3 = st.columns(3)

with col1:
    st.write(' ')

with col2:
    st.subheader("Aperçu :")
    show_one_label()
    st.download_button(label=f"Imprimer {label_limit} étiquettes", 
        data=create_label(),
        file_name="_".join(i for i in ["Etiquettes", container, product] if i!="") + ".pdf",
        mime='application/octet-stream')

with col3:
    st.write(' ')