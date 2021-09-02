import time


def scanChanges(self):

    self.debugLogger.debug('Region is starting - Scan ERP for changes.')
    changes = dict()
    cacheIdsOnHold = [order['cacheId'] for order in self.ordersOnHold]
    for cacheId, summary in self.orderSummaries.items():
        if cacheId in cacheIdsOnHold:
            self.debugLogger.debug('Region scan erp for changes. - Order is on hold. Skipping order... - saleOrderId: {} - cacheId: {}'.format(summary['saleOrder']['id']))
            continue
        changes[cacheId] = list()

        #region check sale.order
        self.debugLogger.debug('Checking if sale.order changed...')
        saleorder_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(self.models, self.uid, 'sale.order', int(summary['saleOrder']['id']), ['__last_update'], cacheId)
        if isSucceed_pullFromOdoo:
            old, new, isChanged, isSucceed_compare = self.compare(summary['saleOrder']['__last_update'], saleorder_remote['__last_update'], 'flat')
            if isSucceed_compare:
                if isChanged:
                    self.debugLogger.debug('sale.order changed.')

                    changes, isSucceed_check = self.check(self.models, self.uid, cacheId, 'sale.order', 'saleOrder', self.saleOrder_fields, int(summary['saleOrder']['id']), 'saleOrder', changes)
                    if not isSucceed_check:
                        self.debugLogger.error('check function failed! - Couldn\'t check sale.order[{}].'.format(summary['saleOrder']['id']))
                        self.errorLogger.error('check function failed! - Couldn\'t check sale.order[{}].'.format(summary['saleOrder']['id']))
                        self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check sale.order')

            else:
                self.debugLogger.error('compare function failed! - Couldn\'t check sale.order[{}].'.format(summary['saleOrder']['id']))
                self.errorLogger.error('compare function failed! - Couldn\'t check sale.order[{}].'.format(summary['saleOrder']['id']))
                self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check sale.order')

        else:
            self.debugLogger.error('sale.order data for checking updates couldn\'t retrieve from odoo')
            self.errorLogger.error('sale.order data for checking updates couldn\'t retrieve from odoo')
            self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check sale.order')
        #endregion

        #region check stock.picking --> res.partner // stock.move
        for pickingId, picking in summary['saleOrder']['stockPicking'].items():

            #region check stock.picking
            self.debugLogger.debug('Cheking if stock.picking changed...')
            picking_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(self.models, self.uid, 'stock.picking', int(pickingId), ['message_ids', '__last_update'], cacheId)
            if isSucceed_pullFromOdoo:
                old, new, isChanged, isSucceed_compare = self.compare(picking['__last_update'], picking_remote['__last_update'], 'flat')
                if isSucceed_compare:
                    if isChanged:
                        self.debugLogger.debug('stock.picking changed.')

                        changes , isSucceed_check = self.check(self.models, self.uid, cacheId, 'stock.picking', 'stockPicking', {'origin': 'flat', 'state': 'flat', 'move_lines': 'list', 'partner_id': 'flat', 'carrier_tracking_ref': 'flat', 'picking_type_id': 'flat', '__last_update': 'flat'}, int(pickingId), 'saleOrder.stockPicking.{}'.format(pickingId), changes, int(pickingId))
                        if not isSucceed_check:
                            self.debugLogger.error('check function failed! - Couldn\'t check stock.picking[{}].'.format(pickingId))
                            self.errorLogger.error('check function failed! - Couldn\'t check stock.picking[{}].'.format(pickingId))
                            self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check stock.picking')

                else:
                    self.debugLogger.error('compare function failed! - Couldn\'t check stock.picking[{}].'.format(pickingId))
                    self.errorLogger.error('compare function failed! - Couldn\'t check stock.picking[{}].'.format(pickingId))
                    self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check stock.picking')

                # check message_ids
                removed, added, isChanged, isSucceed_compare = self.compare(picking['message_ids'], picking_remote['message_ids'], 'list')
                if isSucceed_compare:
                    if isChanged:
                        changes[cacheId].append({'type': 'list', 'index': 'saleOrder.stockPicking.{}.message_ids'.format(pickingId), 'removed': removed, 'added': added})
                        self.debugLogger.info('Change found: {}'.format(changes[cacheId][-1]))
                else:
                    self.debugLogger.error('Couldn\'t check stock.picking.message_ids')
                    self.errorLogger.error('Couldn\'t check stock.picking.message_ids')
                    self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check message_ids')

            else:
                self.debugLogger.error('stock.picking data for checking updates couldn\'t retrieve from odoo')
                self.errorLogger.error('stock.picking data for checking updates couldn\'t retrieve from odoo')
                self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check stock.picking')
            #endregion

            #region check res.partner
            self.debugLogger.debug('Cheking if res.partner changed...')
            respartner_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(self.models, self.uid, 'res.partner', int(picking['resPartner']['id']), ['__last_update'], cacheId)
            if isSucceed_pullFromOdoo:
                old, new, isChanged, isSucceed_compare = self.compare(picking['resPartner']['__last_update'], respartner_remote['__last_update'], 'flat')
                if isSucceed_compare:
                    if isChanged:
                        self.debugLogger.debug('res.partner changed.')

                        changes , isSucceed_check = self.check(self.models, self.uid, cacheId, 'res.partner', 'resPartner', self.resPartner_fields, int(picking['resPartner']['id']), 'saleOrder.stockPicking.{}.resPartner'.format(pickingId), changes)
                        if not isSucceed_check:
                            self.debugLogger.error('check function failed! - Couldn\'t check res.partner[{}].'.format(picking['resPartner']['id']))
                            self.errorLogger.error('check function failed! - Couldn\'t check res.partner[{}].'.format(picking['resPartner']['id']))
                            self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check res.partner')

                else:
                    self.debugLogger.error('compare function failed! - Couldn\'t check res.partner[{}].'.format(picking['resPartner']['id']))
                    self.errorLogger.error('compare function failed! - Couldn\'t check res.partner[{}].'.format(picking['resPartner']['id']))
                    self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check res.partner')

            else:
                self.debugLogger.error('res.partner data for checking updates couldn\'t retrieve from odoo')
                self.errorLogger.error('res.partner data for checking updates couldn\'t retrieve from odoo')
                self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check res.partner')
            #endregion

            #region check stock.moveS
            for moveId, move in picking['stockMove'].items():

                # check stock.move
                self.debugLogger.debug('Cheking if stock.move changed...')
                moveLU_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(self.models, self.uid, 'stock.move', int(moveId), ['__last_update'], cacheId)
                if isSucceed_pullFromOdoo:
                    old, new, isChanged, isSucceed_compare = self.compare(move['__last_update'], moveLU_remote['__last_update'], 'flat')
                    if isSucceed_compare:
                        if isChanged:
                            self.debugLogger.debug('stock.move changed.')

                            changes , isSucceed_check = self.check(self.models, self.uid, cacheId, 'stock.move', 'stockMove', self.stockMove_fields, int(moveId), 'saleOrder.stockPicking.{}.stockMove.{}'.format(pickingId, moveId), changes, int(moveId))
                            if not isSucceed_check:
                                self.debugLogger.error('check function failed! - Couldn\'t check stock.move[{}].'.format(moveId))
                                self.errorLogger.error('check function failed! - Couldn\'t check stock.move[{}].'.format(moveId))
                                self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check stock.move')

                    else:
                        self.debugLogger.error('compare function failed! - Couldn\'t check stock.move[{}].'.format(moveId))
                        self.errorLogger.error('compare function failed! - Couldn\'t check stock.move[{}].'.format(moveId))
                        self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check stock.move')

                else:
                    self.debugLogger.error('stock.move data for checking updates couldn\'t retrieve from odoo')
                    self.errorLogger.error('stock.move data for checking updates couldn\'t retrieve from odoo')
                    self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check stock.move')

            #endregion

        #endregion

        #region check account.invoiceS
        for invoiceId, invoice in summary['saleOrder']['accountInvoice'].items():

            # check account.invoice
            self.debugLogger.debug('Cheking if account.invoice changed...')
            invoiceLU_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(self.models, self.uid, 'account.invoice', int(invoiceId), ['__last_update'], cacheId)
            if isSucceed_pullFromOdoo:
                old, new, isChanged, isSucceed_compare = self.compare(invoice['__last_update'], invoiceLU_remote['__last_update'], 'flat')
                if isSucceed_compare:
                    if isChanged:
                        self.debugLogger.debug('account.invoice changed.')

                        changes , isSucceed_check = self.check(self.models, self.uid, cacheId, 'account.invoice', 'accountInvoice', self.accountInvoice_fields, int(invoiceId), 'saleOrder.accountInvoice.{}'.format(invoiceId), changes, int(invoiceId))
                        if not isSucceed_check:
                            self.debugLogger.error('check function failed! - Couldn\'t check account.invoice[{}].'.format(invoiceId))
                            self.errorLogger.error('check function failed! - Couldn\'t check account.invoice[{}].'.format(invoiceId))
                            self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check account.invoice')

                
                else:
                    self.debugLogger.error('compare function failed! - Couldn\'t check account.invoice[{}].'.format(invoiceId))
                    self.errorLogger.error('compare function failed! - Couldn\'t check account.invoice[{}].'.format(invoiceId))
                    self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check account.invoice')
            
            else:
                self.debugLogger.error('account.invoice data for checking updates couldn\'t retrieve from odoo')
                self.errorLogger.error('account.invoice data for checking updates couldn\'t retrieve from odoo')
                self.orderOnHoldEvent(summary['saleOrder']['id'], cacheId, 'Couldn\'t check account.invoice')
        
        time.sleep(float(self.endpointCycleTime)/10)
        #endregion

    self.debugLogger.debug('Region completed. - Scan ERP for changes.')
    return changes