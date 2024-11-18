import time
import os
import json
import logging
import mysql.connector
from mysql.connector import errorcode
from web3 import Web3
from dotenv import load_dotenv

# Attempt to import RPi.GPIO, otherwise use a mock for non-RPi systems
try:
    import RPi.GPIO as GPIO
except ImportError:
    class MockGPIO:
        BCM = 'BCM'
        OUT = 'OUT'
        HIGH = True
        LOW = False

        @staticmethod
        def setmode(mode):
            print(f"GPIO mode set to {mode}")

        @staticmethod
        def setup(pin, mode):
            print(f"GPIO pin {pin} set up as {mode}")

        @staticmethod
        def output(pin, state):
            if state == MockGPIO.LOW:  # Only print when setting the motor to LOW
                print(f"GPIO pin {pin} output set to LOW")

        @staticmethod
        def cleanup():
            print("GPIO cleanup called")


    GPIO = MockGPIO()

# Load environment variables
load_dotenv()
logging.basicConfig(filename='update_eth_motor_time.log', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')

STATE_FILE_ETH_SPENT = './ethSpentState.txt'
STATE_FILE_TIME_REMAINING = './motorTimeRemaining.txt'
INFURA_URL = os.getenv('INFURA_URL')
GPIO_PIN = 21


# Load state
def load_state_eth_spent():
    if os.path.exists(STATE_FILE_ETH_SPENT):
        with open(STATE_FILE_ETH_SPENT, 'r') as f:
            try:
                eth_spent = float(f.read().strip())
                logging.debug(f"Loaded ETH spent from state file: {eth_spent}")
                return eth_spent
            except ValueError:
                logging.error("Failed to convert ETH spent value to float. Resetting to 0.0.")
                return 0.0
    return 0.0


def load_state_time_remaining():
    if os.path.exists(STATE_FILE_TIME_REMAINING):
        with open(STATE_FILE_TIME_REMAINING, 'r') as f:
            try:
                time_remaining = float(f.read().strip())
                logging.debug(f"Loaded time remaining from state file: {time_remaining}")
                return time_remaining
            except ValueError:
                logging.error("Failed to convert time remaining value to float. Resetting to 0.0.")
                return 0.0
    return 0.0


# Save state
def save_state_eth_spent(eth_spent):
    with open(STATE_FILE_ETH_SPENT, 'w') as f:
        f.write(f"{eth_spent:.18f}")
    logging.debug(f"Saved ETH spent to state file: {eth_spent}")


def save_state_time_remaining(time_remaining):
    with open(STATE_FILE_TIME_REMAINING, 'w') as f:
        f.write(f"{time_remaining:.2f}")
    logging.debug(f"Saved time remaining to state file: {time_remaining}")


# Connect to database
def connect_db():
    try:
        cnx = mysql.connector.connect(
            user='renderer',
            password=os.getenv("DBPASS"),
            host=os.getenv("DBHOST"),
            database='downonly'
        )
        return cnx
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return None


# Update motor status in the database
def update_motor_status(is_pushing, motor_running):
    if motor_running == is_pushing:
        # No need to update the database if the motor is already in the correct state
        #logging.debug(f"Motor status is already correct (is_pushing={is_pushing}), skipping database update.")
        return True

    connection = connect_db()
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE pushing SET isPushing = %s WHERE id = 1", (1 if is_pushing else 0,))
        connection.commit()
        return True
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return False
    finally:
        if connection:
            cursor.close()
            connection.close()


# Update motor time based on blockchain ETH spent value
def update_motor_time(web3, contract_address, contract_abi):
    try:
        contract = web3.eth.contract(address=contract_address, abi=contract_abi)
        current_eth_spent = load_state_eth_spent()
        eth_spent_from_contract = contract.functions.motorPushedByCM().call()
        eth_spent_from_contract = float(web3.from_wei(eth_spent_from_contract, 'ether'))
        logging.debug(f"ETH spent from blockchain: {eth_spent_from_contract}, current state: {current_eth_spent}")
        overTheCliff=contract.functions.isAuctionOverTheCliff().call()
        ended=contract.functions.ended().call()
        if overTheCliff or ended:
            save_state_time_remaining(500)
            print("end auction here")
        if eth_spent_from_contract > current_eth_spent:

            eth_difference = eth_spent_from_contract - current_eth_spent
            logging.debug(
                f"ETH difference calculation: eth_difference = eth_spent_from_contract - current_eth_spent -> {eth_difference} ETH")
            seconds_to_add = eth_difference * 63.16  # 63.16 minutes per 1 ETH
            logging.debug(
                f"Calculating seconds to add for motor push: seconds_to_add = eth_difference * 63.16 -> {seconds_to_add} seconds (ETH difference: {eth_difference} * 63.16 minutes per ETH)")
            time_remaining = load_state_time_remaining() + seconds_to_add
            save_state_time_remaining(time_remaining)
            save_state_eth_spent(eth_spent_from_contract)
            logging.info(f"Updated time remaining by {seconds_to_add} seconds, new time remaining: {time_remaining}")
        elif eth_spent_from_contract < current_eth_spent:
            logging.warning(
                f"ETH spent decreased from {current_eth_spent} to {eth_spent_from_contract}, resetting state to match blockchain.")
            save_state_eth_spent(eth_spent_from_contract)
    except Exception as e:
        logging.error(f"An error occurred in update_motor_time: {e}", exc_info=True)


# Control motor
def control_motor(web3, contract_address, contract_abi):
    motor_running = False
    last_update_time = 0
    while True:
        try:
            current_time = time.time()

            # Update blockchain data every 10 seconds
            if current_time - last_update_time > 30:
                update_motor_time(web3, contract_address, contract_abi)
                last_update_time = current_time

            time_remaining = load_state_time_remaining()
            logging.debug(f"Motor control loop: time remaining = {time_remaining}")
            if time_remaining > 0:
                if not motor_running:
                    if update_motor_status(True, motor_running):
                        GPIO.output(GPIO_PIN, GPIO.HIGH)
                        motor_running = True
                        logging.info("Motor turned ON")
                time.sleep(0.098)
                time_remaining -= 0.1
                save_state_time_remaining(max(time_remaining, 0))
            else:
                GPIO.output(GPIO_PIN, GPIO.LOW)
                if motor_running:
                    if update_motor_status(False, motor_running):
                        motor_running = False
                        logging.info("Motor turned OFF")
                time.sleep(1)
        except Exception as e:
            logging.error(f"An unexpected error occurred in the motor control loop: {e}", exc_info=True)


if __name__ == "__main__":
    # Register signal handler for graceful termination
    import signal
    import sys


    def signal_handler(sig, frame):
        logging.info('Exiting gracefully')
        GPIO.output(GPIO_PIN, GPIO.LOW)
        update_motor_status(False, motor_running=True)
        GPIO.cleanup()
        sys.exit(0)


    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GPIO_PIN, GPIO.OUT)

        # Initialize Web3
        web3 = Web3(Web3.HTTPProvider(INFURA_URL))
        contract_address = os.getenv('AUCTIONCONTRACT_ADDRESS')
        contract_data_path = "./contracts/dutchAuction.json"
        contract_abi = None
        with open(contract_data_path, 'r') as file:
            contract_abi = json.load(file)

        # Control motor and update blockchain data
        control_motor(web3, contract_address, contract_abi)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        GPIO.output(GPIO_PIN, GPIO.LOW)
        update_motor_status(False, motor_running=True)
        GPIO.cleanup()
