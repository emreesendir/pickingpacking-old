from enum import Flag
import mysql.connector, json, os

def markOrder(self, cacheId, eventId):
    self.debugLogger.debug('{} - markOrder parameters - cacheId: {}'.format(eventId, cacheId))

    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT {} FROM {} WHERE id = %s'.format('saleOrder', self.cacheTable), (cacheId, ))
        for row in cur : saleOrder = json.loads(row[0])
    except Exception as e:
        self.debugLogger.exception('{} - markOrder - Couldn\'t retrieve the cache data or json error - saleOrder. -  error: {}'.format(eventId, e))
        self.errorLogger.error('{} - markOrder - Couldn\'t retrieve the cache data or json error - saleOrder. -  error: {}'.format(eventId, e))
        return False
    finally:
        conn.close()

    try:
        order = self.saleOrder_env.browse([saleOrder['id']])
        id2 = self.InternalStatus.search([('x_studio_code','=', 'autoprint')])[0]
        id3 = self.InternalStatus.search([('x_studio_code','=', 'printed')])[0]
        notMarkedYet = True
        for status in order.x_InternalStatus:
            if status.id == id3 : notMarkedYet = False
        if notMarkedYet:
            order.x_InternalStatus = [(3, id2, 0)]
            order.x_InternalStatus = [(4, id3, 0)]
            order.message_post(body = 'WMS: Internal Status: autoprint --> printed', subtype_id = 2)
        else:
            self.debugLogger.error('{} - markOrder - order has been marked already! - cacheId: {} - saleOrder.id: {}'.format(eventId, cacheId, saleOrder['id']))
            self.errorLogger.error('{} - markOrder - order has been marked already! - cacheId: {} - saleOrder.id: {}'.format(eventId, cacheId, saleOrder['id']))
            return False

    except Exception as e:
        self.debugLogger.exception('{} - markOrder - Internal status update failed! - cacheId: {} - error: {}'.format(eventId, cacheId, e))
        self.errorLogger.error('{} - markOrder - Internal status update failed! - cacheId: {} - error: {}'.format(eventId, cacheId, e))
        return False

    self.debugLogger.debug('{} - markOrder - Successful.'.format(eventId))
    return True

def postMessage(self, cacheId, message):
    self.debugLogger.debug('postMessage parameters - cacheId: {} - message: {}'.format(cacheId, message))
    
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT {} FROM {} WHERE id = %s'.format('stockPicking', self.cacheTable), (cacheId, ))
        for row in cur : stockPicking_cache = json.loads(row[0])
    except Exception as e:
        self.debugLogger.exception('postMessage - Couldn\'t retrieve the cache data or json error - stockPicking. -  error: {}'.format(e))
        self.errorLogger.error('postMessage - Couldn\'t retrieve the cache data or json error - stockPicking. -  error: {}'.format(e))
        return False
    finally:
        conn.close()

    try:
        for odooId in stockPicking_cache.keys():
            picking = self.stockPicking_env.browse([int(odooId)])
            picking.message_post(body = message, subtype_id = 2)
            break
    except Exception as e:
        self.debugLogger.exception('postMessage - Couldn\'t post to message to stock.picking -  error: {}'.format(e))
        self.errorLogger.error('postMessage - Couldn\'t post to message to stock.picking -  error: {}'.format(e))
        return False

    self.debugLogger.debug('postMessage - Successful.')
    return True

def deleteOrder(self, cacheId):
    self.debugLogger.debug('deleteOrder parameters - cacheId: {}'.format(cacheId))

    # remove order from scanningThread
    self.debugLogger.debug('deleteOrder - Removing order from scanningThread... - orderSummaries: {}')
    try:
        self.deleteList.append(cacheId)
        while str(cacheId) in self.orderSummaries : continue
    except Exception as e:
        self.debugLogger.exception('deleteOrder - Failed to remove order from scanningThread! - error: {}'.format(e))
        self.errorLogger.error('deleteOrder - Failed to remove order from scanningThread! - error: {}'.format(e))
        return False
    else : self.debugLogger.debug('delteOrder - Successful to remove order from scanningThread.')

    # checkout message
    self.debugLogger.debug('deleteOrder - Posting check out message...')
    try : self.postMessage(cacheId, 'WMS: Check Out')
    except Exception as e:
        self.debugLogger.exception('deleteOrder - Failed to post checkout message! - error: {}'.format(e))
        self.errorLogger.error('deleteOrder - Failed to post checkout message! - error: {}'.format(e))
    else : self.debugLogger.debug('deleteOrder - Successful to post check out message.')

    # DELETE DATA
    self.debugLogger.debug('deleteOrder - Deleting from cache table...')
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('DELETE FROM {} WHERE id = %s'.format(self.cacheTable), (cacheId, ))
        conn.commit()
    except Exception as e:
        self.debugLogger.error('deleteOrder - Failed to delete from cache table! - error: {}'.format(e))
        return False
    finally : conn.close()
    self.debugLogger.debug('deleteOrder - Successful to delete from cache table...')

    self.debugLogger.debug('deleteOrder successful.')
    return True

def deleteInvoices(self, cacheId, remoteId):
    self.debugLogger.debug('deleteInvoice parameters - cacheId: {}'.format(cacheId))
    try:
        for file in os.listdir(self.invoiceFolder):
            if file.startswith(remoteId) : os.remove('{}{}'.format(self.invoiceFolder, file))
    except Exception as e:
        self.debugLogger.exception('deleteInvoice error: {}'.format(e))
        self.errorLogger.error('deleteInvoice error: {}'.format(e))
        return False
    self.debugLogger.debug('deleteInvoice successful.')
    return True

# ========= LATER ========= #
def orderShipped(self, cacheId):
    pass