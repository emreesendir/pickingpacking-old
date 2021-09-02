import mysql.connector, json, datetime, time

def OrderOnHold(self, event):
    self.debugLogger.debug('{} - OrderOnHold parameters - event: {}'.format(event['id'], event))
    try:

        # check if order record created
        self.debugLogger.debug('{} - OrderOnHold - Checking if order record created...'.format(event['id']))
        orderId = -1
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            if event['cacheId'] != -1 : cur.execute('SELECT id FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
            else : cur.execute('SELECT id FROM dataflow_order WHERE endpoint_id = %s AND remoteId = %s AND status != %s', (event['endpoint_id'], event['data']['remoteId'], 'SHIPPED'))
            for row in cur : orderId = row[0]
        except Exception as e:
            self.debugLogger.exception('{} - OrderOnHold - Failed to load! - error: {}'.format(event['id'], e))
            self.errorLogger.critical('{} - OrderOnHold - Failed to load! - error: {}'.format(event['id'], e))
            #self.smtpLogger.critical('{} - OrderOnHold - Failed to load! - error: {}'.format(event['id'], e))
            return False
        finally:
            conn.close()

        # create a dummy order for hold
        if orderId == -1:
            self.debugLogger.debug('{} - OrderOnHold - Couldn\'t find order record. Creating a dummy order for hold...'.format(event['id']))
            try:
                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                cur = conn.cursor()
                cur.execute('INSERT INTO dataflow_order (endpoint_id, cacheId, productLines, shippingInformation, invoice, status, remoteId, size, commands) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], json.dumps([]), json.dumps({}), '', 'ON HOLD', event['data']['remoteId'], '', ''))
                cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, remoteId, time, event, status) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], event['data']['remoteId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'An error occured before the order has been recorded! - time: {1} - source: {0[source]} - reason: {0[reason]}'.format(event['data'], event['time']), 'ON HOLD'))
                conn.commit()
            except Exception as e:
                self.debugLogger.exception('{} - OrderOnHold - Couldn\'t insert new order. error: {} - event: {}'.format(event['id'], e, event))
                self.errorLogger.critical('{} - OrderOnHold - Couldn\'t insert new order. error: {} - event: {}'.format(event['id'], e, event))
                #self.smtpLogger.critical('{} - OrderOnHold - Couldn\'t insert new order. error: {} - event: {}'.format(event['id'], e, event))
                return False
            finally:
                conn.close()
            self.debugLogger.debug('{} - OrderOnHold - A dummy order created for hold.'.format(event['id']))

        # put order on hold
        else:
            self.debugLogger.debug('{} - OrderOnHold - Order found. Putting order on hold...'.format(event['id']))
            try:
                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                cur = conn.cursor()
                cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'An error occured! - time: {1} - source: {0[source]} - reason: {0[reason]}'.format(event['data'], event['time']), 'ON HOLD', ''))
                cur.execute('UPDATE dataflow_order SET status = %s WHERE id = %s', ('ON HOLD', orderId))
                conn.commit()
            except Exception as e:
                self.debugLogger.exception('{} - OrderOnHold - Couldn\'t insert history. error: {} - event: {}'.format(event['id'], e, event))
                self.errorLogger.critical('{} - OrderOnHold - Couldn\'t insert history. error: {} - event: {}'.format(event['id'], e, event))
                #self.smtpLogger.critical('{} - OrderOnHold - Couldn\'t insert history. error: {} - event: {}'.format(event['id'], e, event))
                return False
            finally:
                conn.close()
            self.debugLogger.debug('{} - OrderOnHold - Successful to put order on hold.'.format(event['id']))

        # post message
        if event['cacheId'] != -1:
            self.debugLogger.debug('{} - OrderOnHold - Posting message: "Order On Hold"...')
            if self.endpoints[str(event['endpoint_id'])].postMessage(event['cacheId'], 'WMS: Order On Hold') : self.debugLogger.debug('{} - OrderOnHold - Successful to post message.'.format(event['id']))
            else:
                self.debugLogger.error('{} - OrderOnHold - Failed to post message!'.format(event['id']))
                self.errorLogger.error('{} - OrderOnHold - Failed to post message!'.format(event['id']))

        # close event
        if event['id'] != -1:
            self.debugLogger.debug('{} - OrderOnHold - Closing event...'.format(event['id']))
            if self.closeEvent(event, 'OK') : self.debugLogger.debug('{} - OrderOnHold - Successful to close event.'.format(event['id']))
            else:
                self.debugLogger.exception('{} - OrderOnHold - Failed to close event! - event: {}'.format(event['id'], event))
                self.errorLogger.error('{} - OrderOnHold - Failed to close event! - event: {}'.format(event['id'], event))
                return False

    finally:
        if event['id'] != -1:
            del self.workingThreads[str(event['id'])]
            self.debugLogger.debug('{} - OrderOnHold - workingThreads updated. - workingThreads lenght: {} - workingThreads: {}'.format(event['id'], len(self.workingThreads), self.workingThreads))
            self.ordersInProgress.remove((event['endpoint_id'], event['cacheId']))
            self.debugLogger.debug('{} - OrderOnHold - ordersInProgress updated. - ordersInProgress lenght: {} - ordersInProgress: {}'.format(event['id'], len(self.ordersInProgress), self.ordersInProgress))

def Warning(self, event):
    self.debugLogger.debug('{} - Warning parameters - event: {}'.format(event['id'], event))

    try:
        # create history record
        self.debugLogger.debug('{} - Warning - Creating history record...'.format(event['id']))
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            cur.execute('SELECT status FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
            row = cur.fetchone()
            cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'WARNING: {}'.format(event['data']['warning']), row[0], ''))
            conn.commit()
        except Exception as e:
            self.debugLogger.exception('{} - Warning - Failed to create history record! - error: {} - event: {}'.format(event['id'], e, event))
            self.errorLogger.error('{} - Warning - Failed to create history record! - error: {} - event: {}'.format(event['id'], e, event))
            raise Exception
        finally : conn.close()
        self.debugLogger.debug('{} - Warning - Successful to create history record.'.format(event['id']))

        # close event
        self.debugLogger.debug('{} - Warning - Closing event...'.format(event['id']))
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            cur.execute('UPDATE dataflow_event SET result = %s WHERE id = %s', ('OK', event['id']))
            conn.commit()
        except Exception as e:
            self.debugLogger.exception('{} - Warning - Failed to close event! - error: {} - event: {}'.format(event['id'], e, event))
            self.errorLogger.error('{} - Warning - Failed to close event! - error: {} - event: {}'.format(event['id'], e, event))
            raise Exception
        finally : conn.close()
        self.debugLogger.debug('{} - Warning - Successful to close event.'.format(event['id']))

        self.debugLogger.debug('{} - Warning - Successful. - event: {}'.format(event['id'], event))
        return True

    except:
        self.debugLogger.error('{} - Warning - Something went wrong. Putting order on hold...'.format(event['id']))
        self.errorLogger.error('{} - Warning - Something went wrong. Putting order on hold...'.format(event['id']))
        onholdevent = {'id' : -1, 'cacheId' : event['cacheId'], 'type' : 'OrderOnHold', 'priority' : -1, 'time' : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'data' : {'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'source': 'Warning', 'reason': 'An error occured while tying execute Warning event!', 'remoteId': ''}, 'endpoint_id' : event['endpoint_id']}
        self.OrderOnHold(onholdevent)
    finally:
        del self.workingThreads[str(event['id'])]
        self.ordersInProgress.remove((event['endpoint_id'], event['cacheId']))

def ERPNewOrder(self, event):
    self.debugLogger.debug('{} - ERPNewOrder parameters - event: {}'.format(event['id'], event))
    try:

        # save order
        self.debugLogger.debug('{} - ERPNewOrder - Creating order record...'.format(event['id']))
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            cur.execute('INSERT INTO dataflow_order (endpoint_id, cacheId, productLines, shippingInformation, invoice, status, remoteId, size, commands) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], json.dumps(event['data']['productLines']), json.dumps(event['data']['shippingInformation']), event['data']['invoice'], 'WAITING FOR SIZING', event['data']['remoteId'], '', ''))
            cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Order Created', 'WAITING FOR SIZING', ''))
            conn.commit()
        except Exception as e:
            self.debugLogger.exception('{} - ERPNewOrder - Couldn\'t insert new order. error: {} - event: {}'.format(event['id'], e, event))
            self.errorLogger.error('{} - ERPNewOrder - Couldn\'t insert new order. error: {} - event: {}'.format(event['id'], e, event))
            raise Exception
        finally:
            conn.close()
        self.debugLogger.debug('{} - ERPNewOrder - Order created successfully.'.format(event['id']))

        # post message
        self.debugLogger.debug('{} - ERPNewOrder - Posting message: "Order Record Created"...'.format(event['id']))
        isSucceed_postMessage = self.endpoints[str(event['endpoint_id'])].postMessage(event['cacheId'], 'WMS: Order Record Created')
        if isSucceed_postMessage : self.debugLogger.debug('{} - ERPNewOrder - Successful to post message.'.format(event['id']))
        else:
            self.debugLogger.error('{} - ERPNewOrder - Failed to post message!'.format(event['id']))
            self.errorLogger.error('{} - ERPNewOrder - Failed to post message!'.format(event['id']))
        self.debugLogger.debug('ERPNewOrder - Successful to post message: "Order Record Created"...'.format(event['id']))

        # close event
        self.debugLogger.debug('{} - ERPNewOrder - Closing event...'.format(event['id']))
        if self.closeEvent(event, 'OK') : self.debugLogger.debug('{} - ERPNewOrder - Successful to close event.'.format(event['id']))
        else:
            self.debugLogger.exception('{} - ERPNewOrder - Failed to close event! - event: {}'.format(event['id'], event))
            self.errorLogger.error('{} - ERPNewOrder - Failed to close event! - event: {}'.format(event['id'], event))
            raise Exception

    except:
        self.debugLogger.error('{} - ERPNewOrder - Something went wrong. Putting order on hold...'.format(event['id']))
        self.errorLogger.error('{} - ERPNewOrder - Something went wrong. Putting order on hold...'.format(event['id']))
        onholdevent = {'id' : -1, 'cacheId' : event['cacheId'], 'type' : 'OrderOnHold', 'priority' : -1, 'time' : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'data' : {'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'source': 'ERPNewOrder', 'reason': 'An error occured while tying to execute ERPNewOrder event!', 'remoteId': ''}, 'endpoint_id' : event['endpoint_id']}
        self.OrderOnHold(onholdevent)
    finally:
        del self.workingThreads[str(event['id'])]
        self.ordersInProgress.remove((event['endpoint_id'], event['cacheId']))

def ERPNewMessage(self, event):
    self.debugLogger.debug('{} - ERPNewMessage parameters - event: {}'.format(event['id'], event))
    try:

        # create history record
        self.debugLogger.debug('{} - ERPNewMessage - Creating history record...'.format(event['id']))
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            cur.execute('SELECT status FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
            status = cur.fetchone()[0]
            cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'REMOTE MESSAGE - time: {0[time]} - author: {0[author]} - message: {0[message]}'.format(event['data']), status, ''))
            conn.commit()
        except Exception as e:
            self.debugLogger.exception('{} - ERPNewMessage - Failed to create history record! - error: {} - event: {}'.format(event['id'], e, event))
            self.errorLogger.error('{} - ERPNewMessage - Failed to create history record! - error: {} - event: {}'.format(event['id'], e, event))
            raise Exception
        finally : conn.close()
        self.debugLogger.debug('{} - ERPNewMessage - Successful to create history record.'.format(event['id']))

        # close event
        self.debugLogger.debug('{} - ERPNewMessage - Closing event...'.format(event['id']))
        if self.closeEvent(event, 'OK') : self.debugLogger.debug('{} - ERPNewMessage - Successful to close event.'.format(event['id']))
        else:
            self.debugLogger.exception('{} - ERPNewMessage - Failed to close event! - event: {}'.format(event['id'], event))
            self.errorLogger.error('{} - ERPNewMessage - Failed to close event! - event: {}'.format(event['id'], event))
            raise Exception

    except Exception as e:
        self.debugLogger.error('{} - ERPNewMessage - Something went wrong! Putting order on hold... - error: {}'.format(event['id'], e))
        self.errorLogger.error('{} - ERPNewMessage - Something went wrong! Putting order on hold... - error: {}'.format(event['id'], e))
        onholdevent = {'id' : -1, 'cacheId' : event['cacheId'], 'type' : 'OrderOnHold', 'priority' : -1, 'time' : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'data' : {'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'source': 'ERPNewMessage', 'reason': 'An error occured while tying to execute ERPNewMessage event!', 'remoteId': ''}, 'endpoint_id' : event['endpoint_id']}
        self.OrderOnHold(onholdevent)
    else: self.debugLogger.debug('{} - ERPNewMessage Succesful.'.format(event['id']))
    finally:
        del self.workingThreads[str(event['id'])]
        self.ordersInProgress.remove((event['endpoint_id'], event['cacheId']))

def ERPNewCommand(self, event):
    self.debugLogger.debug('{} - ERPNewCommand parameters - event: {}'.format(event['id'], event))
    try:

        # idetify command and call required function
        self.debugLogger.debug('{} - ERPNewCommand - Trying to identify command...'.format(event['id']))
        if event['data']['command'].startswith('NO INVOICE', 4) : result, isSucceed_commandFunction = self.NoInvoice(event, event['data'])
        elif event['data']['command'].startswith('NO SHIPMENT', 4) : result, isSucceed_commandFunction = self.NoShipment(event, event['data'])
        elif event['data']['command'].startswith('MERGE', 4) : result, isSucceed_commandFunction = self.Merge(event, event['data'])
        elif event['data']['command'].startswith('HOLDFORMERGE', 4) : result, isSucceed_commandFunction = self.HoldForMerge(event, event['data'])
        else:
            self.debugLogger.error('{} - ERPNewCommand - Invalid Message! - event: {} - command: {}'.format(event['id'], event, event['data']))
            self.errorLogger.error('{} - ERPNewCommand - Invalid Message! - event: {} - command: {}'.format(event['id'], event, event['data']))
            raise Exception
        if not isSucceed_commandFunction:
            self.debugLogger.error('{} - ERPNewCommand - Command function failed! - event: {} - command: {}'.format(event['id'], event, event['data']))
            self.errorLogger.error('{} - ERPNewCommand - Command function failed! - event: {} - command: {}'.format(event['id'], event, event['data']))
            raise Exception
        self.debugLogger.debug('{} - ERPNewCommand - Command function successful.'.format(event['id']))

    except Exception as e:
        self.debugLogger.error('{} - ERPNewCommand - Something went wrong! Putting order on hold... - error: {}'.format(event['id'], e))
        self.errorLogger.error('{} - ERPNewCommand - Something went wrong! Putting order on hold... - error: {}'.format(event['id'], e))
        onholdevent = {'id' : -1, 'cacheId' : event['cacheId'], 'type' : 'OrderOnHold', 'priority' : -1, 'time' : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'data' : {'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'source': 'ERPNewCommand', 'reason': 'An error occured while tying to execute ERPNewCommand event!', 'remoteId': ''}, 'endpoint_id' : event['endpoint_id']}
        self.OrderOnHold(onholdevent)

        # close event
        self.debugLogger.debug('{} - ERPNewCommand - Closing event...'.format(event['id']))
        if self.closeEvent(event, 'ERROR: Something went wrong while executing ERPNewCommand function!') : self.debugLogger.debug('{} - ERPNewCommand - Successful to close event.'.format(event['id']))
        else:
            self.debugLogger.error('{} - ERPNewCommand - Failed to close event! - event: {}'.format(event['id'], event))
            self.errorLogger.error('{} - ERPNewCommand - Failed to close event! - event: {}'.format(event['id'], event))

        # post message
        self.debugLogger.debug('{} - ERPNewCommand - Posting message: "ERROR: Something went wrong while executing ERPNewCommand function!"...'.format(event['id']))
        isSucceed_postMessage = self.endpoints[str(event['endpoint_id'])].postMessage(event['cacheId'], 'WMS: ERROR: Something went wrong while executing ERPNewCommand function!')
        if isSucceed_postMessage : self.debugLogger.debug('{} - ERPNewCommand - Successful to post message.'.format(event['id']))
        else:
            self.debugLogger.error('{} - ERPNewCommand - Failed to post message!'.format(event['id']))
            self.errorLogger.error('{} - ERPNewCommand - Failed to post message!'.format(event['id']))

    else:
        # close event
        self.debugLogger.debug('{} - ERPNewCommand - Closing event...'.format(event['id']))
        if self.closeEvent(event, 'OK') : self.debugLogger.debug('{} - ERPNewCommand - Successful to close event.'.format(event['id']))
        else:
            self.debugLogger.error('{} - ERPNewCommand - Failed to close event! - event: {}'.format(event['id'], event))
            self.errorLogger.error('{} - ERPNewCommand - Failed to close event! - event: {}'.format(event['id'], event))

    finally:
        del self.workingThreads[str(event['id'])]
        self.ordersInProgress.remove((event['endpoint_id'], event['cacheId']))

def ERPOrderCanceled(self, event):
    self.debugLogger.debug('{} - ERPOrderCanceled parameters - event: {}'.format(event['id'], event))
    try:

        # retrieve order status
        self.debugLogger.debug('{} - ERPOrderCanceled - Retrieving order status...'.format(event['id']))
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            cur.execute('SELECT status, remoteId FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
            row = cur.fetchone()
            status = row[0]
            eventRemoteId = row[1]
        except Exception as e:
            self.debugLogger.exception('{} - ERPOrderCanceled - Failed to retrieve order status! - error: {} - event: {}'.format(event['id'], e, event))
            self.errorLogger.error('{} - ERPOrderCanceled - Failed to retrieve order status! - error: {} - event: {}'.format(event['id'], e, event))
            raise Exception
        finally : conn.close()
        self.debugLogger.debug('{} - ERPOrderCanceled - Successful to retrieve order status. - status: {}'.format(event['id'], status))

        # execute cancelation
        if status == 'WAITING FOR SIZING' or status == 'WAITING FOR PICKING' or status == 'PICKING IN PROGRESS' or status == 'WAITING FOR PACKING' or status.startswith('ON HOLD')  or status == 'MERGED':

            #region OPERATIONS FOR MERGED ORDERS
            if status == 'MERGED':
                self.debugLogger.debug('{} - ERPOrderCanceled - It is a child order. Detaching from parent order...'.format(event['id']))

                # - retrieve parent order id -
                # retrieve order commands
                self.debugLogger.debug('{} - ERPOrderCanceled - Retrieving order commands...'.format(event['id']))
                try:
                    conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                    cur = conn.cursor()
                    cur.execute('SELECT commands, remoteId FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
                    row = cur.fetchone()
                    commands = row[0]
                    childRemoteId = row[1]
                except Exception as e:
                    self.debugLogger.exception('{} - ERPOrderCanceled - Failed to retrieve order commands! - error: {} - event: {}'.format(event['id'], e, event))
                    self.errorLogger.error('{} - ERPOrderCanceled - Failed to retrieve order commands! - error: {} - event: {}'.format(event['id'], e, event))
                    raise Exception
                finally : conn.close()
                self.debugLogger.debug('{} - ERPOrderCanceled - Successful to retrieve order commands. - commands: {} - childRemoteId: {}'.format(event['id'], commands, childRemoteId))

                # extract parent order id
                self.debugLogger.debug('{} - ERPOrderCanceled - Extracting parent id...'.format(event['id']))
                try:
                    commands = commands.split('.')
                    parentRemoteId = str()
                    for command in commands:
                        if command.startswith('PARENT '):
                            parentRemoteId = int(command.split(' ')[1])
                except Exception as e:
                    self.debugLogger.exception('{} - ERPOrderCanceled - Failed to extract parent id! - error: {} - event: {}'.format(event['id'], e, event))
                    self.errorLogger.error('{} - ERPOrderCanceled - Failed to extract parent id! - error: {} - event: {}'.format(event['id'], e, event))
                    raise Exception
                finally : conn.close()
                self.debugLogger.debug('{} - ERPOrderCanceled - Successful to extract parent id. - parentRemoteId: {}'.format(event['id'], parentRemoteId))

                # retrieve parent order cacheId
                self.debugLogger.debug('{} - ERPOrderCanceled - Retrieving parent order cacheId...'.format(event['id']))
                try:
                    conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                    cur = conn.cursor()
                    cur.execute('SELECT cacheId FROM dataflow_order WHERE endpoint_id = %s AND remoteId = %s', (event['endpoint_id'], parentRemoteId))
                    parentCacheId = cur.fetchone()[0]
                except Exception as e:
                    self.debugLogger.exception('{} - ERPOrderCanceled - Failed to retrieve parent order cacheId! - error: {} - event: {}'.format(event['id'], e, event))
                    self.errorLogger.error('{} - ERPOrderCanceled - Failed to retrieve parent order cacheId! - error: {} - event: {}'.format(event['id'], e, event))
                    raise Exception
                finally : conn.close()
                self.debugLogger.debug('{} - ERPOrderCanceled - Successful to retrieve parent order cacheId. - parentCacheId: {}'.format(event['id'], parentCacheId))

                try:
                    # block the parent order
                    self.debugLogger.debug('{} - ERPOrderCanceled - Internal block for parent order...'.format(event['id']))
                    try:
                        self.requestForInternalBlock.append((event['endpoint_id'], parentCacheId, event))
                        start = time.perf_counter()
                        while (event['endpoint_id'], parentCacheId, event) not in self.internalBlock : continue
                    except Exception as e:
                        self.debugLogger.exception('{} - ERPOrderCanceled - Failed: Internal block for parent order! - error: {} - event: {}'.format(event['id'], e, event))
                        self.errorLogger.error('{} - ERPOrderCanceled - Failed: Internal block for parent order! - error: {} - event: {}'.format(event['id'], e, event))
                        raise Exception
                    self.debugLogger.debug('{} - ERPOrderCanceled - Successful: Internal block for parent order. - Completed in {} second'.format(event['id'], time.perf_counter() - start))

                    # retrieve parent order status
                    self.debugLogger.debug('{} - ERPOrderCanceled - Retrieving parent order status...'.format(event['id']))
                    try:
                        conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                        cur = conn.cursor()
                        cur.execute('SELECT status FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], parentCacheId))
                        parentStatus = cur.fetchone()[0]
                    except Exception as e:
                        self.debugLogger.exception('{} - ERPOrderCanceled - Failed to retrieve parent order status! - error: {} - event: {}'.format(event['id'], e, event))
                        self.errorLogger.error('{} - ERPOrderCanceled - Failed to retrieve parent order status! - error: {} - event: {}'.format(event['id'], e, event))
                        raise Exception
                    finally : conn.close()
                    self.debugLogger.debug('{} - ERPOrderCanceled - Successful to retrieve parent order status. - parentStatus: {}'.format(event['id'], parentStatus))

                    # remove child order
                    if parentStatus == 'WAITING FOR SIZING' or parentStatus == 'WAITING FOR PICKING' or parentStatus == 'PICKING IN PROGRESS' or parentStatus == 'WAITING FOR PACKING' or parentStatus.startswith('ON HOLD'):

                        # remove child order
                        self.debugLogger.debug('{} - ERPOrderCanceled - Remove child order...'.format(event['id']))
                        try:
                            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                            cur = conn.cursor()
                            cur.execute('SELECT commands FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], parentCacheId))
                            parentCommands = cur.fetchone()[0]
                            parentCommands = parentCommands.split('.')
                            parentCommands.remove('CHILD {}'.format(childRemoteId))
                            parentCommandsStr = str()
                            for command in parentCommands : parentCommandsStr += '.{}'.format(command)
                            cur.execute('UPDATE dataflow_order SET commands = %s WHERE endpoint_id = %s AND cacheId = %s', (parentCommandsStr, event['endpoint_id'], parentCacheId))
                            cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], parentCacheId, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Child Detached: {}'.format(event['cacheId']), parentStatus))
                            cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Detached from parent: {}'.format(parentCacheId), parentStatus, ''))
                            conn.commit()
                        except Exception as e:
                            self.debugLogger.exception('{} - ERPOrderCanceled - Failed to remove child order! - error: {} - event: {}'.format(event['id'], e, event))
                            self.errorLogger.error('{} - ERPOrderCanceled - Failed to remove child order! - error: {} - event: {}'.format(event['id'], e, event))
                            raise Exception
                        finally : conn.close()
                        self.debugLogger.debug('{} - ERPOrderCanceled - Successful to remove child order.'.format(event['id']))

                        # post message
                        self.debugLogger.debug('{} - ERPOrderCanceled - Posting message: "Child Detached"...'.format(event['id']))
                        isSucceed_postMessage = self.endpoints[str(event['endpoint_id'])].postMessage(parentCacheId, 'WMS: Child Detached: {}'.format(childRemoteId))
                        isSucceed_postMessage = self.endpoints[str(event['endpoint_id'])].postMessage(event['cacheId'], 'WMS: Detached from: {}'.format(parentRemoteId))
                        if isSucceed_postMessage : self.debugLogger.debug('{} - ERPOrderCanceled - Successful to post message.'.format(event['id']))
                        else:
                            self.debugLogger.error('{} - ERPOrderCanceled - Failed to post message!'.format(event['id']))
                            self.errorLogger.error('{} - ERPOrderCanceled - Failed to post message!'.format(event['id']))

                    else:
                        self.debugLogger.error('{} - ERPOrderCanceled - Invalid parent order status! - status: {} - event: {}'.format(event['id'], status, event))
                        self.errorLogger.error('{} - ERPOrderCanceled - Invalid parent order status! - status: {} - event: {}'.format(event['id'], status, event))
                        raise Exception
                except : raise Exception
                finally:
                    self.requestForInternalBlock.remove((event['endpoint_id'], parentCacheId, event))
                    self.internalBlock.remove((event['endpoint_id'], parentCacheId, event))

            else:
                self.debugLogger.debug('{} - ERPOrderCanceled - Checking for child orders...'.format(event['id']))

                # retrieve order commands
                self.debugLogger.debug('{} - ERPOrderCanceled - Retrieving order commands...'.format(event['id']))
                try:
                    conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                    cur = conn.cursor()
                    cur.execute('SELECT commands, remoteId FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
                    row = cur.fetchone()
                    commands = row[0]
                    remoteId = row[1]
                except Exception as e:
                    self.debugLogger.exception('{} - ERPOrderCanceled - Failed to retrieve order commands! - error: {} - event: {}'.format(event['id'], e, event))
                    self.errorLogger.error('{} - ERPOrderCanceled - Failed to retrieve order commands! - error: {} - event: {}'.format(event['id'], e, event))
                    raise Exception
                finally : conn.close()
                self.debugLogger.debug('{} - ERPOrderCanceled - Successful to retrieve order commands. - commands: {} - remoteId: {}'.format(event['id'], commands, remoteId))

                # extract childs
                self.debugLogger.debug('{} - ERPOrderCanceled - Extract child commands...'.format(event['id']))
                try:
                    childOrderCommands = list()
                    commands = commands.split('.')
                    for command in commands:
                        if command.startswith('CHILD ') : childOrderCommands.append(command)
                except Exception as e:
                    self.debugLogger.exception('{} - ERPOrderCanceled - Failed to extract child commands! - error: {} - event: {}'.format(event['id'], e, event))
                    self.errorLogger.error('{} - ERPOrderCanceled - Failed to extract child commands! - error: {} - event: {}'.format(event['id'], e, event))
                    raise Exception
                self.debugLogger.debug('{} - ERPOrderCanceled - Successful to extract child commands. - childOrderCommands: {}'.format(event['id'], childOrderCommands))

                # seperate orders
                if len(childOrderCommands) > 0:
                    self.debugLogger.debug('{} - ERPOrderCanceled - Seperating child orders...'.format(event['id']))
                    try:

                        for childOrderCommand in childOrderCommands:

                            # separating child order
                            self.debugLogger.debug('{} - ERPOrderCanceled - Separating child order...'.format(event['id']))
                            try:
                                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                                cur = conn.cursor()
                                cur.execute('SELECT cacheId, commands FROM dataflow_order WHERE endpoint_id = %s AND remoteId = %s', (event['endpoint_id'], childOrderCommand.split(' ')[1]))
                                row = cur.fetchone()
                                childCahceId = row[0]
                                childCommands = row[1]
                                childCommands = childCommands.split('.')
                                self.debugLogger.debug('{} - ERPOrderCanceled - childCommands: {}, childCahceId'.format(event['id'], childCommands, childCahceId))
                                childCommands.remove('PARENT {}'.format(remoteId))
                                childCommandsStr = str()
                                cur.execute('SELECT status FROM dataflow_history WHERE endpoint_id = %s AND cacheId = %s AND status != %s ORDER BY time DESC LIMIT 1', (event['endpoint_id'], childCahceId, 'MERGED'))
                                childLastStatus = cur.fetchone()[0]
                                for command in childCommands : childCommandsStr += '.{}'.format(command)
                                cur.execute('UPDATE dataflow_order SET commands = %s, status = %s WHERE endpoint_id = %s AND cacheId = %s', (childCommandsStr, childLastStatus, event['endpoint_id'], childCahceId))
                                cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Child Detached: {}'.format(childCahceId), status, ''))
                                cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], childCahceId, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Detached from: {}'.format(event['cacheId']), childLastStatus, ''))
                                conn.commit()
                            except Exception as e:
                                self.debugLogger.exception('{} - ERPOrderCanceled - Failed separate child order! - error: {}'.format(event['id'], e))
                                self.errorLogger.error('{} - ERPOrderCanceled - Failed separate child order! - error: {}'.format(event['id'], e))
                                raise Exception
                            finally : conn.close()
                            self.debugLogger.debug('{} - ERPOrderCanceled - Successful to separate child order. - childLastStatus: {}'.format(event['id'], childLastStatus))

                            # post message
                            self.debugLogger.debug('{} - ERPOrderCanceled - Posting message: "Child Detached"...'.format(event['id']))
                            isSucceed_postMessage = self.endpoints[str(event['endpoint_id'])].postMessage(event['cacheId'], 'WMS: Child Detached: {}'.format(childOrderCommand.split(' ')[1]))
                            isSucceed_postMessage = self.endpoints[str(event['endpoint_id'])].postMessage(childCahceId, 'WMS: Detached from: {}'.format(remoteId))
                            if isSucceed_postMessage : self.debugLogger.debug('{} - ERPOrderCanceled - Successful to post message.'.format(event['id']))
                            else:
                                self.debugLogger.error('{} - ERPOrderCanceled - Failed to post message!'.format(event['id']))
                                self.errorLogger.error('{} - ERPOrderCanceled - Failed to post message!'.format(event['id']))

                    except Exception as e:
                        self.debugLogger.exception('{} - ERPOrderCanceled - Failed to seperate child orders! - error: {} - event: {}'.format(event['id'], e, event))
                        self.errorLogger.error('{} - ERPOrderCanceled - Failed to seperate child orders! - error: {} - event: {}'.format(event['id'], e, event))
                        raise Exception

            self.debugLogger.debug('{} - ERPOrderCanceled - Operations for merged orders successful.'.format(event['id']))
            #endregion

            # BLOCK EVENT SOURCES
            # delete from endpoint
            self.debugLogger.debug('{} - ERPOrderCanceled - Calling endpoint function deleteOrder...'.format(event['id']))
            isSucceed_deleteOrder = self.endpoints[str(event['endpoint_id'])].deleteOrder(event['cacheId'])
            if not isSucceed_deleteOrder:
                self.debugLogger.error('{} - ERPOrderCanceled - deleteOrder failed! - event: {}'.format(event['id'], event))
                self.errorLogger.error('{} - ERPOrderCanceled - deleteOrder failed! - event: {}'.format(event['id'], event))
                raise Exception
            self.debugLogger.debug('{} - ERPOrderCanceled - deleteOrder function successful'.format(event['id']))

            # status --> canceled and add history record
            self.debugLogger.debug('{} - ERPOrderCanceled - Setting order status to canceled...'.format(event['id']))
            try:
                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                cur = conn.cursor()
                cur.execute('UPDATE dataflow_order SET status = %s WHERE endpoint_id = %s AND cacheId = %s', ('CANCELED', event['endpoint_id'], event['cacheId']))
                cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ORDER CANCELED', 'CANCELED', ''))
                conn.commit()
            except Exception as e:
                self.debugLogger.exception('{} - ERPOrderCanceled - Failed to set order status to canceled! - error: {} - event: {}'.format(event['id'], e, event))
                self.errorLogger.error('{} - ERPOrderCanceled - Failed to set order status to canceled! - error: {} - event: {}'.format(event['id'], e, event))
                raise Exception
            finally : conn.close()
            self.debugLogger.debug('{} - ERPOrderCanceled - Successful to set order status to canceled.'.format(event['id']))

            # wait for possible events on the road
            time.sleep(1)

            # clear rest
            # delete invoices
            self.debugLogger.debug('{} - ERPOrderCanceled - Calling endpoint function deleteInvoices...'.format(event['id']))
            isSucceed_deleteInvoices = self.endpoints[str(event['endpoint_id'])].deleteInvoices(event['cacheId'], eventRemoteId)
            if not isSucceed_deleteInvoices:
                self.debugLogger.error('{} - ERPOrderCanceled - deleteInvoices failed! - event: {}'.format(event['id'], event))
                self.errorLogger.error('{} - ERPOrderCanceled - deleteInvoices failed! - event: {}'.format(event['id'], event))
                raise Exception
            self.debugLogger.debug('{} - ERPOrderCanceled - deleteInvoices function successful'.format(event['id']))

            # event results --> error
            self.debugLogger.debug('{} - ERPOrderCanceled - Canceling open events...'.format(event['id']))
            try:
                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                cur = conn.cursor()
                cur.execute('UPDATE dataflow_event SET result = %s WHERE endpoint_id = %s AND cacheId = %s AND id != %s and result = %s', ('ERROR: Order Canceled', event['endpoint_id'], event['cacheId'], event['id'], ''))
                conn.commit()
            except Exception as e:
                self.debugLogger.exception('{} - ERPOrderCanceled - Failed to cancel open events! - error: {} - event: {}'.format(event['id'], e, event))
                self.errorLogger.error('{} - ERPOrderCanceled - Failed to cancel open events! - error: {} - event: {}'.format(event['id'], e, event))
                raise Exception
            finally: conn.close()
            self.debugLogger.debug('{} - ERPOrderCanceled - Successful to cancel open events.'.format(event['id']))

            # close event
            self.debugLogger.debug('{} - ERPOrderCanceled - Closing event...'.format(event['id']))
            if self.closeEvent(event, 'OK') : self.debugLogger.debug('{} - ERPOrderCanceled - Successful to close event.'.format(event['id']))
            else:
                self.debugLogger.exception('{} - ERPOrderCanceled - Failed to close event! - event: {}'.format(event['id'], event))
                self.errorLogger.error('{} - ERPOrderCanceled - Failed to close event! - event: {}'.format(event['id'], event))
                raise Exception

        elif status == 'CANCELED' or status == 'SHIPPED' or status == 'MARKED':
            self.debugLogger.error('{} - ERPOrderCanceled - Can not cancel closed order! - status: {}'.format(event['id'], status))
            self.errorLogger.error('{} - ERPOrderCanceled - Can not cancel closed order! - status: {}'.format(event['id'], status))

            # close event
            self.debugLogger.debug('{} - ERPOrderCanceled - Closing event...'.format(event['id']))
            if self.closeEvent(event, 'ERROR: Can not cancel closed order! - status: {}'.format(status)) : self.debugLogger.debug('ERPOrderCanceled - Successful to close event.'.format(event['id']))
            else:
                self.debugLogger.exception('{} - ERPOrderCanceled - Failed to close event! - event: {}'.format(event['id'], event))
                self.errorLogger.error('{} - ERPOrderCanceled - Failed to close event! - event: {}'.format(event['id'], event))
                raise Exception

        else:
            self.debugLogger.error('{} - ERPOrderCanceled - Invalid order status! - status: {} - event: {}'.format(event['id'], status, event))
            self.errorLogger.error('{} - ERPOrderCanceled - Invalid order status! - status: {} - event: {}'.format(event['id'], status, event))
            raise Exception

    except:
        self.debugLogger.error('{} - ERPOrderCanceled - Something went wrong! Putting order on hold...'.format(event['id']))
        self.errorLogger.error('{} - ERPOrderCanceled - Something went wrong! Putting order on hold...'.format(event['id']))
        onholdevent = {'id' : -1, 'cacheId' : event['cacheId'], 'type' : 'OrderOnHold', 'priority' : -1, 'time' : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'data' : {'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'source': 'ERPOrderCanceled', 'reason': 'An error occured while tying to execute ERPOrderCancel event!', 'remoteId': ''}, 'endpoint_id' : event['endpoint_id']}
        self.OrderOnHold(onholdevent)
    else : self.debugLogger.debug('{} - ERPOrderCanceled successful. - event: {}'.format(event['id'], event))
    finally:
        del self.workingThreads[str(event['id'])]
        self.ordersInProgress.remove((event['endpoint_id'], event['cacheId']))

def ERPOrderUpdated(self, event):
    self.debugLogger.debug('{} - ERPOrderUpdated parameters - event: {}'.format(event['id'], event))

    try:
        # retrieve order information
        self.debugLogger.debug('{} - ERPOrderUpdated - Retrieving order informations...'.format(event['id']))
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            cur.execute('SELECT remoteId FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
            remoteId = cur.fetchone()[0]
        except Exception as e:
            self.debugLogger.exception('{} - ERPOrderUpdated - Failed to retrieve order informations! - error: {} - event: {}'.format(event['id'], e, event))
            self.errorLogger.error('{} - ERPOrderUpdated - Failed to retrieve order informations! - error: {} - event: {}'.format(event['id'], e, event))
            raise Exception
        else:
            self.debugLogger.debug('{} - ERPOrderUpdated - Successful to retrieve order informations. - remoteId: {}'.format(event['id'], remoteId))
        finally : conn.close()

        if event['data']['event'] == 'ORDER MARKED':

            isWMSMarkedIt = False

            self.debugLogger.debug('{} - ERPOrderUpdated - Who marked the order?'.format(event['id']))

            # check order history
            self.debugLogger.debug('{} - ERPOrderUpdated - Checking order history...'.format(event['id']))
            try:
                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                cur = conn.cursor()
                cur.execute('SELECT COUNT(id) FROM dataflow_history WHERE endpoint_id = %s AND cacheId = %s AND event = %s', (event['endpoint_id'], event['cacheId'], 'Order marked by WMS.'))
                if cur.fetchone()[0] > 0: isWMSMarkedIt = True
            except Exception as e:
                self.debugLogger.exception('{} - ERPOrderUpdated - Failed to check order history! - error: {} - event: {}'.format(event['id'], e, event))
                self.errorLogger.error('{} - ERPOrderUpdated - Failed to check order history! - error: {} - event: {}'.format(event['id'], e, event))
                raise Exception
            else:
                self.debugLogger.debug('{} - ERPOrderUpdated - Successful to check order history. - isWMSMarkedIt: {}'.format(event['id'], isWMSMarkedIt))
            finally : conn.close()

            if isWMSMarkedIt:
                self.debugLogger.debug('{} - ERPOrderUpdated - WMS marked the order.'.format(event['id']))
                # close event
                self.debugLogger.debug('{} - ERPOrderUpdated - Closing event...'.format(event['id']))
                if self.closeEvent(event, 'OK') : self.debugLogger.debug('{} - ERPOrderUpdated - Successful to close event.'.format(event['id']))
                else:
                    self.debugLogger.exception('{} - ERPOrderUpdated - Failed to close event! - event: {}'.format(event['id'], event))
                    self.errorLogger.error('{} - ERPOrderUpdated - Failed to close event! - event: {}'.format(event['id'], event))
                    raise Exception

            else:
                self.debugLogger.debug('{} - ERPOrderUpdated - Order marked by another source!'.format(event['id']))
                # BLOCK EVENT SOURCES
                # delete from endpoint
                self.debugLogger.debug('{} - ERPOrderUpdated - Calling endpoint function deleteOrder...'.format(event['id']))
                isSucceed_deleteOrder = self.endpoints[str(event['endpoint_id'])].deleteOrder(event['cacheId'])
                if not isSucceed_deleteOrder:
                    self.debugLogger.error('{} - ERPOrderUpdated - deleteOrder failed! - event: {}'.format(event['id'], event))
                    self.errorLogger.error('{} - ERPOrderUpdated - deleteOrder failed! - event: {}'.format(event['id'], event))
                    raise Exception
                self.debugLogger.debug('{} - ERPOrderUpdated - deleteOrder function successful'.format(event['id']))

                # status --> shipped and add history record
                self.debugLogger.debug('{} - ERPOrderUpdated - Order shipped by another source! Closing order...'.format(event['id']))
                try:
                    conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                    cur = conn.cursor()
                    cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Order shipped by another source!', 'SHIPPED', ''))
                    cur.execute('UPDATE dataflow_order SET status = %s WHERE endpoint_id = %s AND cacheId = %s', ('SHIPPED', event['endpoint_id'], event['cacheId']))
                    conn.commit()
                except Exception as e:
                    self.debugLogger.exception('{} - ERPOrderUpdated - Failed to close order! - error: {} - event: {}'.format(event['id'], e, event))
                    self.errorLogger.error('{} - ERPOrderUpdated - Failed to close order! - error: {} - event: {}'.format(event['id'], e, event))
                    raise Exception
                finally: conn.close()
                self.debugLogger.debug('{} - ERPOrderUpdated - Successful to close order.'.format(event['id']))

                # wait for possible events on the road
                time.sleep(1)

                # CLEAR REST
                # delete invoices
                self.debugLogger.debug('{} - ERPOrderUpdated - Calling endpoint function deleteInvoices...'.format(event['id']))
                isSucceed_deleteInvoices = self.endpoints[str(event['endpoint_id'])].deleteInvoices(event['cacheId'], remoteId)
                if not isSucceed_deleteInvoices:
                    self.debugLogger.error('{} - ERPOrderUpdated - deleteInvoices failed! - event: {}'.format(event['id'], event))
                    self.errorLogger.error('{} - ERPOrderUpdated - deleteInvoices failed! - event: {}'.format(event['id'], event))
                    raise Exception
                self.debugLogger.debug('{} - ERPOrderUpdated - deleteInvoices function successful'.format(event['id']))

                # event results --> error
                self.debugLogger.debug('{} - ERPOrderUpdated - Canceling open events...'.format(event['id']))
                try:
                    conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                    cur = conn.cursor()
                    cur.execute('UPDATE dataflow_event SET result = %s WHERE endpoint_id = %s AND cacheId = %s AND id != %s and result = %s', ('ERROR: Order Canceled', event['endpoint_id'], event['cacheId'], event['id'], ''))
                    conn.commit()
                except Exception as e:
                    self.debugLogger.exception('{} - ERPOrderUpdated - Failed to cancel open events! - error: {} - event: {}'.format(event['id'], e, event))
                    self.errorLogger.error('{} - ERPOrderUpdated - Failed to cancel open events! - error: {} - event: {}'.format(event['id'], e, event))
                    raise Exception
                finally: conn.close()

                # close order
                self.debugLogger.debug('{} - ERPOrderUpdated - Order marked by another source! Closing order...'.format(event['id']))
                try:
                    conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                    cur = conn.cursor()
                    cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Order marked by another source!', 'MARKED', ''))
                    cur.execute('UPDATE dataflow_order SET status = %s WHERE endpoint_id = %s AND cacheId = %s', ('MARKED', event['endpoint_id'], event['cacheId']))
                    conn.commit()
                except Exception as e:
                    self.debugLogger.exception('{} - ERPOrderUpdated - Failed to close order! - error: {} - event: {}'.format(event['id'], e, event))
                    self.errorLogger.error('{} - ERPOrderUpdated - Failed to close order! - error: {} - event: {}'.format(event['id'], e, event))
                    raise Exception
                finally: conn.close()
                self.debugLogger.debug('{} - ERPOrderUpdated - Successful to close order.'.format(event['id']))

                # close event
                self.debugLogger.debug('{} - ERPOrderUpdated - Closing event...'.format(event['id']))
                if self.closeEvent(event, 'OK') : self.debugLogger.debug('{} - ERPOrderUpdated - Successful to close event.'.format(event['id']))
                else:
                    self.debugLogger.exception('{} - ERPOrderUpdated - Failed to close event! - event: {}'.format(event['id'], event))
                    self.errorLogger.error('{} - ERPOrderUpdated - Failed to close event! - event: {}'.format(event['id'], event))
                    raise Exception

        elif event['data']['event'] == 'ORDER SHIPPED':

            # BLOCK EVENT SOURCES
            # delete from endpoint
            self.debugLogger.debug('{} - ERPOrderUpdated - Calling endpoint function deleteOrder...'.format(event['id']))
            isSucceed_deleteOrder = self.endpoints[str(event['endpoint_id'])].deleteOrder(event['cacheId'])
            if not isSucceed_deleteOrder:
                self.debugLogger.error('{} - ERPOrderUpdated - deleteOrder failed! - event: {}'.format(event['id'], event))
                self.errorLogger.error('{} - ERPOrderUpdated - deleteOrder failed! - event: {}'.format(event['id'], event))
                raise Exception
            self.debugLogger.debug('{} - ERPOrderUpdated - deleteOrder function successful'.format(event['id']))

            # status --> shipped and add history record
            self.debugLogger.debug('{} - ERPOrderUpdated - Order shipped by another source! Closing order...'.format(event['id']))
            try:
                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                cur = conn.cursor()
                cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Order shipped by another source!', 'SHIPPED', ''))
                cur.execute('UPDATE dataflow_order SET status = %s WHERE endpoint_id = %s AND cacheId = %s', ('SHIPPED', event['endpoint_id'], event['cacheId']))
                conn.commit()
            except Exception as e:
                self.debugLogger.exception('{} - ERPOrderUpdated - Failed to close order! - error: {} - event: {}'.format(event['id'], e, event))
                self.errorLogger.error('{} - ERPOrderUpdated - Failed to close order! - error: {} - event: {}'.format(event['id'], e, event))
                raise Exception
            finally: conn.close()
            self.debugLogger.debug('{} - ERPOrderUpdated - Successful to close order.'.format(event['id']))

            # wait for possible events on the road
            time.sleep(1)

            # CLEAR REST
            # delete invoices
            self.debugLogger.debug('{} - ERPOrderUpdated - Calling endpoint function deleteInvoices...'.format(event['id']))
            isSucceed_deleteInvoices = self.endpoints[str(event['endpoint_id'])].deleteInvoices(event['cacheId'], remoteId)
            if not isSucceed_deleteInvoices:
                self.debugLogger.error('{} - ERPOrderUpdated - deleteInvoices failed! - event: {}'.format(event['id'], event))
                self.errorLogger.error('{} - ERPOrderUpdated - deleteInvoices failed! - event: {}'.format(event['id'], event))
                raise Exception
            self.debugLogger.debug('{} - ERPOrderUpdated - deleteInvoices function successful'.format(event['id']))

            # event results --> error
            self.debugLogger.debug('{} - ERPOrderUpdated - Canceling open events...'.format(event['id']))
            try:
                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                cur = conn.cursor()
                cur.execute('UPDATE dataflow_event SET result = %s WHERE endpoint_id = %s AND cacheId = %s AND id != %s and result = %s', ('ERROR: Order Canceled', event['endpoint_id'], event['cacheId'], event['id'], ''))
                conn.commit()
            except Exception as e:
                self.debugLogger.exception('{} - ERPOrderUpdated - Failed to cancel open events! - error: {} - event: {}'.format(event['id'], e, event))
                self.errorLogger.error('{} - ERPOrderUpdated - Failed to cancel open events! - error: {} - event: {}'.format(event['id'], e, event))
                raise Exception
            finally: conn.close()
            self.debugLogger.debug('{} - ERPOrderUpdated - Successful to cancel open events.'.format(event['id']))

            # close event
            self.debugLogger.debug('{} - ERPOrderUpdated - Closing event...'.format(event['id']))
            if self.closeEvent(event, 'OK') : self.debugLogger.debug('ERPOrderUpdated - Successful to close event.'.format(event['id']))
            else:
                self.debugLogger.exception('{} - ERPOrderUpdated - Failed to close event! - event: {}'.format(event['id'], event))
                self.errorLogger.error('{} - ERPOrderUpdated - Failed to close event! - event: {}'.format(event['id'], event))
                raise Exception

        else:
            self.debugLogger.error('{} - ERPOrderUpdated - Invalid event data! - event: {}'.format(event['id'], event))
            self.errorLogger.error('{} - ERPOrderUpdated - Invalid event data! - event: {}'.format(event['id'], event))
            raise Exception

    except Exception as e:
        self.debugLogger.error('{} - ERPOrderUpdated - Something went wrong! Putting order on hold... - error: {}'.format(event['id'], e))
        self.errorLogger.error('{} - ERPOrderUpdated - Something went wrong! Putting order on hold... - error: {}'.format(event['id'], e))
        onholdevent = {'id' : -1, 'cacheId' : event['cacheId'], 'type' : 'OrderOnHold', 'priority' : -1, 'time' : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'data' : {'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'source': 'ERPNewMessage', 'reason': 'An error occured while tying to execute ERPNewMessage event!', 'remoteId': ''}, 'endpoint_id' : event['endpoint_id']}
        self.OrderOnHold(onholdevent)
    finally:
        del self.workingThreads[str(event['id'])]
        self.ordersInProgress.remove((event['endpoint_id'], event['cacheId']))

def OrderContinue(self, event):
    self.debugLogger.debug('{} - OrderContinue parameters - event: {}'.format(event['id'], event))
    try:

        # retrieve last status
        self.debugLogger.debug('{} - OrderContinue - Retrieving last status...'.format(event['id']))
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            if event['cacheId'] == -1 : cur.execute('SELECT status FROM dataflow_history WHERE endpoint_id = %s AND remoteId = %s AND status != %s AND status!= %s ORDER BY time ASC LIMIT 1', (event['endpoint_id'], event['data']['remoteId'], 'ON HOLD', 'ON HOLD FOR MERGE'))
            else : cur.execute('SELECT status FROM dataflow_history WHERE endpoint_id = %s AND cacheId = %s AND status != %s AND status!= %s ORDER BY time ASC LIMIT 1', (event['endpoint_id'], event['cacheId'], 'ON HOLD', 'ON HOLD FOR MERGE'))
            lastStatus = cur.fetchone()
        except Exception as e:
            self.debugLogger.exception('{} - OrderContinue - Failed retrieve last status! - error: {}'.format(event['id'], e))
            self.errorLogger.error('{} - OrderContinue - Failed retrieve last status! - error: {}'.format(event['id'], e))
            raise Exception
        finally : conn.close()
        self.debugLogger.debug('{} - OrderContinue - Successful to retrieve last status. - lastStatus: {}'.format(event['id'], lastStatus))

        # if order record was not created before hold, delete order and history
        if lastStatus == None:
            self.debugLogger.debug('{} - OrderContinue - It is a dummy record for hold. Deleting order and history for continue...'.format(event['id']))
            try:
                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                cur = conn.cursor()
                cur.execute('DELETE FROM dataflow_order WHERE endpoint_id = %s AND remoteId = %s', (event['endpoint_id'], event['data']['remoteId']))
                cur.execute('DELETE FROM dataflow_history WHERE endpoint_id = %s AND remoteId = %s', (event['endpoint_id'], event['data']['remoteId']))
                conn.commit()
            except Exception as e:
                self.debugLogger.exception('{} - OrderContinue - Failed to delete dummy order and history! - error: {} - event: {}'.format(event['id'], e, event))
                self.errorLogger.error('{} - OrderContinue - Failed to delete dummy order and history! - error: {} - event: {}'.format(event['id'], e, event))
                raise Exception
            finally : conn.close()
            self.debugLogger.debug('{} - OrderContinue - Successful to delete dummy order and history!'.format(event['id']))

        # if order record was created before hold, update order status and create new history record
        else:
            self.debugLogger.debug('{} - OrderContinue - Updating order status...'.format(event['id']))
            try:
                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                cur = conn.cursor()
                cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Order Continue', lastStatus[0], ''))
                cur.execute('UPDATE dataflow_order SET status = %s WHERE endpoint_id = %s AND cacheId = %s', (lastStatus[0], event['endpoint_id'], event['cacheId']))
                conn.commit()
            except Exception as e:
                self.debugLogger.exception('{} - OrderOnHold - Failed to update order status! - error: {} - event: {}'.format(event['id'], e, event))
                self.errorLogger.error('{} - OrderOnHold - Failed to update order status! - error: {} - event: {}'.format(event['id'], e, event))
                raise Exception
            finally:
                conn.close()
            self.debugLogger.debug('{} - OrderContinue - Successful to update order status.'.format(event['id']))

        # post message
        if event['cacheId'] != -1:
            self.debugLogger.debug('{} - ERPNewOrder - Posting message: "Order Continue"...'.format(event['id']))
            if self.endpoints[str(event['endpoint_id'])].postMessage(event['cacheId'], 'WMS: Order Continue') : self.debugLogger.debug('ERPNewOrder - Successful to post message.'.format(event['id']))
            else:
                self.debugLogger.error('{} - ERPNewOrder - Failed to post message!'.format(event['id']))
                self.errorLogger.error('{} - ERPNewOrder - Failed to post message!'.format(event['id']))

    except:
        # close event
        self.debugLogger.debug('{} - OrderContinue - Closing event...')
        if self.closeEvent(event, 'ERROR: Something went wrong!') : self.debugLogger.debug('{} - OrderContinue - Successful to close event.'.format(event['id']))
        else:
            self.debugLogger.exception('{} - OrderContinue - Failed to close event! - event: {}'.format(event['id'], event))
            self.errorLogger.error('{} - OrderContinue - Failed to close event! - event: {}'.format(event['id'], event))
        self.debugLogger.error('{} - OrderContinue Failed! - event: {}'.format(event['id'], event))
        self.errorLogger.error('{} - OrderContinue Failed! - event: {}'.format(event['id'], event))

    else:
        # close event
        self.debugLogger.debug('{} - OrderContinue - Closing event...'.format(event['id']))
        if self.closeEvent(event, 'OK') : self.debugLogger.debug('OrderContinue - Successful to close event.'.format(event['id']))
        else:
            self.debugLogger.exception('{} - OrderContinue - Failed to close event! - event: {}'.format(event['id'], event))
            self.errorLogger.error('{} - OrderContinue - Failed to close event! - event: {}'.format(event['id'], event))
        self.debugLogger.debug('{} - OrderContinue Successful. - event: {}'.format(event['id'], event))

    finally:
        del self.workingThreads[str(event['id'])]
        self.ordersInProgress.remove((event['endpoint_id'], event['cacheId']))

# =================== LATER =================== #

def PickingRequestForAssignment(self, event):
    pass

def PickingPicked(self, event):
    pass

def PackingRequestForAssignment(self, event):
    pass

def PackingShipped(self, event):
    pass

def ManagementSizing(self, event):
    self.debugLogger.debug('{} - ManagementSizing parameters - event: {}'.format(event['id'], event))
    try:
        # mark order
        self.debugLogger.debug('{} - ManagementSizing - Marking order...'.format(event['id']))
        isSucceed_markOrder = self.endpoints[str(event['endpoint_id'])].markOrder(event['cacheId'], event['id'])
        if isSucceed_markOrder : self.debugLogger.debug('{} - ManagementSizing - Successful to post message.'.format(event['id']))
        else:
            self.debugLogger.error('{} - ManagementSizing - Failed to post message!'.format(event['id']))
            self.errorLogger.error('{} - ManagementSizing - Failed to post message!'.format(event['id']))
            raise Exception

        # create history record - order marked
        # update size field
        # update status
        # create history record - size updated
        self.debugLogger.debug('{} - ManagementSizing - Executing sizing...'.format(event['id']))
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            cur.execute('SELECT status FROM dataflow_order WHERE endpoint_id = %s AND cacheId = %s', (event['endpoint_id'], event['cacheId']))
            status = cur.fetchone()[0]
            cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Order marked by WMS.', status, ''))
            cur.execute('UPDATE dataflow_order SET size = %s, status = %s WHERE endpoint_id = %s AND cacheId = %s', (event['data']['size'], 'WAITING FOR PICKING', event['endpoint_id'], event['cacheId']))
            cur.execute('INSERT INTO dataflow_history (endpoint_id, cacheId, time, event, status, remoteId) VALUES (%s, %s, %s, %s, %s, %s)', (event['endpoint_id'], event['cacheId'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Order size updated by {}'.format(event['data']['user']), 'WAITING FOR PICKING', ''))
            conn.commit()
        except Exception as e:
            self.debugLogger.exception('{} - ManagementSizing - Failed to execute sizing! - error: {} - event: {}'.format(event['id'], e, event))
            self.errorLogger.error('{} - ManagementSizing - Failed to execute sizing! - error: {} - event: {}'.format(event['id'], e, event))
            raise Exception
        else:
            self.debugLogger.debug('{} - ManagementSizing - Successful to execute sizing.'.format(event['id']))
        finally : conn.close()

        # post message
        self.debugLogger.debug('{0} - ManagementSizing - Posting message: "WMS: Order size updated. - user: {1[user]} - size: {1[size]}"...'.format(event['id'], event['data']))
        isSucceed_postMessage = self.endpoints[str(event['endpoint_id'])].postMessage(event['cacheId'], 'WMS: Order size updated. - user: {0[user]} - size: {0[size]}'.format(event['data']))
        if isSucceed_postMessage : self.debugLogger.debug('{} - ManagementSizing - Successful to post message.'.format(event['id']))
        else:
            self.debugLogger.error('{} - ManagementSizing - Failed to post message!'.format(event['id']))
            self.errorLogger.error('{} - ManagementSizing - Failed to post message!'.format(event['id']))

    except Exception as e:
        self.debugLogger.error('{} - ManagementSizing - Something went wrong! Putting order on hold... - error: {}'.format(event['id'], e))
        self.errorLogger.error('{} - ManagementSizing - Something went wrong! Putting order on hold... - error: {}'.format(event['id'], e))
        onholdevent = {'id' : -1, 'cacheId' : event['cacheId'], 'type' : 'OrderOnHold', 'priority' : -1, 'time' : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'data' : {'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'source': 'ManagementSizing', 'reason': 'An error occured while tying to execute ManagementSizing event!', 'remoteId': ''}, 'endpoint_id' : event['endpoint_id']}
        self.OrderOnHold(onholdevent)

        # close event
        self.debugLogger.debug('{} - ManagementSizing - Closing event...'.format(event['id']))
        if self.closeEvent(event, 'ERROR: Something went wrong while executing ManagementSizing function!') : self.debugLogger.debug('{} - ManagementSizing - Successful to close event.'.format(event['id']))
        else:
            self.debugLogger.error('ManagementSizing - Failed to close event! - event: {}'.format(event['id'], event))
            self.errorLogger.error('ManagementSizing - Failed to close event! - event: {}'.format(event['id'], event))

    else:
        # close event
        self.debugLogger.debug('{} - ManagementSizing - Closing event...'.format(event['id']))
        if self.closeEvent(event, 'OK') : self.debugLogger.debug('{} - ManagementSizing - Successful to close event.'.format(event['id']))
        else:
            self.debugLogger.error('{} - ManagementSizing - Failed to close event! - event: {}'.format(event['id'], event))
            self.errorLogger.error('{} - ManagementSizing - Failed to close event! - event: {}'.format(event['id'], event))

    finally:
        del self.workingThreads[str(event['id'])]
        self.ordersInProgress.remove((event['endpoint_id'], event['cacheId']))
