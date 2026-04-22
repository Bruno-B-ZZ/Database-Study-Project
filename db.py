import pymysql


def conectar():
    return pymysql.connect(
        host="localhost",
        port=3306,  # pode ser diferente
        user="root",
        password="123456",  # pode ser diferente
        database="Ejogos",
        cursorclass=pymysql.cursors.DictCursor,
    )
