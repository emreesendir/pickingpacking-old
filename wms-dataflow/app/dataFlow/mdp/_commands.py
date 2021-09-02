import mysql.connector, json, time, datetime

def NoInvoice(self, event, command):
    self.debugLogger.debug('{} - NoInvoice parameters - event: {} - command: {}'.format(event['id'], event, command))

    # retrieve order status
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT status FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
        status = cur.fetchone()[0]
    except Exception as e:
        self.debugLogger.exception('{} - NoInvoice - Couldn\'t retrieve order status! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
        self.errorLogger.error('{} - NoInvoice - Couldn\'t retrieve order status! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
        return 'NO INVOICE Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False
    finally:
        conn.close()

    # execute the command
    if status == 'WAITING FOR SIZING' or status == 'WAITING FOR PICKING' or status == 'PICKING IN PROGRESS' or status == 'WAITING FOR PACKING' or status.startswith('ON HOLD') or status == 'MERGED':

        # APPEND THE COMMAND TO THE ORDER IF IT IS NOT EXIST
        # retrieve order commands
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            cur.execute('SELECT commands FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
            commands = cur.fetchone()[0]
            commandList = commands.split('.')
        except Exception as e:
            self.debugLogger.exception('{} - NoInvoice - Couldn\'t retrieve order commands! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
            self.errorLogger.error('{} - NoInvoice - Couldn\'t retrieve order commands! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
            return 'NO INVOICE Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False
        finally:
            conn.close()

        # if status is 'MERGED', check parent status
        if status == 'MERGED':
            parentEndpointId = -1
            parentCacheId = -1

            for oneCommand in commandList:
                if oneCommand.startswith('PARENT'):
                    identifier = oneCommand[7:]
                    identifier = identifier.split('-')
                    try:
                        parentEndpointId = identifier[0]
                        parentCacheId = identifier[1]
                    except Exception as e:
                        self.debugLogger.exception('{} - NoInvoice - Problem while trying to reach parent order! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
                        self.errorLogger.error('{} - NoInvoice - Problem while trying to reach parent order! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
                        return 'NO INVOICE Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False

            if parentCacheId != -1 and parentEndpointId != -1:
                try:
                    conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                    cur = conn.cursor()
                    cur.execute('SELECT status FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (parentEndpointId, parentCacheId))
                    parentStatus = cur.fetchone()[0]
                except Exception as e:
                    self.debugLogger.exception('{} - NoInvoice - Couldn\'t retrieve parent order status! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
                    self.errorLogger.error('{} - NoInvoice - Couldn\'t retrieve parent order status! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
                    return 'NO INVOICE Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False
                finally:
                    conn.close()

                if parentStatus == None:
                    self.debugLogger.error('{} - NoInvoice - Parent status = None! - event: {} - command: {}'.format(event['id'], event, command))
                    self.errorLogger.error('{} - NoInvoice - Parent status = None! - event: {} - command: {}'.format(event['id'], event, command))
                    return 'NO INVOICE Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False

                elif parentStatus == 'WAITING FOR SIZING' or parentStatus == 'WAITING FOR PICKING' or parentStatus == 'PICKING IN PROGRESS' or parentStatus == 'WAITING FOR PACKING' or parentStatus.startswith('ON HOLD') : self.debugLogger.debug('{} - NoInvoice - Parent Order Status OK.'.format(event['id']))

                elif status == 'PACKING IN PROGRESS' or status == 'SHIPPED' or status == 'CANCELED' or status == 'MARKED':
                    self.debugLogger.error('{} - NoInvoice - A command executed after parent order closed! - event: {} - command: {} - parentStatus: {}'.format(event['id'], event, command, parentStatus))
                    self.errorLogger.error('{} - NoInvoice - A command executed after parent order closed! - event: {} - command: {} - parentStatus: {}'.format(event['id'], event, command, parentStatus))
                    return 'NO INVOICE Command Failed! - Parent Order Closed', False

                else:
                    self.debugLogger.error('{} - NoInvoice - Invalid order status! - event: {} - command: {}'.format(event['id'], event, command))
                    self.errorLogger.error('{} - NoInvoice - Invalid order status! - event: {} - command: {}'.format(event['id'], event, command))
                    return 'NO INVOICE Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False

            else:
                self.debugLogger.error('{} - NoInvoice - Could\'t reach parent id! - event: {} - command: {}'.format(event['id'], event, command))
                self.errorLogger.error('{} - NoInvoice - Could\'t reach parent id! - event: {} - command: {}'.format(event['id'], event, command))
                return 'NO INVOICE Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False

        # update order commands
        if 'NO INVOICE' not in commandList:
            try:
                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                cur = conn.cursor()
                cur.execute('UPDATE dataflow_order SET commands = %s WHERE endpoint_id = %s AND cacheId = %s', (commands+'.NO INVOICE', event['endpoint_id'], event['cacheId']))
                conn.commit()
            except Exception as e:
                self.debugLogger.exception('{} - NoInvoice - Couldn\'t update order commands! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
                self.errorLogger.error('{} - NoInvoice - Couldn\'t update order commands! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
                return 'NO INVOICE Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False
            finally:
                conn.close()

            self.debugLogger.debug('{} - NoInvoice - Comaand Successful. - event: {} - command: {}'.format(event['id'], event, command))
            return 'NO INVOICE Command Successful', True

        else:
            self.debugLogger.warning('{} - NoInvoice - Command has already been recorded! - event: {} - command: {}'.format(event['id'], event, command))
            return 'NO INVOICE Command Failed! - Command Already Exist', False

    elif status == 'PACKING IN PROGRESS' or status == 'SHIPPED' or status == 'CANCELED' or status == 'MARKED':
        self.debugLogger.error('{} - NoInvoice - A command executed after order has been shipped! - event: {} - command: {}'.format(event['id'], event, command))
        self.errorLogger.error('{} - NoInvoice - A command executed after order has been shipped! - event: {} - command: {}'.format(event['id'], event, command))
        return 'NO INVOICE Command Failed! - Order Closed', False

    else:
        self.debugLogger.error('{} - NoInvoice - Invalid order status! - event: {} - command: {}'.format(event['id'], event, command))
        self.errorLogger.error('{} - NoInvoice - Invalid order status! - event: {} - command: {}'.format(event['id'], event, command))
        return 'NO INVOICE Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False

def NoShipment(self, event, command):
    self.debugLogger.debug('{} - NoShipment parameters - event: {} - command: {}'.format(event['id'], event, command))

    # retrieve order status
    self.debugLogger.debug('{} - NoShipment - Retrieving order status...'.format(event['id']))
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT status FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
        status = cur.fetchone()[0]
    except Exception as e:
        self.debugLogger.exception('{} - NoShipment - Couldn\'t retrieve order status! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
        self.errorLogger.error('{} - NoShipment - Couldn\'t retrieve order status! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
        return 'NO SHIPMENT Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False
    finally : conn.close()
    self.debugLogger.debug('{} - NoShipment - Successful to retrieve order status.'.format(event['id']))

    # execute the command
    if status == 'WAITING FOR SIZING' or status == 'WAITING FOR PICKING' or status == 'PICKING IN PROGRESS' or status == 'WAITING FOR PACKING' or status.startswith('ON HOLD') or status == 'MERGED':

        # APPEND THE COMMAND TO THE ORDER IF IT IS NOT EXIST
        # retrieve order commands
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            cur.execute('SELECT commands FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
            commands = cur.fetchone()[0]
            commandList = commands.split('.')
        except Exception as e:
            self.debugLogger.exception('{} - NoShipment - Couldn\'t retrieve order commands! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
            self.errorLogger.error('{} - NoShipment - Couldn\'t retrieve order commands! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
            return 'NO SHIPMENT Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False
        finally : conn.close()

        # if status is 'MERGED', check parent status
        if status == 'MERGED':
            parentEndpointId = -1
            parentCacheId = -1

            for oneCommand in commandList:
                if oneCommand.startswith('PARENT'):
                    identifier = oneCommand[7:]
                    identifier = identifier.split('-')
                    try:
                        parentEndpointId = identifier[0]
                        parentCacheId = identifier[1]
                    except Exception as e:
                        self.debugLogger.exception('{} - NoShipment - Problem while trying to reach parent order! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
                        self.errorLogger.error('{} - NoShipment - Problem while trying to reach parent order! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
                        return 'NO SHIPMENT Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False

            if parentCacheId != -1 and parentEndpointId != -1:
                try:
                    conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                    cur = conn.cursor()
                    cur.execute('SELECT status FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (parentEndpointId, parentCacheId))
                    parentStatus = cur.fetchone()[0]
                except Exception as e:
                    self.debugLogger.exception('{} - NoShipment - Couldn\'t retrieve parent order status! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
                    self.errorLogger.error('{} - NoShipment - Couldn\'t retrieve parent order status! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
                    return 'NO SHIPMENT Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False
                finally : conn.close()

                if parentStatus == 'WAITING FOR SIZING' or parentStatus == 'WAITING FOR PICKING' or parentStatus == 'PICKING IN PROGRESS' or parentStatus == 'WAITING FOR PACKING' or parentStatus.startswith('ON HOLD') : self.debugLogger.debug('{} - NoShipment - Parent Order Status OK.'.format(event['id']))

                elif status == 'PACKING IN PROGRESS' or status == 'SHIPPED' or status == 'CANCELED' or status == 'MARKED':
                    self.debugLogger.error('{} - NoShipment - A command executed after parent order closed! - event: {} - command: {} - parentStatus: {}'.format(event['id'], event, command, parentStatus))
                    self.errorLogger.error('{} - NoShipment - A command executed after parent order closed! - event: {} - command: {} - parentStatus: {}'.format(event['id'], event, command, parentStatus))
                    return 'NO SHIPMENT Command Failed! - Parent Order Closed', False

                else:
                    self.debugLogger.error('{} - NoShipment - Invalid order status! - event: {} - command: {}'.format(event['id'], event, command))
                    self.errorLogger.error('{} - NoShipment - Invalid order status! - event: {} - command: {}'.format(event['id'], event, command))
                    return 'NO SHIPMENT Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False

            else:
                self.debugLogger.error('{} - NoShipment - Could\'t reach parent id! - event: {} - command: {}'.format(event['id'], event, command))
                self.errorLogger.error('{} - NoShipment - Could\'t reach parent id! - event: {} - command: {}'.format(event['id'], event, command))
                return 'NO SHIPMENT Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False

        # update order commands
        if 'NO SHIPMENT' not in commandList:
            try:
                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                cur = conn.cursor()
                cur.execute('UPDATE dataflow_order SET commands = %s WHERE endpoint_id = %s AND cacheId = %s', (commands+'.NO SHIPMENT', event['endpoint_id'], event['cacheId']))
                conn.commit()
            except Exception as e:
                self.debugLogger.exception('{} - NoShipment - Couldn\'t update order commands! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
                self.errorLogger.error('{} - NoShipment - Couldn\'t update order commands! - error: {} - event: {} - command: {}'.format(event['id'], e, event, command))
                return 'NO SHIPMENT Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False
            finally : conn.close()

            self.debugLogger.debug('{} - NoShipment - Comaand Successful. - event: {} - command: {}'.format(event['id'], event, command))
            return 'NO SHIPMENT Command Successful', True

        else:
            self.debugLogger.warning('{} - NoShipment - Command has already been recorded! - event: {} - command: {}'.format(event['id'], event, command))
            return 'NO SHIPMENT Command Failed! - Command Already Exist', False

    elif status == 'PACKING IN PROGRESS' or status == 'SHIPPED' or status == 'CANCELED' or status == 'MARKED':
        self.debugLogger.error('{} - NoShipment - A command executed after order has been shipped! - event: {} - command: {}'.format(event['id'], event, command))
        self.errorLogger.error('{} - NoShipment - A command executed after order has been shipped! - event: {} - command: {}'.format(event['id'], event, command))
        return 'NO SHIPMENT Command Failed! - Order Closed', False

    else:
        self.debugLogger.error('{} - NoShipment - Invalid order status! - event: {} - command: {}'.format(event['id'], event, command))
        self.errorLogger.error('{} - NoShipment - Invalid order status! - event: {} - command: {}'.format(event['id'], event, command))
        return 'NO SHIPMENT Command Failed! - Software Error! Please Contact System Administrator and Warehouse Supervisor', False

def Merge(self, event, command):
    self.debugLogger.debug('{} - Merge parameters - command: {}'.format(event['id'], command))

    # extract parent's remote Id
    self.debugLogger.debug('{} - Merge - Parsing command...'.format(event['id']))
    try : parentRemoteId = command['command'][10:command['command'].find('</p>')].strip()
    except Exception as e:
        self.debugLogger.error('{} - Merge - Failed to parse command! - error: {}'.format(event['id'], e))
        self.errorLogger.error('{} - Merge - Failed to parse command! - error: {}'.format(event['id'], e))
        return '', False
    else : self.debugLogger.debug('{} - Merge - Successful to parse command. - parentRemoteId: {}'.format(event['id'], parentRemoteId))

    # retrieve parent and child informations
    self.debugLogger.debug('{} - Merge - Retrieveng parent and child informations...'.format(event['id']))
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT remoteId, status, commands FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
        row = cur.fetchone()
        childRemoteId = row[0]
        childStatus = row[1]
        childCommands = row[2]
        cur.execute('SELECT cacheId, status, commands FROM dataflow_order WHERE endpoint_id = %s AND remoteId = %s', (event['endpoint_id'], parentRemoteId))
        row  = cur.fetchone()
        parentCacheId = row[0]
        parentStatus = row[1]
        parentCommands = row[2]
    except Exception as e:
        self.debugLogger.exception('{} - Merge - Failed to retrieve parent and child informations! - error: {}'.format(event['id'], e))
        self.errorLogger.error('{} - Merge - Failed to retrieve parent and child informations! - error: {}'.format(event['id'], e))
        return False
    else : self.debugLogger.debug('{} - Merge - Successful to retrieve parent and child informations - childStatus: {} - childCommands: {} -  parentCacheId: {} - parentStatus: {}'.format(event['id'], childStatus, childCommands, parentCacheId, parentStatus))
    finally : conn.close()

    if (childStatus == 'WAITING FOR SIZING' or childStatus == 'WAITING FOR PICKING') and parentStatus == 'ON HOLD FOR MERGE':

        try:
            # block the parent order
            self.debugLogger.debug('{} - Merge - Internal block for parent order...'.format(event['id']))
            try:
                self.requestForInternalBlock.append((event['endpoint_id'], parentCacheId, event))
                start = time.perf_counter()
                while (event['endpoint_id'], parentCacheId, event) not in self.internalBlock : continue
            except Exception as e:
                self.debugLogger.exception('{} - Merge - Failed: Internal block for parent order! - error: {} - event: {}'.format(event['id'], e, event))
                self.errorLogger.error('{} - Merge - Failed: Internal block for parent order! - error: {} - event: {}'.format(event['id'], e, event))
                return '', False
            else : self.debugLogger.debug('{} - Merge - Successful: Internal block for parent order. - Completed in {} second'.format(event['id'], time.perf_counter() - start))

            # execute merge

            # PARENT
            # add CHILD <<remoteId>> command to parent order commands
            # history
            # order continue

            # CHILD
            # add PARENT <<remoteId>> command to parent order commands + status --> MERGED
            # history

            self.debugLogger.debug('{} - Merge - Executing merge...'.format(event['id']))
            try:
                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                cur = conn.cursor()
                cur.execute('UPDATE dataflow_order SET commands = %s WHERE endpoint_id = %s AND cacheId = %s', (parentCommands+'.CHILD {}'.format(childRemoteId), event['endpoint_id'], parentCacheId))
                cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], parentCacheId, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Child attached. - childCahceId: {} - childRemoteId: {}'.format(event['cacheId'], childRemoteId), parentStatus, ''))
                cur.execute('INSERT INTO dataflow_event (endpoint_id, cacheId, priority, time, type, data, result) VALUES (%s, %s, %s, %s, %s, %s, %s)', (event['endpoint_id'], parentCacheId, 4, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'OrderContinue', json.dumps({'remoteId': parentRemoteId}), ''))
                cur.execute('UPDATE dataflow_order SET commands = %s, status = %s WHERE endpoint_id = %s AND cacheId = %s', (childCommands+'.PARENT {}'.format(parentRemoteId), 'MERGED', event['endpoint_id'], event['cacheId']))
                cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Merged to cacheId: {} remoteId: {}'.format(parentCacheId, parentRemoteId), 'MERGED', ''))
                conn.commit()
            except Exception as e:
                self.debugLogger.exception('{} - Merge - Failed to execute merge! - error: {}'.format(event['id'], e))
                self.errorLogger.error('{} - Merge - Failed to execute merge! - error: {}'.format(event['id'], e))
                return '', False
            else : self.debugLogger.debug('{} - Merge - Successful to execute merge.'.format(event['id']))
            finally : conn.close()

            # post message
            # PARENT --> WMS: An order has been attached. Child ID: <<childReomteId>>
            # CHILD  --> WMS: Merge successful. Parent ID: <<parentRemoteId>>

            self.debugLogger.debug('{} - Merge - Posting messages...'.format(event['id']))
            isSucceed_postMessage1 = self.endpoints[str(event['endpoint_id'])].postMessage(parentCacheId, 'WMS: An order has been attached. Child ID: {}'.format(childRemoteId))
            isSucceed_postMessage2 = self.endpoints[str(event['endpoint_id'])].postMessage(event['cacheId'], 'WMS: Merge successful. Parent ID: {}'. format(parentRemoteId))
            if isSucceed_postMessage1 and isSucceed_postMessage2 : self.debugLogger.debug('{} - Merge - Successful to post messages.'.format(event['id']))
            else:
                self.debugLogger.error('{} - Merge - Failed to post messages!'.format(event['id']))
                self.errorLogger.error('{} - Merge - Failed to post messages!'.format(event['id']))

            self.debugLogger.debug('{} - Merge Successful.'.format(event['id']))
            return '', True

        finally:
            self.debugLogger.debug('{} - Merge - Removing block... - tuple: {} - requestForInternalBlock: {} - internalBlock: {}'.format((event['id'], event['endpoint_id'], parentCacheId, event), self.requestForInternalBlock, self.internalBlock))
            self.requestForInternalBlock.remove((event['endpoint_id'], parentCacheId, event))
            self.internalBlock.remove((event['endpoint_id'], parentCacheId, event))

    else:
        self.debugLogger.error('{} - Merge - Failed to validate merge! - childStatus: {} - parentStatus: {}'.format(event['id'], childStatus, parentStatus))
        self.errorLogger.error('{} - Merge - Failed to validate merge! - childStatus: {} - parentStatus: {}'.format(event['id'], childStatus, parentStatus))
        return '', False

def HoldForMerge(self, event, command):
    self.debugLogger.debug('{} - HoldForMerge parameters - event: {} - command: {}'.format(event['id'], event, command))

    # retrieve order status
    self.debugLogger.debug('{} - HoldForMerge - Retrieving order status...'.format(event['id']))
    try:
        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
        cur = conn.cursor()
        cur.execute('SELECT status FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
        status = cur.fetchone()[0]
    except Exception as e:
        self.debugLogger.exception('{} - HoldForMerge - Failed to retrieve order status! - error: {} - event: {}'.format(event['id'], e, event))
        self.errorLogger.error('{} - HoldForMerge - Failed to retrieve order status! - error: {} - event: {}'.format(event['id'], e, event))
        return '', False
    finally : conn.close()
    self.debugLogger.debug('{} - HoldForMerge - Successful to retrieve order status. - status: {}'.format(event['id'], status))

    if status == 'WAITING FOR SIZING' or status == 'WAITING FOR PICKING' or status == 'PICKING IN PROGRESS' or status == 'WAITING FOR PACKING' or status == 'ON HOLD':

        # put order on hold
        self.debugLogger.debug('{} - HoldForMerge - Putting order on hold...'.format(event['id']))
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Hold for merge command. - time: {0[time]} - author{0[author]}'.format(event['data']), 'ON HOLD FOR MERGE', ''))
            cur.execute('UPDATE dataflow_order SET status = %s WHERE endpoint_id = %s AND cacheId = %s', ('ON HOLD FOR MERGE', event['endpoint_id'], event['cacheId']))
            conn.commit()
        except Exception as e:
            self.debugLogger.exception('{} - HoldForMerge - Failed to put order on hold! - error: {} - event: {}'.format(event['id'], e, event))
            self.errorLogger.error('{} - HoldForMerge - Failed to put order on hold! - error: {} - event: {}'.format(event['id'], e, event))
            return '', False
        finally : conn.close()
        self.debugLogger.debug('{} - HoldForMerge - Successful to put order on hold.'.format(event['id']))

        # post message
        self.debugLogger.debug('{} - HoldForMerge - Posting message: "Waiting for merge"...'.format(event['id']))
        isSucceed_postMessage = self.endpoints[str(event['endpoint_id'])].postMessage(event['cacheId'], 'WMS: Waiting for merge')
        if isSucceed_postMessage : self.debugLogger.debug('{} - HoldForMerge - Successful to post message.'.format(event['id']))
        else:
            self.debugLogger.error('{} - HoldForMerge - Failed to post message!'.format(event['id']))
            self.errorLogger.error('{} - HoldForMerge - Failed to post message!'.format(event['id']))

        self.debugLogger.debug('{} - HoldForMerge Successful.'.format(event['id']))
        return '', True

    elif status == 'PACKING IN PROGRESS' or status == 'SHIPPED':

        # post message
        self.debugLogger.debug('{} - HoldForMerge - Posting message: "Error! Too late for merge"...'.format(event['id']))
        isSucceed_postMessage = self.endpoints[str(event['endpoint_id'])].postMessage(event['cacheId'], 'WMS: Error! Too late for merge')
        if isSucceed_postMessage : self.debugLogger.debug('{} - HoldForMerge - Successful to post message.'.format(event['id']))
        else:
            self.debugLogger.error('{} - HoldForMerge - Failed to post message!'.format(event['id']))
            self.errorLogger.error('{} - HoldForMerge - Failed to post message!'.format(event['id']))

        self.debugLogger.debug('HoldForMerge Successful.'.format(event['id']))
        return '', True

    else:
        self.debugLogger.error('{} - HoldForMerge - Invalid order status! - status: {} - event: {}'.format(event['id'], status, event))
        self.errorLogger.error('{} - HoldForMerge - Invalid order status! - status: {} - event: {}'.format(event['id'], status, event))
        return '', False
