import io
import re
import numpy as np
import pandas as pd
from pypdf import PdfReader
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Conversor de Notas - Destinatário",
    page_icon="🧾",
    layout="centered",
)

st.title("🧾 Conversor de Notas por Destinatário para o Domínio Web")
st.write(
    "Faça o upload do relatório de notas em **PDF** para gerar o arquivo TXT"
    " formatado."
)

uploaded_file = st.file_uploader(
    "Selecione o arquivo de notas (.pdf)", type=["pdf"]
)

if uploaded_file is not None:
  try:
    reader = PdfReader(uploaded_file)
    layout_text = ""
    for page in reader.pages:
      layout_text += page.extract_text(extraction_mode="layout") + "\n"

    lines = layout_text.split("\n")
    parsed_notes = []

    for line in lines:
      # Identifica a linha que contém o número da nota (formato numérico)
      match_nota = re.search(r"\b(\d{7})\b", line)
      if match_nota:
        num_nota = match_nota.group(1)

        dates = re.findall(r"\d{2}/\d{2}/\d{4}", line)
        vals = re.findall(r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b", line)

        data_emissao = dates[0] if dates else ""
        valor_str = vals[-1] if vals else "0,00"

        # Extração do nome do destinatário na linha
        parts = line.split()
        text_tokens = [
            p
            for p in parts
            if not re.match(
                r"^\d{2}/\d{2}/\d{4}$|^\d+([.,]\d+)?$|^AUTORIZADA$|^PAGO$", p
            )
        ]
        destinatario = " ".join(text_tokens)
        if not destinatario or len(destinatario) < 3:
          destinatario = "DESTINATARIO GERAL"

        parsed_notes.append({
            "nota": num_nota,
            "data": data_emissao,
            "destinatario": destinatario.strip(),
            "valor": valor_str,
        })

    df_dest = pd.DataFrame(parsed_notes)

    if df_dest.empty:
      st.warning(
          "Não foi possível extrair as notas do PDF. Verifique se o layout"
          " confere com o modelo."
      )
    else:
      st.success(
          f"✨ PDF lido com sucesso! Total de notas extraídas: {len(df_dest)}"
      )
      with st.expander("🔍 Ver prévia dos dados extraídos"):
        st.dataframe(df_dest.head(15))

      st.markdown("---")

      if st.button(
          "🚀 Processar e Gerar TXT para o Domínio",
          type="primary",
          key="btn_proc",
      ):
        linhas_processadas = []

        for _, row in df_dest.iterrows():
          data = row["data"]
          nota = row["nota"]
          dest = row["destinatario"]
          val_clean = row["valor"].replace(".", "").replace(",", ".")
          try:
            val_num = float(val_clean)
          except:
            val_num = 0.0

          # Regra de Contas baseada no destinatário
          if "RAPHAEL" in dest.upper():
            conta_deb = "949"
            conta_cred = "880"
          else:
            conta_deb = "14"
            conta_cred = "949"

          # Histórico: NF [Número Nota] - [Nome Destinatário]
          historico = f"NF {nota} - {dest}"

          val_fmt = f"{val_num:.2f}".replace(".", ",")
          linha_txt = f"{data};{conta_deb};{conta_cred};{val_fmt};{historico}"
          linhas_processadas.append(linha_txt)

        txt_final = "\n".join(linhas_processadas)

        st.success("✨ Arquivo TXT gerado com sucesso!")

        df_preview = pd.DataFrame(
            [l.split(";") for l in linhas_processadas],
            columns=["Data", "Conta Débito", "Conta Crédito", "Valor", "Histórico"],
        )
        with st.expander("👀 Visualizar prévia dos lançamentos gerados"):
          st.dataframe(df_preview.head(15))

        st.download_button(
            label="📥 Baixar Arquivo TXT para o Domínio Web",
            data=txt_final.encode("cp1252", errors="replace"),
            file_name="notas_destinatario_dominio.txt",
            mime="text/plain",
        )
  except Exception as e:
    st.error(f"Ocorreu um erro ao processar o arquivo PDF: {e}")