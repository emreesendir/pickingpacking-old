import odoorpc, xmlrpc.client as xmlrpclib, mysql.connector, json, datetime

def compare(self, old, new, mode):
    self.debugLogger.debug('compare parameters - old : {} - new  : {} - mode: {}'.format(old, new, mode))
    if mode == 'list':
        if type(old) == type([]) and type(new) == type([]):
            old.sort()
            new.sort()
            if old != new:
                removed = list()
                added = list()
                for item in old:
                    if item in new : new.remove(item)
                    else : removed.append(item)
                added = new
                self.debugLogger.debug('compare result - removed : {} - added  : {}'.format(removed, added))
                # return removedlist, addedlist, ifthereischange, iffunctionsucceed
                return removed, added, True, True
            else:
                self.debugLogger.debug('compare result - no change')
                # return removedlist, addedlist, ifthereischange, iffunctionsucceed
                return [], [], False, True
        else:
            # return removedlist, addedlist, ifthereischange, iffunctionsucceed
            self.debugLogger.error('compare - bad parameters - old: {} - new: {} - mode: {}'.format(old, new, mode))
            self.errorLogger.error('compare - bad parameters - old: {} - new: {} - mode: {}'.format(old, new, mode))
            return [], [], False, False
    elif mode == 'flat':
        if type(old) == type(new) or old == False:
            if old != new:
                self.debugLogger.debug('compare result - old : {} - new  : {}'.format(old, new))
                # return old, new, ifthereischange, iffunctionsucceed
                return old, new, True, True
            else:
                self.debugLogger.debug('compare result - no change')
                # return removedlist, addedlist, ifthereischange, iffunctionsucceed
                return [], [], False, True
        else:
            # return old, new, ifthereischange, iffunctionsucceed
            self.debugLogger.error('compare - bad parameters - old: {} - new: {} - mode: {}'.format(old, new, mode))
            self.errorLogger.error('compare - bad parameters - old: {} - new: {} - mode: {}'.format(old, new, mode))
            return '', '', False, False
    else:
        self.debugLogger.error('compare - bad mode - mode: {}'.format(mode))
        self.errorLogger.error('compare - bad mode - mode: {}'.format(mode))
        return '', '', False, False

def updateOpenEvents(self):
    self.debugLogger.debug('updateOpenEvents parameters - none')
    self.openEvents.clear()
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT id, cacheId, priority, time, type, data FROM dataflow_event WHERE endpoint_id = %s AND type IN (\'ERPNewOrder\', \'ERPNewMessage\', \'ERPNewCommand\', \'ERPOrderCanceled\', \'ERPOrderUpdated\', \'OrderOnHold\', \'Warning\') AND result = \'\'', (self.endpointId, ))
        for row in cur : self.openEvents[str(row[0])] = {'cacheId': row[1], 'priority': row[2], 'time': row[3], 'type': row[4], 'data': json.loads(row[5])}
    except Exception as e:
        self.debugLogger.exception('updateOpenEvents - Couldn\'t retrieve the openEvents - error: {}'.format(e))
        self.errorLogger.critical('updateOpenEvents - Couldn\'t retrieve the openEvents - error: {}'.format(e))
        #self.smtpLogger.critical('updateOpenEvents - Couldn\'t retrieve the openEvents - error: {}'.format(e))
        return False
    finally : conn.close()

    self.debugLogger.debug('openEvents updated lenght: {} - data: {}'.format(len(self.openEvents), self.openEvents))
    return True

def updateOrdersOnHold(self):
    self.debugLogger.debug('updateOrdersOnHold parameters - none')
    self.ordersOnHold.clear()
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT cacheId, remoteId FROM dataflow_order WHERE endpoint_id = %s AND status LIKE %s', (self.endpointId, 'ON HOLD%'))
        for row in cur : self.ordersOnHold.append({'cacheId': row[0], 'remoteId': row[1]})
    except Exception as e:
        self.debugLogger.exception('updateOrdersOnHold - Couldn\'t retrieve the ordersOnHold - error: {}'.format(e))
        self.errorLogger.critical('updateOrdersOnHold - Couldn\'t retrieve the ordersOnHold - error: {}'.format(e))
        #self.smtpLogger.critical('updateOrdersOnHold - Couldn\'t retrieve the ordersOnHold - error: {}'.format(e))
        return False
    finally:
        conn.close()

    self.debugLogger.debug('updateOrdersOnHold updated lenght: {} - data: {}'.format(len(self.ordersOnHold), self.ordersOnHold))
    return True

def odooLogin(self):
    self.debugLogger.debug('odooLogin parameters - none')

    try:
        self.odoo = odoorpc.ODOO(self.url, 'jsonrpc+ssl', 443)
        self.odoo.login(self.db, self.username, self.password)
        saleOrder_env = self.odoo.env['sale.order']
        self.saleOrder_env = saleOrder_env
        self.InternalStatus = self.odoo.env['x_internalstatus']
        self.stockPicking_env = self.odoo.env['stock.picking']

        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format('https://' + self.url))
        self.models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format('https://' + self.url))
        self.uid = common.authenticate(self.db, self.username, self.password, {})
    except Exception as e:
        self.debugLogger.exception('Failed to login: {}'.format(e))
        self.errorLogger.error('Failed to login: {}'.format(e))
        return '', '', '', '', False

    self.debugLogger.debug('odooLogin results - uid: {} - models: {} - saleOrder_env: {}'.format(self.uid, self.models, saleOrder_env))
    return self.odoo, self.uid, self.models, saleOrder_env, True

def retrieveFromCache(self, column, id):
    self.debugLogger.debug('retrieveFromCache parameters - column: {} - id: {}'.format(column, id))
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT {} FROM {} WHERE id = %s'.format(column, self.cacheTable), (id, ))
        cache = json.loads(cur.fetchone()[0])
    except Exception as e:
        self.debugLogger.exception('retrieveFromCache - Couldn\'t retrieve the cache data or json error. -  error: {}'.format(e))
        self.errorLogger.error('retrieveFromCache - Couldn\'t retrieve the cache data or json error. -  error: {}'.format(e))
        return {}, False
    finally : conn.close()
    self.debugLogger.debug('retrieveFromCache result - data: {}'.format(cache))
    return cache, True

def pullFromOdoo(self, models, uid, model, id, fields, cacheId=-1):
    self.debugLogger.debug('pullFromOdoo parameters - uid : {} - models : {} - model  : {} - id : {} - fields: {}'.format(uid, models, model, id, fields))
    try:
        if type(id) != type([]):
            data = models.execute_kw(self.db, uid, self.password, model, 'search_read', [[['id', '=', id]]], {'fields': fields})
        else:
            data = models.execute_kw(self.db, uid, self.password, model, 'search_read', [[['id', 'in', id]]], {'fields': fields})
        if not cacheId == -1:
            if len(data) > 0 and type(id) != type([]) : data = data[0]
            elif len(data) > 0 and type(id) == type([]) : pass
            else:
                self.debugLogger.error('Data deleted from odoo side! - sale.order.id: {} - caheId: {}'.format(id, cacheId))
                self.errorLogger.error('Data deleted from odoo side! - sale.order.id: {} - caheId: {}'.format(id, cacheId))
                return {}, False
        else:
            if len(data) > 0 and type(id) != type([]) : data = data[0]
            elif len(data) > 0 and type(id) == type([]) : pass
    except Exception as e:
        self.debugLogger.exception('pullFromOdoo - Couldn\'t retrieve data - error: {} - uid: {} - model: {} - id: {}'.format(e, uid, model, id))
        self.errorLogger.error('pullFromOdoo - Couldn\'t retrieve data - error: {} - uid: {} - model: {} - id: {}'.format(e, uid, model, id))
        eventsOfOrder = dict()
        for event in self.openEvents.values():
            if event['cacheId'] == cacheId : eventsOfOrder.append(event)
        isSucceed_createEvent, isNewEventCreated = createEvent(cacheId, 5, 'OrderOnHold', {'source': self.endpointName, 'reason': 'can not reach remote data'}, eventsOfOrder)
        if not isSucceed_createEvent:
            self.debugLogger.critical('failed to create OnHold event! - sale.order.id: {} - cacheId: {}'.format(id, cacheId))
            self.errorLogger.critical('failed to create OnHold event! - sale.order.id: {} - cacheId: {}'.format(id, cacheId))
            #self.smtpLogger.critical('failed to create OnHold event! - sale.order.id: {} - cacheId: {}'.format(id, cacheId))
        return {}, False

    self.debugLogger.debug(r'pullFromOdoo return - data: {}'.format(data))
    return data, True

def ignoreChange(self, cacheId, column, newLastUpdate, index, internalId = -1, cacheData = dict()):
    self.debugLogger.debug('ignoreChange parameters - cacheId: {} - column: {} - cacheData: {} - newLastUpdate {}'.format(cacheId, column, cacheData, newLastUpdate))

    # update cache data
    self.debugLogger.debug('ignoreChange - Updating cache data...')
    if internalId == -1:
        cacheData['__last_update'] = newLastUpdate
    else:
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            cur.execute('SELECT {} FROM {} WHERE id = %s'.format(column, self.cacheTable), (cacheId, ))
            for row in cur : cacheData = json.loads(row[0])
        except Exception as e:
            self.debugLogger.exception('ignoreChange - Couldn\'t retrieve the cache data or json error. -  error: {}'.format(e))
            self.errorLogger.error('ignoreChange - Couldn\'t retrieve the cache data or json error. -  error: {}'.format(e))
            return False
        finally : conn.close()
        cacheData[str(internalId)]['__last_update'] = newLastUpdate
    self.debugLogger.debug('ignoreChange - Successful to update cache data. - cacheData:{} '.format(cacheData))

    # update orderSummaries
    self.debugLogger.debug('ignoreChange - Updating orderSummaries...')
    try:
        indexList = index.split('.')
        if indexList[-1] == 'message_ids' : indexList.remove(indexList[-1])
        if len(indexList) == 1 : self.orderSummaries[cacheId][str(indexList[0])]['__last_update'] = newLastUpdate
        elif len(indexList) == 2 : self.orderSummaries[cacheId][str(indexList[0])][str(indexList[1])]['__last_update'] = newLastUpdate
        elif len(indexList) == 3 : self.orderSummaries[cacheId][str(indexList[0])][str(indexList[1])][str(indexList[2])]['__last_update'] = newLastUpdate
        elif len(indexList) == 4 : self.orderSummaries[cacheId][str(indexList[0])][str(indexList[1])][str(indexList[2])][str(indexList[3])]['__last_update'] = newLastUpdate
        elif len(indexList) == 5 : self.orderSummaries[cacheId][str(indexList[0])][str(indexList[1])][str(indexList[2])][str(indexList[3])][str(indexList[4])]['__last_update'] = newLastUpdate
    except Exception as e:
        self.debugLogger.exception('ignoreChange - Couldn\'t update data. error: {} - data: {}'.format(e, cacheData))
        self.errorLogger.error('ignoreChange - Couldn\'t update data. error: {} - data: {}'.format(e, cacheData))
        return False
    self.debugLogger.debug('ignoreChange - Successful to update orderSummaries. - orderSummaries: {}'.format(self.orderSummaries[cacheId]))

    # update database
    self.debugLogger.debug('ignoreChange - Updating database...')
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('UPDATE {} SET {} = %s WHERE id = %s'.format(self.cacheTable, column), (json.dumps(cacheData), cacheId))
        cur.execute('UPDATE {} SET summary = %s WHERE id = %s'.format(self.cacheTable), (json.dumps(self.orderSummaries[str(cacheId)]), int(cacheId)))
        conn.commit()
    except Exception as e:
        self.debugLogger.exception('ignoreChange - Couldn\'t update data. error: {} - data: {}'.format(e, cacheData))
        self.errorLogger.error('ignoreChange - Couldn\'t update data. error: {} - data: {}'.format(e, cacheData))
        return False
    finally : conn.close()
    self.debugLogger.debug('ignoreChange - Successful to update database.')

    self.debugLogger.debug('ignoreChange successful')
    return True

def check(self, models, uid, cacheId, model, column, fields, odooId, index, changes, iId=-1):
    self.debugLogger.debug('check parameters - cacheId: {} - column: {} - index: {}'.format(cacheId, column, index))
    try:
        data_cache, isSucceed_retrieveFromCache = self.retrieveFromCache(column, cacheId)
        if model in ['stock.picking', 'account.invoice', 'stock.move', 'mail.message', 'product.product'] : data_cache = data_cache[str(odooId)]
        data_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(models, uid, model, odooId, [f for f in fields], cacheId)
        if isSucceed_retrieveFromCache and isSucceed_pullFromOdoo:

            relatedChange = False
            for field, mode in fields.items():
                if field != '__last_update':
                    if '{}.{}'.format(model, field) in ['stock.picking.partner_id', 'stock.picking.picking_type_id', 'stock.move.product_id'] : var1, var2, isChanged, isSucceed_compare = self.compare(data_cache[field], data_remote[field][0], mode)
                    else : var1, var2, isChanged, isSucceed_compare = self.compare(data_cache[field], data_remote[field], mode)
                    if isSucceed_compare:
                        if isChanged:
                            if mode == 'flat' : changes[cacheId].append({'type': mode, 'index': '{}.{}'.format(index, field), 'old': var1, 'new': var2, '__last_update': data_remote['__last_update']})
                            if mode == 'list' : changes[cacheId].append({'type': mode, 'index': '{}.{}'.format(index, field), 'removed': var1, 'added': var2, '__last_update': data_remote['__last_update']})
                            relatedChange = True
                            self.debugLogger.info('Change found: {}'.format(changes[cacheId][-1]))
                    else:
                        self.debugLogger.error('Couldn\'t check {}.{}'.format(model, field))
                        self.errorLogger.error('Couldn\'t check {}.{}'.format(model, field))
                        return changes, False

            if not relatedChange:
                self.debugLogger.debug('{} ignoring change ...'.format(model))
                if iId != -1 : isSucceed_ignoreChange = self.ignoreChange(cacheId, column, data_remote['__last_update'], index, internalId=iId)
                else : isSucceed_ignoreChange = self.ignoreChange(cacheId, column, data_remote['__last_update'], index, cacheData=data_cache)
                if isSucceed_ignoreChange : self.debugLogger.info('{}.{} changed out of my focus area. Change ignored'.format(cacheId, index))
                else:
                    self.debugLogger.error('Couldn\'t ignore change')
                    self.errorLogger.error('Couldn\'t ignore change')
                    return changes, False

        else:
            if not isSucceed_retrieveFromCache:
                self.debugLogger.error('Couldn\'t retrieve {} from database.'.format(column))
                self.errorLogger.error('Couldn\'t retrieve {} from database.'.format(column))
            if not isSucceed_pullFromOdoo:
                self.debugLogger.error('Couldn\'t retrieve {} from odoo.'.format(model))
                self.errorLogger.error('Couldn\'t retrieve {} from odoo.'.format(model))
            return changes, False

    except Exception as e:
        self.debugLogger.exception('check function - Something went wrong! : {}'.format(e))
        self.errorLogger.error('check function - Something went wrong! : {}'.format(e))
        return changes, False

    self.debugLogger.debug('check function successfull.')
    return changes, True

def createEvent(self, cacheId, priority, type, data, eventsOfOrder):
    self.debugLogger.debug('createEvent parameters - cacheId: {} - priority: {} - type: {} - data: {} - eventsOfOrder: {}'.format(cacheId, priority, type, data, eventsOfOrder))
    for event in eventsOfOrder:
        if event['type'] == type and event['data'] == data:
            self.debugLogger.debug('createEvent - Event exist.')
            return True, False
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('INSERT INTO dataflow_event (endpoint_id, cacheId, priority, time, type, data, result) VALUES (%s, %s, %s, %s, %s, %s, %s)', (self.endpointId, cacheId, priority, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), type, json.dumps(data), ''))
        conn.commit()
    except Exception as e:
        self.debugLogger.exception('Couldn\'t insert event. error: {}'.format(e))
        self.errorLogger.critical('Couldn\'t insert event. error: {}'.format(e))
        #self.smtpLogger.critical('Couldn\'t insert event. error: {}'.format(e))
        return False, False
    finally:
        conn.close()
    return True, True

def newMessages(self, cacheId, added, models, uid, pickingId):
    self.debugLogger.debug('newMessages parameters - cacheId: {} - added: {}'.format(cacheId, added))

    # pull mail.messageS
    self.debugLogger.debug('newMessages - Trying to retreive mail.messageS... - messageIds: {}'.format(added))
    mailMessageS_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(models, uid, 'mail.message', added, ['body', 'author_id', 'date'])
    if not isSucceed_pullFromOdoo:
        self.debugLogger.error('newMessages - Caching new messages failed when trying to pull mail.messageS data from odoo! - messageIds - {}'.format(added))
        self.errorLogger.error('newMessages - Caching new messages failed when trying to pull mail.messageS data from odoo! - messageIds - {}'.format(added))
        return False
    self.debugLogger.debug('newMessages - Successful to retrieve mail.messageS remote. - messageIds: {}'.format(added))

    # validate and create event
    self.debugLogger.debug('newMessages - Trying to validate and create event...')

    eventsOfOrder = list()
    for event in self.openEvents.values():
            if event['cacheId'] == int(cacheId) : eventsOfOrder.append(event)
    self.debugLogger.debug('newMessages - eventsOfOrder: {}'.format(eventsOfOrder))

    newMessageIds = list()

    for mailMessage in mailMessageS_remote:

        if type(mailMessage['author_id']) == type([]) and len(mailMessage['author_id']) > 1 and type(mailMessage['date']) == type('') and mailMessage['date'] != '' and type(mailMessage['body']) == type (''):

            if mailMessage['body'].startswith('<p>$'):

                self.debugLogger.debug('newMessages - creating ERPNewCommand event...')
                isSucceed_createEvent, newEventCreated = self.createEvent(cacheId, 4, 'ERPNewCommand', {'time': mailMessage['date'], 'author': mailMessage['author_id'][1], 'command': mailMessage['body']}, eventsOfOrder)
                if not isSucceed_createEvent:
                    self.debugLogger.error('newMessages - Failed to create ERPNewCommand event!')
                    self.errorLogger.error('newMessages - Failed to create ERPNewCommand event!')
                    return False
                if newEventCreated : newMessageIds.append(mailMessage['id'])

            else:
                self.debugLogger.debug('newMessages - creating ERPNewMessage event...')
                isSucceed_createEvent, newEventCreated = self.createEvent(cacheId, 4, 'ERPNewMessage', {'time': mailMessage['date'], 'author': mailMessage['author_id'][1], 'message': mailMessage['body']}, eventsOfOrder)
                if not isSucceed_createEvent:
                    self.debugLogger.error('newMessages - Failed to create ERPNewMessage event!')
                    self.errorLogger.error('newMessages - Failed to create ERPNewMessage event!')
                    return False
                if newEventCreated : newMessageIds.append(mailMessage['id'])

        else:
            self.debugLogger.error('newMessages - Failed to validate mail.message remote! - mailMessage: {}'.format(mailMessage))
            self.errorLogger.error('newMessages - Failed to validate mail.message remote! - mailMessage: {}'.format(mailMessage))
            return False

    self.debugLogger.debug('newMessages - Successful to validate and create event.')

    # update database
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT stockPicking, summary FROM {} WHERE id = %s'.format(self.cacheTable), (cacheId, ))
        row  = cur.fetchone()
        stockPicking_cache = json.loads(row[0])
        summary_cache = json.loads(row[1])
        stockPicking_cache[str(pickingId)]['message_ids'].extend(newMessageIds)
        summary_cache['saleOrder']['stockPicking'][str(pickingId)]['message_ids'].extend(newMessageIds)
        cur.execute('UPDATE {} SET stockPicking = %s, summary = %s WHERE id = %s'.format(self.cacheTable), (json.dumps(stockPicking_cache), json.dumps(summary_cache), cacheId))
        conn.commit()
    except Exception as e:
        self.debugLogger.exception('newMessages - Couldn\'t retrieve the cache data or json error. -  error: {}'.format(e))
        self.errorLogger.error('newMessages - Couldn\'t retrieve the cache data or json error. -  error: {}'.format(e))
        return False
    finally : conn.close()

    # update orderSummaries
    self.debugLogger.debug('newMessages - Trying to update dictionary orderSummaries...')
    try: self.orderSummaries[str(cacheId)]['saleOrder']['stockPicking'][str(pickingId)]['message_ids'].extend(newMessageIds)
    except Exception as e:
        self.debugLogger.exception('newMessages - Failed to update dictionary orderSummaries! error: {}'.format(e))
        self.errorLogger.error('newMessages - Failed to update dictionary orderSummaries! error: {}'.format(e))
    self.debugLogger.debug('newMessages - Successful to update dictionary orderSummaries.')

    self.debugLogger.debug('newMessages - Successful to cacheNewMessages.')
    return True

def orderOnHoldEvent(self, remoteId, cacheId, reason):
    self.debugLogger.debug('orderOnHoldEvent parameters - remoteId: {} - cacheId: {} - reason: {}'.format(remoteId, cacheId, reason))
    eventsOfOrder = list()
    for event in self.openEvents.values():
        if event['cacheId'] == int(cacheId) : eventsOfOrder.append(event)
    self.debugLogger.debug('orderOnHoldEvent eventsOfOrder: {}'.format(eventsOfOrder))
    isSucceed_createEvent, isNewEventCreated = self.createEvent(cacheId, 5, 'OrderOnHold', {'source': self.endpointName, 'reason': reason, 'remoteId': remoteId}, eventsOfOrder)
    if isSucceed_createEvent : self.debugLogger.debug('orderOnHoldEvent Successful.')
    else:
        self.debugLogger.critical('Failed to create OnHold event! - sale.order.id: {} - cacheId: {}'.format(remoteId, cacheId))
        self.errorLogger.critical('Failed to create OnHold event! - sale.order.id: {} - cacheId: {}'.format(remoteId, cacheId))
        #self.smtpLogger.critical('Failed to create OnHold event! - sale.order.id: {} - cacheId: {}'.format(remoteId, cacheId))

def updateCacheData(self, cacheId, change):
    self.debugLogger.debug('updateCacheData parameters - cacheId: {} - change: {}'.format(cacheId, change))

    # parse data
    self.debugLogger.debug('updateCacheData - Parsing data...')
    try:
        indexList = change['index'].split('.')
        indexIgnore = indexList.copy()
        indexIgnore.remove(indexIgnore[-1])
        try : int(indexList[-2])
        except : columnIndex = -2
        else : columnIndex = -3
    except Exception as e:
        self.debugLogger.exception('updateCacheData - Couldn\'t retrieve the cache data or json error. -  error: {}'.format(e))
        self.errorLogger.error('updateCacheData - Couldn\'t retrieve the cache data or json error. -  error: {}'.format(e))
        return False
    self.debugLogger.debug('updateCacheData - Successful to parse data.')

    # pull cache data
    self.debugLogger.debug('updateCacheData - Retrieving cache data...')
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT {} FROM {} WHERE id = %s'.format(indexList[columnIndex], self.cacheTable), (int(cacheId), ))
        cacheData = json.loads(cur.fetchone()[0])
    except Exception as e:
        self.debugLogger.exception('updateCacheData - Couldn\'t retrieve the cache data or json error. -  error: {}'.format(e))
        self.errorLogger.error('updateCacheData - Couldn\'t retrieve the cache data or json error. -  error: {}'.format(e))
        return False
    finally : conn.close()
    self.debugLogger.debug('updateCacheData - Successful to retrieve cache data. - cacheData: {}'.format(cacheData))

    # update ordersummaries
    self.debugLogger.debug('updateCacheData - Updating orderSummaries...')
    try:
        if len(indexIgnore) == 1 : self.orderSummaries[str(cacheId)][str(indexIgnore[0])]['__last_update'] = change['__last_update']
        elif len(indexIgnore) == 2 : self.orderSummaries[str(cacheId)][str(indexIgnore[0])][str(indexIgnore[1])]['__last_update'] = change['__last_update']
        elif len(indexIgnore) == 3 : self.orderSummaries[str(cacheId)][str(indexIgnore[0])][str(indexIgnore[1])][str(indexIgnore[2])]['__last_update'] = change['__last_update']
        elif len(indexIgnore) == 4 : self.orderSummaries[str(cacheId)][str(indexIgnore[0])][str(indexIgnore[1])][str(indexIgnore[2])][str(indexIgnore[3])]['__last_update'] = change['__last_update']
        elif len(indexIgnore) == 5 : self.orderSummaries[str(cacheId)][str(indexIgnore[0])][str(indexIgnore[1])][str(indexIgnore[2])][str(indexIgnore[3])][str(indexIgnore[4])]['__last_update'] = change['__last_update']
    except Exception as e:
        self.debugLogger.exception('updateCacheData - Failed to update orderSummaries! - error: {} - data: {}'.format(e, cacheData))
        self.errorLogger.error('updateCacheData - Failed to update orderSummaries! - error: {} - data: {}'.format(e, cacheData))
        return False
    self.debugLogger.debug('updateCacheData - Successful to update orderSummaries.')

    # update field and lastupdate in column
    self.debugLogger.debug('updateCacheData - Updating cacheData...')
    try:
        if change['type'] == 'flat' : cacheData[indexList[-1]] = change['new']
        else:
            cacheData[indexList[-1]] += change['added']
            for x in change['removed'] : cacheData[indexList[-1]].remove(x)
        if columnIndex == -2 : cacheData['__last_update'] = change['__last_update']
        else : cacheData[indexList[-2]]['__last_update'] = change['__last_update']
    except Exception as e:
        self.debugLogger.exception('updateCacheData - Failed to update cacheData! - error: {} - data: {}'.format(e, cacheData))
        self.errorLogger.error('updateCacheData - Failed to update cacheData! - error: {} - data: {}'.format(e, cacheData))
        return False
    self.debugLogger.debug('updateCacheData - Successful to update cacheData.')

    # update database
    self.debugLogger.debug('updateCacheData - Updating database...')
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('UPDATE {} SET {} = %s WHERE id = %s'.format(self.cacheTable, indexList[columnIndex]), (json.dumps(cacheData), cacheId))
        cur.execute('UPDATE {} SET summary = %s WHERE id = %s'.format(self.cacheTable), (json.dumps(self.orderSummaries[str(cacheId)]), int(cacheId)))
        conn.commit()
    except Exception as e:
        self.debugLogger.exception('updateCacheData - Couldn\'t update data. error: {} - data: {}'.format(e, cacheData))
        self.errorLogger.error('updateCacheData - Couldn\'t update data. error: {} - data: {}'.format(e, cacheData))
        return False
    finally : conn.close()
    self.debugLogger.debug('updateCacheData - Successful to update database.')

    self.debugLogger.debug('updateCacheData Successful')
    return True