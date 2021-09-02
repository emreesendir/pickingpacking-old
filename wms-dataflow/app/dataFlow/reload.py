import mysql.connector, datetime
from .odoo12 import odoo12

def reloadEndpoints(debugLogger, errorLogger, smtpLogger, logFolder, db_host, db_user, db_pass, db_db, invoiceFolder, endpointStatuses, endpointCommands, endpoints, scanningThreads):
    debugLogger.debug('reloadEndpoints - load - invoiceFolder: {} - logFolder: {} - endpointStatuses: {} - endpointCommands: {} - endpoints: {} - scanningThreads: {}'.format(invoiceFolder, logFolder, endpointStatuses, endpointCommands, endpoints, scanningThreads))

    #region kill and reset all endpoints
    debugLogger.debug('reloadEndpoints - Trying to kill and reset...')
    try:

        # stop scanningThreads
        debugLogger.debug('reloadEndpoints - Stopping scanningThreads...')
        for endpointId, endpointStatus in endpointStatuses.items():
            if endpointStatus == 'RUNNING' : endpoints[endpointId].quit = True
        for endpointId, thread in  scanningThreads.items():
            thread.join()
        debugLogger.debug('reloadEndpoints - Successful to stop scanningThreads.')

        # clear all dictionaries
        debugLogger.debug('reloadEndpoints - Resetting dictionaries...')
        endpointStatuses.clear()
        endpointCommands.clear()
        endpoints.clear()
        scanningThreads.clear()
        debugLogger.debug('reloadEndpoints - Successful reset dictionaries.')

    except Exception as e:
        debugLogger.exception('reloadEndpoints - Failed kill an reset: {}'.format(e))
        errorLogger.error('reloadEndpoints - Failed kill an reset: {}'.format(e))
        return {}, {}, {}, {}, [], False
    debugLogger.debug('reloadEndpoints - Successful to kill and reset...')
    #endregion

    #region read settings from database
    debugLogger.debug('reloadEndpoints - Trying to read settings from database...')
    dataflow_dataflow = dict()
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_pass, db=db_db)
        cur = conn.cursor()
        cur.execute('SELECT id, name, type, status, cycleTime, command FROM dataflow_dataflow WHERE name != %s AND name != %s', ('MAIN', 'MDP'))
        for row in cur : dataflow_dataflow[str(row[0])] = {'name' : row[1], 'type' : row[2], 'status' : row[3], 'cycleTime' : row[4], 'command' : row[5]}
        conn.close()
    except Exception as e:
        debugLogger.exception('reloadEndpoints - Error while reading database: {}'.format(e))
        errorLogger.error('reloadEndpoints - Error while reading database: {}'.format(e))
        return {}, {}, {}, {}, [], False
    debugLogger.debug('reloadEndpoints - Successful to read settings from database. - dataflow_dataflow: {}'.format(dataflow_dataflow))
    #endregion

    #region create endpoint instances
    debugLogger.debug('reloadEndpoints - Trying to create endpoint instances...')

    for endpointId, endpointSettings in dataflow_dataflow.items():
        try:
            if endpointSettings['command'] == 'SUSPEND':
                endpointStatuses[endpointId] = 'SUSPENDED'
                endpointCommands[endpointId] = 'SUSPEND'
                endpoints[endpointId] = endpointSettings
                debugLogger.debug('reloadEndpoints - Endpoint suspended. - endpointId: {} - endpoint settings: {}'.format(endpointId, endpointSettings))

            elif endpointSettings['command'] == 'STAND BY':
                if endpointSettings['type'] == 'odoo12':
                    try:
                        debugLogger.debug('reloadEndpoints - Trying to instantiate {}'.format(endpointSettings['name']))
                        odoo12_instance = odoo12(db_host, db_user, db_pass, db_db, invoiceFolder, logFolder, endpointId, endpointSettings['type'], endpointSettings['name'], endpointSettings['status'], endpointSettings['cycleTime'])

                        isSuceed_test = odoo12_instance.test()

                        if isSuceed_test:
                            isSucceed_load = odoo12_instance.load()
                            if isSucceed_load:
                                endpointStatuses[endpointId] = 'STANDING BY'
                                endpointCommands[endpointId] = 'STAND BY'
                                endpoints[endpointId] = odoo12_instance
                                debugLogger.debug('reloadEndpoints - Successful to load endpoint. - endpointId: {} - endpoint settings: {}'.format(endpointId, endpointSettings))

                            else:
                                debugLogger.error('reloadEndpoints - Failed to load! - endpoint: {}'.format(endpointSettings['name']))
                                errorLogger.error('reloadEndpoints - Failed to load! - endpoint: {}'.format(endpointSettings['name']))
                                raise Exception

                        else:
                            debugLogger.error('reloadEndpoints - Test Failed! - endpoint: {}'.format(endpointSettings['name']))
                            errorLogger.error('reloadEndpoints - Test Failed! - endpoint: {}'.format(endpointSettings['name']))
                            raise Exception

                    except Exception as e:
                        debugLogger.exception('reloadEndpoints - Failed to instantiate! - endpoint: {} - error: {}'.format(endpointSettings['name'], e))
                        errorLogger.error('reloadEndpoints - Failed to instantiate! - endpoint: {} - error: {}'.format(endpointSettings['name'], e))
                        raise Exception

                else:
                    debugLogger.error('reloadEndpoints - Unknown endpoint! - id: {0} - type: {1[type]} - name: {1[name]}'.format(endpointId, endpointSettings))
                    errorLogger.error('reloadEndpoints - Unknown endpoint! - id: {0} - type: {1[type]} - name: {1[name]}'.format(endpointId, endpointSettings))
                    raise Exception

            else:
                debugLogger.error('reloadEndpoints - Unknown command! - id: {0} - type: {1[type]} - name: {1[name]}'.format(endpointId, endpointSettings))
                errorLogger.error('reloadEndpoints - Unknown command! - id: {0} - type: {1[type]} - name: {1[name]}'.format(endpointId, endpointSettings))
                raise Exception

        except:
            endpointStatuses[endpointId] = 'FAILED'
            endpointCommands[endpointId] = endpointSettings['command']
            endpoints[endpointId] = endpointSettings
            debugLogger.debug('reloadEndpoints - Failed to create endpoint instances! - endpointId: {} - endpoint settings: {}'.format(endpointId, endpointSettings))

    debugLogger.debug('reloadEndpoints - create endpoint instances result - endpointStatuses: {} - endpointCommands: {} - endpoints: {}'.format(endpointStatuses, endpointCommands, endpoints))
    #endregion

    #region update database
    debugLogger.debug('reloadEndpoints - Trying to update database...')
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_pass, db=db_db)
        cur = conn.cursor()
        for endpointId, status in endpointStatuses.items() : cur.execute('UPDATE dataflow_dataflow SET status = %s, lastupdate = %s WHERE id = %s', (status, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), endpointId))
        conn.commit()
    except Exception as e:
        debugLogger.exception('reloadEndpoints - Failed to update database: {}'.format(e))
        errorLogger.error('reloadEndpoints - Failed to update database: {}'.format(e))
    else:
        debugLogger.debug('reloadEndpoints - Successful to update database')
    finally:
        conn.close()
    #endregion

    debugLogger.info('reloadEndpoints - Reload completed. endpointStatuses: {} - endpointCommands: {} - endpoints: {} - scanningThreads: {}'.format(endpointStatuses, endpointCommands, endpoints, scanningThreads))
    return endpointStatuses, endpointCommands, endpoints, scanningThreads, True