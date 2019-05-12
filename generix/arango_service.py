
class ArangoService:
    def __init__(self, connection, db_name):
        self.__connection = connection
        self.__db_name = db_name
    