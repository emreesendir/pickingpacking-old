import logging, logging.handlers, mysql.connector, odoorpc, xmlrpc.client as xmlrpclib, json
from configparser import ConfigParser

class odoo12:

    from ._mdp import markOrder, postMessage, deleteOrder, deleteInvoices, orderShipped
    from ._scanningThread import scanningThread
    from ._func import compare, updateOpenEvents, updateOrdersOnHold, odooLogin, retrieveFromCache, pullFromOdoo, ignoreChange, check, createEvent, newMessages, orderOnHoldEvent, updateCacheData
    from ._scan import scanChanges
    from ._react import reactChanges
    from ._newOrders import cacheNewOrders

    def __init__(self, db_host, db_user, db_pass, db_db, invoiceFolder, logFolder, endpointId, endpointType, endpointName, endpointStatus, endpointCycleTime):
        parser = ConfigParser()
        parser.read('/home/app/config/dataFlowSecret.conf')
        # ============================== FROM CONTROLLER ============================== #
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_db = db_db
        self.invoiceFolder = invoiceFolder
        self.logFolder = logFolder
        self.endpointId = endpointId
        self.endpointType = endpointType
        self.endpointName = endpointName
        self.endpointStatus = endpointStatus
        self.endpointCycleTime = endpointCycleTime
        self.url = parser.get('odoo', 'url')
        self.db = parser.get('odoo', 'db')
        self.username = parser.get('odoo', 'username')
        self.password = parser.get('odoo', 'password')
        self.quit = False
        # ============================================================================== #

        # ============================= OTHER GLOBAL VARIABLES ========================= #
        self.cacheTable = 'dataflow_{}'.format(self.endpointName)
        self.orderSummaries = dict()
        self.openEvents = dict()
        self.ordersOnHold = list()
        self.deleteList = list()

        self.saleOrder_fields = {'x_InternalStatus': 'list', 'invoice_ids': 'list', 'state': 'flat', 'picking_ids': 'list', '__last_update': 'flat'}
        self.stockPicking_fields = {'origin': 'flat', 'state': 'flat', 'move_lines': 'list', 'partner_id': 'flat', 'carrier_tracking_ref': 'flat', 'picking_type_id': 'flat', '__last_update': 'flat', 'message_ids': 'list'}
        self.resPartner_fields = {'name': 'flat', 'wk_company': 'flat', 'street': 'flat', 'zip': 'flat', 'city': 'flat', '__last_update': 'flat'}
        self.stockMove_fields = {'product_id': 'flat', 'product_uom_qty': 'flat', '__last_update': 'flat'}
        self.accountInvoice_fields = {'state': 'flat', '__last_update': 'flat'}
        self.mailMessage_fields = {'body': 'flat', 'author_id': 'flat', 'date': 'flat'}
        self.productProduct_fields = {'barcode': 'flat', 'x_studio_pickingorder': 'flat', 'name': 'flat'}

        # debug logger
        self.debugLogger = logging.getLogger('{}Debug'.format(self.endpointName))
        self.debugLogger.setLevel(logging.DEBUG)
        debugFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        debugFileHandler = logging.FileHandler('{}{}'.format(self.logFolder, '{}Debug.log'.format(self.endpointName)))
        debugFileHandler.setFormatter(debugFormatter)
        while self.debugLogger.hasHandlers() : self.debugLogger.removeHandler(self.debugLogger.handlers[0])
        self.debugLogger.addHandler(debugFileHandler)

        # error logger
        self.errorLogger = logging.getLogger('{}Error'.format(self.endpointName))
        self.errorLogger.setLevel(logging.ERROR)
        errorFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        errorFileHandler = logging.FileHandler('{}{}'.format(self.logFolder, 'error.log'))
        errorFileHandler.setFormatter(errorFormatter)
        while self.errorLogger.hasHandlers() : self.errorLogger.removeHandler(self.errorLogger.handlers[0])
        self.errorLogger.addHandler(errorFileHandler)

        # smtp logger
        self.smtpLogger = logging.getLogger('{}SMTP'.format(self.endpointName))
        self.smtpLogger.setLevel(logging.CRITICAL)
        smtpFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        smtpHandler = logging.handlers.SMTPHandler(mailhost=(parser.get('smtp', 'mailhost'), 587), fromaddr=parser.get('smtp', 'fromaddr'), toaddrs=parser.get('smtp', 'toaddrs'), subject='WMS CRITICAL FAILURE', credentials=(parser.get('smtp', 'fromaddr'),parser.get('smtp', 'password')), secure=())
        smtpHandler.setFormatter(smtpFormatter)
        while self.smtpLogger.hasHandlers() : self.smtpLogger.removeHandler(self.smtpLogger.handlers[0])
        self.smtpLogger.addHandler(smtpHandler)
        # ============================================================================== #

    def test(self):
        self.debugLogger.info('Testing...')
        isSucceed = True

        #TEST DATABASE CONNECTION
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            cur.execute('SELECT id, summary FROM {} LIMIT 1'.format(self.cacheTable))
        except Exception as e:
            self.debugLogger.exception('Failed to load! - error: {}'.format(e))
            self.errorLogger.error('Failed to load! - error: {}'.format(e))
            isSucceed = False
        else : self.debugLogger.debug('Test - DATABASE OK!')
        finally : conn.close()

        #TEST ODOORPC CONNECTION
        try:
            odoo = odoorpc.ODOO(self.url, 'jsonrpc+ssl', 443)
            odoo.login(self.db, self.username, self.password)
        except Exception as e:
            self.debugLogger.exception('Test - ODOORPC CONNECTION FAILED!')
            self.errorLogger.error('Test - ODOORPC CONNECTION FAILED!')
            isSucceed = False
        else:
            self.debugLogger.debug('Test - ODOORPC OK!')

        #TEST XMLRPC CONNECTION
        try:
            common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format('https://' + self.url))
            models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format('https://' + self.url))
            uid = common.authenticate(self.db, self.username, self.password, {})
        except Exception as e:
            self.debugLogger.exception('Test - XMLRPC CONNECTION FAILED! - error: {}'.format(e))
            self.errorLogger.error('Test - XMLRPC CONNECTION FAILED! - error: {}'.format(e))
            isSucceed = False
        else:
            self.debugLogger.debug('Test - XMLRPC OK!')

        if isSucceed: self.debugLogger.info('Test is successful.')
        else:
            self.debugLogger.critical('Test failed!')
            self.errorLogger.critical('Test failed!')
            #self.smtpLogger.critical('Test failed!')
        return isSucceed

    def load(self):
        self.debugLogger.info('Loading {}...'.format(self.endpointName))
        isSucceed = True

        #LOAD ORDER SUMMARIES
        self.debugLogger.debug('load - Loading order summaries...')
        try:
            conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
            cur = conn.cursor()
            cur.execute('SELECT id, summary FROM {}'.format(self.cacheTable))
            self.orderSummaries.clear()
            for row in cur : self.orderSummaries[str(row[0])] = json.loads(row[1])
        except Exception as e:
            self.debugLogger.exception('Failed to load! - error: {}'.format(e))
            self.errorLogger.critical('Failed to load! - error: {}'.format(e))
            #self.smtpLogger.critical('Failed to load! - error: {}'.format(e))
            isSucceed = False
        else : self.debugLogger.debug('Summaries are loaded from database successfully. - orderSummaries: {}'.format(self.orderSummaries))
        finally : conn.close()

        if isSucceed: self.debugLogger.info('Load is successful.')
        else:
            self.debugLogger.critical('Load failed!')
            self.errorLogger.critical('Load failed!')
            #self.smtpLogger.critical('Load failed!')
        return isSucceed