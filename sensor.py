import serial
import json
import mysql.connector
import time

# Conexão com o banco local
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="", # Coloque a senha do MySQL se o seu XAMPP tiver
        database="axon"
    )
    cursor = db.cursor()
    print("✅ Conectado ao banco de dados MySQL ('axon')!")
except Exception as e:
    print(f"❌ Erro ao conectar no MySQL: {e}")
    exit()

PORTA_USB = 'COM3' # Verifique se a sua porta é COM3, COM4, COM5...
BAUD_RATE = 115200

# Função que descobre quem é o usuário logado
def pegar_usuario_logado():
    try:
        cursor.execute("SELECT usuario_id FROM dispositivo_ativo WHERE id = 1 LIMIT 1")
        resultado = cursor.fetchone()
        if resultado and resultado[0]:
            return resultado[0]
    except Exception as err:
        pass
    return 1 # Se der erro, usa 1 como padrão

try:
    conexao = serial.Serial(PORTA_USB, BAUD_RATE, timeout=1)
    print(f"✅ Lendo dados da ESP32 na porta {PORTA_USB}...")

    while True:
        if conexao.in_waiting > 0:
            linha = conexao.readline().decode('utf-8', errors='ignore').strip()
            
            if linha.startswith("{") and linha.endswith("}"):
                try:
                    dados = json.loads(linha)
                    bpm = dados.get("bpm", 0)
                    spo2 = dados.get("spo2", 0)

                    if bpm > 0:
                        # 🔍 Pega o ID do usuário que está logado no momento
                        user_id = pegar_usuario_logado()

                        # 📥 Salva com o ID correto do usuário
                        sql = "INSERT INTO leituras_sensor (usuario_id, bpm, spo2) VALUES (%s, %s, %s)"
                        cursor.execute(sql, (user_id, bpm, spo2))
                        db.commit()
                        print(f"📥 Salvo para Usuário ID {user_id} -> BPM: {bpm} | SpO2: {spo2}%")

                except Exception as err:
                    print(f"⚠️ Erro ao salvar: {err}")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n🛑 Programa parado pelo usuário.")
finally:
    if 'db' in locals() and db.is_connected():
        cursor.close()
        db.close()