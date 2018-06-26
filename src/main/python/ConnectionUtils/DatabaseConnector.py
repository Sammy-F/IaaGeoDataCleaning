import psycopg2 as psy
from configparser import ConfigParser

from tkinter import Tk, filedialog

class DatabaseConnector:

    def __init__(self):
        self.connection = None

    def __setConfig(self, filePath, section='postgresql'):
        """
        Load config file and return database params
        based off of it
        :param filePath:
        :param section:
        :return:
        """
        parser = ConfigParser()
        parser.read(filePath)

        db = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filePath))
        return db

    def getConnectFromConfig(self, section='postgresql', filePath=False):
        """
        Connect to database from parameters
        :param filePath:
        :param section:
        :return:
        """
        if filePath is False or filePath == '':
            Tk().withdraw()
            filePath = filedialog.askopenfilename(title='Please select a config.ini file')

        if not self.connection is None:
            self.connection.close()
            self.connection = None
        try:
            params = self.__setConfig(filePath, section)

            print('Attempting connection to PostgreSQL database...')
            self.connection = psy.connect(**params)

            cur = self.connection.cursor()
            print('PostgreSQL database version:')
            cur.execute('SELECT version()')

            db_version = cur.fetchone()
            print(db_version)

            cur.close()

            print("Connection opened. Don't forget to call closeConnection() on the DatabaseConnector when you're done!")

            return self.connection
        except (Exception, psy.DatabaseError) as error:
            print(error)
            print("Woops")
            if self.connection is not None:
                self.connection.close()
                print('Connection closed.')
                self.connection = None

    def getConnectFromKeywords(self, host, dbname, username, password, port=5432):
        """
        Set up from keywords, not secure
        :param host:
        :param dbname:
        :param username:
        :param password:
        :param port:
        """
        if not self.connection is None:
            self.connection.close
            self.connection = None

        try:
            print('Attempting connection to PostgreSQL database...')
            self.connection = None
            self.connection = psy.connect(host=host, database=dbname, user=username, password=password, port=port)

            cur = self.connection.cursor()
            print('PostgreSQL database version:')
            cur.execute('SELECT version()')
            db_version = cur.fetchone()
            print(db_version)
            cur.close()

            return self.connection
        except (Exception, psy.DatabaseError) as error:
            print(error)
            if self.connection is not None:
                self.connection.close()
                print('Connection closed.')
                self.connection = None

    def getExistingConnection(self):
        return self.connection

    def closeConnection(self):
        """
        Close the connection to the database if it exists.
        :return:
        """
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            print("Connection closed.")
