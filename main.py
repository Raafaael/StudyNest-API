from fastapi import FastAPI, HTTPException
import mysql.connector
import datetime

mydb = mysql.connector.connect(
  host="uom.h.filess.io",
  user="StudyNest_terribleus",
  password="e94cfa743e1d5dfb3e65b45c0075034f012298f4",
  database="StudyNest_terribleus",
  port=3307
)

app = FastAPI()

@app.get("/")
async def root():
    return "welcome!"

@app.post("/users")
async def insert_user(nome: str, nome_usuario: str, email: str, senha: str):
    mycursor = mydb.cursor()
    query = "INSERT INTO usuario(nome, nome_usuario, email, senha, papel, status, data_criacao) VALUES(%s, %s, %s, %s, 'usuario', 'aguardando confirmacao', %s)"
    mycursor.execute(query, (nome, nome_usuario, email, senha, datetime.datetime.now()))
    mydb.commit()
    raise HTTPException(status_code=202, detail="Usuário cadastrado com sucesso")

@app.get("/users/{email}/{senha}")
async def check_users(email: str, senha: str):
    mycursor = mydb.cursor()
    query = "SELECT * FROM usuario WHERE email = %s"
    mycursor.execute(query, (email,))
    linha = mycursor.fetchall()

    if not linha:
        raise HTTPException(status_code=404, detail="Usuário não existe")

    for informacao in linha:
        password = informacao[3]
        if password != senha:
            raise HTTPException(status_code=401, detail="Senha incorreta")

    raise HTTPException(status_code=202, detail="Login realizado com sucesso")