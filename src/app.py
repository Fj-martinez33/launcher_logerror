import pandas as pd
import numpy as np

import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import date #Para calendario interactivo.
from pickle import load

#Antes mostraba la fecha de hoy, pero si el modelo solo puede predecir fechas anteriores a 2017 da error. Lo cambio.
calendar = date(2016,1,15)

#Codificación de zonas: Los Angeles.
cods_zone_LA = [
    "R1-1: Residencial unifamiliar, altura máxima de 45 pies",
    "R2-1: Residencial de dos familias, altura máxima de 45 pies",
    "R3-1: Residencial multifamiliar de alta densidad, altura máxima de 45 pies",
    "C1-1: Comercial de vecindario, altura máxima de 45 pies",
    "C2-1: Comercial general, altura máxima de 45 pies",
    "M1-1: Industrial ligero, altura máxima de 45 pies",
    "M2-1: Industrial pesado, altura máxima de 45 pies",
    "A1-1: Agricultura general, altura máxima de 45 pies",
    "A2-1: Agricultura intensiva, altura máxima de 45 pies",
    "Q1-1: Cuidador de parques, altura máxima de 45 pies"
]
#Carga del modelo
model = load(open("../src/models/ensemble.sav", "rb"))

#CONFIG    
st.set_page_config(
    page_title = "LogError Predictor", #Titulo de la pestaña
    #page_icon = favicon
    layout="wide"
)

#CSS
st.markdown("""
    <style>
    
        [data-testid="stAppViewContainer"] {
            background-color: #2E2E2E;
        }
    
        /*Header Nativo*/
        .st-emotion-cache-h4xjwg{
            display: None;
        }
        
        /* Elimino el padding para evitar el scrolling */
        .block-container {
            padding: 0 !important;
        }
        
        /* Sidebar */
        .st-emotion-cache-zlnqiy {
            background-color: #A8A29E;
            border-radius: 20px;
            border-style: hidden;
            padding: 50px;
            margin-left: 25px;
        }
        
        /*Main*/
        .st-emotion-cache-4ih3hc {
            background-color: #A8A29E;
            border-radius: 20px;
            border-style: hidden;
            padding: 50px;
            margin: 0px 25px 0px 0px;
        }
        
        /*Footer y Header*/
        .st-emotion-cache-132j0fg {
            background-color: #A8A29E;
            border-radius: 15px;
            border-style: hidden;
            padding: 10px;
            text-align: center;
            margin: 0px  25px 0px 25px;
        }
        
        
        #model-name {
            padding-bottom: 10 px;
        }
        
        /*text*/
        .st-emotion-cache-183lzff {
            font-size: 14px;
        }
        
        .footer{
            font-size:8px;
            text-align: center;
            border-radius: 10px;
        }
        
        /*Botones*/
        .st-emotion-cache-15hul6a {
            background-color: #2C3E50;
            color: #E0E0E0;
        }
        
        /*Results*/
        .st-emotion-cache-1sno8jx p{
            text-align : center;
            font-size : 21px;
        }
        
        
    </style>
""", unsafe_allow_html=True)

#Como los containers han sido un fracaso vamos a crear una especie de estructura cutre al estilo Bootstrap con columnas del mismo streamlit
header_col = st.columns([1])
sidebar_col, main_col = st.columns([1,3], gap =	"large", vertical_alignment="center") #Dividimos el espacio en 4, Sidebar será 1 columna y main serán 3.
footer_col = st.columns([1])

#Header
with header_col[0]:
    st.title("Log-Error Predictor")
    
#Sidebar
with sidebar_col:  #Se que se puede usar un st.sidebar pero no quiero que se pueda contraer. Me da toc.
    transaction_date = st.date_input("Fecha de transacción:", value=calendar, format="DD/MM/YYYY")
    transaction_month = transaction_date.month #VALOR UTILIZADO EN LA SIMULACION
    transaction_day = transaction_date.day #VALOR UTILIZADO EN LA SIMULACION
    construction_date = st.date_input("Fecha de construcción:", value=calendar, format="DD/MM/YYYY", max_value=date(2016,12,31))
    construction_year = construction_date.year #VALOR UTILIZADO EN LA SIMULACION
    st.divider()
    calculated_sqmf = st.slider("Metros Cuadrados calculados:", min_value=0, max_value=1000, format= "%d m²")
    finished_living_area = st.slider("Metros Cuadrados habitables:", min_value=0, max_value=500, format="%d m²")
    total_sqm = st.slider("Area total:", min_value=0, max_value=500, format="%d m²")
    lotsizesqft = st.slider("Superficie total de la parcela", min_value=0, max_value=1000, format="%d m²")
    if lotsizesqft and calculated_sqmf != 0:
        lot_sqft_ratio = calculated_sqmf/lotsizesqft  if calculated_sqmf != 0 else 0 #VALOR UTILIZADO EN LA SIMULACION!!!!!!
    else:
        lot_sqft_ratio = 0
    st.divider()
    structureTaxValue = st.slider("Tasación del inmueble:", min_value=0, max_value=1000000, format="%d $")
    taxamount = st.slider("Impuestos sobre la propiedad:", min_value=0, max_value=10000, format="%d $")
    if structureTaxValue and calculated_sqmf != 0:
        price_sqft = structureTaxValue/calculated_sqmf if structureTaxValue != 0 else 0 #VALOR UTILIZADO EN LA SIMULACION!!!!
    else:
        price_sqft = 0
    st.divider()
    baths = st.slider("Baños", min_value=0, max_value=5)
    beds = st.slider("Dormitorios", min_value=0, max_value=5)
    if baths and beds != 0:
        bathbedratio = beds / baths if beds != 0 else 0#VALOR UTILIZADO EN LA SIMULACION!!!!!!!
    else:
        bathbedratio = 0
    st.divider()
    zipCode = st.text_input("ZIP Code:", max_chars=5)
    #Verificador
    if zipCode:
        if zipCode.isdigit() and len(zipCode) == 5:
            st.success("Código aceptado")
        elif zipCode.isdigit() and not len(zipCode) == 5:
            st.error("El código debe de tener 5 digitos.")
        else:
            st.error("Código Zip incorrecto.")
    #Seteamos el valor en 0 cuando no pongan datos.
    if zipCode is None or zipCode == "":
        zipCode = 0
    #countyCode = st.selectbox("Codigo de Zonificación", cods_zone_LA) #No puedo prometer que funcione con codigos que no sean de Los Angeles.
    censusTractBlock = st.text_input("FIPS+ Codigo Condal + Tracto Censal + Bloque", max_chars=14) #14 digitos. (FIPS)(Codigo Condal)(Tracto Censal)(Bloque)
    #Vamos a pasar un verificador para que no cuelen numeros ni menos caracteres que 14.
    if censusTractBlock:
        if censusTractBlock.isdigit() and len(censusTractBlock) == 14:
            st.success("Código aceptado.")
        elif censusTractBlock.isdigit() and not len(censusTractBlock) == 14:
            st.error("El código debe de tener 14 digitos.")
        else:
            st.error("Código erróneo. Por favor ingrese un valor de 14 digitos validos.")
    #Vamos a fijas el valor en 0 cuando no se ingrese.
    if censusTractBlock is None or censusTractBlock == "":
        censusTractBlock = 0
    
#############################################################################################

def Get_inputs():
    input_data = {
        'transaction_month' : transaction_month,
        'transaction_day' : transaction_day,
        'calculatedfinishedsquarefeet' : calculated_sqmf,
        'finishedsquarefeet12': finished_living_area,
        'finishedsquarefeet15': total_sqm,
        'latitude' : 0, #NO IMPREMENTADO
        'longitude' : 0, #NO IMPREMENTADO
        'propertycountylandusecode' : 0, #NO IMPREMENTADO
        'propertyzoningdesc' : 0,
        'rawcensustractandblock' : censusTractBlock,
        'regionidcity' : 0, #NO IMPREMENTADO
        'regionidneighborhood' : 0, #NO IMPREMENTADO
        'regionidzip': zipCode,
        'yearbuilt' : construction_year,
        'structuretaxvaluedollarcnt' : structureTaxValue,
        'taxamount' : taxamount,
        'bath_bed_ratio' : bathbedratio,
        'distantce_to_la' : 0, #NO IMPREMENTADO
        'price_per_sqft' : price_sqft,
        'lot_sqft_ratio' : lot_sqft_ratio}
    
    return input_data

def ParsingArray(data):
    parse = np.array([list(data.values())]).astype(float)
    return parse


#Main
#Inicializamos log_error
log_error = None
with main_col:
    left_empty_Col, pred_buttom, clear_buttom, right_empty_col = st.columns([3,1,1,3])
    
    with left_empty_Col:
        pass
        
    with pred_buttom:
        if st.button("Predict"):
            arrayInputs = ParsingArray(Get_inputs())
            
            if arrayInputs is not None:
                predictor = model.predict(arrayInputs)
                log_error = float((np.exp(predictor) - 1) * 100)
        
    
    with clear_buttom:
        if st.button("Clear"):
            st.rerun()
    
    with right_empty_col:
        pass
    
    st.divider()
    if log_error is not None:
        st.write(f"La predicción del Error Relativo es de: ")
        st.markdown(f"<span style= \"color:red; font-weight: bold;\">{log_error:.2f}%</span>", unsafe_allow_html=True)

#Footer
with footer_col[0]:
    st.markdown("<div class=\"footer\"></div>", unsafe_allow_html=True)
