import json
import os
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega variáveis de ambiente (do .env local, se existir)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Tenta pegar a chave do ambiente (GitHub Secrets ou .env local)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("AVISO: GEMINI_API_KEY não encontrada nas variáveis de ambiente.")

NICHES = [
    "Tecnologia e Inovação",
    "Venture Capital & M&A",
    "Cultura, Liderança & Execução"
]

GEMINI_WEEKLY_PROMPT_TEMPLATE = """
Você é o motor de curadoria IA do NextWave, encarregado de criar o Relatório Semanal Executivo para empreendedores.
Abaixo está uma lista de manchetes que ocorreram nesta semana na categoria: {niche}.

Manchetes da Semana:
{headlines}

Sua tarefa:
Redija um resumo parcial de inteligência (cerca de 2 parágrafos) analisando o cenário geral dessa categoria baseado apenas nestes fatos. Formate em HTML com as seguintes regras:
- Use a tag <p style='margin-bottom: 15px; color: #d0d0d0; line-height: 1.8; font-family: \"Mulish\", sans-serif;'> para os parágrafos.
- Seja estratégico, analítico, apontando consequências para fundadores de startups.
- Não adicione marcação de bloco de código (ex: ```html) no início, retorne APENAS as tags <p>.

Além disso, forneça uma frase curta (1 linha) que resuma o destaque da semana.

Retorne EXATAMENTE este JSON:
{{
    "summary": "Frase de 1 linha de resumo",
    "body": "O código HTML gerado..."
}}
"""

GEMINI_FINAL_REPORT_TEMPLATE = """
Você é o analista-chefe do NextWave. Seu objetivo é unir os 3 relatórios parciais (que resumem o que rolou nas áreas de Tecnologia, Venture Capital e Operações) em um único grande Relatório Semanal Executivo.

Aqui estão os 3 relatórios parciais:
{partial_reports}

Sua tarefa:
Escreva um relatório coeso, analítico e maduro. Siga o roteiro oficial, usando tags HTML:
- Título principal (<h2>)
- Parágrafo Introdutório (<h2>O cenário da semana</h2> + texto conectando os pontos principais).
- EXATAMENTE 4 Seções Numeradas de Insights transversais (<h3>). Para cada insight, destaque as "Notícias base" envolvidas e escreva um bloco "Como isso conversa com o mercado / Consequências".
- 1 Conclusão Estratégica (<h3>) resumindo o aprendizado da semana para fundadores. (Formando assim os 5 blocos estruturais que compõem o relatório).

Regras de Estilo HTML:
- Use <h2 style='color: #00f0ff; font-family: "Syncopate", sans-serif; margin-bottom: 20px;'> para o título principal e seções grandes.
- Use <h3 style='color: #00e676; font-family: "Syncopate", sans-serif; margin-top: 30px; margin-bottom: 15px;'> para subseções.
- Use <p style='color: #d0d0d0; line-height: 1.8; font-family: "Mulish", sans-serif; margin-bottom: 15px;'> para textos longos.
- Use blocos <div style='background: rgba(255, 255, 255, 0.05); padding: 15px; border-left: 3px solid #ff9800; margin-bottom: 20px; font-family: "Mulish", sans-serif;'> para destacar a "Notícia base".

Retorne EXATAMENTE um JSON neste formato:
{{
    "report_html": "O código HTML gerado de todo o relatório"
}}
"""

def generate_weekly_report():
    print("Iniciando geração do Relatório Semanal...")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    weekly_storage_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weekly_news_storage.json')
    report_output_file = os.path.join(root_dir, 'weekly_report.json')
    
    weekly_storage = []
    if os.path.exists(weekly_storage_file):
        with open(weekly_storage_file, 'r', encoding='utf-8') as f:
            try:
                weekly_storage = json.load(f)
            except json.JSONDecodeError:
                pass
                
    if not weekly_storage:
        print("Nenhuma notícia armazenada nesta semana. Simulando base para o relatório...")
        weekly_storage = [{"nicho_primario": n, "headline": f"Acontecimento base para o nicho {n}"} for n in NICHES]
        
    # Separando por nicho para gerar os relatórios parciais (resumos das categorias)
    categorized_news = {niche: [] for niche in NICHES}
    for item in weekly_storage:
        niche = item.get("nicho_primario")
        if niche in categorized_news:
            categorized_news[niche].append(item)
            
    report_sections = []
    
    # 1. Gerando Resumos Parciais por Nicho via Gemini
    try:
        model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
    except Exception:
        model = None

    for niche in NICHES:
        items = categorized_news[niche]
        count = len(items)
        if count > 0:
            print(f"Gerando relatório parcial para {niche} ({count} notícias)...")
            
            headlines = "\\n".join([f"- {item.get('headline', 'Fato não identificado')}" for item in items])
            prompt = GEMINI_WEEKLY_PROMPT_TEMPLATE.format(niche=niche, headlines=headlines)
            
            summary = f"Análise agregada de {count} movimentações estratégicas na semana."
            summary_html = f"<p style='margin-bottom: 15px; color: #d0d0d0; line-height: 1.8; font-family: \"Mulish\", sans-serif;'>Nesta semana, analisamos {count} eventos nesta categoria. A IA identificou padrões apontando para mudanças estruturais.</p>"
            
            if model and GEMINI_API_KEY != "COLOQUE_SUA_CHAVE_AQUI":
                try:
                    response = model.generate_content(prompt)
                    ai_data = json.loads(response.text)
                    summary = ai_data.get("summary", summary)
                    summary_html = ai_data.get("body", summary_html)
                except Exception as e:
                    print(f"Erro na IA para a seção {niche}. Motivo: {e}")
            else:
                print("AVISO: GEMINI_API_KEY não configurada. Usando fallback text.")

            # Sempre adicionamos um cabeçalho customizado para a seção
            final_html = f"<p style='color: #00f0ff; font-weight: bold; margin-bottom: 10px; font-family: \"Syncopate\", sans-serif;'>RESUMO PARCIAL - {niche}</p>"
            final_html += summary_html

            report_sections.append({
                "section": niche,
                "summary": summary,
                "body": final_html
            })
            
    # 2. Unindo os três relatórios no Relatório Semanal Final
    print("Unificando relatórios parciais no Relatório Semanal final...")
    
    final_report_html = "<p style='color:#fff'>Relatório consolidado não pôde ser gerado (Falta de dados ou limite de API).</p>"
    
    if len(report_sections) > 0 and model and GEMINI_API_KEY != "COLOQUE_SUA_CHAVE_AQUI":
        print("Enviando parciais para síntese final no formato oficial do relatório...")
        partial_reports_text = "\\n\\n".join([f"=== {sec['section']} ===\\nResumo: {sec['summary']}\\nCorpo: {sec['body']}" for sec in report_sections])
        final_prompt = GEMINI_FINAL_REPORT_TEMPLATE.format(partial_reports=partial_reports_text)
        
        try:
            final_response = model.generate_content(final_prompt)
            final_ai_data = json.loads(final_response.text)
            final_report_html = final_ai_data.get("report_html", final_report_html)
        except Exception as e:
            print(f"Erro na IA ao gerar relatório consolidado. Motivo: {e}")
            final_report_html = "<p style='color:red'>Erro na consolidação final da IA.</p>"
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    final_report = {
        "date": current_date,
        "report_html": final_report_html
    }
    
    # 1. Salvar como relatório atual (weekly_report.json)
    with open(report_output_file, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=4, ensure_ascii=False)
        
    # 2. Sistema de Arquivamento Histórico (Memória)
    archive_dir = os.path.join(root_dir, 'reports_archive')
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        
    # Salvar cópia imutável com a data no nome
    archive_file = os.path.join(archive_dir, f'weekly_report_{current_date}.json')
    with open(archive_file, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=4, ensure_ascii=False)
        
    # Atualizar o indexador de relatórios para o frontend
    index_file = os.path.join(archive_dir, 'index.json')
    archive_index = []
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            try:
                archive_index = json.load(f)
            except json.JSONDecodeError:
                pass
                
    # Adicionar no índice se a data ainda não existir (ou atualizar o caminho)
    existing_entry = next((item for item in archive_index if item["date"] == current_date), None)
    if not existing_entry:
        archive_index.insert(0, {
            "date": current_date,
            "file": f'reports_archive/weekly_report_{current_date}.json',
            "title": f"Relatório da Semana - {current_date}"
        })
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(archive_index, f, indent=4, ensure_ascii=False)
            
    print(f"Relatório Semanal ({current_date}) gerado, publicado e arquivado com sucesso!")
    
    # 3. Limpar o storage semanal
    # COMENTADO TEMPORARIAMENTE PARA EVITAR PERDA DE DADOS EM CASO DE ERRO DE API
    # with open(weekly_storage_file, 'w', encoding='utf-8') as f:
    #     json.dump([], f)
    print("Cofre semanal preservado durante os testes de cota da API.")

if __name__ == "__main__":
    generate_weekly_report()
