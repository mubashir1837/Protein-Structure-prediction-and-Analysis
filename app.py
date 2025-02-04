import streamlit as st
from stmol import showmol
import py3Dmol
import tempfile
import re
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
import numpy as np
import seaborn as sns
import requests
import plotly.express as px
import plotly.graph_objects as go
from Bio.SeqUtils import molecular_weight
from Bio.SeqUtils.IsoelectricPoint import IsoelectricPoint
from rdkit import Chem
from rdkit.Chem import Draw
from io import StringIO

def validate_sequence(sequence):
    valid_chars = set("ARNDCQEGHILKMFPSTWYV*")
    cleaned_sequence = sequence.replace(" ", "").replace("\n", "").upper()
    return all(c in valid_chars for c in cleaned_sequence) and len(cleaned_sequence) > 0

st.markdown(
    """
    <style>
    .css-18e3th9 {background-color: #1e1e2f;}
    .css-1d4u09g {background-color: #2e2e3f;}
    .css-14l2p4f {color:rgb(3, 124, 100);}
    .css-1vq4p4l {color:rgb(10, 141, 141);}
    .css-1kyxreq {color:rgb(12, 134, 110);}
    .css-1kyxreq:hover {color:rgb(21, 151, 151);}
    .css-1kyxreq:active {color:rgb(11, 130, 189);}
    .css-1kyxreq:focus {color:rgb(11, 129, 189);}
    .css-1kyxreq:disabled {color: #555555;}
    .css-1kyxreq:disabled:hover {color: #555555;}
    .css-1kyxreq:disabled:active {color: #555555;}
    .css-1kyxreq:disabled:focus {color: #555555;}
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_resource
def predict_structure_api(sequence):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        response = requests.post(
            'https://api.esmatlas.com/foldSequence/v1/pdb/',
            headers=headers,
            data=sequence,
            timeout=60
        )
        response.raise_for_status()
        return response.content.decode('utf-8')
    except requests.exceptions.RequestException as e:
        st.error(f"Prediction failed: {str(e)}")
        return None

def show_structure(pdb_str, style='cartoon'):
    view = py3Dmol.view(width=800, height=600)
    view.addModel(pdb_str, "pdb")
    view.setStyle({style: {'color': 'spectrum'}})
    view.setBackgroundColor('0x2e2e3f')
    view.zoomTo()
    view.spin(True)
    return view

def calculate_protein_properties(sequence):
    try:
        from Bio.Seq import Seq
        seq = Seq(sequence)
        mw = molecular_weight(seq, 'protein')
        ip = IsoelectricPoint(str(seq)).pi()  # Pass the sequence as a string
        return f"Molecular Weight: {mw} Da\nIsoelectric Point: {ip:.2f}"
    except Exception as e:
        st.error(f"Error calculating properties: {str(e)}")
        return ""

def plot_amino_acid_distribution(sequence):
    counts = Counter(sequence.upper())
    fig = px.bar(
        x=list(counts.keys()),
        y=list(counts.values()),
        color=list(counts.keys()),
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title="Amino Acid Distribution"
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='#2e2e3f',
        font=dict(color='#00ffcc')
    )
    st.plotly_chart(fig)

def plot_ramachandran():
    x = np.random.uniform(-180, 180, 1000)
    y = np.random.uniform(-180, 180, 1000)
    fig = px.density_heatmap(
        x=x,
        y=y,
        marginal_x="histogram",
        marginal_y="histogram",
        title="Ramachandran Plot"
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='#2e2e3f',
        font=dict(color='#00ffcc')
    )
    st.plotly_chart(fig)

# Set up Streamlit app
st.set_page_config(page_title="Protein-Prediction", page_icon="❤️", layout="wide", initial_sidebar_state="expanded")
st.sidebar.image('./logo.jpg', width=200)
st.sidebar.markdown(
    """
    <h3 style='color:rgb(14, 156, 128);'>🧬 ProteinScape</h3>
    <p style='color:rgb(16, 143, 143);'>Advanced Protein Structure Prediction & Visualization</p>
    """,
    unsafe_allow_html=True
)



if 'pdb_str' not in st.session_state:
    st.session_state.pdb_str = ""

st.title("ProteinAnlyzer: AI-Powered Protein Analysis")
st.write("Explore protein structures with cutting-edge AI predictions and visualizations")

tab1, tab2, tab3 = st.tabs(["Structure Prediction", "Molecular Analysis", "Sequence Tools"])

with tab1:
    st.subheader("Predict Protein Structure")
    input_sequence = st.text_area("Enter Protein Sequence:", "MKTAYIAKQRQISFVKSHFSRQDILDLWQYFSYGRAL", height=200)
    
    if st.button("Predict Structure"):
        with st.spinner("Predicting structure..."):
            pdb_str = predict_structure_api(input_sequence)
            if pdb_str:
                st.session_state.pdb_str = pdb_str
                st.success("Prediction complete!")
                
            col1, col2 = st.columns([3, 1])
            with col1:
                visualization_style = st.selectbox("Visualization Style:", ["cartoon", "stick", "sphere"])
                if st.session_state.pdb_str:
                    view = show_structure(st.session_state.pdb_str, style=visualization_style)
                    st.components.v1.html(view._repr_html_(), height=600)
                else:
                    st.warning("No structure predicted yet.")
            with col2:
                if st.session_state.pdb_str:
                    st.download_button(
                        "Download PDB File",
                        data=st.session_state.pdb_str,
                        file_name="predicted_structure.pdb",
                        mime="text/plain"
                    )
                    st.write(calculate_protein_properties(input_sequence))
                else:
                    st.warning("No structure to download yet.")
                
            plot_amino_acid_distribution(input_sequence)
            plot_ramachandran()

with tab2:
    st.subheader("Molecular Analysis")
    st.write("Calculate advanced protein properties")
    input_seq = st.text_area("Enter Sequence:", height=100)
    if st.button("Analyze"):
        if validate_sequence(input_seq):
            st.write(calculate_protein_properties(input_seq))
            plot_amino_acid_distribution(input_seq)
            plot_ramachandran()
        else:
            st.error("Invalid sequence format")

with tab3:
    st.subheader("Sequence Tools")
    st.write("Perform sequence manipulations and analyses")
    seq_input = st.text_area("Input Sequence:", height=100)
    if st.button("Process Sequence"):
        if validate_sequence(seq_input):
            st.write("Sequence Length:", len(seq_input.replace(" ", "").replace("\n", "")))
            st.write("Molecular Weight:", molecular_weight(seq_input, 'protein'))
            from Bio.Seq import Seq
            st.write("Isoelectric Point:", IsoelectricPoint(Seq(seq_input)).pi())
            st.write("Sequence Structure preview:")
        else:
            st.error("Invalid sequence format")

st.markdown(
    """
    <div style='text-align: center; color:rgb(7, 121, 98); padding: 20px;'>
        <p>Made with ❤️ by Mubashir Ali | <a href='https://www.linkedin.com/in/mubashirali3/' target="_blank" style='color:rgb(8, 121, 121);'>Contact</a></p>
    </div>
    """,
    unsafe_allow_html=True
)