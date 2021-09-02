import time

def scanningThread(self):
    self.debugLogger.info('Scannig thread has started')

    while True:
        start = time.perf_counter()
        self.debugLogger.debug('============================================================')
        self.debugLogger.debug('Scanning cycle has started')

        # check quit command from controller
        self.debugLogger.debug('Checking for quit order...')
        if self.quit:
            self.debugLogger.info('Scanning thread quited peacefully')
            break

        # clear order.Summaries
        for cacheId in self.deleteList:
            try : del self.orderSummaries[str(cacheId)]
            except Exception as e:
                self.debugLogger.exception('Failed to delete order summary! - error: {}'.format(e))
                self.errorLogger.error('Failed to delete order summary! - error: {}'.format(e))
            finally : self.deleteList.remove(cacheId)

        # update openEvents
        self.debugLogger.debug('Updating openEvents...')
        isSucceed_openevents = self.updateOpenEvents()

        # update ordersOnHold
        self.debugLogger.debug('Updating ordersOnHold...')
        isSucceed_ordersonhold = self.updateOrdersOnHold()

        # odoo login
        self.debugLogger.debug('Odoo Login...')
        odoo, uid, models, saleOrder_env, isSucceed_odoologin = self.odooLogin()

        # detect new orders
        if isSucceed_odoologin:
            self.debugLogger.debug('Detecting New Orders...')
            id2 = self.InternalStatus.search([('x_studio_code','=', 'autoprint')])[0]
            id3 = self.InternalStatus.search([('x_studio_code','=', 'printed')])[0]
            newOrders = models.execute_kw(self.db, uid, self.password, 'sale.order', 'search_read', [[['state', '!=', 'cancel']]], {'fields': ['x_InternalStatus']})
            newSaleOrderIds = [newOrder['id'] for newOrder in newOrders]
            for newOrder in newOrders :
                if not (id2 in newOrder['x_InternalStatus'] and id3 not in newOrder['x_InternalStatus']) : newSaleOrderIds.remove(newOrder['id'])
            for cacheId, summary in self.orderSummaries.items():
                if int(summary['saleOrder']['id']) in newSaleOrderIds : newSaleOrderIds.remove(summary['saleOrder']['id'])
            self.debugLogger.info('newSaleOrderIds - length : {} - data: {}'.format(len(newSaleOrderIds), newSaleOrderIds))
        else:
            self.debugLogger.critical('Can not login to Odoo. Detect new orders can not work.')
            self.errorLogger.critical('Can not login to Odoo. Detect new orders can not work.')
            #self.smtpLogger.critical('Can not login to Odoo. Detect new orders can not work.')
        
        if isSucceed_openevents and isSucceed_odoologin and isSucceed_ordersonhold:

            changes = self.scanChanges()
            self.reactChanges(changes)
            self.cacheNewOrders(newSaleOrderIds)

        else:
            if not isSucceed_odoologin:
                self.debugLogger.critical('Can not login to Odoo. Scan erp for changes can not work.')
                self.errorLogger.critical('Can not login to Odoo. Scan erp for changes can not work.')
                #self.smtpLogger.critical('Can not login to Odoo. Scan erp for changes can not work.')
            if not isSucceed_openevents:
                self.debugLogger.critical('Can not retreive open events. Scan erp for changes can not work.')
                self.errorLogger.critical('Can not retreive open events. Scan erp for changes can not work.')
                #self.smtpLogger.critical('Can not retreive open events. Scan erp for changes can not work.')
            if not isSucceed_ordersonhold:
                self.debugLogger.critical('Can not retrieve orders on hold. Scan erp for changes can not work.')
                self.errorLogger.critical('Can not retrieve orders on hold. Scan erp for changes can not work.')
                #self.smtpLogger.critical('Can not retrieve orders on hold. Scan erp for changes can not work.')

        stop = time.perf_counter()
        self.debugLogger.info('Cycle completed in {} seconds.'.format(stop - start))