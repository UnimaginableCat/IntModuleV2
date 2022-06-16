import retailcrm

from Main.models import ZoneSmartProduct, ZoneSmartListing


class RetailCRMHelper:
    def __init__(self):
        self.address = None
        self.api_key = None
        self.client = None

    def init_and_setup(self, address, api_key):
        self.address = address
        self.api_key = api_key
        self.client = retailcrm.v5(self.address, self.api_key)

    def get_product_quantity(self, product_id):
        product_filter = {
            'ids': product_id
        }

        total_count = self.client.inventories(product_filter).get_response()['pagination']['totalCount']

        if total_count != 0:
            offers_query = self.client.inventories(product_filter, 20, 1).get_response()
            offer = offers_query['offers']
            quantity = offer[0]['quantity']
            return True, quantity
        else:
            return False, 0

    def get_offer_price(self, offer_id):
        product_filter = {
            'offerIds': [offer_id]
        }
        total_count = self.client.products(product_filter).get_response()['pagination']['totalCount']
        if total_count != 0:
            total_page_count = self.client.products(product_filter).get_response()['pagination']['totalPageCount']
            for i in range(1, total_page_count + 1):
                products_query = self.client.products(product_filter, 20, i).get_response()['products']

                for product in products_query:
                    for offer in product['offers']:
                        price = offer['prices'][0]['price']
                        return price


    def get_products(self, access_token, dict_groups, active=0, min_quantity=0, groups=None, ):
        if groups is None:
            groups = []
        if not groups:
            product_filter = {
                'active': active,
                'minQuantity': min_quantity,
            }
        else:
            product_filter = {
                'active': active,
                'minQuantity': min_quantity,
                'groups': groups,
            }
        products = []
        total_count = self.client.products(product_filter).get_response()['pagination']['totalCount']
        if total_count != 0:
            total_page_count = self.client.products(product_filter).get_response()['pagination']['totalPageCount']
            # test = self.client.products(product_filter).get_response()
            # print(test)

            for i in range(1, total_page_count + 1):
                products_query = self.client.products(product_filter, 20, i).get_response()['products']

                for product in products_query:

                    offers = []
                    images = None
                    for offer in product['offers']:
                        images = offer.get('images')
                        new_offer = ZoneSmartProduct(offer.get('id'),
                                                     offer.get('quantity'),
                                                     offer.get('price'),
                                                     offer.get('barcode'),
                                                     product.get('imageUrl'),
                                                     images,
                                                     access_token,
                                                     offer.get('properties'))
                        offers.append(new_offer)

                    new_listing = ZoneSmartListing(product.get('name'),
                                                   product.get('description'),
                                                   product.get('id'),
                                                   product['groups'][0]['externalId'],
                                                   dict_groups.get(product['groups'][0]['id']),
                                                   product.get('manufacturer'),
                                                   offers,
                                                   product.get('imageUrl'),
                                                   images,
                                                   access_token)
                    products.append(new_listing)
        return products

    def get_product_groups(self):
        groups = dict()

        groups_filter = {'active': 1}

        total_page_count = self.client.product_groups(groups_filter).get_response()['pagination']['totalPageCount']
        for i in range(1, total_page_count + 1):
            group_query = self.client.product_groups(groups_filter, 20, i).get_response()['productGroup']
            for group in group_query:
                groups[group['id']] = group['name']
        tuple_groups = [(k, v) for k, v in groups.items()]
        # Возвращаем группы в нужном виде, и в виде Dict
        return tuple_groups, groups