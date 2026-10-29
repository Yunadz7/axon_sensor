import serial
import time
import json
import mysql.connector

# ==========================================
# CONEXÃO COM O BANCO DE DADOS
# ==========================================
def conectar_banco():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Insira a senha se o seu MySQL tiver
            database="axon",
            autocommit=True
        )
    except Exception as e:
        print(f"❌ Erro ao conectar no MySQL: {e}")
        return None

def pegar_usuario_logado(conexao_db):
    try:
        conexao_db.ping(reconnect=True, attempts=3, delay=1)
        cursor = conexao_db.cursor()
        cursor.execute("SELECT usuario_id FROM dispositivo_ativo WHERE id = 1 LIMIT 1")
        resultado = cursor.fetchone()
        cursor.close()

        if resultado and resultado[0] is not None:
            return resultado[0]
    except Exception as err:
        pass
    return 1

db = conectar_banco()
if not db:
    exit()

print("✅ Conectado ao banco de dados MySQL ('axon')!")

# ==========================================
# LEITURA SERIAL E GRAVAÇÃO
# ==========================================
PORTA_USB = 'COM3'
BAUD_RATE = 115200

try:
    print(f"Tentando abrir a porta {PORTA_USB}...")
    conexao = serial.Serial(PORTA_USB, BAUD_RATE, timeout=2)
    conexao.reset_input_buffer()
    print("✅ Porta Serial aberta com sucesso! Aguardando dados da ESP32...\n")

    while True:
        if conexao.in_waiting > 0:
            linha = conexao.readline().decode('utf-8', errors='ignore').strip()
            print(f"[RECEBIDO] -> {linha}")

            # Salva no banco quando a linha for um JSON válido
            if linha.startswith("{") and linha.endswith("}"):
                try:
                    dados = json.loads(linha)
                    bpm = dados.get("bpm", 0)
                    spo2 = dados.get("spo2", 98)

                    if bpm > 0:
                        user_id = pegar_usuario_logado(db)
                        
                        db.ping(reconnect=True, attempts=3, delay=1)
                        cursor_insert = db.cursor()
                        sql = "INSERT INTO leituras_sensor (usuario_id, bpm, spo2) VALUES (%s, %s, %s)"
                        cursor_insert.execute(sql, (user_id, bpm, spo2))
                        cursor_insert.close()
                        
                        print(f"   └─ 💾 [SALVO NO BANCO] usuario_id: {user_id} | bpm: {bpm} | spo2: {spo2}%")
                except Exception as err:
                    print(f"   └─ ⚠️ Erro ao gravar no banco: {err}")

        time.sleep(0.01)

except serial.SerialException as e:
    print(f"\n❌ ERRO DE COMUNICAÇÃO SERIAL: {e}")
    print("\nO que verificar:")
    print("1. O Monitor Serial do Arduino IDE está ABERTO? (Se estiver, FECHE agora).")
    print("2. A porta no Gerenciador de Dispositivos ainda é a COM3?")
except KeyboardInterrupt:
    print("\nTeste encerrado.")
finally:
    if 'db' in locals() and db and db.is_connected():
        db.close()
        print("🔒 Conexão com o banco encerrada.")