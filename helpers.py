import json
import math
from decimal import Decimal

import pytz

from datetime import datetime, date, timedelta, time

from django.db.models import Min, Max
from django.utils import timezone

from diners.models import AccessLog, Diner
from kitchen.models import Warehouse, ProcessedProduct, WarehouseDetails
from products.models import Supply, Cartridge, PackageCartridge, CartridgeRecipe, PackageCartridgeRecipe, \
    ExtraIngredient
from sales.models import Ticket, TicketDetail, TicketExtraIngredient


class Helper(object):
    def __init__(self):
        self.tz = pytz.timezone('America/Mexico_City')
        self.days_dict = {
            'MONDAY': 'Lunes',
            'TUESDAY': 'Martes',
            'WEDNESDAY': 'Miércoles',
            'THURSDAY': 'Jueves',
            'FRIDAY': 'Viernes',
            'SATURDAY': 'Sábado',
            'SUNDAY': 'Domingo'
        }
        self.number_days_dict = {
            'Lunes': 0,
            'Martes': 1,
            'Miércoles': 2,
            'Jueves': 3,
            'Viernes': 4,
            'Sábado': 5,
            'Domingo': 6,
        }
        super(Helper, self).__init__()

    def naive_to_datetime(self, nd):
        if type(nd) == datetime:
            if nd.tzinfo is not None and nd.tzinfo.utcoffset(nd) is not None:  # Is Aware
                return nd
            else:  # Is Naive
                return self.tz.localize(nd)

        elif type(nd) == date:
            d = nd
            t = time(0, 0)
            new_date = datetime.combine(d, t)
            return self.tz.localize(new_date)

    def get_name_day(self, datetime_now):
        name_day = date(datetime_now.year, datetime_now.month, datetime_now.day)
        return self.days_dict[name_day.strftime('%A').upper()]

    def get_number_day(self, dt):
        return self.number_days_dict[self.get_name_day(dt)]

    def start_datetime(self, back_days):
        start_date = date.today() - timedelta(days=back_days)
        return self.naive_to_datetime(start_date)

    def end_datetime(self, back_days):
        end_date = self.start_datetime(back_days) + timedelta(days=1)
        return self.naive_to_datetime(end_date)

    def parse_to_datetime(self, dt):
        day = int(dt.split('-')[0])
        month = int(dt.split('-')[1])
        year = int(dt.split('-')[2])
        parse_date = date(year, month, day)
        return self.naive_to_datetime(parse_date)

    def are_equal_lists(self, list_1, list_2):
        """
         Checks if two lists are identical
        """
        list_1 = self.items_list_to_int(list_1)
        list_2 = self.items_list_to_int(list_2)

        list_1.sort()
        list_2.sort()

        if len(list_1) != len(list_2):
            return False
        else:
            for element in range(0, len(list_1)):
                if list_1[element] != list_2[element]:
                    return False

        return True

    @staticmethod
    def get_week_number(dt):
        return dt.isocalendar()[1]

    @staticmethod
    def items_list_to_int(list_to_cast):
        """
        Evaluates each of the elements of the list received and casts them to integers
        """
        cast_list = []
        for item in range(0, len(list_to_cast)):
            cast_list.append(int(list_to_cast[item]))

        return cast_list


class LeastSquares(object):
    def __init__(self, x: list, y: list):
        super(LeastSquares, self).__init__()
        if len(x) != len(y):
            raise NameError('Las listas deben tener misma longitud.')

        self.__x = x
        self.__y = y
        self.__periodic_list = []
        self.__n = len(self.__x)
        self.set_periodic_list()

    def get_sum_x(self):
        return sum(self.__x)

    def get_sum_y(self):
        return sum(self.__y)

    def get_x_average(self):
        return math.ceil(self.get_sum_x() / len(self.__x))

    def get_y_average(self):
        return math.ceil(self.get_sum_y() / len(self.__y))

    def get_sum_x_pow(self):
        auxiliary_list = []
        count = 0

        for _ in self.__x:
            auxiliary_list.append(self.__x[count] ** 2)
            count += 1
        return sum(auxiliary_list)

    def get_sum_y_pow(self):
        auxiliary_list = []
        count = 0

        for _ in self.__y:
            auxiliary_list.append(self.__y[count] ** 2)
            count += 1
        return sum(auxiliary_list)

    def get_sum_x_y_prod(self):
        count = 0
        auxiliary_list = []

        for _ in self.__x:
            auxiliary_list.append(self.__x[count] * self.__y[count])
            count += 1

        return sum(auxiliary_list)

    def set_periodic_list(self):
        difference_list = []
        count = 0
        is_periodic = True

        for _ in self.__x:
            if count != 0:
                difference_list.append(self.__x[count] - self.__x[count - 1])

            count += 1

        count = 0

        for _ in difference_list:
            if count != 0:
                if difference_list[count] != difference_list[count - 1]:
                    is_periodic = False
                    break
            count += 1

        if is_periodic:
            count = 0
            periodic_value = difference_list[0]

            for _ in self.__x:
                self.__periodic_list.append(self.__x[len(self.__x) - 1] + periodic_value * (count + 1))
                count += 1
        else:
            raise NameError('Tu lista de Periodo no es continua')

    def get_a(self):
        return math.ceil(self.get_y_average() - self.get_b() * self.get_x_average())

    def get_b(self):
        return math.ceil((self.get_sum_x_y_prod() - (self.get_sum_x() * self.get_sum_y() / self.__n)) / (
            self.get_sum_x_pow() - (self.get_sum_x() ** 2) / self.__n))

    def get_forecast(self):
        forecast_list = []
        count = 0

        for _ in self.__x:
            forecast_list.append(self.get_a() + self.get_b() * self.__periodic_list[count])
            count += 1

        return forecast_list


class KitchenHelper(object):
    def __init__(self):
        super(KitchenHelper, self).__init__()
        self.__all_processed_products = None
        self.__all_warehouse = None

    def get_all_processed_products(self):
        if self.__all_processed_products is None:
            self.set_all_processed_products()
        return self.__all_processed_products

    def get_all_warehouse(self):
        if self.__all_warehouse is None:
            self.set_all_processed_products()
        return self.__all_warehouse

    def get_processed_products(self):
        processed_products_list = []
        sales_helper = SalesHelper()
        products_helper = ProductsHelper()

        for processed in self.get_all_processed_products().filter(status='PE')[:15]:
            processed_product_object = {
                'ticket_id': processed.ticket,
                'cartridges': [],
                'packages': [],
                'ticket_order': processed.ticket.order_number
            }

            for ticket_detail in sales_helper.get_all_tickets_details():
                if ticket_detail.ticket == processed.ticket:
                    if ticket_detail.cartridge:
                        cartridge = {
                            'quantity': ticket_detail.quantity,
                            'cartridge': ticket_detail.cartridge,
                        }
                        for extra_ingredient in sales_helper.get_all_extra_ingredients():
                            if extra_ingredient.ticket_detail == ticket_detail:
                                try:
                                    cartridge['name'] += extra_ingredient['extra_ingredient']
                                except Exception as e:
                                    cartridge['name'] = ticket_detail.cartridge.name
                                    cartridge['name'] += ' con ' + extra_ingredient.extra_ingredient.ingredient.name
                        processed_product_object['cartridges'].append(cartridge)

                    elif ticket_detail.package_cartridge:
                        package = {
                            'quantity': ticket_detail.quantity,
                            'package_recipe': []
                        }
                        package_recipe = products_helper.get_all_packages_cartridges_recipes().filter(
                            package_cartridge=ticket_detail.package_cartridge)

                        for recipe in package_recipe:
                            package['package_recipe'].append(recipe.cartridge)
                        processed_product_object['packages'].append(package)

            processed_products_list.append(processed_product_object)
        return processed_products_list

    def set_all_warehouse(self):
        self.__all_warehouse = Warehouse.objects.select_related('supply').all()

    def set_all_processed_products(self):
        self.__all_processed_products = ProcessedProduct.objects. \
            select_related('ticket'). \
            all()


class SalesHelper(object):
    def __init__(self):
        self.__all_tickets = None
        self.__all_tickets_details = None
        self.__all_extra_ingredients = None
        super(SalesHelper, self).__init__()

    def set_all_tickets(self):
        self.__all_tickets = Ticket.objects.select_related('seller').all()

    def set_all_tickets_details(self):
        self.__all_tickets_details = TicketDetail.objects. \
            select_related('ticket'). \
            select_related('cartridge'). \
            select_related('ticket__seller'). \
            select_related('package_cartridge'). \
            all()

    def set_all_extra_ingredients(self):
        self.__all_extra_ingredients = TicketExtraIngredient.objects. \
            select_related('ticket_detail'). \
            select_related('extra_ingredient'). \
            select_related('extra_ingredient__ingredient'). \
            all()

    def get_all_tickets(self):
        """
        :rtype: django.db.models.query.QuerySet
        """
        if self.__all_tickets is None:
            self.set_all_tickets()
        return self.__all_tickets

    def get_all_tickets_details(self):
        """
        :rtype: django.db.models.query.QuerySet
        """
        if self.__all_tickets_details is None:
            self.set_all_tickets_details()
        return self.__all_tickets_details

    def get_tickets_details(self, initial_date, final_date):
        """
        :rtype: django.db.models.query.QuerySet
        """
        if self.__all_tickets_details is None:
            self.set_all_tickets_details()
        return self.__all_tickets_details.filter(ticket__created_at__range=[initial_date, final_date])

    def get_all_extra_ingredients(self):
        """
        :rtype: django.db.models.query.QuerySet
        """
        if self.__all_extra_ingredients is None:
            self.set_all_extra_ingredients()
        return self.__all_extra_ingredients

    def get_years_list(self):
        """
        Returns a list of all the years in which there have been sales
        """
        years_list = []

        for ticket in self.get_all_tickets():
            if ticket.created_at.year not in years_list:
                years_list.append(ticket.created_at.year)

        return years_list

    def get_tickets_today_list(self):
        helper = Helper()

        tickets_list = []
        filtered_tickets = self.get_all_tickets().filter(created_at__gte=helper.naive_to_datetime(date.today()))

        for ticket in filtered_tickets:
            ticket_object = {
                'ticket_parent': ticket,
                'order_number': ticket.order_number,
                'cartridges': [],
                'packages': [],
                'total': Decimal(0.00),
            }

            for ticket_details in self.get_all_tickets_details():
                if ticket_details.ticket == ticket:
                    if ticket_details.cartridge:
                        cartridge_object = {
                            'cartridge': ticket_details.cartridge,
                            'quantity': ticket_details.quantity
                        }
                        ticket_object['cartridges'].append(cartridge_object)
                        ticket_object['total'] += ticket_details.price
                    elif ticket_details.package_cartridge:
                        package_cartridge_object = {
                            'package': ticket_details.package_cartridge,
                            'quantity': ticket_details.quantity
                        }
                        ticket_object['packages'].append(package_cartridge_object)
                        ticket_object['total'] += ticket_details.price

            tickets_list.append(ticket_object)

        return tickets_list

    def get_dates_range_json(self):
        """
        Returns a JSON with a years list.
        The years list contains years objects that contains a weeks list
            and the Weeks list contains a weeks objects with two attributes: 
            start date and final date. Ranges of each week.
        """
        helper = Helper()
        try:
            min_year = self.get_all_tickets().aggregate(Min('created_at'))['created_at__min'].year
            max_year = self.get_all_tickets().aggregate(Max('created_at'))['created_at__max'].year
            years_list = []  # [2015:object, 2016:object, 2017:object, ...]
        except:
            min_year = datetime.now().year
            max_year = datetime.now().year
            years_list = []  # [2015:object, 2016:object, 2017:object, ...]

        while max_year >= min_year:
            year_object = {  # 2015:object or 2016:object or 2017:object ...
                'year': max_year,
                'weeks_list': [],
            }

            tickets_per_year = self.get_all_tickets().filter(
                created_at__range=[helper.naive_to_datetime(date(max_year, 1, 1)),
                                   helper.naive_to_datetime(date(max_year, 12, 31))])
            for ticket_item in tickets_per_year:
                if len(year_object['weeks_list']) == 0:
                    """
                    Creates a new week_object in the weeks_list of the actual year_object
                    """
                    week_object = {
                        'week_number': ticket_item.created_at.isocalendar()[1],
                        'start_date': ticket_item.created_at.date().strftime("%d-%m-%Y"),
                        'end_date': ticket_item.created_at.date().strftime("%d-%m-%Y"),
                    }
                    year_object['weeks_list'].append(week_object)
                    # End if
                else:
                    """
                    Validates if exists some week with an similar week_number of the actual year
                    If exists a same week in the list validates the start_date and the end_date,
                    In each case valid if there is an older start date or a more current end date 
                        if it is the case, update the values.
                    Else creates a new week_object with the required week number
                    """
                    existing_week = False
                    for week_object in year_object['weeks_list']:

                        if week_object['week_number'] == ticket_item.created_at.isocalendar()[1]:
                            # There's a same week number
                            if datetime.strptime(week_object['start_date'],
                                                 "%d-%m-%Y").date() > ticket_item.created_at.date():
                                week_object['start_date'] = ticket_item.created_at.date().strftime("%d-%m-%Y")
                            elif datetime.strptime(week_object['end_date'],
                                                   "%d-%m-%Y").date() < ticket_item.created_at.date():
                                week_object['end_date'] = ticket_item.created_at.date().strftime("%d-%m-%Y")

                            existing_week = True
                            break

                    if not existing_week:
                        # There's a different week number
                        week_object = {
                            'week_number': ticket_item.created_at.isocalendar()[1],
                            'start_date': ticket_item.created_at.date().strftime("%d-%m-%Y"),
                            'end_date': ticket_item.created_at.date().strftime("%d-%m-%Y"),
                        }
                        year_object['weeks_list'].append(week_object)

                        # End else
            years_list.append(year_object)
            max_year -= 1
        # End while
        return json.dumps(years_list)

    def get_sales_list(self, start_dt, final_dt):
        """
        Gets the following properties for each week's day: Name, Date and Earnings
        """
        helper = Helper()
        limit_day = start_dt + timedelta(days=1)
        total_days = (final_dt - start_dt).days
        week_sales_list = []
        count = 1
        total_earnings = 0

        while count <= total_days:
            day_tickets = self.get_all_tickets().filter(created_at__range=[start_dt, limit_day])
            day_object = {
                'date': str(start_dt.date().strftime('%d-%m-%Y')),
                'day_name': None,
                'earnings': None,
                'number_day': helper.get_number_day(start_dt),
            }

            for ticket_item in day_tickets:
                for ticket_detail_item in self.get_all_tickets_details():
                    if ticket_detail_item.ticket == ticket_item:
                        total_earnings += ticket_detail_item.price

            day_object['day_name'] = helper.get_name_day(start_dt.date())
            day_object['earnings'] = str(total_earnings)

            week_sales_list.append(day_object)

            # Reset data
            limit_day += timedelta(days=1)
            start_dt += timedelta(days=1)
            total_earnings = 0
            count += 1

        return week_sales_list

    def get_sales_actual_week(self):
        """
        Gets the following properties for each week's day: Name, Date and Earnings
        """
        helper = Helper()
        week_sales_list = []
        total_earnings = 0
        days_to_count = helper.get_number_day(datetime.now())
        day_limit = days_to_count
        start_date_number = 0

        while start_date_number <= day_limit:
            day_object = {
                'date': str(helper.start_datetime(days_to_count).date().strftime('%d-%m-%Y')),
                'day_name': None,
                'earnings': None,
                'number_day': helper.get_number_day(helper.start_datetime(days_to_count).date()),
            }

            day_tickets = self.get_all_tickets().filter(
                created_at__range=[helper.start_datetime(days_to_count), helper.end_datetime(days_to_count)])

            for ticket_item in day_tickets:
                for ticket_detail_item in self.get_all_tickets_details():
                    if ticket_detail_item.ticket == ticket_item:
                        total_earnings += ticket_detail_item.price

            day_object['earnings'] = str(total_earnings)
            day_object['day_name'] = helper.get_name_day(helper.start_datetime(days_to_count).date())

            week_sales_list.append(day_object)

            # restarting counters
            days_to_count -= 1
            total_earnings = 0
            start_date_number += 1

        return json.dumps(week_sales_list)

    def get_tickets_list(self, initial_date, final_date):
        """
        :rtype: list
        :param initial_date: datetime 
        :param final_date: datetime
        """
        all_tickets = self.get_all_tickets().filter(
            created_at__range=(initial_date, final_date)).order_by('-created_at')
        all_tickets_details = self.get_all_tickets_details()
        tickets_list = []

        for ticket in all_tickets:
            ticket_object = {
                'id': ticket.id,
                'order_number': ticket.order_number,
                'created_at': datetime.strftime(ticket.created_at, "%B %d, %Y, %H:%M:%S %p"),
                'seller': ticket.seller.username,
                'ticket_details': {
                    'cartridges': [],
                    'packages': [],
                },
                'total': 0,
            }

            for ticket_detail in all_tickets_details:
                if ticket_detail.ticket == ticket:
                    ticket_detail_object = {}
                    if ticket_detail.cartridge:
                        ticket_detail_object = {
                            'name': ticket_detail.cartridge.name,
                            'quantity': ticket_detail.quantity,
                            'price': float(ticket_detail.price),
                        }
                        ticket_object['ticket_details']['cartridges'].append(ticket_detail_object)
                    elif ticket_detail.package_cartridge:
                        ticket_detail_object = {
                            'name': ticket_detail.package_cartridge.name,
                            'quantity': ticket_detail.quantity,
                            'price': float(ticket_detail.price),
                        }
                        ticket_object['ticket_details']['packages'].append(ticket_detail_object)

                    ticket_object['total'] += float(ticket_detail.price)

                    try:
                        ticket_object['ticket_details'].append(ticket_detail_object)
                    except Exception as e:
                        pass
            ticket_object['total'] = str(ticket_object['total'])
            tickets_list.append(ticket_object)
        return tickets_list


class ProductsHelper(object):
    def __init__(self):
        super(ProductsHelper, self).__init__()
        self.__all_cartridges = None
        self.__all_packages_cartridges = None
        self.__all_supplies = None
        self.__all_extra_ingredients = None
        self.__all_cartridges_recipes = None
        self.__all_tickets_details = None
        self.__elements_in_warehouse = None
        self.__all_warehouse_details = None
        self.__predictions = None
        self.__required_supplies_list = None
        self.__today_popular_cartridge = None
        self.__all_packages_cartridges_recipes = None
        self.__always_popular_cartridge = None

    def set_all_supplies(self):
        self.__all_supplies = Supply.objects. \
            select_related('category'). \
            select_related('supplier'). \
            select_related('location').all()

    def set_all_cartridges(self):
        self.__all_cartridges = Cartridge.objects.all()

    def set_all_packages_cartridges(self):
        self.__all_packages_cartridges = PackageCartridge.objects.all()

    def set_all_cartridges_recipes(self):
        self.__all_cartridges_recipes = CartridgeRecipe.objects. \
            select_related('cartridge'). \
            select_related('supply'). \
            all()

    def set_all_package_cartridges_recipes(self):
        self.__all_packages_cartridges_recipes = PackageCartridgeRecipe.objects. \
            select_related('package_cartridge'). \
            select_related('cartridge'). \
            all()

    def set_all_extra_ingredients(self):
        self.__all_extra_ingredients = ExtraIngredient.objects. \
            select_related('ingredient'). \
            select_related('cartridge'). \
            all()

    def set_all_warehouse_details(self):
        self.__all_warehouse_details = WarehouseDetails.objects.prefetch_related('warehouse__supply').all()

    def set_predictions(self):
        sales_helper = SalesHelper()
        all_tickets_details = sales_helper.get_all_tickets_details()

        prediction_list = []

        for ticket_details in all_tickets_details:
            cartridge_object = {
                'cartridge': ticket_details.cartridge,
                'cantidad': 1,
            }

            prediction_list.append(cartridge_object)

        self.__predictions = prediction_list

    def set_all_tickets_details(self):
        self.__all_tickets_details = TicketDetail.objects.select_related(
            'ticket').select_related('cartridge').select_related('package_cartridge').all()

    def set_always_popular_cartridge(self):
        sales_helper = SalesHelper()
        cartridges_frequency_dict = {}
        for cartridge in self.get_all_cartridges():
            cartridges_frequency_dict[cartridge.id] = {
                'frequency': 0,
                'name': cartridge.name,
            }
        for ticket_detail in sales_helper.get_all_tickets_details():
            if ticket_detail.cartridge:
                ticket_detail_id = ticket_detail.cartridge.id
                ticket_detail_frequency = ticket_detail.quantity
                cartridges_frequency_dict[ticket_detail_id]['frequency'] += ticket_detail_frequency

        for element in cartridges_frequency_dict:
            if self.__always_popular_cartridge is None:
                """ Base case """
                self.__always_popular_cartridge = {
                    'id': element,
                    'name': cartridges_frequency_dict[element]['name'],
                    'frequency': cartridges_frequency_dict[element]['frequency'],
                }
            else:
                if cartridges_frequency_dict[element]['frequency'] > self.__always_popular_cartridge['frequency']:
                    self.__always_popular_cartridge = {
                        'id': element,
                        'name': cartridges_frequency_dict[element]['name'],
                        'frequency': cartridges_frequency_dict[element]['frequency'],
                    }

    def set_elements_in_warehouse(self):
        self.__elements_in_warehouse = Warehouse.objects.select_related('supply').all()

    def set_today_popular_cartridge(self):
        sales_helper = SalesHelper()
        cartridges_frequency_dict = {}
        helper = Helper()
        start_date = helper.naive_to_datetime(date.today())
        limit_day = helper.naive_to_datetime(start_date + timedelta(days=1))
        filtered_ticket_details = sales_helper.get_tickets_details(start_date, limit_day)

        for cartridge in self.get_all_cartridges():
            cartridges_frequency_dict[cartridge.id] = {
                'frequency': 0,
                'name': cartridge.name,
            }

        for ticket_detail in filtered_ticket_details:
            if ticket_detail.cartridge:
                ticket_detail_id = ticket_detail.cartridge.id
                ticket_detail_frequency = ticket_detail.quantity
                cartridges_frequency_dict[ticket_detail_id]['frequency'] += ticket_detail_frequency

        for element in cartridges_frequency_dict:
            if self.__today_popular_cartridge is None:
                """ Base case """
                self.__today_popular_cartridge = {
                    'id': element,
                    'name': cartridges_frequency_dict[element]['name'],
                    'frequency': cartridges_frequency_dict[element]['frequency'],
                }
            else:
                if cartridges_frequency_dict[element]['frequency'] > self.__today_popular_cartridge['frequency']:
                    self.__today_popular_cartridge = {
                        'id': element,
                        'name': cartridges_frequency_dict[element]['name'],
                        'frequency': cartridges_frequency_dict[element]['frequency'],
                    }

    def get_all_supplies(self):
        """
        :rtype: django.db.models.query.QuerySet
        """
        if self.__all_supplies is None:
            self.set_all_supplies()
        return self.__all_supplies

    def get_all_cartridges(self):
        """
        :rtype: django.db.models.query.QuerySet
        """
        if self.__all_cartridges is None:
            self.set_all_cartridges()
        return self.__all_cartridges

    def get_all_packages_cartridges(self):
        """
        :rtype: django.db.models.query.QuerySet
        """
        if self.__all_packages_cartridges is None:
            self.set_all_packages_cartridges()
        return self.__all_packages_cartridges

    def get_all_extra_ingredients(self):
        """
        :rtype: django.db.models.query.QuerySet
        """
        if self.__all_extra_ingredients is None:
            self.set_all_extra_ingredients()

        return self.__all_extra_ingredients

    def get_all_cartridges_recipes(self):
        """
        :rtype: django.db.models.query.QuerySet
        """
        if self.__all_cartridges_recipes is None:
            self.set_all_cartridges_recipes()

        return self.__all_cartridges_recipes

    def get_all_packages_cartridges_recipes(self):
        """
        :rtype: django.db.models.query.QuerySet
        """
        if self.__all_packages_cartridges_recipes is None:
            self.set_all_package_cartridges_recipes()

        return self.__all_packages_cartridges_recipes

    def get_all_warehouse_details(self):
        """
        :rtype: django.db.models.query.QuerySet
        """
        if self.__all_warehouse_details is None:
            self.set_all_warehouse_details()
        return self.__all_warehouse_details

    def get_required_supplies(self):
        """
        :rtype: list 
        """
        required_supplies_list = []
        all_cartridges = self.get_all_cartridges()
        predictions = self.get_predictions_supplies()
        supplies_on_stock = self.get_all_warehouse_details().filter(status="ST")

        ingredients = self.get_all_cartridges_recipes()

        for prediction in predictions:
            for cartridge in all_cartridges:
                if prediction['cartridge'] == cartridge:

                    ingredients = ingredients.filter(cartridge=cartridge)
                    for ingredient in ingredients:
                        supply = ingredient.supply
                        name = ingredient.supply.name
                        cost = ingredient.supply.presentation_cost
                        measurement = ingredient.supply.measurement_unit
                        measurement_quantity = ingredient.supply.measurement_quantity
                        quantity = ingredient.quantity

                        count = 0

                        required_supply_object = {
                            'supply': supply,
                            'name': name,
                            'cost': cost,
                            'measurement': measurement,
                            'measurement_quantity': measurement_quantity,
                            'quantity': quantity,
                            'stock': 0,
                            'required': 0,
                            'full_cost': 0,
                        }

                        if len(required_supplies_list) == 0:
                            count = 1
                        else:
                            for required_supplies in required_supplies_list:
                                if required_supplies['name'] == name:
                                    required_supplies['quantity'] += quantity
                                    count = 0
                                    break
                                else:
                                    count = 1
                        if count == 1:
                            required_supplies_list.append(required_supply_object)

        for required_supply in required_supplies_list:
            if len(supplies_on_stock) > 0:
                for supply_on_stock in supplies_on_stock:
                    if supply_on_stock.warehouse.supply == required_supply['supply']:
                        required_supply['stock'] = supply_on_stock.quantity
                        required_supply['required'] = max(0, required_supply['quantity'] - required_supply['stock'])
                        required_supply['full_cost'] = \
                            required_supply['cost'] * \
                            math.ceil(required_supply['required'] / required_supply['measurement_quantity'])
                        break
                    else:
                        required_supply['required'] = max(0, required_supply['quantity'] - required_supply['stock'])
                        required_supply['full_cost'] = \
                            required_supply['cost'] * \
                            math.ceil(required_supply['required'] / required_supply['measurement_quantity'])
                        required_supply['full_cost'] = \
                            required_supply['cost'] * \
                            math.ceil(required_supply['required'] / required_supply['measurement_quantity'])

            else:
                required_supply['required'] = max(0, required_supply['quantity'] - required_supply['stock'])
                required_supply['full_cost'] = \
                    required_supply['cost'] * \
                    math.ceil(required_supply['required'] / required_supply['measurement_quantity'])

        return required_supplies_list

    def get_always_popular_cartridge(self):
        """ 
        :rtype: django.db.models.query.QuerySet 
        """
        if self.__always_popular_cartridge is None:
            self.set_always_popular_cartridge()
        return self.__always_popular_cartridge

    def get_predictions_supplies(self):
        """ :rtype: list """
        if self.__predictions is None:
            self.set_predictions()
        return self.__predictions

    def get_supplies_on_stock_list(self):
        """ :rtype: list """
        stock_list = []
        all_elements = self.__elements_in_warehouse.filter(status='ST')
        if all_elements.count() > 0:
            for element in all_elements:
                stock_object = {
                    'name': element.supply.name,
                    'quantity': element.quantity,
                }
                stock_list.append(stock_object)

        return stock_list

    def get_today_popular_cartridge(self):
        if self.__today_popular_cartridge is None:
            self.set_today_popular_cartridge()
        return self.__always_popular_cartridge


class DinersHelper(object):
    def __init__(self):
        self.__all_diners = None
        self.__all_access_logs = None
        super(DinersHelper, self).__init__()

    def get_all_diners_logs_list(self, initial_date, final_date):
        helper = Helper()
        diners_logs_list = []

        diners_logs_objects = self.get_access_logs(initial_date, final_date)

        for diner_log in diners_logs_objects:
            diner_log_object = {
                'rfid': diner_log.RFID,
                'access': datetime.strftime(timezone.localtime(diner_log.access_to_room), "%B %d, %I, %H:%M:%S %p"),
                'number_day': helper.get_number_day(diner_log.access_to_room),
            }
            if diner_log.diner:
                diner_log_object['SAP'] = diner_log.diner.employee_number
                diner_log_object['name'] = diner_log.diner.name
            else:
                diner_log_object['SAP'] = ''
                diner_log_object['name'] = ''
            diners_logs_list.append(diner_log_object)
        return diners_logs_list

    def get_weeks_entries(self, initial_dt, final_dt):
        """
        Gets the following properties for each week's day: Name, Date and Earnings
        """
        if self.__all_access_logs is None:
            self.set_all_access_logs()

        helper = Helper()
        limit_day = initial_dt + timedelta(days=1)
        weeks_list = []
        count = 1
        total_days = (final_dt - initial_dt).days

        while count <= total_days:
            diners_entries = self.__all_access_logs.filter(access_to_room__range=[initial_dt, limit_day])
            day_object = {
                'date': str(timezone.localtime(initial_dt).date().strftime('%d-%m-%Y')),
                'day_name': helper.get_name_day(initial_dt.date()), 'entries': diners_entries.count(),
                'number_day': helper.get_number_day(initial_dt)}

            weeks_list.append(day_object)

            # Reset data
            limit_day += timedelta(days=1)
            initial_dt += timedelta(days=1)
            count += 1

        return weeks_list

    def get_access_logs(self, initial_date, final_date):
        if self.__all_access_logs is None:
            self.set_all_access_logs()

        return self.__all_access_logs. \
            filter(access_to_room__range=(initial_date, final_date)). \
            order_by('-access_to_room')

    def get_access_logs_today(self):
        if self.__all_access_logs is None:
            self.set_all_access_logs()
        helper = Helper()
        year = int(datetime.now().year)
        month = int(datetime.now().month)
        day = int(datetime.now().day)
        initial_date = helper.naive_to_datetime(date(year, month, day))
        final_date = helper.naive_to_datetime(initial_date + timedelta(days=1))
        return self.__all_access_logs. \
            filter(access_to_room__range=(initial_date, final_date)). \
            order_by('-access_to_room')

    def get_all_access_logs(self):
        if self.__all_access_logs is None:
            self.set_all_access_logs()
        return self.__all_access_logs

    def get_diners_per_hour_json(self):
        hours_list = []
        hours_to_count = 12
        start_hour = 5
        customer_count = 0
        logs = self.get_access_logs_today()

        while start_hour <= hours_to_count:
            hour = {'count': None, }
            for log in logs:
                log_datetime = str(log.access_to_room)
                log_date, log_time = log_datetime.split(" ")

                if log_time.startswith("0" + str(start_hour)):
                    customer_count += 1
                hour['count'] = customer_count

            hours_list.append(hour)
            customer_count = 0
            start_hour += 1

        return json.dumps(hours_list)

    def get_diners_actual_week(self):
        if self.__all_access_logs is None:
            self.set_all_access_logs()
        helper = Helper()
        week_diners_list = []
        total_entries = 0
        days_to_count = helper.get_number_day(date.today())
        day_limit = days_to_count
        start_date_number = 0

        while start_date_number <= day_limit:
            day_object = {
                'date': str(helper.start_datetime(days_to_count).date().strftime('%d-%m-%Y')),
                'day_name': None,
                'entries': None,
                'number_day': helper.get_number_day(helper.start_datetime(days_to_count).date())
            }

            logs = self.__all_access_logs. \
                filter(access_to_room__range=[helper.start_datetime(days_to_count), helper.end_datetime(days_to_count)])

            for _ in logs:
                total_entries += 1

            day_object['entries'] = str(total_entries)
            day_object['day_name'] = helper.get_name_day(helper.start_datetime(days_to_count).date())

            week_diners_list.append(day_object)

            # restarting counters
            days_to_count -= 1
            total_entries = 0
            start_date_number += 1

        return json.dumps(week_diners_list)

    def get_all_diners(self):
        if self.__all_diners is None:
            self.set_all_diners()
        return self.__all_diners

    def set_all_access_logs(self):
        self.__all_access_logs = AccessLog.objects.select_related('diner').order_by('-access_to_room')

    def set_all_diners(self):
        self.__all_diners = Diner.objects.all()
