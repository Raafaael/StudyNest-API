from fastapi import FastAPI, HTTPException, Response, Request
import mysql.connector
import datetime
import bcrypt
import smtplib
from email.mime.text import MIMEText
import random
import json

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
    return {"message": "welcome!"}

@app.post("/users")
async def insert_user(nome: str, nome_usuario: str, email: str, senha: str, confirma_senha: str):
    if senha == confirma_senha:
        mycursor = mydb.cursor()
        query = "SELECT * FROM usuario WHERE email = %s OR nome_usuario = %s"
        mycursor.execute(query, (email, nome_usuario))
        linha = mycursor.fetchall()
        if not linha:
            hashed_password = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
            hashed_password_str = hashed_password.decode('utf-8')
            verification_code = random.randint(100000, 999999)
            query = "INSERT INTO usuario(nome, nome_usuario, email, senha, papel, status, data_criacao, codigo_verificacao) VALUES(%s, %s, %s, %s, 'usuario', 'aguardando ativacao', %s, %s)"
            mycursor.execute(query, (
            nome, nome_usuario, email, hashed_password_str, datetime.datetime.now(), verification_code))
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
    else:
        raise HTTPException(status_code=422, detail="As senhas não são iguais")

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
        user_status = informacao[6]
        if not bcrypt.checkpw(senha.encode('utf-8'), password.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Senha incorreta")

        if bcrypt.checkpw(senha.encode('utf-8'), password.encode('utf-8')) and user_status != "aguardando ativacao":
            raise HTTPException(status_code=202, detail="Login realizado com sucesso")
        else:
            raise HTTPException(status_code=422,
                                detail="Conta não ativada. Ative sua conta com o código enviado por email para prosseguir")


@app.post("/sendemail")
async def send_email(email: str, typeofmessage: str):
    mycursor = mydb.cursor()
    query = "SELECT * FROM usuario WHERE email = %s"
    mycursor.execute(query, (email,))
    linha = mycursor.fetchall()

    if not linha:
        raise HTTPException(status_code=404, detail="Email não cadastrado")

    verification_code = random.randint(100000, 999999)

    query = "UPDATE usuario SET codigo_verificacao = %s WHERE email = %s"
    mycursor.execute(query, (verification_code, email))
    mydb.commit()

    servidor_email = smtplib.SMTP('smtp.gmail.com', 587)
    servidor_email.starttls()
    servidor_email.login('studynestapp@gmail.com', 'fhyh vikm mpph yhdl')
    remetente = 'studynestapp@gmail.com'
    destinatario = [email]

    for informacao in linha:
        bd_nome = informacao[0]

        if typeofmessage == "recover_password":
            conteudo = (f'Olá, {bd_nome}!\n'
                        f'Codigo de recuperação de senha: {verification_code}.\n'
                        f'Se tiver algum problema, entre em contato conosco!\n')
            msg = MIMEText(conteudo, _charset='UTF-8')
            msg['Subject'] = 'Recuperação de senha'
            msg['From'] = remetente
            msg['To'] = ', '.join(destinatario)

            servidor_email.sendmail(remetente, destinatario, msg.as_string())
            raise HTTPException(status_code=202, detail="Email enviado com sucesso")
        elif typeofmessage == "activate_account":
            conteudo = (f'Olá, {bd_nome}!\n'
                        f'Codigo para ativar sua conta: {verification_code}.\n'
                        f'Se tiver algum problema, entre em contato conosco!\n')
            msg = MIMEText(conteudo, _charset='UTF-8')
            msg['Subject'] = 'Ativação da conta'
            msg['From'] = remetente
            msg['To'] = ', '.join(destinatario)

            servidor_email.sendmail(remetente, destinatario, msg.as_string())
            raise HTTPException(status_code=202, detail="Email enviado com sucesso")


@app.get("/code/{email}/{code}")
async def verify_code(email: str, code: int):
    mycursor = mydb.cursor()
    query = "SELECT * FROM usuario WHERE email = %s"
    mycursor.execute(query, (email,))
    linha = mycursor.fetchall()

    for informacao in linha:
        bd_code = informacao[8]
        bd_user_status = informacao[6]

        if bd_user_status == "ativo":
            if code == bd_code:
                raise HTTPException(status_code=202, detail="Código correto")
            else:
                raise HTTPException(status_code=401, detail="Código incorreto")
        else:
            if code == bd_code:
                query = "UPDATE usuario SET status = %s WHERE email = %s"
                mycursor.execute(query, ('ativo', email))
                mydb.commit()
                raise HTTPException(status_code=202, detail="Código correto")
            else:
                raise HTTPException(status_code=401, detail="Código incorreto")

@app.post("/newpassword")
async def new_password(email: str, senha: str, confirma_senha: str):
    if senha == confirma_senha:
        mycursor = mydb.cursor()
        hashed_password = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
        hashed_password_str = hashed_password.decode('utf-8')
        query = "UPDATE usuario SET senha = %s WHERE email = %s"
        mycursor.execute(query, (hashed_password_str, email))
        mydb.commit()
        raise HTTPException(status_code=202, detail="Senha atualizada com sucesso")
    else:
        raise HTTPException(status_code=422, detail="As senhas não são iguais")

@app.get("/disciplinas")
async def get_disciplinas():
    mycursor = mydb.cursor()
    query = "SELECT codigo, disciplina FROM disciplina"
    mycursor.execute(query)
    disciplinas = mycursor.fetchall()

    codigos_unicos = set()
    result = []

    for codigo, disciplina in disciplinas:
        if codigo not in codigos_unicos:
            codigos_unicos.add(codigo)
            result.append(f"{codigo}/{disciplina}")

    return Response(content=json.dumps(result), media_type="application/json")

@app.get("/turmas/{codigo_disciplina:path}")
async def get_turmas(codigo_disciplina: str):
    codigo = codigo_disciplina.split('/')[0]
    mycursor = mydb.cursor()
    query = "SELECT turma FROM disciplina WHERE codigo = %s"
    mycursor.execute(query, (codigo,))
    turmas = mycursor.fetchall()

    if not turmas:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")

    result = [turma[0] for turma in turmas]

    return Response(content=json.dumps(result), media_type="application/json")

@app.post("/add_grade")
async def add_grade(email_usuario: str, codigo_disciplina: str, turma_disciplina: str):
    try:
        if not all([email_usuario, codigo_disciplina, turma_disciplina]):
            raise HTTPException(status_code=400, detail="Todos os campos são obrigatórios")

        mycursor = mydb.cursor()
        query = "INSERT INTO grade (email_usuario, codigo_disciplina, turma_disciplina) VALUES (%s, %s, %s)"
        mycursor.execute(query, (email_usuario, codigo_disciplina, turma_disciplina))
        mydb.commit()

        return {"message": "Dados inseridos com sucesso"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a requisição: {str(e)}")

@app.get("/resumos")
async def get_resumos():
    mycursor = mydb.cursor()
    query = "SELECT DISTINCT disciplina.disciplina, disciplina.codigo, resumo.titulo FROM resumo LEFT JOIN disciplina ON resumo.codigo_disciplina = disciplina.codigo"
    mycursor.execute(query)
    resumos = mycursor.fetchall()

    result = []

    for nome_disciplina, codigo_disciplina, titulo in resumos:
        result.append({"nome_disciplina": nome_disciplina, "codigo_disciplina": codigo_disciplina, "titulo": titulo})

    return Response(content=json.dumps(result), media_type="application/json")

@app.post("/add_resumo")
async def add_resumo(email_usuario: str, codigo_disciplina: str, titulo: str, conteudo: str):
    if not all([email_usuario, codigo_disciplina, titulo, conteudo]):
        raise HTTPException(status_code=400, detail="Todos os campos são obrigatórios")

    mycursor = mydb.cursor()
    query = "INSERT INTO resumo (email_usuario, codigo_disciplina, titulo, conteudo, data) VALUES (%s, %s, %s, %s, %s)"
    codigo_disciplina_separado = codigo_disciplina.split('/')[0]
    mycursor.execute(query, (email_usuario, codigo_disciplina_separado, titulo, conteudo, datetime.datetime.now()))
    mydb.commit()

    raise HTTPException(status_code=201, detail="Resumo criado com sucesso")

@app.get("/disciplinasCadastradas/{email_usuario}")
async def get_disciplinasCadastradas(email_usuario: str):
    mycursor = mydb.cursor()
    query = "SELECT codigo_disciplina FROM grade WHERE email_usuario = %s"
    mycursor.execute(query, (email_usuario,))
    disciplinas = mycursor.fetchall()

    if not disciplinas:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")

    result = [disciplina[0] for disciplina in disciplinas]

    return Response(content=json.dumps(result), media_type="application/json")