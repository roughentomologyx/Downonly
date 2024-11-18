

import mysql.connector, time
from mysql.connector import errorcode
from datetime import datetime
import re, os
from dotenv import load_dotenv
load_dotenv()
table=os.getenv("TABLE")
def nextinc():
    cnx = connect_db()
    if cnx is None:
        print("Connection to database failed.")
        return
    try:
        cursor = cnx.cursor()
        # Check if bc_mintID matches the next auto_increment ID
        cursor.execute(f"SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'downonly' AND TABLE_NAME = '{table}'")
        next_auto_inc = cursor.fetchone()[0]
        print("nextinc:")
        print(next_auto_inc)
        if next_auto_inc is None:
            next_auto_inc=1
        return next_auto_inc
    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")
        raise Exception
    finally:
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()


def write2Mints(Jobstate, Surface, Obstacle, Characte, mintPrice, buyerAdress, buytxHash, blockHeight, bc_mintID, fullname):
    cnx = connect_db()
    if cnx is None:
        print("Connection to database failed.")
        return
    try:
        cursor = cnx.cursor()
        # Check if bc_mintID matches the next auto_increment ID
        cursor.execute(f"SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'downonly' AND TABLE_NAME = '{table}'")
        next_auto_inc = cursor.fetchone()[0]
        print("nextinc:")
        print(next_auto_inc)
        if next_auto_inc is None:
            next_auto_inc=1
        if next_auto_inc != bc_mintID:
            print("bc_mintID does not match the next auto increment value. Operation aborted.")
            print(next_auto_inc)
            print(bc_mintID)
            return

        now = datetime.now()
        formatted_now = now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        add_mint = (f"INSERT INTO {table} "
                    "(jobState, surface, obstacle, figure, openSea, ipfsGIF, ipfsJPEG, ipfsMP4, ipfsMP3, ipfsGLB, ipfsJSON, mintprice, fullname, buyerAddress, buytxHash, blockHeight, fallDistance) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
        data_mint = (
        Jobstate, Surface, Obstacle, Characte, None, None, None, None, None, None, None, mintPrice, fullname,
        buyerAdress, buytxHash, blockHeight, "10")

        print(data_mint)
        print("here")
        cursor.execute(add_mint, data_mint)
        cnx.commit()
    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")
        raise Exception
    finally:
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()


def read_from_database():
    cnx = connect_db()
    cursor = cnx.cursor()
    query = f"SELECT * FROM {table} ORDER BY id DESC LIMIT 1"
    cursor.execute(query)

    last_row = cursor.fetchone()
    print(last_row)

    cursor.close()
    cnx.close()





#def state_sanity_check():
def read_last_successfull_request():
    cnx = connect_db()
    cursor = cnx.cursor()
    query = f"SELECT * FROM {table} WHERE jobState = 'done' ORDER BY id DESC LIMIT 1;"
    cursor.execute(query)

    last_row = cursor.fetchone()
   # print(last_row)

    cursor.close()
    cnx.close()
    return last_row




def connect_db():
    try:
        cnx = mysql.connector.connect(user='renderer', password=os.getenv("DBPASS"),
                                      host=os.getenv("DBHOST"),
                                      database='downonly')

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    return cnx
'''
def update_job_state(newState, mintID):
    cnx=aconnect_db()
    try:
        cursor = cnx.cursor()
        update_statement = "UPDATE mints3 SET jobState = %s WHERE mintID = %s"
        async with cursor as cursor:
            await cursor.execute(update_statement, (newState, mintID))
        await cursor.commit()

    except Exception as e:
        # Handle any errors that occur
        print(f"Error: {e}")

    finally:
        # Ensure the cursor is closed properly
        if cnx.is_connected():
            cursor.close()  # Close cursor
            cnx.close()  # Close connection
            print("MySQL connection is closed")
'''
def update_column(columnName, newValue, mintID):
    cnx = connect_db()
    if cnx is None:
        print("Connection to database failed.")
        return

    try:
        cursor = cnx.cursor()
        update_statement = f"UPDATE {table} SET {columnName} = %s WHERE ID = %s"
        data = (newValue, mintID)
        cursor.execute(update_statement, data)
        cnx.commit()
        print(f"{columnName} updated to '{newValue}' for mintID {mintID}.")
    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")
    finally:
        if cnx:
            cnx.close()
def queryRow(mintID):
    cnx = connect_db()
    if cnx is None:
        return "Connection to database failed."
    try:
        cursor = cnx.cursor(dictionary=True)
        query = f"SELECT * FROM {table} WHERE mintID = %s"
        cursor.execute(query, (mintID,))
        row = cursor.fetchone()
        return row
    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")
        return None
    finally:
        if cnx:
            cnx.close()

def queryLastRow():
    cnx = connect_db()
    if cnx is None:
        return "Connection to database failed."
    try:
        cursor = cnx.cursor(dictionary=True)
        query = f"SELECT * FROM {table} ORDER BY id DESC LIMIT 1"
        cursor.execute(query)
        row = cursor.fetchone()
        return row
    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")
        return None
    finally:
        if cnx:
            cnx.close()

# Example usage


def getLastSuccess(retry_attempts=3):
    for attempt in range(retry_attempts):
        cnx = connect_db()
        if cnx is None:
            print("Connection to database failed.")
            if attempt < retry_attempts - 1:
                print("Retrying in 10 seconds...")

                continue
            else:
                raise Exception("Failed to connect to database after several attempts.")

        try:
            cursor = cnx.cursor(dictionary=True)
            # Check if table is empty first
            cursor.execute(f"SELECT COUNT(*) AS count FROM {table}")
            count_result = cursor.fetchone()
            if count_result and count_result['count'] == 0:
                return {"jobState": "first", "blockHeight": None}


                # Proceed to fetch the last successful entry
            query = f"SELECT * FROM {table} WHERE jobState = 'done' ORDER BY ID DESC LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            if result:
                return result

        except mysql.connector.Error as err:
                print(f"An error occurred: {err}")
                if attempt < retry_attempts - 1:
                    print("Retrying in 10 seconds...")
                    time.sleep(5)
                    continue
                else:
                    raise
        finally:
            if cnx:
                cnx.close()


def getFirstUnsuccess(retry_attempts=3):
    for attempt in range(retry_attempts):
        cnx = connect_db()
        if cnx is None:
            print("Connection to database failed.")
            if attempt < retry_attempts - 1:
                print("Retrying in 10 seconds...")
                time.sleep(10)
                continue
            else:
                raise Exception("Failed to connect to database after several attempts.")

        try:
            cursor = cnx.cursor(dictionary=True)
            # Query to find the first 'unsuccessful' job (not 'done')
            query = f"SELECT * FROM {table} WHERE jobState != 'done' ORDER BY ID ASC LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            if result:
                return result
            else:
                # If no entry is found that is not 'done', return an indication of such
                return {"jobState": "no_unsuc", "blockHeight": 0}
        except mysql.connector.Error as err:
            print(f"An error occurred: {err}")
            if attempt < retry_attempts - 1:
                print("Retrying in 10 seconds...")
                time.sleep(10)
                continue
            else:
                raise
        finally:
            if cnx:
                cnx.close()
        break


# Example usage
def read_value_from_column(columnName, mintID):
    cnx = connect_db()
    if cnx is None:
        print("Connection to database failed.")
        return None

    try:
        cursor = cnx.cursor()
        query = f"SELECT {columnName} FROM {table} WHERE id = %s"
        cursor.execute(query, (mintID,))
        result = cursor.fetchone()
        if result:
            return result[0]  # Return the value from the specified column
        else:
            return None  # Return None if no entry is found for the mintID
    except mysql.connector.Error as err:
        print(f"An error occurred: {err}")
        return None
    finally:
        if cnx:
            cnx.close()


def setup_new_table():
    cnx = connect_db()
    cursor = cnx.cursor()
    NEW_DB_NAME = 'downonly'
    SCHEMA_FILE = 'mints.sql'
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{NEW_DB_NAME}`")
        print(f"Database '{NEW_DB_NAME}' created successfully.")
    except mysql.connector.Error as err:
        print(f"Failed to create database: {err}")
        exit(1)

    # Read the schema.sql file
    with open(SCHEMA_FILE, 'r') as file:
        schema_sql = file.read()

    # Replace the database name in the schema
    schema_sql = re.sub(
        r'(?i)USE `.*?`;',
        f'USE `{NEW_DB_NAME}`;',
        schema_sql
    )
    schema_sql = re.sub(
        r'(?i)CREATE DATABASE IF NOT EXISTS `.*?`;',
        f'CREATE DATABASE IF NOT EXISTS `{NEW_DB_NAME}`;',
        schema_sql
    )

    # Split the SQL commands considering delimiters
    def split_sql_commands(sql):
        commands = []
        statement = ''
        delimiter = ';'
        for line in sql.splitlines():
            line = line.strip()
            if line.startswith('DELIMITER'):
                delimiter = line.split()[1]
                continue
            if line.endswith(delimiter):
                statement += line.rstrip(delimiter)
                commands.append(statement.strip())
                statement = ''
            else:
                statement += line + ' '
        return commands

    commands = split_sql_commands(schema_sql)

    # Execute each command
    for command in commands:
        if not command:
            continue
        try:
            cursor.execute(command)
        except mysql.connector.Error as err:
            print(f"Failed to execute command: {err}")
            print(f"Command: {command}\n")
            continue

    print("Schema imported successfully.")

    # Clean up
    cursor.close()
    cnx.close()

setup_new_table()