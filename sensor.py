import serial
import json
import mysql.connector
import time
# python sensor.py
def conectar_banco():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Coloque sua senha do MySQL se o XAMPP tiver
            database="axon",
            autocommit=True
        )
    except Exception as e:
        print(f"❌ Erro ao conectar no MySQL: {e}")
        return None

db = conectar_banco()
if not db:
    exit()

print("✅ Conectado ao banco de dados MySQL ('axon')!")

PORTA_USB = 'COM3'  # Verifique sua porta COM no Gerenciador de Dispositivos
BAUD_RATE = 115200

# 🧠 FUNÇÃO PARA CALCULAR O NÍVEL DE ANSIEDADE BASEADO NO BPM
def calcular_nivel_ansiedade(bpm):
    if bpm < 80:
        return "Calmo"
    elif 80 <= bpm <= 100:
        return "Ansiedade Média"
    else:
        return "Ansiedade Alta"

def pegar_usuario_logado(conexao_db):
    try:
        conexao_db.ping(reconnect=True, attempts=3, delay=1)
        cursor_temp = conexao_db.cursor()
        cursor_temp.execute("SELECT usuario_id FROM dispositivo_ativo WHERE id = 1 LIMIT 1")
        resultado = cursor_temp.fetchone()
        cursor_temp.close()

        if resultado and resultado[0] is not None:
            return resultado[0]
    except Exception as err:
        print(f"⚠️ Erro ao consultar dispositivo_ativo: {err}")
    return 1

try:
    conexao_serial = serial.Serial(PORTA_USB, BAUD_RATE, timeout=1)
    print(f"✅ Lendo dados da ESP32 na porta {PORTA_USB}...")

    while True:
        if conexao_serial.in_waiting > 0:
            linha = conexao_serial.readline().decode('utf-8', errors='ignore').strip()

            if linha.startswith("{") and linha.endswith("}"):
                try:
                    dados = json.loads(linha)
                    bpm = dados.get("bpm", 0)
                    spo2 = dados.get("spo2", 0)

                    if bpm > 0:
                        # 1. Pega o ID atual do usuário no banco
                        user_id = pegar_usuario_logado(db)

                        # 2. Calcula a categoria de ansiedade
                        status_ansiedade = calcular_nivel_ansiedade(bpm)

                        # 3. Garante reconexão e insere no banco
                        db.ping(reconnect=True, attempts=3, delay=1)
                        cursor_insert = db.cursor()
                        sql = "INSERT INTO leituras_sensor (usuario_id, bpm, spo2) VALUES (%s, %s, %s)"
                        cursor_insert.execute(sql, (user_id, bpm, spo2))
                        cursor_insert.close()

                        # 4. Exibe no monitor/terminal com a classificação
                        print(f"📥 BPM: {bpm} | SpO2: {spo2}% | Status: {status_ansiedade}")

                except json.JSONDecodeError:
                    pass
                except Exception as err:
                    print(f"⚠️ Erro ao salvar: {err}")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n🛑 Programa parado pelo usuário.")
except Exception as e:
    print(f"❌ Erro na porta Serial ({PORTA_USB}): {e}")
finally:
    if 'db' in locals() and db and db.is_connected():
        db.close()
        print("🔒 Conexão com o banco encerrada.")