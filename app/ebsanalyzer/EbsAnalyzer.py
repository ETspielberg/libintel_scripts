import math
from statistics import mean


class EbsAnalyzer(object):

    def __init__(self, ebs_mode):
        self._method = getattr(self, ebs_mode, lambda: 0)

    def make_selection(self, ebs_limit, ebs_titles):
        return self._method(ebs_limit=ebs_limit, ebs_titles=ebs_titles)

    def only_usage(self, ebs_limit, ebs_titles):
        self.set_bools_usage_for_cost_limit(ebs_titles, ebs_limit)
        return self.get_price_for_selection(ebs_titles)

    def only_cost_per_usage(self, ebs_limit, ebs_titles):
        self.set_bools_cost_per_usage_for_cost_limit(ebs_titles, ebs_limit)
        return self.get_price_for_selection(ebs_titles)

    def price_normalized_percentiles(self, ebs_titles, ebs_limit):
        print(ebs_limit)
        virtual_limit = 1.5 * ebs_limit
        self.set_bools_usage_for_cost_limit(ebs_titles, virtual_limit)
        self.set_bools_cost_per_usage_for_cost_limit(ebs_titles, virtual_limit)
        price_selected = self.get_price_for_selection(ebs_titles)
        step_differ = True
        n_cycles = 0
        while step_differ:
            n_cycles += 1
            difference = price_selected - ebs_limit
            virtual_limit -= difference * 0.8
            old_selected_sum = price_selected
            self.set_bools_usage_for_cost_limit(ebs_titles, virtual_limit)
            self.set_bools_cost_per_usage_for_cost_limit(ebs_titles, virtual_limit)
            price_selected = self.get_price_for_selection(ebs_titles)
            if (price_selected - old_selected_sum) == 0:
                step_differ = False
            if n_cycles == 100:
                step_differ = False
        return price_selected

    def percentage_normalized_percentiles(self, ebs_titles, ebs_limit):
        mean_price = mean(title.price for title in ebs_titles)
        number = ebs_limit // mean_price
        self.make_selection_for_usage_with_threshold(ebs_titles, number)
        self.make_selection_for_cost_per_usage_with_threshold(ebs_titles, number)
        price_selected = self.get_price_for_selection(ebs_titles)
        step_differ = True
        n_cycles = 0
        while step_differ:
            n_cycles += 1
            old_selected_sum = price_selected
            if price_selected != 0:
                fraction = float((price_selected - ebs_limit)) / float(price_selected)
            else:
                fraction = 2
            number = number * (1 - fraction)
            self.make_selection_for_usage_with_threshold(ebs_titles, int(number))
            self.make_selection_for_cost_per_usage_with_threshold(ebs_titles, int(number))
            price_selected = self.get_price_for_selection(ebs_titles)
            print(price_selected)
            if (price_selected - old_selected_sum) == 0:
                step_differ = False
            if n_cycles == 100:
                step_differ = False
        return price_selected

    def usage_normalized_percentiles(self, ebs_titles, ebs_limit):
        mean_usage = mean(title.total_usage for title in ebs_titles)
        mean_price = mean(title.price for title in ebs_titles)
        usage_threshold = int(ebs_limit / mean_price * mean_usage)
        self.set_bools_usage_for_usage_limit(ebs_titles, usage_threshold)
        self.set_bools_cost_per_usage_for_usage_limit(ebs_titles, usage_threshold)
        price_selected = self.get_price_for_selection(ebs_titles)
        print(price_selected)
        step_differ = True
        n_cycles = 0
        while step_differ:
            n_cycles += 1
            old_selected_sum = price_selected
            if price_selected != 0:
                fraction = float((price_selected - ebs_limit)) / (8 * ebs_limit)
            else:
                fraction = 2
            usage_threshold = usage_threshold * (1 - fraction)
            self.set_bools_usage_for_usage_limit(ebs_titles, usage_threshold)
            self.set_bools_cost_per_usage_for_usage_limit(ebs_titles, usage_threshold)
            price_selected = self.get_price_for_selection(ebs_titles)
            print(price_selected)
            if (price_selected - old_selected_sum) == 0:
                step_differ = False
            if n_cycles == 100:
                step_differ = False
        return price_selected

    def index(self, ebs_titles, ebs_limit):
        self.set_position_for_usage(ebs_titles)
        self.set_position_for_cost_per_usage(ebs_titles)
        return self.get_price_for_list_with_factor(ebs_titles, ebs_limit)

    def index_weighting(self, ebs_titles, ebs_limit):
        self.set_weighting_for_position_usage(ebs_titles)
        self.set_weighting_for_position_cost_per_usage(ebs_titles)
        return self.get_price_for_list_with_weighting(ebs_titles, ebs_limit)

    def value_weighting(self, ebs_titles, ebs_limit):
        self.set_weighting_for_usage(ebs_titles)
        self.set_weighting_for_cost_per_usage(ebs_titles)
        return self.get_price_for_list_with_weighting(ebs_titles, ebs_limit)

    def index_weighting_exponential(self, ebs_titles, ebs_limit):
        self.set_exponential_weighting_for_position_usage(ebs_titles)
        self.set_exponential_weighting_for_position_cost_per_usage(ebs_titles)
        return self.get_price_for_list_with_weighting(ebs_titles, ebs_limit)

    def value_weighting_exponential(self, ebs_titles, ebs_limit):
        self.set_exponential_weighting_for_usage(ebs_titles)
        self.set_exponential_weighting_for_cost_per_usage(ebs_titles)
        return self.get_price_for_list_with_weighting(ebs_titles, ebs_limit)

    def set_bools_usage_for_cost_limit(self, ebs_titles, cost_limit):
        total_sum = 0
        ebs_titles.sort(key=lambda x: x.total_usage, reverse=True)
        for title in ebs_titles:
            total_sum += title.price
            title.selection_usage = (total_sum < cost_limit)

    def set_bools_cost_per_usage_for_cost_limit(self, ebs_titles, cost_limit):
        total_sum = 0
        ebs_titles.sort(key=lambda x: x.cost_per_usage, reverse=False)
        for title in ebs_titles:
            total_sum += title.price
            title.selection_cost_per_usage = (total_sum < cost_limit)

    def set_bools_usage_for_usage_limit(self, ebs_titles, usage_limit):
        total_sum = 0
        ebs_titles.sort(key=lambda x: x.total_usage, reverse=True)
        for title in ebs_titles:
            total_sum += title.total_usage
            title.selection_usage = (total_sum < usage_limit)

    def set_bools_cost_per_usage_for_usage_limit(self, ebs_titles, usage_limit):
        total_sum = 0
        ebs_titles.sort(key=lambda x: x.cost_per_usage, reverse=False)
        for title in ebs_titles:
            total_sum += title.total_usage
            title.selection_cost_per_usage = (total_sum < usage_limit)

    def set_position_for_usage(self, ebs_titles):
        ebs_titles.sort(key=lambda x: x.total_usage, reverse=True)
        for idx, val in enumerate(ebs_titles):
            val.weighting_factor += idx

    def set_position_for_cost_per_usage(self, ebs_titles):
        ebs_titles.sort(key=lambda x: x.cost_per_usage, reverse=False)
        for idx, val in enumerate(ebs_titles):
            val.weighting_factor += idx

    def set_weighting_for_usage(self, ebs_titles):
        max_usage = max(title.total_usage for title in ebs_titles)
        for title in ebs_titles:
            title.weighting_factor = title.weighting_factor * title.total_usage / max_usage

    def set_weighting_for_cost_per_usage(self, ebs_titles):
        max_cost_per_usage = max(title.cost_per_usage for title in ebs_titles)
        for title in ebs_titles:
            title.weighting_factor = title.weighting_factor * float(
                max_cost_per_usage - title.cost_per_usage) / max_cost_per_usage

    def set_weighting_for_position_usage(self, ebs_titles):
        ebs_titles.sort(key=lambda x: x.total_usage, reverse=False)
        for idx, val in enumerate(ebs_titles):
            val.weighting_factor = val.weighting_factor * float(idx - 1) / ebs_titles.__len__()

    def set_weighting_for_position_cost_per_usage(self, ebs_titles):
        ebs_titles.sort(key=lambda x: x.cost_per_usage, reverse=True)
        for idx, val in enumerate(ebs_titles):
            val.weighting_factor = val.weighting_factor * float(idx - 1) / ebs_titles.__len__()

    def set_exponential_weighting_for_usage(self, ebs_titles):
        mean_usage = mean(title.total_usage for title in ebs_titles)
        for title in ebs_titles:
            title.weighting_factor = title.weighting_factor * math.exp(
                float(title.total_usage - mean_usage) / mean_usage)

    def set_exponential_weighting_for_cost_per_usage(self, ebs_titles):
        mean_cost_per_usage = mean(title.cost_per_usage for title in ebs_titles)
        for title in ebs_titles:
            title.weighting_factor = title.weighting_factor * math.exp(-title.cost_per_usage / mean_cost_per_usage)

    def set_exponential_weighting_for_position_usage(self, ebs_titles):
        ebs_titles.sort(key=lambda x: x.total_usage, reverse=True)
        for idx, val in enumerate(ebs_titles):
            val.weighting_factor = val.weighting_factor * math.exp(-float(idx - 1) / ebs_titles.__len__())

    def set_exponential_weighting_for_position_cost_per_usage(self, ebs_titles):
        ebs_titles.sort(key=lambda x: x.cost_per_usage, reverse=False)
        for idx, val in enumerate(ebs_titles):
            val.weighting_factor = val.weighting_factor * math.exp(-float(idx - 1) / ebs_titles.__len__())

    def make_selection_for_usage_with_threshold(self, ebs_titles, threshold):
        total_sum = 0
        ebs_titles.sort(key=lambda x: x.total_usage, reverse=True)
        for idx, val in enumerate(ebs_titles):
            if idx < threshold:
                val.selection_usage = True
                total_sum += val.price
            else:
                val.selection_usage = False
        return total_sum

    def make_selection_for_cost_per_usage_with_threshold(self, ebs_titles, threshold):
        total_sum = 0
        ebs_titles.sort(key=lambda x: x.cost_per_usage, reverse=False)
        for idx, val in enumerate(ebs_titles):
            if idx < threshold:
                val.selection_cost_per_usage = True
                total_sum += val.price
            else:
                val.selection = False
        return total_sum

    def get_price_for_selection(self, ebs_titles):
        total_sum = 0
        for title in ebs_titles:
            title.selected = title.selection_cost_per_usage and title.selection_usage
            if title.selected:
                total_sum += title.price
        return total_sum

    def get_price_for_list_with_weighting(self, ebs_titles, limit):
        total_sum = 0
        ebs_titles.sort(key=lambda x: x.weighting_factor, reverse=True)
        for title in ebs_titles:
            if total_sum < limit:
                total_sum += title.price
                title.selected = True
            else:
                title.selected = False
        return total_sum

    def get_price_for_list_with_factor(self, ebs_titles, limit):
        total_sum = 0
        ebs_titles.sort(key=lambda x: x.weighting_factor, reverse=False)
        for title in ebs_titles:
            if total_sum < limit:
                total_sum += title.price
                title.selected = True
            else:
                title.selected = False
        return total_sum
