import threading, logging, logging.handlers, os, mysql.connector, datetime, time, signal
from configparser import ConfigParser
from dataFlow.mdp import mainDataProcessor
from dataFlow.reload import reloadEndpoints as REP

#=========================== CONFIG ============================#
parser = ConfigParser()
parser.read('/home/app/config/dataFlowSecret.conf')

db_host = parser.get('db', 'host')
db_user = parser.get('db', 'user')
db_pass = parser.get('db', 'password')
db_db = parser.get('db', 'db')

smtp_mailhost = parser.get('smtp', 'mailhost')
smtp_fromaddr = parser.get('smtp', 'fromaddr')
smtp_toaddrs = parser.get('smtp', 'toaddrs')
smtp_password = parser.get('smtp', 'password')

invoiceFolder = '/home/app/invoices/'
logFolder = '/home/app/dataFlowLogs/'

#=========================== LOGGING ============================#
# debug logger
debugLogger = logging.getLogger('dataFlowDebug')
debugLogger.setLevel(logging.DEBUG)
debugFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
debugFileHandler = logging.FileHandler('{}{}'.format(logFolder, 'dataFlowDebug.log'))
debugFileHandler.setFormatter(debugFormatter)
debugLogger.addHandler(debugFileHandler)

# error logger
errorLogger = logging.getLogger('dataFlowError')
errorLogger.setLevel(logging.ERROR)
errorFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
errorFileHandler = logging.FileHandler('{}{}'.format(logFolder, 'error.log'))
errorFileHandler.setFormatter(errorFormatter)
errorLogger.addHandler(errorFileHandler)

# smtp logger
smtpLogger = logging.getLogger('dataFlowSMTP')
smtpLogger.setLevel(logging.CRITICAL)
smtpFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
smtpHandler = logging.handlers.SMTPHandler(mailhost=(smtp_mailhost, 587), fromaddr=smtp_fromaddr, toaddrs=smtp_toaddrs, subject='WMS CRITICAL FAILURE', credentials=(smtp_fromaddr,smtp_password), secure=())
smtpHandler.setFormatter(smtpFormatter)
smtpLogger.addHandler(smtpHandler)

#================ GLOBAL VARIABLES AND FUNCTIONS ================#
# main
mainStatus = str()
mainCommand = str()
mainCycleTime = int()
mainQuit = False
# mdp
mdpStatus = str()
mdpCommand = str()
mdpCycleTime = int()
mdpDecisionThread = None
MDP = None
#endpoints
endpointStatuses = dict()
endpointCommands = dict()
endpoints = dict()
scanningThreads = dict()

def signal_handler(sig, frame):
    debugLogger.debug('signal_handler - sig: {} - frame: {}'.format(sig, frame))
    global mainQuit
    try:
        mainQuit = True
    except:
        debugLogger.exception('signal_handler traceback')
        errorLogger.error('signal_handler traceback')

signal.signal(signal.SIGINT, signal_handler)

def setToReloading():
    debugLogger.debug('setToReloading...')
    global mainStatus, mainCommand, mdpStatus, mdpCommand

    if mainCommand == 'SUSPEND' or mdpCommand == 'SUSPEND':
        debugLogger.error('Can not reload while command is suspend!')
        errorLogger.error('Can not reload while command is suspend!')
        return False

    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_pass, db=db_db)
        cur = conn.cursor()
        cur.execute('UPDATE dataflow_dataflow SET status = %s, command = %s WHERE command != %s AND name != %s', ('RELOADING', 'STAND BY', 'SUSPEND', 'MAIN'))
        cur.execute('UPDATE dataflow_dataflow SET status = %s, command = %s WHERE name = %s', ('RELOADING', 'RUN', 'MAIN'))
        conn.commit()
    except Exception as e:
        debugLogger.exception('Failed to reset statuses and commands: {}'.format(e))
        errorLogger.error('Failed to reset statuses and commands: {}'.format(e))
        return False
    finally:
        try: conn.close()
        except: pass

    mainStatus = 'RELOADING'
    mainCommand = 'STAND BY'
    mdpStatus = 'RELOADING'
    mdpCommand = 'STAND BY'

    debugLogger.debug('setToReloading successful.')
    return True

def getSettings():
    debugLogger.debug('getSettings...')
    global mainCycleTime, mdpCycleTime
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_pass, db=db_db)
        cur = conn.cursor()
        cur.execute('SELECT name, cycleTime FROM dataflow_dataflow WHERE name = %s OR name = %s ORDER BY name ASC', ('MAIN', 'MDP'))
        mainCycleTime = cur.fetchone()[1]
        mdpCycleTime = cur.fetchone()[1]
    except Exception as e:
        debugLogger.exception('Failed to getSettings: {}'.format(e))
        errorLogger.error('Failed to getSettings: {}'.format(e))
        return False
    finally:
        try: conn.close()
        except: pass

    debugLogger.debug('getSettings - mainCycleTime: {} - mdpCycleTime:{}'.format(mainCycleTime, mdpCycleTime))
    return True

def updateMainStatus():
    debugLogger.debug('Updating status - mainStatus: {}'.format(mainStatus))
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_pass, db=db_db)
        cur = conn.cursor()
        cur.execute('UPDATE dataflow_dataflow SET status = %s, lastupdate = %s WHERE name = %s', (mainStatus, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'MAIN'))
        conn.commit()
    except Exception as e:
        debugLogger.exception('Failed to update main status! - error: {}'.format(e))
        errorLogger.error('Failed to update main status! - error: {}'.format(e))
        return False
    finally:
        try: conn.close()
        except: pass

    debugLogger.debug('Successful to update main status.')
    return True

def updateMDPStatus():
    debugLogger.debug('Updating status - mdpStatus: {}'.format(mdpStatus))
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_pass, db=db_db)
        cur = conn.cursor()
        cur.execute('UPDATE dataflow_dataflow SET status = %s, lastupdate = %s WHERE name = %s', (mdpStatus, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'MDP'))
        conn.commit()
    except Exception as e:
        debugLogger.exception('Failed to update MDP status! - error: {}'.format(e))
        errorLogger.error('Failed to update MDP status! - error: {}'.format(e))
        return False
    finally:
        try: conn.close()
        except: pass

    debugLogger.debug('Successful to update MDP status.')
    return True

def updateEndpointStatuses():
    debugLogger.debug('updateEndpointStatuses - Trying to update database...')
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_pass, db=db_db)
        cur = conn.cursor()
        for endpointId, status in endpointStatuses.items() : cur.execute('UPDATE dataflow_dataflow SET status = %s, lastupdate = %s WHERE id = %s', (status, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), endpointId))
        conn.commit()
    except Exception as e:
        debugLogger.exception('updateEndpointStatuses - Failed to update database: {}'.format(e))
        errorLogger.error('updateEndpointStatuses - Failed to update database: {}'.format(e))
        return False
    finally:
        try: conn.close()
        except: pass

    debugLogger.debug('updateEndpointStatuses - Successful to update database.')
    return True

def getCommands():
    debugLogger.debug('getCommands')
    global mainCommand, mdpCommand, endpointCommands
    endpointCommands.clear()
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_pass, db=db_db)
        cur = conn.cursor()
        cur.execute('SELECT name, command FROM dataflow_dataflow WHERE name = %s OR name = %s ORDER BY name ASC', ('MAIN', 'MDP'))
        mainCommand = cur.fetchone()[1]
        mdpCommand = cur.fetchone()[1]
        cur.execute('SELECT id, command FROM dataflow_dataflow WHERE name != %s AND name != %s', ('MAIN', 'MDP'))
        for row in cur : endpointCommands[str(row[0])] = row[1]
    except Exception as e:
        debugLogger.exception('Failed to getCommands: {}'.format(e))
        errorLogger.error('Failed to getCommands: {}'.format(e))
        return False
    finally:
        try: conn.close()
        except: pass

    debugLogger.debug('getCommands - mainCommand: {} - mdpCommand: {} - endpointCommands: {}'.format(mainCommand, mdpCommand, endpointCommands))
    return True

def reloadEndpoints():
    debugLogger.debug('reloadEndpoints - Reloading endpoints...')
    global endpointStatuses, endpointCommands, endpoints, scanningThreads
    endpointStatuses, endpointCommands, endpoints, scanningThreads, isSucceed_reloadFunc = REP(debugLogger, errorLogger, smtpLogger, logFolder, db_host, db_user, db_pass, db_db, invoiceFolder, endpointStatuses, endpointCommands, endpoints, scanningThreads)
    if not isSucceed_reloadFunc:
        debugLogger.critical('reloadEndpoints - Reload Failed - Fix the problem and send reload command again.')
        errorLogger.critical('reloadEndpoints - Reload Failed - Fix the problem and send reload command again.')
        #smtpLogger.critical('reloadEndpoints - Reload Failed - Fix the problem and send reload command again.')
        return False

    debugLogger.debug('reloadEndpoints - Successful to reload endpoints.')
    return True

def mainLoop():
    global mainStatus, mainCommand, mainCycleTime, mdpStatus, mdpCommand, mdpCycleTime, mdpDecisionThread, MDP, endpointStatuses, endpointCommands, endpoints, scanningThreads

    debugLogger.debug('****** DATAFLOW MAIN LOOP IS RUNNING ******')
    mainStatus = 'RUNNING'
    if not updateMainStatus():
        debugLogger.error('mainLoop - Failed to update main status!')
        errorLogger.error('mainLoop - Failed to update main status!')

    while True:
        start = time.perf_counter()
        debugLogger.debug('============================================================')
        debugLogger.debug('mainLoop - Cycle is starting...')

        # check for quit command
        debugLogger.debug('mainLoop - Checking for quit order...')
        if mainQuit: break

        # get commands
        debugLogger.debug('mainLoop - Retrieving commands from database...')
        if not getCommands():
            debugLogger.critical('mainLoop - getCommands failed!')
            errorLogger.critical('mainLoop - getCommands failed!')
            #smtpLogger.critical('dataFlow mainloop couldn\'t retrieve commands from database!')
            time.sleep(5)
            continue

        #region main operations and status update
        debugLogger.debug('mainLoop - Region main operations...')

        if mainCommand == 'RELOAD' and mainCommand != 'RELOADING':
            debugLogger.debug('mainLoop - Main reload command...')

            # stop decision thread
            debugLogger.debug('mainLoop - Stopping MDP...')
            if MDP != None: MDP.quit = True
            if mdpDecisionThread!= None: mdpDecisionThread.join()

            # setToReloading
            debugLogger.debug('mainLoop - SetToReloading...')
            if not setToReloading():
                debugLogger.critical('mainLoop - setToReloading Failed!')
                errorLogger.critical('mainLoop - setToReloading Failed!')
                continue
            debugLogger.debug('mainLoop - SetToReloading Successful.')

            # LOAD SETTINGS FOR MAIN AND MDP FROM DATABASE
            debugLogger.debug('mainLoop - Load settings...')
            if not getSettings():
                debugLogger.critical('mainLoop - getSettings Failed!')
                errorLogger.critical('mainLoop - getSettings Failed!')
                continue
            debugLogger.debug('mainLoop - Load settings successful.')

            # reload enpoints
            debugLogger.debug('mainLoop - Load endpoints...')
            if not reloadEndpoints():
                debugLogger.critical('mainLoop - reloadEndpoints Failed!')
                errorLogger.critical('mainLoop - reloadEndpoints Failed!')
                continue
            debugLogger.debug('mainLoop - Load endpoints successful.')

            # LOAD MDP AND UPDATE STATUS
            debugLogger.debug('mainLoop - Loading MDP...')
            try:
                MDP = mainDataProcessor(db_host, db_user, db_pass, db_db, logFolder, mdpCycleTime, endpointStatuses, endpoints, scanningThreads)
            except Exception as e:
                debugLogger.exception('mainLoop - Failed to load MDP!')
                errorLogger.critical('mainLoop - Failed to load MDP!')
                continue
            debugLogger.debug('mainLoop - Load MDP successful.')

            # UPDATE STATUS FOR MAIN AND MDP
            mainStatus = 'RUNNING'
            mdpStatus = 'STANDING BY'
            debugLogger.debug('mainLoop - Update Main and MDP status...')
            if not (updateMainStatus() and updateMDPStatus()):
                debugLogger.critical('mainLoop - updateStatus Failed!')
                errorLogger.critical('mainLoop - updateStatus Failed!')
                continue
            debugLogger.debug('mainLoop - Update Main and MDP status successful.')

            debugLogger.debug('mainLoop - Reload successful.')
            continue

        debugLogger.debug('mainLoop - Main status update...')
        if updateMainStatus():
            debugLogger.debug('mainLoop - Main status updated.')
        else:
            debugLogger.critical('updateStatus Failed!')
            errorLogger.critical('updateStatus Failed!')
            #smtpLogger.critical('updateStatus Failed!')
        #endregion

        #region endpoint operations and status updates
        debugLogger.debug('mainLoop - Region endpoint operations...')
        for endpointId, endpoint in endpoints.items():

            if endpointCommands[endpointId] == 'RUN':

                if endpointStatuses[endpointId] == 'RUNNING' : pass

                elif endpointStatuses[endpointId] == 'STANDING BY':
                    debugLogger.debug('mainLoop - Endpoint run command... - endpointId: {} - endpointStatus: {}'.format(endpointId, endpointStatuses[endpointId]))
                    try:
                        endpoint.quit = False
                        x = threading.Thread(target=endpoint.scanningThread)
                        x.start()
                        scanningThreads[str(endpointId)] = x
                    except Exception as e:
                        debugLogger.exception('mainLoop - Failed to initiate scanningThread! - endpointId: {} - error: {}'.format(endpointId, e))
                        errorLogger.critical('mainLoop - Failed to initiate scanningThread! - endpointId: {} - error: {}'.format(endpointId, e))
                        #smtpLogger.critical('mainLoop - Failed to initiate scanningThread! - endpointId: {} - error: {}'.format(endpointId, e))
                        endpointStatuses[endpointId] = 'FAILED'
                    else:
                        debugLogger.info('ScanningThread initiated successfully. - endpointId: {}'.format(endpointId))
                        endpointStatuses[endpointId] = 'RUNNING'

                elif endpointStatuses[endpointId] == 'RELOADING' : pass

                elif endpointStatuses[endpointId] == 'SUSPENDED' : pass

                elif endpointStatuses[endpointId] == 'FAILED' : pass

                else:
                    debugLogger.critical('mainLoop - Bad status! - endPointId: {} - endpointStatus: {}'.format(endpointId, endpointStatuses[endpointId]))
                    errorLogger.critical('mainLoop - Bad status! - endPointId: {} - endpointStatus: {}'.format(endpointId, endpointStatuses[endpointId]))
                    #smtpLogger.critical('mainLoop - Bad status! - endPointId: {} - endpointStatus: {}'.format(endpointId, endpointStatuses[endpointId]))

            elif endpointCommands[endpointId] == 'STAND BY':

                if endpointStatuses[endpointId] == 'RUNNING':
                    debugLogger.debug('mainLoop - Endpoint stand by command... - endpointId: {} - endpointStatus: {}'.format(endpointId, endpointStatuses[endpointId]))
                    try:
                        endpoint.quit = True
                        scanningThreads[endpointId].join()
                        del scanningThreads[endpointId]
                    except Exception as e:
                        debugLogger.exception('mainLoop - Failed to pause scanningThread! - endpointId: {} - error: {}'.format(endpointId, e))
                        errorLogger.critical('mainLoop - Failed to pause scanningThread! - endpointId: {} - error: {}'.format(endpointId, e))
                        #smtpLogger.critical('mainLoop - Failed to pause scanningThread! - endpointId: {} - error: {}'.format(endpointId, e))
                    else:
                        debugLogger.info('ScanningThread paused. - endpointId: {}'.format(endpointId))
                        endpointStatuses[endpointId] = 'STANDING BY'

                elif endpointStatuses[endpointId] == 'STANDING BY' : pass

                elif endpointStatuses[endpointId] == 'RELOADING' : pass

                elif endpointStatuses[endpointId] == 'SUSPENDED' : pass

                elif endpointStatuses[endpointId] == 'FAILED' : pass

                else:
                    debugLogger.critical('mainLoop - Bad status! - endpointId: {} - endpointStatus: {}'.format(endpointId, endpointStatuses[endpointId]))
                    errorLogger.critical('mainLoop - Bad status! - endpointId: {} - endpointStatus: {}'.format(endpointId, endpointStatuses[endpointId]))
                    #smtpLogger.critical('mainLoop - Bad status! - endpointId: {} - endpointStatus: {}'.format(endpointId, endpointStatuses[endpointId]))

            elif endpointCommands[endpointId] == 'SUSPEND':

                if endpointStatuses[endpointId] == 'RUNNING':
                    debugLogger.debug('mainLoop - Endpoint suspend command... - endpointId: {} - endpointStatus: {}'.format(endpointId, endpointStatuses[endpointId]))
                    try:
                        endpoint.quit = True
                        scanningThreads[endpointId].join()
                        del scanningThreads[endpointId]
                    except Exception as e:
                        debugLogger.exception('mainLoop - Failed to suspend endpoint! - endpointId: {} - error: {}'.format(endpointId, e))
                        errorLogger.critical('mainLoop - Failed to suspend endpoint! - endpointId: {} - error: {}'.format(endpointId, e))
                        #smtpLogger.critical('mainLoop - Failed to suspend endpoint! - endpointId: {} - error: {}'.format(endpointId, e))
                    else:
                        debugLogger.info('Endpoint suspended. - endpointId: {}'.format(endpointId))
                        endpointStatuses[endpointId] = 'SUSPENDED'

                elif endpointStatuses[endpointId] == 'STANDING BY' : endpointStatuses[endpointId] = 'SUSPENDED'

                elif endpointStatuses[endpointId] == 'RELOADING' : pass

                elif endpointStatuses[endpointId] == 'SUSPENDED' : pass

                elif endpointStatuses[endpointId] == 'FAILED' : pass

                else:
                    debugLogger.critical('mainLoop - Bad status! - endPointId: {} - endpointStatus: {}'.format(endpointId, endpointStatuses[endpointId]))
                    errorLogger.critical('mainLoop - Bad status! - endPointId: {} - endpointStatus: {}'.format(endpointId, endpointStatuses[endpointId]))
                    #smtpLogger.critical('mainLoop - Bad status! - endPointId: {} - endpointStatus: {}'.format(endpointId, endpointStatuses[endpointId]))

            else:
                debugLogger.critical('mainLoop - Bad command! - endPointId: {} - endpointCommand: {}'.format(endpointId, endpointCommands[endpointId]))
                errorLogger.critical('mainLoop - Bad command! - endPointId: {} - endpointCommand: {}'.format(endpointId, endpointCommands[endpointId]))
                #smtpLogger.critical('mainLoop - Bad command! - endPointId: {} - endpointCommand: {}'.format(endpointId, endpointCommands[endpointId]))
            
            if endpointStatuses[endpointId] == 'RUNNING':
                if not scanningThreads[endpointId].is_alive():
                    endpointStatuses[endpointId] = 'FAILED'
                    del scanningThreads[endpointId]
                    debugLogger.critical('mainLoop - Scanning thread failed! - endpointId: {}'.format(endpointId))
                    errorLogger.critical('mainLoop - Scanning thread failed! - endpointId: {}'.format(endpointId))
                    #smtpLogger.critical('mainLoop - Scanning thread failed! - endpointId: {}'.format(endpointId))

        MDP.endpointStatuses = endpointStatuses
        MDP.scanningThreads = scanningThreads
        if updateEndpointStatuses():
            debugLogger.debug('mainLoop - Endpoint statuses updated.')
        else:
            debugLogger.critical('mainLoop - Failed to update endpoint statuses!')
            errorLogger.critical('mainLoop - Failed to update endpoint statuses!')
            #smtpLogger.critical('mainLoop - Failed to update endpoint statuses!')
        #endregion

        #region mdp operations and status update
        debugLogger.debug('mainLoop - Region mdp operations...')
        if mdpCommand == 'RUN':

            if mdpStatus == 'RUNNING' : pass

            elif mdpStatus == 'STANDING BY':
                debugLogger.debug('mainLoop - MDP run command... - mdpStatus: {}'.format(mdpStatus))
                try:
                    MDP.quit = False
                    mdpDecisionThread = threading.Thread(target=MDP.decisionThread)
                    mdpDecisionThread.start()
                except Exception as e:
                    debugLogger.exception('mainLoop - Failed to initiate mdpDecisionThread! - error: {}'.format(e))
                    errorLogger.critical('mainLoop - Failed to initiate mdpDecisionThread! - error: {}'.format(e))
                    #smtpLogger.critical('mainLoop - Failed to initiate mdpDecisionThread! - error: {}'.format(e))
                    mdpStatus = 'FAILED'
                else:
                    debugLogger.info('mainLoop - Decision thread initiated successfully.')
                    mdpStatus = 'RUNNING'

            elif mdpStatus == 'RELOADING' : pass

            elif mdpStatus == 'SUSPENDED' : pass

            elif mdpStatus == 'FAILED' : pass

            else:
                debugLogger.critical('mainLoop - Bad status! - mdpStatus: {}'.format(mdpStatus))
                errorLogger.critical('mainLoop - Bad status! - mdpStatus: {}'.format(mdpStatus))
                #smtpLogger.critical('mainLoop - Bad status! - mdpStatus: {}'.format(mdpStatus))

        elif mdpCommand == 'STAND BY':

            if mdpStatus == 'RUNNING':
                debugLogger.debug('mainLoop - MDP stand by command... - mdpStatus: {}'.format(mdpStatus))
                try:
                    MDP.quit = True
                    mdpDecisionThread.join()
                except Exception as e:
                    debugLogger.exception('mainLoop - Failed to pause mdpDecisionThread! - error: {}'.format(e))
                    errorLogger.critical('mainLoop - Failed to pause mdpDecisionThread! - error: {}'.format(e))
                    #smtpLogger.critical('mainLoop - Failed to pause mdpDecisionThread! - error: {}'.format(e))
                else:
                    debugLogger.info('mainLoop - MDP standing by.')
                    mdpStatus = 'STANDING BY'

            elif mdpStatus == 'STANDING BY' : pass

            elif mdpStatus == 'RELOADING' : pass

            elif mdpStatus == 'SUSPENDED' : pass

            elif mdpStatus == 'FAILED' : pass

            else:
                debugLogger.critical('mainLoop - Bad status! - mdpStatus: {}'.format(mdpStatus))
                errorLogger.critical('mainLoop - Bad status! - mdpStatus: {}'.format(mdpStatus))
                #smtpLogger.critical('mainLoop - Bad status! - mdpStatus: {}'.format(mdpStatus))

        elif mdpCommand == 'SUSPEND':

            if mdpStatus == 'RUNNING':
                debugLogger.debug('mainLoop - MDP suspend command... - mdpStatus: {}'.format(mdpStatus))
                try:
                    MDP.quit = True
                    mdpDecisionThread.join()
                except Exception as e:
                    debugLogger.exception('mainLoop - Failed to suspend mdpDecisionThread! - error: {}'.format(e))
                    errorLogger.critical('mainLoop - Failed to suspend mdpDecisionThread! - error: {}'.format(e))
                    #smtpLogger.critical('mainLoop - Failed to suspend mdpDecisionThread! - error: {}'.format(e))
                else:
                    debugLogger.info('mainLoop - MDP suspended.')
                    mdpStatus = 'SUSPENDED'

            elif mdpStatus == 'STANDING BY' : mdpStatus = 'SUSPENDED'

            elif mdpStatus == 'RELOADING' : pass

            elif mdpStatus == 'SUSPENDED' : pass

            elif mdpStatus == 'FAILED' : pass

            else:
                debugLogger.critical('mainLoop - Bad status! - mdpStatus: {}'.format(mdpStatus))
                errorLogger.critical('mainLoop - Bad status! - mdpStatus: {}'.format(mdpStatus))
                #smtpLogger.critical('mainLoop - Bad status! - mdpStatus: {}'.format(mdpStatus))

        else:
            debugLogger.critical('mainLoop - Bad command! - mdpCommand: {}'.format(mdpCommand))
            errorLogger.critical('mainLoop - Bad command! - mdpCommand: {}'.format(mdpCommand))
            #smtpLogger.critical('mainLoop - Bad command! - mdpCommand: {}'.format(mdpCommand))

        if mdpStatus == 'RUNNING':
            if not mdpDecisionThread.is_alive():
                mdpStatus = 'FAILED'
                debugLogger.critical('mainLoop - Scanning thread failed! - endpointId: {}'.format(endpointId))
                errorLogger.critical('mainLoop - Scanning thread failed! - endpointId: {}'.format(endpointId))
                #smtpLogger.critical('mainLoop - Scanning thread failed! - endpointId: {}'.format(endpointId))

        if updateMDPStatus():
            debugLogger.debug('mainLoop - MDP status updated.')
        else:
            debugLogger.critical('mainLoop - updateMDPStatus Failed!')
            errorLogger.critical('mainLoop - updateMDPStatus Failed!')
            #smtpLogger.critical('mainLoop - updateMDPStatus Failed!')

        #endregion

        stop = time.perf_counter()
        debugLogger.debug('Cycle completed in {} seconds. Going to sleep for {} seconds.'.format(stop - start, float(mainCycleTime) - stop + start))
        if (float(mainCycleTime) - stop + start) > 0 : time.sleep(float(mainCycleTime) - stop + start)

#region========================== INITIATION ===========================#
debugLogger.debug('Initializing...')
try:
    # GETCOMMANDS
    debugLogger.debug('GetCommands...')
    if not getCommands():
        debugLogger.critical('getCommands Failed!')
        errorLogger.critical('getCommands Failed!')
        raise Exception
    debugLogger.debug('GetCommands Successful.')

    # SET TO RELOADING
    debugLogger.debug('SetToReloading...')
    if not setToReloading():
        debugLogger.critical('setToReloading Failed!')
        errorLogger.critical('setToReloading Failed!')
        raise Exception
    debugLogger.debug('SetToReloading Successful.')

    # LOAD SETTINGS FOR MAIN AND MDP FROM DATABASE
    debugLogger.debug('Load settings...')
    if not getSettings():
        debugLogger.critical('getSettings Failed!')
        errorLogger.critical('getSettings Failed!')
        raise Exception
    debugLogger.debug('Load settings successful.')

    # LOAD ENDPOINTS
    debugLogger.debug('Load endpoints...')
    if not reloadEndpoints():
        debugLogger.critical('reloadEndpoints Failed!')
        errorLogger.critical('reloadEndpoints Failed!')
        raise Exception
    debugLogger.debug('Load endpoints successful.')

    # LOAD MDP AND UPDATE STATUS
    debugLogger.debug('Loading MDP...')
    try:
        MDP = mainDataProcessor(db_host, db_user, db_pass, db_db, logFolder, mdpCycleTime, endpointStatuses, endpoints, scanningThreads)
    except Exception as e:
        debugLogger.exception('Failed to load MDP!')
        errorLogger.critical('Failed to load MDP!')
        raise Exception
    debugLogger.debug('Load MDP successful.')

    # UPDATE STATUS FOR MAIN AND MDP
    mainStatus = 'STANDING BY'
    mdpStatus = 'STANDING BY'
    debugLogger.debug('Update Main and MDP status...')
    if not (updateMainStatus() and updateMDPStatus()):
        debugLogger.critical('updateStatus Failed!')
        errorLogger.critical('updateStatus Failed!')
        raise Exception
    debugLogger.debug('Update Main and MDP status successful.')

    # START MAIN LOOP
    try:
        mainLoop()
    except Exception as e:
        debugLogger.exception('mainLoop Failed!')
        errorLogger.critical('mainLoop Failed!')
        raise Exception

# IF DATAFLOW STOPPED WORKING, STOP EVERTHING
except:
    mainStatus = 'FAILED'
    updateMainStatus()
    debugLogger.critical('dataFlow failed!')
    errorLogger.critical('dataFlow failed!')
    #smtpLogger.critical('dataFlow failed!')
else:
    mainStatus = 'STOPPED'
    updateMainStatus()
    debugLogger.debug('dataFlow peacefully quited.')
finally:
    debugLogger.debug('Stopping scanningThreads...')
    for endpointId, endpointStatus in endpointStatuses.items():
        if endpointStatus == 'RUNNING' : endpoints[endpointId].quit = True
        elif endpointStatus == 'STANDING BY' : endpointStatuses[endpointId] = 'STOPPED'
    for endpointId, thread in  scanningThreads.items():
        thread.join()
        endpointStatuses[endpointId] = 'STOPPED'
    updateEndpointStatuses()
    debugLogger.debug('Successful to stop scanningThreads.')
    debugLogger.debug('Stopping mdpDecisionThread...')
    if MDP != None: MDP.quit = True
    if mdpDecisionThread!= None: mdpDecisionThread.join()
    mdpStatus = 'STOPPED'
    updateMDPStatus()
    debugLogger.debug('Successful to stop mdpDecisionThread.')
#endregion===============================================================#