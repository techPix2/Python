import  mysql.connector
from mysql.connector import Error

try:
    insert = mysql.connector.connect(
    host="localhost",
    port="3306",
    user="root",
    password="@",
    database="TechPix",
    ssl_disabled=True
)
except mysql.connector.Error as err:
    print(f"Error connecting to MySQL: {err}")
    raise

select = mysql.connector.connect(
    host="localhost",
    port="3306",
    user="root",
    password="@",
    database="TechPix",
    ssl_disabled=True
)   

cursorInsert = insert.cursor()
cursorSelect = select.cursor()

def buscarUsuario(name, password):
    """Retorna (success, company_id) se válido, False caso contrário"""
    query = "SELECT idEmployer, fkCompany FROM Employer WHERE name = %s AND password = %s"
    try:
        cursorSelect.execute(query, (name, password))
        result = cursorSelect.fetchone()
        if result:
            print("Login realizado com sucesso!")
            return (True, result[1])  # (success, company_id)
        else:
            print("Usuário ou senha incorretos!")
            return False
    except Error as e:
        print(f"Erro ao buscar usuário: {e}")
        return False

def cadastrarMaquina(hostname, macAdress, mobuId, fkCompany):
    query = """INSERT INTO Server 
               (hostname, macAddress, mobuId, fkCompany, status) 
               VALUES (%s, %s, %s, %s, 'active')"""
    try:
        cursorInsert.execute(query, (hostname, macAdress, mobuId, fkCompany))
        insert.commit()
        print("Máquina cadastrada com sucesso!")
    except Error as e:
        print(f"Erro ao cadastrar máquina: {e}")
        insert.rollback()

def buscarMaquina(mobuId, fkCompany):
    query = """SELECT idServer FROM Server 
               WHERE mobuId = %s AND fkCompany = %s"""
    cursorSelect.execute(query, (mobuId, fkCompany))
    result = cursorSelect.fetchone()
    return result[0] if result else None

def get_company_name(company_id):
    query = "SELECT socialReason FROM Company WHERE idCompany = %s"
    cursorSelect.execute(query, (company_id,))
    result = cursorSelect.fetchone()
    return result[0] if result else "TechPix"
