import json, os, mysql.connector, time

def cacheNewOrders(self, newSaleOrderIds):

    if len(newSaleOrderIds) > 0:
        self.debugLogger.debug('Region is starting - Cache new orders...')
        saleOrdersOnHold = [order['remoteId'] for order in self.ordersOnHold]
        for saleOrderId in newSaleOrderIds:
            if str(saleOrderId) in saleOrdersOnHold:
                self.debugLogger.debug('Region cache new orders. - Order is on hold. Skipping order... - saleOrderId: {}'.format(saleOrderId))
                continue
            self.debugLogger.debug('Trying to cache an order... - sale.order.id: {}'.format(saleOrderId))

            #LAYER0

            # retrieve sale.order remote
            self.debugLogger.debug('Trying to retrieve sale.order remote... - saleOrderId: {}'.format(saleOrderId))
            saleOrder_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(self.models, self.uid, 'sale.order', saleOrderId, [f for f in self.saleOrder_fields])
            if not isSucceed_pullFromOdoo:
                self.debugLogger.error('Caching new order failed when trying to pull sale.order data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.errorLogger.error('Caching new order failed when trying to pull sale.order data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.orderOnHoldEvent(saleOrderId, -1, 'Caching new order failed when trying to pull sale.order data from odoo.')
                continue
            self.debugLogger.debug('Successful to retrieve sale.order remote. - saleOrderId: {}'.format(saleOrderId))

            # validate sale.order remote
            self.debugLogger.debug('Trying to validate sale.order remote... - saleOrderId: {}'.format(saleOrderId))
            if not (type(saleOrder_remote['invoice_ids']) == type([]) and len(saleOrder_remote['invoice_ids']) > 0 and type(saleOrder_remote['state']) == type('') and saleOrder_remote['state'] != 'cancel' and type(saleOrder_remote['picking_ids']) == type([]) and len(saleOrder_remote['picking_ids']) > 0 and type(saleOrder_remote['__last_update']) == type('') and saleOrder_remote['__last_update'] != ''):
                self.debugLogger.error('Failed to validate sale.order remote. Skipping the order... - sale.order.id: {} - remote data: {}'.format(saleOrderId, saleOrder_remote))
                self.errorLogger.error('Failed to validate sale.order remote. Skipping the order... - sale.order.id: {} - remote data: {}'.format(saleOrderId, saleOrder_remote))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to validate sale.order remote.')
                continue
            self.debugLogger.debug('Successful to validate sale.order remote. - saleOrderId: {}'.format(saleOrderId))

            # update dictionaries sale.order
            self.debugLogger.debug('Trying to update dictionaries... - saleOrderId: {}'.format(saleOrderId))
            try:
                saleOrderDict = saleOrder_remote
            except Exception as e:
                self.debugLogger.exception('Failed to update dictionaries LAYER0. Skipping the order... error: {}'.format(e))
                self.errorLogger.error('Failed to update dictionaries LAYER0. Skipping the order... error: {}'.format(e))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to update dictionaries LAYER0.')
                continue
            self.debugLogger.debug('Successful to update dictionaries. - saleOrderId: {}'.format(saleOrderId))

            # prepare lists for next layer
            self.debugLogger.debug('Trying to prepare lists for next layer... - saleOrderId: {}'.format(saleOrderId))
            try:
                invoice_ids = saleOrder_remote['invoice_ids']
                picking_ids = saleOrder_remote['picking_ids']
                clean_pickings = list()
            except Exception as e:
                self.debugLogger.exception('Failed to prepare lists for next layer LAYER0. Skipping the order... error: {}'.format(e))
                self.errorLogger.error('Failed to prepare lists for next layer LAYER0. Skipping the order... error: {}'.format(e))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to prepare lists for next layer LAYER0.')
                continue
            self.debugLogger.debug('Successful to prepare lists for next layer. - saleOrderId: {}'.format(saleOrderId))

            #LAYER1

            # retreive stock.pickingS
            self.debugLogger.debug('Trying to retreive stock.pickingS... - saleOrderId: {}'.format(saleOrderId))
            stockPickingS_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(self.models, self.uid, 'stock.picking', picking_ids, [f for f in self.stockPicking_fields])
            if not isSucceed_pullFromOdoo:
                self.debugLogger.error('Caching new order failed when trying to pull stock.pickingS data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.errorLogger.error('Caching new order failed when trying to pull stock.pickingS data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.orderOnHoldEvent(saleOrderId, -1, 'Caching new order failed when trying to pull stock.pickingS data from odoo.')
                continue
            self.debugLogger.debug('Successful to retrieve stock.pickingS remote. - saleOrderId: {}'.format(saleOrderId))

            # validate stock.pickingS
            self.debugLogger.debug('Trying to validate stock.pickingS remote... - saleOrderId: {}'.format(saleOrderId))
            for picking in stockPickingS_remote:
                if type(picking['picking_type_id']) == type([]) and len(picking['picking_type_id']) > 0 and type(picking['carrier_tracking_ref']) == type(False) and picking['carrier_tracking_ref'] == False and type(picking['partner_id']) == type([]) and len(picking['partner_id']) > 0 and type(picking['move_lines']) == type([]) and len(picking['move_lines']) > 0 and type(picking['state']) == type('') and picking['state'] != '' and type(picking['origin']) == type('') and picking['origin'] != '' and type(picking['message_ids']) == type([]) and len(picking['message_ids']) > 0 and type(picking['__last_update']) == type('') and picking['__last_update'] != '':
                    if picking['picking_type_id'][0] == 2:
                        clean_pickings.append(picking)
                else:
                    self.debugLogger.error('Failed to validate stock.picking remote. Ignoring the picking... - sale.order.id: {} - remote data: {}'.format(saleOrderId, picking))
                    self.errorLogger.error('Failed to validate stock.picking remote. Ignoring the picking... - sale.order.id: {} - remote data: {}'.format(saleOrderId, picking))
            if len(clean_pickings) != 1:
                self.debugLogger.error('Failed to validate stock.pickingS remote. Skipping the order... - remote data: {}'.format(stockPickingS_remote))
                self.errorLogger.error('Failed to validate stock.pickingS remote. Skipping the order... - remote data: {}'.format(stockPickingS_remote))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to validate stock.picking remote.')
                continue
            self.debugLogger.debug('Successful to validate stock.pickingS remote. - saleOrderId: {}'.format(saleOrderId))

            # update dictionaries stock.pickingS
            self.debugLogger.debug('Trying to update dictionaries stock.pickingS... - saleOrderId: {}'.format(saleOrderId))
            stockPickingDict = dict()
            try:
                for picking in clean_pickings:
                    stockPickingDict[str(picking['id'])] = {'origin': picking['origin'], 'state': picking['state'], 'move_lines': picking['move_lines'], 'partner_id': picking['partner_id'][0], 'carrier_tracking_ref': picking['carrier_tracking_ref'], 'message_ids': picking['message_ids'], 'picking_type_id': picking['picking_type_id'][0], '__last_update': picking['__last_update']}
            except Exception as e:
                self.debugLogger.exception('Failed to update dictionaries LAYER1 stock.picking. Skipping the order... error: {}'.format(e))
                self.errorLogger.error('Failed to update dictionaries LAYER1 stock.picking. Skipping the order... error: {}'.format(e))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to update dictionaries LAYER1 stock.picking.')
                continue
            self.debugLogger.debug('Successful to update dictionaries stock.pickingS. - saleOrderId: {}'.format(saleOrderId))

            # retrieve account.invoiceS
            self.debugLogger.debug('Trying to retreive account.invoiceS... - saleOrderId: {}'.format(saleOrderId))
            accountInvoiceS_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(self.models, self.uid, 'account.invoice', invoice_ids, [f for f in self.accountInvoice_fields])
            if not isSucceed_pullFromOdoo:
                self.debugLogger.error('Caching new order failed when trying to pull account.invoiceS data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.errorLogger.error('Caching new order failed when trying to pull account.invoiceS data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.orderOnHoldEvent(saleOrderId, -1, 'Caching new order failed when trying to pull account.invoiceS data from odoo.')
                continue
            self.debugLogger.debug('Successful to retrieve account.invoiceS remote. - saleOrderId: {}'.format(saleOrderId))

            # validate account.invoiceS
            self.debugLogger.debug('Trying to validate account.invoiceS remote... - saleOrderId: {}'.format(saleOrderId))
            isEndedNormally = False
            for accountInvoice in accountInvoiceS_remote:
                if type(accountInvoice['state']) == type('') and (accountInvoice['state'] == 'open' or accountInvoice['state'] == 'paid') and type(accountInvoice['__last_update']) == type('') and accountInvoice['__last_update'] != '':
                    pass
                else:
                    self.debugLogger.error('Failed to validate account.invoiceS remote. Skipping the order... - sale.order.id: {} - remote data: {}'.format(saleOrderId, accountInvoice))
                    self.errorLogger.error('Failed to validate account.invoiceS remote. Skipping the order... - sale.order.id: {} - remote data: {}'.format(saleOrderId, accountInvoice))
                    self.orderOnHoldEvent(saleOrderId, -1, 'Failed to validate account.invoice remote.')
                    break
                isEndedNormally = True
            if not isEndedNormally: continue
            self.debugLogger.debug('Successful to validate account.invoiceS remote. - saleOrderId: {}'.format(saleOrderId))

            # update dictionaries account.invoiceS
            self.debugLogger.debug('Trying to update dictionaries account.invoiceS... - saleOrderId: {}'.format(saleOrderId))
            accountInvoiceDict = dict()
            try:
                for accountInvoice in accountInvoiceS_remote:
                    accountInvoiceDict[str(accountInvoice['id'])] = {'state': accountInvoice['state'], '__last_update': accountInvoice['__last_update']}
            except Exception as e:
                self.debugLogger.exception('Failed to update dictionaries LAYER1 account.invoice. Skipping the order... error: {}'.format(e))
                self.errorLogger.error('Failed to update dictionaries LAYER1 account.invoice. Skipping the order... error: {}'.format(e))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to update dictionaries LAYER1 account.invoice.')
                continue
            self.debugLogger.debug('Successful to update dictionaries account.invoiceS. - saleOrderId: {}'.format(saleOrderId))

            # prepare lists for next layer
            stockMove_ids = list()
            mailMessages_ids = list()
            resPartner_id = int()
            for picking in stockPickingDict.values():
                for stockMove_id in picking['move_lines']:
                    stockMove_ids.append(stockMove_id)
                for mailMessage_id in picking['message_ids']:
                    mailMessages_ids.append(mailMessage_id)
            for picking in stockPickingDict.values():
                resPartner_id = picking['partner_id']
                break

            #LAYER2

            # retreive stock.moveS
            self.debugLogger.debug('Trying to retreive stock.moveS... - saleOrderId: {}'.format(saleOrderId))
            stockMoveS_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(self.models, self.uid, 'stock.move', stockMove_ids, [f for f in self.stockMove_fields])
            if not isSucceed_pullFromOdoo:
                self.debugLogger.error('Caching new order failed when trying to pull stock.moveS data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.errorLogger.error('Caching new order failed when trying to pull stock.moveS data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.orderOnHoldEvent(saleOrderId, -1, 'Caching new order failed when trying to pull stock.moveS data from odoo.')
                continue
            self.debugLogger.debug('Successful to retrieve stock.moveS remote. - saleOrderId: {}'.format(saleOrderId))

            # validate stock.moveS
            self.debugLogger.debug('Trying to validate stock.moveS remote... - saleOrderId: {}'.format(saleOrderId))
            isEndedNormally = False
            for stockMove in stockMoveS_remote:
                if type(stockMove['product_id']) == type([]) and len(stockMove['product_id']) > 0 and type(stockMove['product_uom_qty']) == type(1.0) and stockMove['product_uom_qty'] != 0.0 and type(stockMove['__last_update']) == type('') and stockMove['__last_update'] != '':
                    pass
                else:
                    self.debugLogger.error('Failed to validate stock.moveS remote. Skipping the order... - sale.order.id: {} - remote data: {}'.format(saleOrderId, stockMoveS_remote))
                    self.errorLogger.error('Failed to validate stock.moveS remote. Skipping the order... - sale.order.id: {} - remote data: {}'.format(saleOrderId, stockMoveS_remote))
                    self.orderOnHoldEvent(saleOrderId, -1, 'Failed to validate stock.move remote.')
                    break
                isEndedNormally = True
            if not isEndedNormally: continue
            self.debugLogger.debug('Successful to validate stock.moveS remote. - saleOrderId: {}'.format(saleOrderId))

            # update dictionaries stock.moveS
            self.debugLogger.debug('Trying to update dictionaries stock.moveS... - saleOrderId: {}'.format(saleOrderId))
            stockMoveDict = dict()
            try:
                for stockMove in stockMoveS_remote:
                    stockMoveDict[str(stockMove['id'])] = {'product_id': stockMove['product_id'][0], 'product_uom_qty': stockMove['product_uom_qty'], '__last_update': stockMove['__last_update']}
            except Exception as e:
                self.debugLogger.exception('Failed to update dictionaries LAYER2 stock.move. Skipping the order... error: {}'.format(e))
                self.errorLogger.error('Failed to update dictionaries LAYER2 stock.move. Skipping the order... error: {}'.format(e))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to update dictionaries LAYER2 stock.move.')
                continue
            self.debugLogger.debug('Successful to update dictionaries stock.moveS. - saleOrderId: {}'.format(saleOrderId))

            # retrieve mail.messageS
            self.debugLogger.debug('Trying to retreive mail.messageS... - saleOrderId: {}'.format(saleOrderId))
            mailMessageS_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(self.models, self.uid, 'mail.message', mailMessages_ids, [f for f in self.mailMessage_fields])
            if not isSucceed_pullFromOdoo:
                self.debugLogger.error('Caching new order failed when trying to pull mail.messageS data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.errorLogger.error('Caching new order failed when trying to pull mail.messageS data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.orderOnHoldEvent(saleOrderId, -1, 'Caching new order failed when trying to pull mail.message data from odoo.')
                continue
            self.debugLogger.debug('Successful to retrieve mail.messageS remote. - saleOrderId: {}'.format(saleOrderId))

            # validate mail.messageS
            self.debugLogger.debug('Trying to validate mail.messageS remote... - saleOrderId: {}'.format(saleOrderId))
            isEndedNormally = False
            for mailMessage in mailMessageS_remote:
                if type(mailMessage['author_id']) == type([]) and len(mailMessage['author_id']) > 1 and type(mailMessage['date']) == type('') and mailMessage['date'] != '' and type(mailMessage['body']) == type (''):
                    pass
                else:
                    self.debugLogger.error('Failed to validate mail.messageS remote. Skipping the order... - sale.order.id: {} - remote data: {}'.format(saleOrderId, mailMessageS_remote))
                    self.errorLogger.error('Failed to validate mail.messageS remote. Skipping the order... - sale.order.id: {} - remote data: {}'.format(saleOrderId, mailMessageS_remote))
                    self.orderOnHoldEvent(saleOrderId, -1, 'Failed to validate mail.message remote.')
                    break
                isEndedNormally = True
            if not isEndedNormally: continue
            self.debugLogger.debug('Successful to validate mail.messageS remote. - saleOrderId: {}'.format(saleOrderId))

            # update dictionaries mail.messageS
            self.debugLogger.debug('Trying to update dictionaries mail.messageS... - saleOrderId: {}'.format(saleOrderId))
            mailMessageDict = dict()
            try:
                for mailMessage in mailMessageS_remote:
                    mailMessageDict[str(mailMessage['id'])] = {'body': mailMessage['body'], 'author_id': mailMessage['author_id'][1], 'date': mailMessage['date']}
            except Exception as e:
                self.debugLogger.exception('Failed to update dictionaries LAYER2 mail.message. Skipping the order... error: {}'.format(e))
                self.errorLogger.error('Failed to update dictionaries LAYER2 mail.message. Skipping the order... error: {}'.format(e))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to update dictionaries LAYER2 mail.message.')
                continue
            self.debugLogger.debug('Successful to update dictionaries mail.messageS. - saleOrderId: {}'.format(saleOrderId))

            # retrieve res.partner
            self.debugLogger.debug('Trying to retreive res.partner... - saleOrderId: {}'.format(saleOrderId))
            resPartner_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(self.models, self.uid, 'res.partner', resPartner_id, [f for f in self.resPartner_fields])
            if not isSucceed_pullFromOdoo:
                self.debugLogger.error('Caching new order failed when trying to pull res.partner data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.errorLogger.error('Caching new order failed when trying to pull res.partner data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.orderOnHoldEvent(saleOrderId, -1, 'Caching new order failed when trying to pull res.partner data from odoo.')
                continue
            self.debugLogger.debug('Successful to retrieve res.partner remote. - saleOrderId: {}'.format(saleOrderId))

            # validate res.partner
            self.debugLogger.debug('Trying to validate res.partner remote... - saleOrderId: {}'.format(saleOrderId))
            if not (type(resPartner_remote['name']) == type('') and resPartner_remote['name'] != '' and type(resPartner_remote['street']) == type('') and resPartner_remote['street'] != '' and type(resPartner_remote['zip']) == type('') and resPartner_remote['zip'] != '' and type(resPartner_remote['city']) == type('') and resPartner_remote['city'] != '' and type(resPartner_remote['__last_update']) == type('') and resPartner_remote['__last_update'] != ''):
                self.debugLogger.error('Failed to validate res.partner remote. Skipping the order... - sale.order.id: {} - remote data: {}'.format(saleOrderId, resPartner_remote))
                self.errorLogger.error('Failed to validate res.partner remote. Skipping the order... - sale.order.id: {} - remote data: {}'.format(saleOrderId, resPartner_remote))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to validate res.partner remote.')
                continue
            self.debugLogger.debug('Successful to validate res.partner remote. - saleOrderId: {}'.format(saleOrderId))

            # update dictionaries res.partner
            self.debugLogger.debug('Trying to update dictionaries res.partner... - saleOrderId: {}'.format(saleOrderId))
            try:
                resPartnerDict = resPartner_remote
            except Exception as e:
                self.debugLogger.exception('Failed to update dictionaries LAYER2 res.partner. Skipping the order... error: {}'.format(e))
                self.errorLogger.error('Failed to update dictionaries LAYER2 res.partner. Skipping the order... error: {}'.format(e))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to update dictionaries LAYER2 res.partner.')
                continue
            self.debugLogger.debug('Successful to update dictionaries res.partner. - saleOrderId: {}'.format(saleOrderId))

            # prepare lists for next layer
            product_ids = list()
            for stockMove in stockMoveDict.values():
                product_ids.append(stockMove['product_id'])

            #LAYER3

            # retrieve product.productS
            self.debugLogger.debug('Trying to retreive product.productS... - saleOrderId: {}'.format(saleOrderId))
            productProductS_remote, isSucceed_pullFromOdoo = self.pullFromOdoo(self.models, self.uid, 'product.product', product_ids, [f for f in self.productProduct_fields])
            if not isSucceed_pullFromOdoo:
                self.debugLogger.error('Caching new order failed when trying to pull product.productS data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.errorLogger.error('Caching new order failed when trying to pull product.productS data from odoo. Skipping the order... - saleOrderId - {}'.format(saleOrderId))
                self.orderOnHoldEvent(saleOrderId, -1, 'Caching new order failed when trying to pull product.product data from odoo.')
                continue
            self.debugLogger.debug('Successful to retrieve product.productS remote. - saleOrderId: {}'.format(saleOrderId))

            # validate product.productS
            self.debugLogger.debug('Trying to validate product.productS remote... - saleOrderId: {}'.format(saleOrderId))
            isEndedNormally = False
            for product in productProductS_remote:
                if type(product['x_studio_pickingorder']) == type(0) and type(product['name']) == type('') and product['name'] != '':
                    pass
                else:
                    self.debugLogger.error('Failed to validate product.productS remote. Skipping the order... - sale.order.id: {} - remote data: {}'.format(saleOrderId, productProductS_remote))
                    self.errorLogger.error('Failed to validate product.productS remote. Skipping the order... - sale.order.id: {} - remote data: {}'.format(saleOrderId, productProductS_remote))
                    self.orderOnHoldEvent(saleOrderId, -1, 'Failed to validate product.product remote.')
                    break
                isEndedNormally = True
            if not isEndedNormally: continue
            self.debugLogger.debug('Successful to validate product.productS remote. - saleOrderId: {}'.format(saleOrderId))

            # update dictionaries product.productS
            self.debugLogger.debug('Trying to update dictionaries product.productS... - saleOrderId: {}'.format(saleOrderId))
            productProductDict = dict()
            try:
                for product in productProductS_remote:
                    productProductDict[str(product['id'])] = {'barcode': product['barcode'], 'x_studio_pickingorder': product['x_studio_pickingorder'], 'name': product['name']}
            except Exception as e:
                self.debugLogger.exception('Failed to update dictionaries LAYER3 product.productS. Skipping the order... error: {}'.format(e))
                self.errorLogger.error('Failed to update dictionaries LAYER3 product.productS. Skipping the order... error: {}'.format(e))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to update dictionaries LAYER3 product.product.')
                continue
            self.debugLogger.debug('Successful to update dictionaries product.productS. - saleOrderId: {}'.format(saleOrderId))

            #CREATE SUMMARY
            try:
                summaryDict = {'saleOrder': {'id': saleOrderDict['id'], '__last_update': saleOrderDict['__last_update'], 'stockPicking': {}, 'accountInvoice': {}}}
                for picking_id, picking in stockPickingDict.items():
                    summaryDict['saleOrder']['stockPicking'][picking_id] = {'message_ids': picking['message_ids'], '__last_update': picking['__last_update'], 'resPartner': {'id': resPartnerDict['id'], '__last_update': resPartnerDict['__last_update']}, 'stockMove': {}}
                    for stockMove_id in picking['move_lines']:
                        summaryDict['saleOrder']['stockPicking'][picking_id]['stockMove'][str(stockMove_id)] = {'product_id': stockMoveDict[str(stockMove_id)]['product_id'], '__last_update': stockMoveDict[str(stockMove_id)]['__last_update']}
                for invoice_id, invoice in accountInvoiceDict.items():
                    summaryDict['saleOrder']['accountInvoice'][str(invoice_id)] = {'__last_update': invoice['__last_update']}
            except Exception as e:
                self.debugLogger.exception('Failed to create summary. Skipping the order... error: {}'.format(e))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to create summary.')
                self.errorLogger.error('Failed to create summary. Skipping the order... error: {}'.format(e))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to create summary.')
                continue
            self.debugLogger.debug('Successful to create summary. - saleOrderId: {}'.format(saleOrderId))

            #DOWNLOAD INVOICES
            try:
                for invoice_id in accountInvoiceDict.keys():
                        if not os.path.exists(self.invoiceFolder) : os.makedirs(self.invoiceFolder)
                        path = '{}{}-{}.pdf'.format(self.invoiceFolder, saleOrderDict['id'], invoice_id)
                        report = self.odoo.report.download('studio_customization1_reports.studio_report_docume_b9c2842a-57de-4007-8b22-4367c48fab53_copy_1', [int(invoice_id)])
                        with open(path, 'wb') as report_file:
                            report_file.write(report.read())
            except Exception as e:
                self.debugLogger.exception('Failed to download invoices. Skipping the order... error: {}'.format(e))
                self.errorLogger.error('Failed to download invoices. Skipping the order... error: {}'.format(e))
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to download invoices.')
                continue
            self.debugLogger.debug('Successful to download invoices. - saleOrderId: {}'.format(saleOrderId))

            # ODOO --> WMS transformation
            self.debugLogger.debug('ODOO --> WMS transformstion...')
            if not len(stockPickingDict) == 1 and len(accountInvoice) == 1 and len(saleOrderDict['invoice_ids']) == 1 and os.path.isfile('{}{}-{}.pdf'.format(self.invoiceFolder, saleOrderDict['id'], saleOrderDict['invoice_ids'][0])):
                self.orderOnHoldEvent(saleOrderId, -1, 'Failed to validate ODOO --> WMS transformstion.')

            productLines = list()
            for move in stockMoveDict.values() : productLines.append({'name': productProductDict[str(move['product_id'])]['name'], 'quantity': move['product_uom_qty'], 'location': productProductDict[str(move['product_id'])]['x_studio_pickingorder'], 'barcode': productProductDict[str(move['product_id'])]['barcode'], 'size': -1 })
            shippingInformation = {'name': resPartnerDict['name'], 'wk_company': resPartnerDict['wk_company'], 'street': resPartnerDict['street'], 'zip': resPartnerDict['zip'], 'city': resPartnerDict['city']}
            invoicePath = '{}{}-{}.pdf'.format(self.invoiceFolder, saleOrderDict['id'], saleOrderDict['invoice_ids'][0])
            order = {'productLines': productLines, 'shippingInformation': shippingInformation, 'invoice': invoicePath, 'remoteId': saleOrderDict['id']}
            self.debugLogger.debug('ODOO --> WMS transformstion Successful')

            #PREPARE STRINGS
            self.debugLogger.debug('Trying to prepare strings...')
            try:
                summaryStr = json.dumps(summaryDict)
                saleOrderStr = json.dumps(saleOrderDict)
                stockPickingStr = json.dumps(stockPickingDict)
                stockmoveStr = json.dumps(stockMoveDict)
                productProductStr = json.dumps(productProductDict)
                resPartnerStr = json.dumps(resPartnerDict)
                accountInvoiceStr = json.dumps(accountInvoiceDict)
            except Exception as e:
                self.debugLogger.exception('Section prepare strings failed! - error: {}'.format(e))
                self.errorLogger.error('Section prepare strings failed! - error: {}'.format(e))
                self.orderOnHoldEvent(saleOrderId, -1, 'Section prepare strings failed!')
                continue
            self.debugLogger.debug('Strings are prepared.')

            #INSERT NEW ORDER
            self.debugLogger.debug('Trying to insert new order data...')
            try:
                conn = mysql.connector.connect(host=self.db_host, user=self.db_user, password=self.db_pass, db=self.db_db)
                cur = conn.cursor()
                cur.execute('INSERT INTO {} (saleOrder, stockPicking, resPartner, accountInvoice, stockMove, productProduct, summary) VALUES (%s, %s, %s, %s, %s, %s, %s)'.format(self.cacheTable), (saleOrderStr, stockPickingStr, resPartnerStr, accountInvoiceStr, stockmoveStr, productProductStr, summaryStr))
                cacheId = cur.lastrowid
                conn.commit()
            except Exception as e:
                self.debugLogger.exception('Section insert new order failed! - error: {}'.format(e))
                self.errorLogger.error('Section insert new order failed! - error: {}'.format(e))
                self.orderOnHoldEvent(saleOrderId, -1, 'Section insert new order failed!')
                continue
            finally:
                conn.close()
            self.debugLogger.debug('New order data inserted successfully. - caheId: {}'.format(cacheId))

            #APPEND SUMMARY
            self.debugLogger.debug('Trying to append summary...')
            self.orderSummaries[str(cacheId)] = summaryDict
            self.debugLogger.debug('Summary appended successfully.')

            # checkin message
            try : self.postMessage(cacheId, 'WMS: Check In')
            except Exception as e:
                self.debugLogger.exception('deleteOrder - Failed to post checkin message! - error: {}'.format(e))
                self.errorLogger.error('deleteOrder - Failed to post checkin message! - error: {}'.format(e))

            #CREATE EVENTS
            self.debugLogger.debug('Trying to create new order and new message events...')
            eventsOfOrder = dict()
            for event in self.openEvents.values():
                    if event['cacheId'] == cacheId : eventsOfOrder.append(event)
            isSucceed_createEvent, isNewEventCreated = self.createEvent(cacheId, 6, 'ERPNewOrder', order, eventsOfOrder)
            for message in mailMessageDict.values():
                if message['body'].startswith('<p>$'):
                    isSucceed_createEvent2, isNewEventCreated2 = self.createEvent(cacheId, 4, 'ERPNewCommand', {'time': message['date'], 'author': message['author_id'][1], 'command': message['body']}, eventsOfOrder)
                else:
                    isSucceed_createEvent2, isNewEventCreated2 = self.createEvent(cacheId, 4, 'ERPNewMessage', {'time': message['date'], 'author': message['author_id'][1], 'message': message['body']}, eventsOfOrder)
                if not isSucceed_createEvent2 : break
            if isSucceed_createEvent and isSucceed_createEvent2 : self.debugLogger.info('New order data cached successfully. cacheId: {} - saleOrderId: {}'.format(cacheId, saleOrderId))
            else:
                self.debugLogger.error('Something went wrong when trying to create new order event. cacheId: {} - saleOrderId - {}'.format(cacheId, saleOrderId))
                self.errorLogger.error('Something went wrong when trying to create new order event. cacheId: {} - saleOrderId - {}'.format(cacheId, saleOrderId))
                self.orderOnHoldEvent(saleOrderId, cacheId, 'Something went wrong when trying to create new order event.')
        
            time.sleep(float(self.endpointCycleTime)/10)

    else : self.debugLogger.info('There are no new orders.')

    self.debugLogger.debug('Region completed. - Cache new orders.')