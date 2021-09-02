import threading, time, logging, logging.handlers, datetime
from configparser import ConfigParser

class mainDataProcessor:

    from ._func import closeEvent, remoteIdTocacheId, retrieveStatus, updateOrdersOnhold, updateInternalBlock, whereClause, pullEvent
    from ._events import OrderOnHold, Warning, ERPNewOrder, ERPNewMessage, ERPNewCommand, ERPOrderCanceled, ERPOrderUpdated, OrderContinue, PickingRequestForAssignment, PickingPicked, PackingRequestForAssignment, PackingShipped, ManagementSizing
    from ._commands import NoInvoice, NoShipment, Merge, HoldForMerge

    def __init__(self, db_host, db_user, db_pass, db_db, logFolder, cycleTime, endpointStatuses, endpoints, scanningThreads):
        # ================= FROM controller =================== #
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_db = db_db
        self.logFolder = logFolder
        self.cycleTime = cycleTime
        self.endpointStatuses = endpointStatuses
        self.endpoints = endpoints
        self.scanningThreads = scanningThreads
        # ===================================================== #

        # ========== Internal Variables and Settings ========== #
        self.workingThreads = dict()
        self.ordersInProgress = list()
        self.ordersOnHold = list()
        self.requestForInternalBlock = list()
        self.internalBlock = list()
        self.quit = False

        # debug logger
        self.debugLogger = logging.getLogger('mdpDebug')
        self.debugLogger.setLevel(logging.DEBUG)
        debugFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        debugFileHandler = logging.FileHandler('{}{}'.format(self.logFolder, 'mdpDebug.log'))
        debugFileHandler.setFormatter(debugFormatter)
        while self.debugLogger.hasHandlers() : self.debugLogger.removeHandler(self.debugLogger.handlers[0])
        self.debugLogger.addHandler(debugFileHandler)

        # error logger
        self.errorLogger = logging.getLogger('mdpError')
        self.errorLogger.setLevel(logging.ERROR)
        errorFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        errorFileHandler = logging.FileHandler('{}{}'.format(self.logFolder, 'error.log'))
        errorFileHandler.setFormatter(errorFormatter)
        while self.errorLogger.hasHandlers() : self.errorLogger.removeHandler(self.errorLogger.handlers[0])
        self.errorLogger.addHandler(errorFileHandler)

        # smtp logger
        parser = ConfigParser()
        parser.read('/home/app/config/dataFlowSecret.conf')
        self.smtpLogger = logging.getLogger('mdpSMTP')
        self.smtpLogger.setLevel(logging.CRITICAL)
        smtpFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        smtpHandler = logging.handlers.SMTPHandler(mailhost=(parser.get('smtp', 'mailhost'), 587), fromaddr=parser.get('smtp', 'fromaddr'), toaddrs=parser.get('smtp', 'toaddrs'), subject='WMS CRITICAL FAILURE', credentials=(parser.get('smtp', 'fromaddr'),parser.get('smtp', 'password')), secure=())
        smtpHandler.setFormatter(smtpFormatter)
        while self.smtpLogger.hasHandlers() : self.smtpLogger.removeHandler(self.smtpLogger.handlers[0])
        self.smtpLogger.addHandler(smtpHandler)

        self.debugLogger.debug('MDP init successful.')

    def decisionThread(self):
        self.debugLogger.info('decisionThread - Decision thread starts.')

        while True:
            start = time.perf_counter()
            self.debugLogger.debug('============================================================')
            self.debugLogger.debug('decisionThread - Cycle is starting...')

            # check if there is quit order from controller
            self.debugLogger.debug('decisionThread - Checking for quit order...')
            if self.quit:
                while len(self.workingThreads) != 0: continue
                break

            # update ordersOnHold
            self.debugLogger.debug('decisionThread - Updating ordersOnHold...')
            isSuceed_updateOrdersOnHold = self.updateOrdersOnhold()

            # update whereclause
            self.debugLogger.debug('decisionThread - Updating internalBlock...')
            isSuceed_updateInternalBlock = self.updateInternalBlock()

            # update whereclause
            self.debugLogger.debug('decisionThread - Updating whereclause...')
            where, whereInProgress, isSuceed_whereClause = self.whereClause()

            # pullEvent
            self.debugLogger.debug('decisionThread - Region pullEvent.')
            if isSuceed_whereClause:
                event, isSuceed_pullEvent = self.pullEvent(where, whereInProgress)
                if not isSuceed_pullEvent:
                    self.debugLogger.critical('decisionThread - pullEvent Failed!')
                    self.errorLogger.critical('decisionThread - pullEvent Failed!')
                    #self.smtpLogger.critical('decisionThread - pullEvent Failed!')
            else:
                self.debugLogger.critical('decisionThread - whereClause Failed!')
                self.errorLogger.critical('decisionThread - whereClause Failed!')
                #self.smtpLogger.critical('MDP - whereClause Failed!')
                isSuceed_pullEvent = False

            # understand the event and start relevant thread
            if isSuceed_whereClause and isSuceed_pullEvent and isSuceed_updateOrdersOnHold and isSuceed_updateInternalBlock:
                if len(event) < 1:
                    pass
                elif event['type'] == 'ERPNewOrder':
                    self.ordersInProgress.append((event['endpoint_id'], event['cacheId']))
                    x = threading.Thread(target=self.ERPNewOrder, args=(event,))
                    x.start()
                    self.workingThreads[str(event['id'])] = x
                elif event['type'] == 'ERPNewMessage':
                    self.ordersInProgress.append((event['endpoint_id'], event['cacheId']))
                    x = threading.Thread(target=self.ERPNewMessage, args=(event,))
                    x.start()
                    self.workingThreads[str(event['id'])] = x
                elif event['type'] == 'ERPNewCommand':
                    self.ordersInProgress.append((event['endpoint_id'], event['cacheId']))
                    x = threading.Thread(target=self.ERPNewCommand, args=(event,))
                    x.start()
                    self.workingThreads[str(event['id'])] = x
                elif event['type'] == 'ERPOrderUpdated':
                    self.ordersInProgress.append((event['endpoint_id'], event['cacheId']))
                    x = threading.Thread(target=self.ERPOrderUpdated, args=(event,))
                    x.start()
                    self.workingThreads[str(event['id'])] = x
                elif event['type'] == 'ERPOrderCanceled':
                    self.ordersInProgress.append((event['endpoint_id'], event['cacheId']))
                    x = threading.Thread(target=self.ERPOrderCanceled, args=(event,))
                    x.start()
                    self.workingThreads[str(event['id'])] = x
                elif event['type'] == 'PickingRequestForAssignment':
                    self.ordersInProgress.append((event['endpoint_id'], event['cacheId']))
                    x = threading.Thread(target=self.PickingRequestForAssignment, args=(event,))
                    x.start()
                    self.workingThreads[str(event['id'])] = x
                elif event['type'] == 'PickingPicked':
                    self.ordersInProgress.append((event['endpoint_id'], event['cacheId']))
                    x = threading.Thread(target=self.PickingPicked, args=(event,))
                    x.start()
                    self.workingThreads[str(event['id'])] = x
                elif event['type'] == 'PackingRequestForAssignment':
                    self.ordersInProgress.append((event['endpoint_id'], event['cacheId']))
                    x = threading.Thread(target=self.PackingRequestForAssignment, args=(event,))
                    x.start()
                    self.workingThreads[str(event['id'])] = x
                elif event['type'] == 'PackingShipped':
                    self.ordersInProgress.append((event['endpoint_id'], event['cacheId']))
                    x = threading.Thread(target=self.PackingShipped, args=(event,))
                    x.start()
                    self.workingThreads[str(event['id'])] = x
                elif event['type'] == 'ManagementSizing':
                    self.ordersInProgress.append((event['endpoint_id'], event['cacheId']))
                    x = threading.Thread(target=self.ManagementSizing, args=(event,))
                    x.start()
                    self.workingThreads[str(event['id'])] = x
                elif event['type'] == 'OrderOnHold':
                    self.ordersInProgress.append((event['endpoint_id'], event['cacheId']))
                    x = threading.Thread(target=self.OrderOnHold, args=(event,))
                    x.start()
                    self.workingThreads[str(event['id'])] = x
                elif event['type'] == 'OrderContinue':
                    self.ordersInProgress.append((event['endpoint_id'], event['cacheId']))
                    x = threading.Thread(target=self.OrderContinue, args=(event,))
                    x.start()
                    self.workingThreads[str(event['id'])] = x
                elif event['type'] == 'Warning':
                    self.ordersInProgress.append((event['endpoint_id'], event['cacheId']))
                    x = threading.Thread(target=self.Warning, args=(event,))
                    x.start()
                    self.workingThreads[str(event['id'])] = x
                else:
                    self.debugLogger.critical('decisionThread - Invalid event type - id: {0[id]} - type: {0[type]}'.format(event))
                    self.errorLogger.critical('decisionThread - Invalid event type - id: {0[id]} - type: {0[type]}'.format(event))
                    #self.smtpLogger.critical('decisionThread - Invalid event type - id: {0[id]} - type: {0[type]}'.format(event))
                    onholdevent = {'id' : -1, 'cacheId' : event['cacheId'], 'type' : 'OrderOnHold', 'priority' : -1, 'time' : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'data' : {'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'source': 'Decision Thread', 'reason': 'Invalid event type!', 'remoteId': ''}, 'endpoint_id' : event['endpoint_id']}
                    self.OrderOnHold(onholdevent)
            else:
                self.debugLogger.critical('decisionThread - Can not work!')
                self.errorLogger.critical('decisionThread - Can not work!')
                #self.smtpLogger.critical('decisionThread - Can not work!')
            stop = time.perf_counter()
            self.debugLogger.debug('decisionThread - Cycle completed in {} seconds. Going to sleep for {} seconds.'.format(stop - start, float(self.cycleTime) - stop + start))
            if (float(self.cycleTime) - stop + start) > 0 : time.sleep(float(self.cycleTime) - stop + start)

        self.debugLogger.info('decisionThread - Quited peacefully.')