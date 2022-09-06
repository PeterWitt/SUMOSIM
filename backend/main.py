import os
from pickle import FALSE, TRUE
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
destitnation_set = ''

# START of functions & variables related to SUMO simulation
# Creation of customer. Every Customer is called Cust and the number of created customers, i.e. cust1 
def createCust(time: int, custCount: int, pos:float, origin:str):
    traci.person.add(f"cust{custCount}",origin, pos, time+1, "DEFAULT_PEDTYPE")
    #Customer waits, Stage will be appended by different function 
    traci.person.appendWaitingStage(f"cust{custCount}", 1, description='waiting', stopID='')
    return f"cust{custCount}"   

# If destination is choosen, function adds Stage to the called costumer 
def createCustDest(custName: str, dest: str):
    traci.person.appendDrivingStage(custName, dest, "taxi")
    return TRUE



def createShuttle(time, num):
    traci.vehicle.add(f'taxiV{num}', 'depot', typeID='shuttle', depart=f'{time+2}', line='taxi')
    return f'taxiV{num}'

def custInfo(custName: str):
    if custName in traci.person.getIDList():
        custVehRes = traci.device
        custVeh = traci.person.getVehicle(custName)
        custDest = traci.person.getEdges(custName, )
        if custVeh == '':
            print('.', end="")

        if custVeh in traci.vehicle.getIDList():
            print(traci.vehicle.getDrivingDistance(custVeh, custDest[1], 0.0))

def shuttleInfo(shuttle_name: str):
     if traci.vehicle.getParameter(shuttle_name, "device.taxi.state") == 0:
            num = numpy.random.randint(1, 4)
            traci.vehicle.changeTarget(shuttle_name, f"depot{num}")
        
#    if shuttleName in traci.vehicle.getIDList():
#        shuttleCust = traci.vehicle.getParameter(shuttleName, "device.taxi.currentCustomers")
#        print(shuttleCust, end="")
#        if shuttleCust in traci.person.getIDList():
#            custDest = traci.person.getEdges(shuttleCust, )
#           print(traci.vehicle.getDrivingDistance(shuttleName, custDest[1], 0.0))
        

originList = ["-E65", "-E46", "E42", "-E55", "E57", "E40", "-E39.532", "-E69", "721302669#2", "-407581698#2", "407568055#4", "504565992#2"]
freihamLiving = ["-E65", "E65", "-E45", "E45", "-E46", "E46", "-E47", "E47", "-E44", "E44", "-E43", "E43", "-E48", "E48", "-E49", "E49", "-E51", "E51", "-E52", "E52", "-E69", "E69", "-E70", "E70", "-E71", "E71", "E72", "-E72", "E73", "-E73", "-E74", "E74", "504569022", "-504569022"]
destList = ["E39", "-721302669#2", "-513657853#0", "143578411#1"]

# END of functions & variables related to SUMO simulation

# START of Flask API

def start_sumo_background_task():
    global connection_established
    global destination_set
    
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    sumoBinary = "C:\Program Files (x86)\Eclipse\Sumo\\bin\sumo-gui"
    sumoCmd = [sumoBinary, "-c", ".\..\test.sumocfg", "--tripinfo-output", "tripinfos.xml",
        "--delay", "360.0", "--device.taxi.dispatch-algorithm", "greedy", "--start", "true"]

    traci.start(sumoCmd)
    step = 0
    count = 1
    managed_cust = []
    prt_shuttle = []
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        if connection_established:
            customer_info = dict()
            customer_info["cust_name"] = createCust(step+1, count, 190, '-E42')
            customer_info["dest_set"] = False
            managed_cust.append(customer_info)
            connection_established = False
        if destination_set != '':
            createCustDest(managed_cust[0]["cust_name"], destination_set)
            managed_cust[0]["dest_set"] = True
            destination_set = ''
        else:
            for cust_info in managed_cust:
                if not cust_info["dest_set"]:
                    traci.person.appendWaitingStage(cust_info["cust_name"], 1, description='waiting', stopID='')
        if step%10 == 0:
            for cust_info in managed_cust:
                if cust_info["dest_set"]:
                    if traci.person.getLaneID(cust_info["cust_name"]) != traci.person.getEdges(cust_info["cust_name"])[1]:
                        x, y = traci.person.getPosition(managed_cust[0]["cust_name"])
                        lon, lat = traci.simulation.convertGeo(x, y)
        
        if step == 20:
            prt_shuttle.append(createShuttle(step, count))
        
        for shuttle in prt_shuttle:
            shuttleInfo(shuttle) 
                    
        #if step % 130 == 0 :
        #    createCust(step, count, 0, freihamLiving[numpy.random.randint(0, 34)], destList[numpy.random.choice(numpy.arange(0,4), p=[0.1, 0.1, 0.1, 0.7])])
        #    print(count)
        #    count += 1
        #if 125 < step and step < 135:
        #    createShuttle(step, count) 
        #    count += 1 
        count += 1
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