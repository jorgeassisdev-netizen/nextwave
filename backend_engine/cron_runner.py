import os
import sys
from datetime import datetime

# Adiciona o diretório atual ao path para poder importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from daily_updater import update_daily
from weekly_report_generator import generate_weekly_report

def main():
    print("==================================================")
    print(" INICIANDO NEXTWAVE CRON BOT")
    print("==================================================")
    
    # 0 = Segunda-feira, 6 = Domingo
    current_weekday = datetime.now().weekday()
    
    if current_weekday == 6:
        print("Hoje é Domingo. Dia de geração EXCLUSIVA do Relatório Semanal (5 pontos).")
        print("Iniciando motor analítico semanal...")
        try:
            generate_weekly_report()
            print("Relatório Semanal gerado com sucesso!")
        except Exception as e:
            print(f"Erro ao gerar relatório semanal: {e}")
            sys.exit(1)
    else:
        print("Hoje é um dia de semana útil (Segunda a Sábado).")
        print("Iniciando geração de Notícias Diárias...")
        try:
            update_daily()
            print("Notícias diárias geradas e armazenadas com sucesso!")
        except Exception as e:
            print(f"Erro ao gerar notícias diárias: {e}")
            sys.exit(1)
            
    print("==================================================")
    print(" CRON BOT FINALIZADO")
    print("==================================================")

if __name__ == "__main__":
    main()
