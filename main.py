from fastapi import FastAPI, HTTPException
import mysql.connector
import datetime
import bcrypt
import smtplib
from email.mime.text import MIMEText
import random

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
    return {"message": "Welcome!"}

@app.post("/users")
async def insert_user(nome: str, nome_usuario: str, email: str, senha: str):
    mycursor = mydb.cursor()
    query = "SELECT * FROM usuario WHERE email = %s OR nome_usuario = %s"
    mycursor.execute(query, (email, nome_usuario))
    linha = mycursor.fetchall()
    if not linha:
        hashed_password = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
        hashed_password_str = hashed_password.decode('utf-8')
        verification_code = random.randint(100000, 999999)
        query = "INSERT INTO usuario(nome, nome_usuario, email, senha, papel, status, data_criacao, codigo_verificacao) VALUES(%s, %s, %s, %s, 'usuario', 'aguardando confirmacao', %s, %s)"
        mycursor.execute(query, (nome, nome_usuario, email, hashed_password_str, datetime.datetime.now(), verification_code))
        mydb.commit()


        servidor_email = smtplib.SMTP('smtp.gmail.com', 587)
        servidor_email.starttls()
        servidor_email.login('studynestapp@gmail.com', 'fhyh vikm mpph yhdl')
        remetente = 'studynestapp@gmail.com'
        destinatario = [email]
        conteudo = (f'Olá, seja bem vindo(a)!\n'
                    f'Este é o seu código de verificação: {verification_code}.')

        msg = MIMEText(conteudo, _charset='UTF-8')
        msg['Subject'] = 'Boas vindas e código de verificação'
        msg['From'] = remetente
        msg['To'] = ', '.join(destinatario)

        servidor_email.sendmail(remetente, destinatario, msg.as_string())

        raise HTTPException(status_code=202, detail="Usuário cadastrado com sucesso")


    for informacao in linha:
        bd_email = informacao[2]
        bd_nome_usuario = informacao[1]

        if email == bd_email and nome_usuario == bd_nome_usuario:
            raise HTTPException(status_code=422, detail="Email e nome de usuário ja cadastrados")
        elif email == bd_email:
            raise HTTPException(status_code=422, detail="Email já cadastrado")
        else:
            raise HTTPException(status_code=422, detail="Nome de usuário já cadastrado")


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
        if not bcrypt.checkpw(senha.encode('utf-8'), password.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Senha incorreta")

    raise HTTPException(status_code=202, detail="Login realizado com sucesso")