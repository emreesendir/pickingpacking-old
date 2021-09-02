import time

def reactChanges(self, changes):

    self.debugLogger.debug('Region is starting - React changes...')
    self.debugLogger.debug('reactChanges - openEvents: {}'.format(self.openEvents))
    for cacheId, changeList in changes.items():
        if len(changeList) > 0 and cacheId in self.orderSummaries:
            self.debugLogger.debug('reactChanges - Trying to understand the changes on order... - cacheId: {} - changeList: {}'.format(cacheId, changeList))

            # evetsOfOrder
            eventsOfOrder = list()
            for event in self.openEvents.values():
                    if event['cacheId'] == int(cacheId) : eventsOfOrder.append(event)
            self.debugLogger.debug('reactChanges - eventsOfOrder: {}'.format(eventsOfOrder))

            # create new events
            for change in changeList:
                indexList = change['index'].split('.')
                self.debugLogger.debug('indexList: {}'.format(indexList))
                indexIgnore = indexList.copy()
                indexIgnore.remove(indexIgnore[-1])
                indexIgnoreStr = indexIgnore[0]
                indexIgnore.remove(indexIgnore[0])
                for i in indexIgnore:  indexIgnoreStr += '.{}'.format(i)

                # sale.order.x_InternalStatus
                if 'x_InternalStatus' in indexList:
                    self.debugLogger.debug('Change found on sale.order.x_InternalStatus')
                    id2 = self.InternalStatus.search([('x_studio_code','=', 'autoprint')])[0]
                    id3 = self.InternalStatus.search([('x_studio_code','=', 'printed')])[0]
                    if id2 in change['removed'] and id3 in change['added']:
                        self.debugLogger.debug('sale.order.x_InternalStatus changed {} --> {}'.format(change['removed'], change['added']))

                        isSucceed_createEvent, isNewEventCreated = self.createEvent(cacheId, 3, 'ERPOrderUpdated', {'event': 'ORDER MARKED'}, eventsOfOrder)
                        if isSucceed_createEvent:
                            if isNewEventCreated : self.debugLogger.info('New Event Created - Section: React to Changes - change: {}'.format(change))
                            else : self.debugLogger.debug('Event Already Exist - change: {}'.format(change, event))
                        else:
                            self.debugLogger.error('Couldn\'t react to change: {}'.format(change))
                            self.errorLogger.error('Couldn\'t react to change: {}'.format(change))
                            self.orderOnHoldEvent(self.orderSummaries[cacheId]['saleOrder']['id'], cacheId, 'Failed to create event! - orderMarked')
                            continue

                    else:
                        self.debugLogger.warning('sale.order.x_InternalStatus changed in a way that I don\'t know how to react. Ignoring Change... - change: {}'.format(change))
                        self.createEvent(cacheId, 4, 'Warning', {'warning': 'sale.order.x_InternalStatus changed in a way that system doesn\'t know how to react. - change: {}'.format(change)}, eventsOfOrder)

                # sale.order.state
                elif change['index'] == 'saleOrder.state':
                    self.debugLogger.debug('Change found on sale.order.state')
                    if change['new'] == 'cancel':
                        self.debugLogger.debug('sale.order.state changed {} --> {}'.format(change['old'], change['new']))

                        isSucceed_createEvent, isNewEventCreated = self.createEvent(cacheId, 5, 'ERPOrderCanceled', {}, eventsOfOrder)
                        if isSucceed_createEvent:
                            if isNewEventCreated : self.debugLogger.info('New Event Created - Section: React to Changes - change: {}'.format(change))
                            else : self.debugLogger.debug('Event Already Exist - change: {}'.format(change, event))
                        else:
                            self.debugLogger.error('Couldn\'t react to change: {}'.format(change))
                            self.errorLogger.error('Couldn\'t react to change: {}'.format(change))
                            self.orderOnHoldEvent(self.orderSummaries[cacheId]['saleOrder']['id'], cacheId, 'Failed to create event! - orderCanceled')
                            continue

                    else:
                        self.debugLogger.warning('sale.order.state changed in a way that I don\'t know how to react. Ignoring change... - change: {}'.format(change))
                        self.createEvent(cacheId, 4, 'Warning', {'warning': 'sale.order.state changed in a way that system doesn\'t know how to react. - change: {}'.format(change)}, eventsOfOrder)

                # stock.picking.carrier_tracking_ref
                elif 'carrier_tracking_ref' in indexList:
                    self.debugLogger.debug('Change found on stock.picking.carrier_tracking_ref')
                    if not change['old'] and type(change['new']) == type('') and change['new'] != '':
                        self.debugLogger.debug('stock.picking.carrier_tracking_ref changed {} --> {}'.format(change['old'], change['new']))

                        isSucceed_createEvent, isNewEventCreated = self.createEvent(cacheId, 5, 'ERPOrderUpdated', {'event': 'ORDER SHIPPED', 'tracking number': change['new']}, eventsOfOrder)
                        if isSucceed_createEvent:
                            if isNewEventCreated : self.debugLogger.info('New Event Created - Section: React to Changes - change: {}'.format(change))
                            else : self.debugLogger.debug('Event Already Exist - change: {}'.format(change, event))
                        else:
                            self.debugLogger.error('Couldn\'t react to change: {}'.format(change))
                            self.errorLogger.error('Couldn\'t react to change: {}'.format(change))
                            self.orderOnHoldEvent(self.orderSummaries[cacheId]['saleOrder']['id'], cacheId, 'Failed to create event! - orderShipped')
                            continue

                    else:
                        self.debugLogger.warning('stock.picking.carrier_tracking_ref changed in a way that I don\'t know how to react - change: {}'.format(change))
                        self.createEvent(cacheId, 4, 'Warning', {'warning': 'stock.picking.carrier_tracking_ref changed in a way that system doesn\'t know how to react. - change: {}'.format(change)}, eventsOfOrder)

                # stock.picking.message_ids
                elif 'message_ids' in indexList:
                    self.debugLogger.debug('Change found on stock.picking.message_ids')
                    if len(change['added']) > 0:
                        self.debugLogger.debug('stock.picking.message_ids changed - added: {}'.format(change['added']))

                        if not self.newMessages(cacheId, change['added'], self.models, self.uid, change['index'].split('.')[2]):
                            self.debugLogger.error('Couldn\'t cache new messages!')
                            self.errorLogger.error('Couldn\'t cache new messages!')
                            self.orderOnHoldEvent(self.orderSummaries[cacheId]['saleOrder']['id'], cacheId, 'Failed to cache new message!')
                            continue
                        else:
                            self.debugLogger.debug('reactChanges - new message function successful.')
                            continue

                    else:
                        self.debugLogger.warning('stock.picking.message_ids changed in a way that I don\'t know how to react - change: {}'.format(change))
                        self.createEvent(cacheId, 4, 'Warning', {'warning': 'stock.picking.message_ids changed in a way that system doesn\'t know how to react. - change: {}'.format(change)}, eventsOfOrder)

                # account.invoice.state
                elif 'accountInvoice' in indexList:
                    self.debugLogger.debug('Change found on account.invoice.state')
                    if change['new'] == 'cancel':
                        self.debugLogger.debug('account.invoice.state changed {} --> {}'.format(change['old'], change['new']))

                        isSucceed_createEvent, isNewEventCreated = self.createEvent(cacheId, 5, 'ERPOrderCanceled', {}, eventsOfOrder)
                        if isSucceed_createEvent:
                            if isNewEventCreated : self.debugLogger.info('New Event Created - Section: React to Changes - change: {}'.format(change))
                            else : self.debugLogger.debug('Event Already Exist - change: {}'.format(change, event))
                        else:
                            self.debugLogger.error('Couldn\'t react to change: {}'.format(change))
                            self.errorLogger.error('Couldn\'t react to change: {}'.format(change))
                            self.orderOnHoldEvent(self.orderSummaries[cacheId]['saleOrder']['id'], cacheId, 'Failed to create event! - orderCanceled')
                            continue

                    else:
                        self.debugLogger.warning('account.invoice.state changed in a way that I don\'t know how to react - change: {}'.format(change))
                        self.createEvent(cacheId, 4, 'Warning', {'warning': 'account.invoice.state changed in a way that system doesn\'t know how to react. - change: {}'.format(change)}, eventsOfOrder)

                # don't know what to do
                else:
                    self.debugLogger.warning('{2} changed. don\'t know what to do. - order id: {0[saleOrder][id]} - data: {1}'.format(self.orderSummaries[cacheId], change, change['index']))
                    self.createEvent(cacheId, 4, 'Warning', {'warning': '{2} changed. don\'t know what to do. - order id: {0[saleOrder][id]} - data: {1}'.format(self.orderSummaries[cacheId], change, change['index'])}, eventsOfOrder)
                
                if self.updateCacheData(cacheId, change) : self.debugLogger.debug('reactChanges - updateCacheData Successful.')
                else:
                    self.debugLogger.error('reactChanges - updateCacheData Failed!')
                    self.errorLogger.error('reactChanges - updateCacheData Failed!')
                    self.orderOnHoldEvent(self.orderSummaries[cacheId]['saleOrder']['id'], cacheId, 'reactChanges - updateCacheData Failed!')

        time.sleep(float(self.endpointCycleTime)/10)

    self.debugLogger.debug('Region completed. - React to changes.')