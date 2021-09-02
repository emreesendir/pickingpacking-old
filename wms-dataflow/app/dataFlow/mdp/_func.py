import mysql.connector, json

def closeEvent(self, event, result):
    self.debugLogger.debug('{} - closeEvent parameters - event: {} - result: {}'.format(event['id'], event, result))
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('UPDATE dataflow_event SET result = %s WHERE id = %s', (result, event['id']))
        conn.commit()
    except Exception as e:
        self.debugLogger.exception('{} - closeEvent - Failed to close event! - error: {} - event: {}'.format(event['id'], e, event))
        self.errorLogger.error('{} - closeEvent - Failed to close event! - error: {} - event: {}'.format(event['id'], e, event))
        return False
    else:
        self.debugLogger.debug('{} - closeEvent - Successful to close event.'.format(event['id']))
        return True
    finally : conn.close()

def remoteIdTocacheId(self, event, remoteId):
    self.debugLogger.debug('{} - remoteIdTocacheId parameters - remoteId: {}'.format(event['id'], remoteId))
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT cacheId FROM dataflow_order WHERE endpoint_id = %s AND remoteId = %s', (event['endpoint_id'], remoteId))
        cacheId = cur.fetchone()[0]
    except Exception as e:
        self.debugLogger.exception('{} - remoteIdTocacheId - Failed to retrieve parent order cacheId! - error: {} - event: {}'.format(event['id'], e, event))
        self.errorLogger.error('{} - remoteIdTocacheId - Failed to retrieve parent order cacheId! - error: {} - event: {}'.format(event['id'], e, event))
        return -1, False
    else:
        self.debugLogger.debug('{} - remoteIdTocacheId Successful - cacheId: {}'.format(event['id'], cacheId))
        return cacheId, True
    finally : conn.close()

def retrieveStatus(self, event, cacheId):
    self.debugLogger.debug('{} - retrieveStatus parameters - event: {} - cacheId: {}'.format(event['id'], event, cacheId))
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT status FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
        status = cur.fetchone()[0]
    except Exception as e:
        self.debugLogger.exception('{} - retrieveStatus - Failed to retrieve order status! - error: {} - event: {}'.format(event['id'], e, event))
        self.errorLogger.error('{} - retrieveStatus - Failed to retrieve order status! - error: {} - event: {}'.format(event['id'], e, event))
        return '', False
    else:
        self.debugLogger.debug('{} - retrieveStatus Successful - status: {}'.format(event['id'], status))
        return status, True
    finally : conn.close()

def updateOrdersOnhold(self):
    self.debugLogger.debug('decisionThread - updateOrdersOnHold parameters - none')
    self.ordersOnHold.clear()
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT endpoint_id, cacheId FROM dataflow_order WHERE status LIKE %s AND cacheId != -1', ('ON HOLD%', ))
        for row in cur : self.ordersOnHold.append((row[0], row[1]))
    except Exception as e:
        self.debugLogger.exception('decisionThread - updateOrdersOnHold - Couldn\'t retrieve the openEvents - error: {}'.format(e))
        self.errorLogger.critical('decisionThread - updateOrdersOnHold - Couldn\'t retrieve the openEvents - error: {}'.format(e))
        #self.smtpLogger.critical('decisionThread - updateOrdersOnHold - Couldn\'t retrieve the openEvents - error: {}'.format(e))
        return False
    finally:
        conn.close()
    self.debugLogger.debug('decisionThread - updateOrdersOnHold updated lenght: {} - data: {}'.format(len(self.ordersOnHold), self.ordersOnHold))
    return True

def updateInternalBlock(self):
    self.debugLogger.debug('decisionThread - updateInternalBlock parameters - requestForInternalBlock: {} - internalBlock: {}'.format(self.requestForInternalBlock, self.internalBlock))
    try:
        self.blockedTupList  = [(blocked[0], blocked[1]) for blocked in self.internalBlock]
        for request in self.requestForInternalBlock:
            if (request[0], request[1]) not in self.blockedTupList : self.internalBlock.append(request)
    except Exception as e:
        self.debugLogger.exception('decisionThread - updateInternalBlock Failed: {}'.format(e))
        self.errorLogger.error('decisionThread - updateInternalBlock Failed: {}'.format(e))
        return False
    else:
        self.debugLogger.debug('decisionThread - updateInternalBlock result - requestForInternalBlock: {} - internalBlock: {}'.format(self.requestForInternalBlock, self.internalBlock))
        return True

def whereClause(self):
    self.debugLogger.debug('decisionThread - whereClause parameters - blockedTupList: {} - ordersInProgress: {} - ordersOnHold: {}'.format(self.blockedTupList, self.ordersInProgress, self.ordersOnHold))
    try:
        where = str()
        whereInProgress = str()
        for tup in list(dict.fromkeys( self.blockedTupList + self.ordersInProgress + self.ordersOnHold )) : where += ' AND ((endpoint_id != {0} OR cacheId != {1}))'.format(tup[0], tup[1])
        for tup in list(dict.fromkeys( self.blockedTupList + self.ordersInProgress )) : whereInProgress += ' AND ((endpoint_id != {0} OR cacheId != {1}))'.format(tup[0], tup[1])
        runningEndpointIds = [endpointId for endpointId, endpointStatus in self.endpointStatuses.items() if endpointStatus == 'RUNNING']
        if len(runningEndpointIds) > 0:
            where += ' AND (endpoint_id = {}'.format(runningEndpointIds[0])
            whereInProgress += ' AND (endpoint_id = {}'.format(runningEndpointIds[0])
            runningEndpointIds.remove(runningEndpointIds[0])
            for endpointId in runningEndpointIds:
                where += ' OR endpoint_id = {}'.format(endpointId)
                whereInProgress += ' OR endpoint_id = {}'.format(endpointId)
            where += ')'
            whereInProgress += ')'
        else:
            where += ' AND endpoint_id = -1'
            whereInProgress += ' AND endpoint_id = -1'
    except Exception as e:
        self.debugLogger.exception('decisionThread - whereClause Failed: {}'.format(e))
        self.errorLogger.error('decisionThread - whereClause Failed: {}'.format(e))
        return '', '', False
    self.debugLogger.debug('decisionThread - whereClause result - where: {} - whereInProgress: {}'.format(where, whereInProgress))
    return where, whereInProgress, True

def pullEvent(self, where, whereInProgress):
    self.debugLogger.debug('decisionThread - pullEvent.')
    try:
        event = dict()
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT id, cacheId, type, priority, time, data, endpoint_id FROM dataflow_event WHERE (result = \'\'{}) OR (result = \'\'{} AND (type = \'OrderContinue\' OR type = \'ERPNewCommand\')) ORDER BY priority DESC, time ASC LIMIT 1'.format(where, whereInProgress))
        for row in cur : event = {'id' : row[0], 'cacheId' : row[1], 'type' : row[2], 'priority' : row[3], 'time' : row[4], 'data' : json.loads(row[5]), 'endpoint_id' : row[6]}
    except Exception as e:
        self.debugLogger.exception('decisionThread - pullEvent failed: {}'.format(e))
        self.errorLogger.error('decisionThread - pullEvent failed: {}'.format(e))
        return {}, False
    else:
        self.debugLogger.debug('decisionThread - pullEvent result - event: {}'.format(event))
        return event, True
    finally:
        conn.close()