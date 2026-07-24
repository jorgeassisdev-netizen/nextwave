import json
import os
import random
from datetime import datetime
import google.generativeai as genai
import textwrap
from dotenv import load_dotenv

# Carrega variáveis de ambiente (do .env local, se existir)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Tenta pegar a chave do ambiente (GitHub Secrets ou .env local)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("AVISO: GEMINI_API_KEY não encontrada nas variáveis de ambiente.")

# Categorization Schema requested in the PDF
NICHES = {
    "Tecnologia e Inovação": [
        "Infraestrutura & DevTools",
        "Cibersegurança & Privacidade",
        "Deep Tech & Pesquisa"
    ],
    "Venture Capital & M&A": [
        "Tendências de Ecossistema & Verticais",
        "Análise Macro & IPOs",
        "Captações & Fundos"
    ],
    "Cultura, Liderança & Execução": [
        "Growth & Estratégia Go-to-Market",
        "Gestão de Produto & Engenharia",
        "Desenvolvimento Organizacional"
    ]
}

NICHE_COLORS = {
    "Tecnologia e Inovação": "#00f0ff", # Azul
    "Venture Capital & M&A": "#ff9800", # Laranja
    "Cultura, Liderança & Execução": "#00e676" # Verde
}


# Prompt Engineering Template para integrar ao Gemini 2.5
GEMINI_PROMPT_TEMPLATE = """
Você é o motor de curadoria IA do NextWave, especializado no ecossistema de startups.
Sua tarefa é analisar a matéria bruta abaixo e gerar uma classificação rigorosa E reescrever a matéria seguindo EXATAMENTE um formato de deep dive HTML.

1. CLASSIFICAÇÃO:
Escolha EXATAMENTE UMA Categoria Primária entre:
- Tecnologia e Inovação
- Venture Capital & M&A
- Cultura, Liderança & Execução

Escolha ATÉ DUAS Subcategorias da documentação relacionadas à categoria primária escolhida:
Tecnologia e Inovação: Infraestrutura & DevTools, Cibersegurança & Privacidade, Deep Tech & Pesquisa
Venture Capital & M&A: Tendências de Ecossistema & Verticais, Análise Macro & IPOs, Captações & Fundos
Cultura, Liderança & Execução: Growth & Estratégia Go-to-Market, Gestão de Produto & Engenharia, Desenvolvimento Organizacional

2. REDAÇÃO (DEEP DIVE HTML):
Gere o conteúdo ("body") da notícia estritamente com as seguintes tags HTML e estrutura, substituindo os textos pelos seus insights:

<h4 class='detail-section-title'>Dossiê Estratégico - [NOME DO NICHO AQUI]</h4>

<p style='color: [COLOR_PLACEHOLDER]; font-weight: bold; margin-bottom: 10px; margin-top: 25px; font-family: "Syncopate", sans-serif;'>1. CONTEXTUALIZAÇÃO (O AMBIENTE ANTERIOR)</p>
<p style='margin-bottom: 15px; color: #d0d0d0; line-height: 1.8; font-family: "Mulish", sans-serif;'>[Seu texto explicando o contexto histórico ou o ambiente antes deste fato ocorrer]</p>

<p style='color: [COLOR_PLACEHOLDER]; font-weight: bold; margin-bottom: 10px; margin-top: 25px; font-family: "Syncopate", sans-serif;'>2. O FATO (A SITUAÇÃO EM SI)</p>
<p style='margin-bottom: 15px; color: #d0d0d0; line-height: 1.8; font-family: "Mulish", sans-serif;'>[Seu texto detalhando o que efetivamente aconteceu na matéria]</p>

<p style='color: [COLOR_PLACEHOLDER]; font-weight: bold; margin-bottom: 10px; margin-top: 25px; font-family: "Syncopate", sans-serif;'>3. O NOVO CENÁRIO (O QUE MUDOU)</p>
<p style='margin-bottom: 15px; color: #d0d0d0; line-height: 1.8; font-family: "Mulish", sans-serif;'>[Seu texto analítico sobre as consequências e o que muda para os empreendedores no ecossistema a partir de agora]</p>

<button class='mark-read-btn' id='mark-read-btn' onclick='closeNews()' style='margin-top: 40px; font-family: "Syncopate", sans-serif;'>Concluir Leitura Profunda</button>


3. FORMATO DE SAÍDA (MUITO IMPORTANTE):
Retorne a sua resposta EXATAMENTE no seguinte formato JSON. Não adicione crases (` ```json `), nem qualquer outro texto fora das chaves do JSON:

{{
    "nicho_primario": "Nome da Categoria Primária escolhida",
    "subcategorias": ["Subcategoria 1", "Subcategoria 2"],
    "headline": "Um título curto e impactante para a matéria",
    "body": "Todo o código HTML gerado conforme o passo 2. Use \\" para aspas duplas dentro da string JSON para não quebrar o código"
}}

---
MATÉRIA BRUTA:
{article_text}
"""

def generate_news_with_gemini():
    # Se o usuário não colocou a chave, vamos cair pro mock.
    if GEMINI_API_KEY == "COLOQUE_SUA_CHAVE_AQUI":
        print("AVISO: GEMINI_API_KEY não configurada. Usando mock gerado via random para não quebrar o app.")
        return generate_mock_daily_news()

    news_items = []
    
    # 9 Fatos brutos base para a IA analisar hoje (Em produção, isso viria de uma API de RSS/Notícias)
    raw_articles = [
        "A OpenAI anunciou um novo modelo de linguagem que promete reduzir os custos de inferência em 90%. Isso afeta diretamente as startups que dependem da API deles para funcionar, barateando a operação e permitindo novos modelos de negócio B2C.",
        "Um fundo americano de Venture Capital acaba de captar 500 milhões de dólares especificamente focado em investir em AgTechs na América Latina, considerando o Brasil o principal celeiro.",
        "Estudos mostram que 70% das startups early stage falham por conta de desentendimentos societários e falta de cultura. Especialistas recomendam a implementação de frameworks ágeis não só em dev, mas em RH.",
        "A AWS lançou novas ferramentas nativas para orquestração de microsserviços em arquiteturas multi-cloud. Especialistas afirmam que isso vai diminuir o tempo de go-to-market para plataformas SaaS B2B.",
        "Uma nova regulamentação na União Europeia e no Brasil sobre o uso de dados de usuários por IAs está forçando startups a repensarem suas políticas de criptografia e mitigação de riscos de vazamento.",
        "Uma grande fusão entre dois unicórnios do setor de mobilidade foi anunciada hoje de manhã. Analistas apontam que a liquidez no setor deve diminuir, forçando startups menores a buscarem lucratividade ao invés de crescimento a qualquer custo.",
        "O Banco Central anunciou mais um corte na taxa Selic, o que tem direcionado investidores institucionais de volta para a renda variável e fundos de private equity, reaquecendo o mercado de capitais para startups tech.",
        "Nova metodologia de Growth hacking que une inteligência artificial e análise preditiva reduz o CAC (Custo de Aquisição de Cliente) em até 40% em startups de e-commerce, focando muito mais em retenção de cohort do que topo de funil.",
        "Grandes corporações estão abandonando metodologias de design engessadas e optando por Design Systems fluidos e focados em priorização centrada no cliente, acelerando o roadmap de produto em meses."
    ]
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
    except Exception as e:
        print(f"Erro ao instanciar o Gemini: {e}")
        return generate_mock_daily_news()

    for article in raw_articles:
        prompt = GEMINI_PROMPT_TEMPLATE.format(article_text=article)
        
        try:
            print(f"Analisando notícia via Gemini 2.5: {article[:50]}...")
            response = model.generate_content(prompt)
            ai_data = json.loads(response.text)
            
            nicho_primario = ai_data.get("nicho_primario", "Tecnologia e Inovação")
            color = NICHE_COLORS.get(nicho_primario, "#00f0ff")
            body = ai_data.get("body", "<p>Erro na formatação HTML</p>").replace("[COLOR_PLACEHOLDER]", color)
            
            # Formatar e sanitizar pro Frontend
            item = {
                "categoria": nicho_primario, # Categoria primária aparece no Card
                "nicho_primario": nicho_primario,
                "subcategorias": ai_data.get("subcategorias", []),
                "headline": ai_data.get("headline", "Notícia Urgente"),
                "body": body,
                "color": color,
                "read": False,
                "date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
            }
            news_items.append(item)
        except Exception as e:
            print(f"Falha na IA para este artigo. Motivo: {e}")
            
    if not news_items:
        return generate_mock_daily_news()
        
    return news_items

def generate_mock_daily_news():
    # Fallback se a API falhar ou não estiver configurada
    news_items = []
    num_news = random.randint(3, 5)
    for i in range(num_news):
        niche = random.choice(list(NICHES.keys()))
        subcats = random.sample(NICHES[niche], k=random.randint(1, 2))
        primary_subcat = subcats[0]
        color = NICHE_COLORS.get(niche, "#00f0ff")
        
        item = {
            "categoria": niche,
            "nicho_primario": niche,
            "subcategorias": subcats,
            "headline": f"Análise Diária: O Impacto de {niche} no mercado atual",
            "body": f"<h4 class='detail-section-title'>Dossiê Estratégico - {niche}</h4><p style='color: {color}; font-weight: bold; margin-bottom: 10px; margin-top: 25px; font-family: \"Syncopate\", sans-serif;'>1. CONTEXTUALIZAÇÃO (O AMBIENTE ANTERIOR)</p><p style='color: #d0d0d0; font-family: \"Mulish\", sans-serif; line-height:1.5;'>Simulação do contexto.</p><p style='color: {color}; font-weight: bold; margin-bottom: 10px; margin-top: 25px; font-family: \"Syncopate\", sans-serif;'>2. O FATO (A SITUAÇÃO EM SI)</p><p style='color: #d0d0d0; font-family: \"Mulish\", sans-serif; line-height:1.5;'>Fato.</p><p style='color: {color}; font-weight: bold; margin-bottom: 10px; margin-top: 25px; font-family: \"Syncopate\", sans-serif;'>3. O NOVO CENÁRIO (O QUE MUDOU)</p><p style='color: #d0d0d0; font-family: \"Mulish\", sans-serif; line-height:1.5;'>Consequências.</p><button class='mark-read-btn' id='mark-read-btn' onclick='closeNews()' style='margin-top: 40px; font-family: \"Syncopate\", sans-serif;'>Concluir Leitura Profunda</button>",
            "color": color,
            "read": False,
            "date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
        }
        news_items.append(item)
    return news_items


def update_daily():
    print("Iniciando motor de curadoria diária...")
    # 1. Obter notícias
    daily_news = generate_news_with_gemini()
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    news_file = os.path.join(root_dir, 'www', 'news_data.json')
    weekly_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weekly_news_storage.json')
    
    # 2. Atualizar o Feed Diário do Frontend
    with open(news_file, 'w', encoding='utf-8') as f:
        json.dump(daily_news, f, indent=4, ensure_ascii=False)
    print(f"-> {len(daily_news)} notícias atualizadas no Dashboard diário.")
    
    # 3. Armazenar para o Relatório Semanal
    weekly_storage = []
    if os.path.exists(weekly_file):
        try:
            with open(weekly_file, 'r', encoding='utf-8') as f:
                weekly_storage = json.load(f)
        except json.JSONDecodeError:
            pass
            
    weekly_storage.extend(daily_news)
    with open(weekly_file, 'w', encoding='utf-8') as f:
        json.dump(weekly_storage, f, indent=4, ensure_ascii=False)
    print(f"-> Notícias armazenadas no cofre semanal (Total acumulado: {len(weekly_storage)}).")


if __name__ == "__main__":
    update_daily()
