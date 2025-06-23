import pandas as pd
import sqlite3
import os
import chardet

print("DEBUG: data_processor.py carregado")

class DataProcessor:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "..", "data", "database", "itsm_data.db")
        self._create_database_if_not_exists()

    def _create_database_if_not_exists(self):
        print("DEBUG: Verificando/criando banco de dados")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS itsm_data (
            `PK Dataset Chamados` TEXT,
            `Título requisição` TEXT,
            `Data criação` TEXT,
            `Data fechamento` TEXT,
            `Analista Responsável` TEXT,
            `Categoria` TEXT,
            `Prioridade` TEXT,
            `Status (descrição)` TEXT,
            `Flag Em Aberto` TEXT,
            `Tempo de Resolução (horas)` REAL,
            `Grau de Satisfação` TEXT,
            `SLA Atendido` TEXT
        )""")
        conn.commit()
        conn.close()
        print("DEBUG: Banco de dados verificado/criado")

    def process_csv_file(self, file_path):
        print(f"DEBUG: Processando arquivo CSV: {file_path}")
        # Detectar a codificação do arquivo
        with open(file_path, "rb") as f:
            raw_data = f.read(10000)  # Ler os primeiros 10KB para detecção
            detection = chardet.detect(raw_data)
            encoding = detection["encoding"]
            print(f"DEBUG: Codificação detectada: {encoding}")

        # Tentar ler o CSV com diferentes delimitadores e cabeçalhos
        try:
            df = pd.read_csv(file_path, encoding=encoding, sep=",", skiprows=1) # Tenta pular a primeira linha
            print("DEBUG: CSV lido com vírgula e skiprows=1")
        except Exception as e:
            print(f"DEBUG: Erro ao ler com vírgula e skiprows=1: {e}")
            try:
                df = pd.read_csv(file_path, encoding=encoding, sep=";", skiprows=1) # Tenta com ponto e vírgula
                print("DEBUG: CSV lido com ponto e vírgula e skiprows=1")
            except Exception as e:
                print(f"DEBUG: Erro ao ler com ponto e vírgula e skiprows=1: {e}")
                try:
                    df = pd.read_csv(file_path, encoding=encoding, sep=",") # Tenta sem pular linha
                    print("DEBUG: CSV lido com vírgula e sem skiprows")
                except Exception as e:
                    print(f"DEBUG: Erro ao ler com vírgula e sem skiprows: {e}")
                    df = pd.read_csv(file_path, encoding=encoding, sep=";") # Tenta com ponto e vírgula sem pular linha
                    print("DEBUG: CSV lido com ponto e vírgula e sem skiprows")

        # Padronizar nomes de colunas para facilitar o acesso
        df.columns = df.columns.str.strip().str.replace(" ", "_").str.replace("(", "").str.replace(")", "")
        df.rename(columns={
            "PK_Dataset_Chamados": "PK Dataset Chamados".replace(" ", "_"),
            "Título_requisição": "Título requisição".replace(" ", "_"),
            "Data_criação": "Data criação".replace(" ", "_"),
            "Data_fechamento": "Data fechamento".replace(" ", "_"),
            "Analista_Responsável": "Analista Responsável".replace(" ", "_"),
            "Status_descrição": "Status (descrição)".replace(" ", "_"),
            "Flag_Em_Aberto": "Flag Em Aberto".replace(" ", "_"),
            "Tempo_de_Resolução_horas": "Tempo de Resolução (horas)".replace(" ", "_"),
            "Grau_de_Satisfação": "Grau de Satisfação".replace(" ", "_"),
            "SLA_Atendido": "SLA Atendido".replace(" ", "_")
        }, inplace=True)

        # Limpeza e conversão de tipos
        print("DEBUG: Limpando e convertendo tipos de dados")
        for col in ["Data criação", "Data fechamento"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        
        if "Tempo de Resolução (horas)" in df.columns:
            df["Tempo de Resolução (horas)"] = pd.to_numeric(df["Tempo de Resolução (horas)"], errors="coerce")

        # Filtrar colunas relevantes para o dashboard
        relevant_columns = [
            "PK Dataset Chamados", "Título requisição", "Data criação", "Data fechamento",
            "Analista Responsável", "Categoria", "Prioridade", "Status (descrição)",
            "Flag Em Aberto", "Tempo de Resolução (horas)", "Grau de Satisfação", "SLA Atendido"
        ]
        df = df[[col for col in relevant_columns if col in df.columns]]
        print(f"DEBUG: DataFrame processado com {len(df)} linhas e {len(df.columns)} colunas")
        return df

    def save_to_database(self, df):
        print("DEBUG: Salvando dados no banco de dados")
        conn = sqlite3.connect(self.db_path)
        df.to_sql("itsm_data", conn, if_exists="replace", index=False)
        conn.close()
        print("DEBUG: Dados salvos no banco de dados")

    def load_from_database(self):
        print("DEBUG: Carregando dados do banco de dados")
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM itsm_data", conn)
        conn.close()
        
        # Converter colunas de data novamente
        for col in ["Data criação", "Data fechamento"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        print(f"DEBUG: Dados carregados do banco de dados: {len(df)} linhas")
        return df

    def calculate_kpis(self, df):
        print("DEBUG: Calculando KPIs")
        total_chamados = len(df)
        chamados_abertos = df[df["Flag Em Aberto"] == "Sim"] if "Flag Em Aberto" in df.columns else pd.DataFrame()
        sla_atendido = df[df["SLA Atendido"] == "Sim"] if "SLA Atendido" in df.columns else pd.DataFrame()
        
        kpis = {
            "total_chamados": total_chamados,
            "chamados_abertos": len(chamados_abertos),
            "sla_atendido_percent": (len(sla_atendido) / total_chamados * 100) if total_chamados > 0 else 0,
            "tempo_medio_resolucao": df["Tempo de Resolução (horas)"].mean() if "Tempo de Resolução (horas)" in df.columns else 0
        }
        print("DEBUG: KPIs calculados")
        return kpis

    def get_summary_stats(self, df):
        print("DEBUG: Obtendo estatísticas de resumo")
        stats = {
            "total_registros": len(df),
            "categorias_unicas": df["Categoria"] .nunique() if "Categoria" in df.columns else 0,
            "analistas_unicos": df["Analista Responsável"] .nunique() if "Analista Responsável" in df.columns else 0,
            "grupos_solucionadores": df["Grupo Solucionador"] .nunique() if "Grupo Solucionador" in df.columns else 0,
            "periodo_inicio": df["Data fechamento"] .min().strftime("%Y-%m-%d") if "Data fechamento" in df.columns and not df["Data fechamento"] .empty else "N/A",
            "periodo_fim": df["Data fechamento"] .max().strftime("%Y-%m-%d") if "Data fechamento" in df.columns and not df["Data fechamento"] .empty else "N/A"
        }
        print("DEBUG: Estatísticas de resumo obtidas")
        return stats


