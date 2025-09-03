import os
from datetime import datetime
from dotenv import load_dotenv
import glob

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco
USER = os.getenv('MYSQL_USER')
PASSWORD = os.getenv('MYSQL_PASSWORD')
HOST = os.getenv('MYSQL_HOST')
PORT = os.getenv('MYSQL_PORT', '3306')
DB = os.getenv('MYSQL_DB')

# Diretório de backup
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# Nome do arquivo com timestamp
now = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = os.path.join(BACKUP_DIR, f"{DB}_backup_{now}.sql")

# Comando de dump do MySQL
dump_cmd = f"mysqldump -h {HOST} -P {PORT} -u {USER} -p{PASSWORD} {DB} > {backup_file}"

# Executar backup
exit_code = os.system(dump_cmd)

if exit_code == 0:
    print(f"Backup criado com sucesso: {backup_file}")
else:
    print("Erro ao criar backup")
    exit(1)

# Manter apenas os últimos 7 backups
backups = sorted(glob.glob(os.path.join(BACKUP_DIR, f"{DB}_backup_*.sql")))
if len(backups) > 7:
    for old_backup in backups[:-7]:
        os.remove(old_backup)
        print(f"Backup antigo removido: {old_backup}")
