import os
from sqlite3 import connect 
import sys
import traci
import numpy
from flask import Flask, request
from threading import Thread

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# True if user launches the app
connection_established = False

# START of functions & variables related to SUMO simulation
def createCust(time: int, custCount: int, pos:float, origin:str, dest:str):
    traci.person.add(f"cust{custCount}",origin, pos, time+1, "DEFAULT_PEDTYPE")
    traci.person.appendDrivingStage(f"cust{custCount}", dest, "taxi")

def createShuttle(time, num):
    traci.vehicle.add(f'taxiV{num}', 'depot', typeID='shuttle', depart=f'{time+2}', line='taxi')

def custInfo(custName: str):
    if custName in traci.person.getIDList():
        custVehRes = traci.device
        custVeh = traci.person.getVehicle(custName)
        custDest = traci.person.getEdges(custName, )
        if custVeh == '':
            print('.', end="")

        if custVeh in traci.vehicle.getIDList():
            print(traci.vehicle.getDrivingDistance(custVeh, custDest[1], 0.0))

def shuttleInfo(shuttleName: str):
    if shuttleName in traci.vehicle.getIDList():
        shuttleCust = traci.vehicle.getParameter(shuttleName, "device.taxi.currentCustomers")
        print(shuttleCust, end="")
        if shuttleCust in traci.person.getIDList():
            custDest = traci.person.getEdges(shuttleCust, )
            print(traci.vehicle.getDrivingDistance(shuttleName, custDest[1], 0.0))
        

originList = ["-E65", "-E46", "E42", "-E55", "E57", "E40", "-E39.532", "-E69", "721302669#2", "-407581698#2", "407568055#4", "504565992#2"]
freihamLiving = ["-E65", "E65", "-E45", "E45", "-E46", "E46", "-E47", "E47", "-E44", "E44", "-E43", "E43", "-E48", "E48", "-E49", "E49", "-E51", "E51", "-E52", "E52", "-E69", "E69", "-E70", "E70", "-E71", "E71", "E72", "-E72", "E73", "-E73", "-E74", "E74", "504569022", "-504569022"]
destList = ["E39", "-721302669#2", "-513657853#0", "143578411#1"]

# END of functions & variables related to SUMO simulation

# START of Flask API

def start_sumo_background_task():
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    sumoBinary = "C:\Program Files (x86)\Eclipse\Sumo\\bin\sumo-gui"
    sumoCmd = [sumoBinary, "-c", "..\SUMOSIM\\test.sumocfg", "--tripinfo-output", "tripinfos.xml",
        "--device.taxi.dispatch-algorithm", "greedy", "--start", "true"]

    traci.start(sumoCmd)
    step = 0
    count = 1
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        #if step % 130 == 0 :
        #    createCust(step, count, 0, freihamLiving[numpy.random.randint(0, 34)], destList[numpy.random.choice(numpy.arange(0,4), p=[0.1, 0.1, 0.1, 0.7])])
        #    print(count)
        #    count += 1
        #if 125 < step and step < 135:
        #    createShuttle(step, count) 
        #    count += 1 

        step += 1

    traci.close()

@app.route('/establish-connection', methods=['POST'])
def establish_connection():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
        if json["connectionEstablished"] == 'true':
            connection_established = True
            print(connection_established)
        return json
    else:
        return 'Content-Type not supported!'


if __name__ == "__main__":
    thread = Thread(target=start_sumo_background_task)
    thread.daemon = True
    thread.start()
    app.run('0.0.0.0', debug=True)