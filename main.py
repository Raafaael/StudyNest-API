from fastapi import FastAPI
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


@app.get("/users/{email}/{senha}")
async def check_users(email: str, senha: str):
    mycursor = mydb.cursor()
    query = "SELECT * FROM usuario WHERE email = %s"
    mycursor.execute(query, (email,))
    linha = mycursor.fetchall()

    if linha is None:
        return {"message": "Usuário não existe"}

    for informacao in linha:
        password = informacao[3]
        if password != senha:
            return {"message": "Senha incorreta"}

    return {"message": "Login bem-sucedido"}


