from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.generic import CreateView
from .models import TemplateItem
from .models import Record
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from .forms import TemplateRecordForm
from django.views.generic import ListView
from django.views.generic.edit import UpdateView, DeleteView
from django.core.exceptions import PermissionDenied
from django.utils.timezone import now
from django.db.models import Sum
import calendar
from collections import defaultdict
from django.db.models.functions import TruncMonth
from django.db.models.functions import TruncDate
from datetime import date
from datetime import timedelta
from django.db.models.functions import ExtractMonth, ExtractYear


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'ledger/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = now().date()
        year = today.year
        last_year = year - 1

        # 今年と昨年の全レコードを取得
        records = (
            Record.objects
            .filter(user=user, date__year__in=[last_year, year])
            .annotate(month=ExtractMonth('date'), year=ExtractYear('date'))
            .values('year', 'month', 'item_type')
            .annotate(total=Sum('amount'))
            .order_by('year', 'month')
        )

        def init_month_data():
            return {m: 0 for m in range(1, 13)}

        income_this_year = init_month_data()
        expense_this_year = init_month_data()
        income_last_year = init_month_data()
        expense_last_year = init_month_data()

        for r in records:
            y, m, t = r['year'], r['month'], r['item_type']
            if y == year:
                if t == 'income':
                    income_this_year[m] = r['total']
                else:
                    expense_this_year[m] = r['total']
            elif y == last_year:
                if t == 'income':
                    income_last_year[m] = r['total']
                else:
                    expense_last_year[m] = r['total']

        labels_ym = [f'{m}月' for m in range(1, 13)]

        context.update({
            'labels_yearly': labels_ym,
            'income_this_year': list(income_this_year.values()),
            'income_last_year': list(income_last_year.values()),
            'expense_this_year': list(expense_this_year.values()),
            'expense_last_year': list(expense_last_year.values()),
        })

        # 今月と先月の比較データ（短期用）
        first_day_this_month = today.replace(day=1)
        first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)

        # 表示する2つの月ラベル（例：['2024-03', '2024-04']）
        labels = [
            first_day_last_month.strftime('%Y-%m'),
            first_day_this_month.strftime('%Y-%m')
        ]

        short_term_data = {m: {'income': 0, 'expense': 0} for m in labels}

        short_term_records = (
            Record.objects
            .filter(user=user, date__gte=first_day_last_month)
            .annotate(month=TruncMonth('date'))
            .values('month', 'item_type')
            .annotate(total=Sum('amount'))
        )

        for r in short_term_records:
            month = r['month'].strftime('%Y-%m')
            if month in short_term_data:
                short_term_data[month][r['item_type']] = r['total']

        context['labels'] = labels
        context['income_data'] = [short_term_data[m]['income'] for m in labels]
        context['expense_data'] = [short_term_data[m]['expense'] for m in labels]

        return context

class TemplateItemConnectionView(LoginRequiredMixin, TemplateView):
    template_name = 'ledger/templateitem_connection.html'

class TemplateItemCreateView(LoginRequiredMixin, CreateView):
    model = TemplateItem
    fields = ['name', 'price', 'item_type']
    template_name = 'ledger/templateitem_form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
class TemplateItemUpdateView(LoginRequiredMixin, UpdateView):
    model = TemplateItem
    fields = ['name', 'price', 'item_type']
    template_name = 'ledger/templateitem_form.html'
    success_url = reverse_lazy('record_list')

    def get_object(self, queryset=None):
        item = super().get_object(queryset)
        if item.user != self.request.user:
            raise PermissionDenied()
        return item

class TemplateItemDeleteView(LoginRequiredMixin, DeleteView):
    model = TemplateItem
    template_name = 'ledger/templateitem_confirm_delete.html'
    success_url = reverse_lazy('record_list')

    def get_object(self, queryset=None):
        item = super().get_object(queryset)
        if item.user != self.request.user:
            raise PermissionDenied()
        return item
    
class RecordConnectionView(LoginRequiredMixin, TemplateView):
    template_name = 'ledger/record_connection.html'
    
class RecordCreateView(LoginRequiredMixin, CreateView):
    model = Record
    fields = ['title', 'amount', 'item_type', 'date', 'receipt_image']
    template_name = 'ledger/record_form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
class TemplateToRecordView(LoginRequiredMixin, FormView):
    template_name = 'ledger/template_to_record_form.html'
    form_class = TemplateRecordForm
    success_url = reverse_lazy('home')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # フォームにログインユーザーを渡す
        return kwargs

    def form_valid(self, form):
        template = form.cleaned_data['template']
        quantity = form.cleaned_data['quantity']
        date = form.cleaned_data['date']  # 日付を取得

        # Record モデルに保存
        Record.objects.create(
            user=self.request.user,
            title=f"{template.name} * {quantity}",
            amount=template.price * quantity,
            item_type=template.item_type,
            date=date  # ← 追加  
        )

        return super().form_valid(form)
    
class RecordListView(LoginRequiredMixin, TemplateView):
    template_name = 'ledger/record_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        view_type = self.request.GET.get('view', 'all')  # ?view=...

        if view_type == 'monthly':
            today = now().date()
            start_date = today.replace(day=1)
            end_day = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=end_day)
            records = Record.objects.filter(user=user, date__range=(start_date, end_date))
            context['current_view'] = 'monthly'
            context['period'] = today.strftime("%Y年%m月")
            records_limited = records

        elif view_type == 'daily':
            today = now().date()
            records = Record.objects.filter(user=user, date=today)
            context['current_view'] = 'daily'
            context['period'] = today.strftime("%Y年%m月%d日")
            records_limited = records

        elif view_type == 'template':
            context['current_view'] = 'template'
            context['period'] = 'テンプレート一覧'
            records_limited = []  # 記録は表示しない

        else:  # all
            records = Record.objects.filter(user=user).order_by('-date')
            records_limited = records[:50]
            context['current_view'] = 'all'
            context['period'] = '最新50件'

        # 合計（テンプレート表示中は0にする）
        if view_type != 'template':
            income_total = records.filter(item_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
            expense_total = records.filter(item_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        else:
            income_total = 0
            expense_total = 0

        # テンプレート一覧は常に渡す（表示はテンプレート内で制御）
        templates = TemplateItem.objects.filter(user=user)

        context.update({
            'records': records_limited,
            'income_total': income_total,
            'expense_total': expense_total,
            'templates': templates,
        })
        return context
    
class RecordUpdateView(LoginRequiredMixin, UpdateView):
    model = Record
    fields = ['title', 'amount', 'item_type', 'date', 'receipt_image']
    template_name = 'ledger/record_form.html'
    success_url = reverse_lazy('record_list')

    def get_object(self, queryset=None):
        record = super().get_object(queryset)
        if record.user != self.request.user:
            raise PermissionDenied()
        return record
    
class RecordDeleteView(LoginRequiredMixin, DeleteView):
    model = Record
    template_name = 'ledger/record_confirm_delete.html'
    success_url = reverse_lazy('record_list')

    def get_object(self, queryset=None):
        record = super().get_object(queryset)
        if record.user != self.request.user:
            raise PermissionDenied()
        return record
    
class MonthlySummaryView(LoginRequiredMixin, TemplateView):
    template_name = 'ledger/monthly_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = now().date()
        user = self.request.user

        # 今月の開始日と終了日
        start_date = today.replace(day=1)
        end_day = calendar.monthrange(today.year, today.month)[1]
        end_date = today.replace(day=end_day)

        # 今月の記録だけフィルタ
        records = Record.objects.filter(user=user, date__range=(start_date, end_date))

        # 収入と支出をそれぞれ集計
        income_total = records.filter(item_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        expense_total = records.filter(item_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

        context['income_total'] = income_total
        context['expense_total'] = expense_total
        context['records'] = records
        context['month'] = today.strftime("%Y年%m月")

        return context
    
class ChartView(LoginRequiredMixin, TemplateView):
    template_name = 'ledger/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 月単位でまとめて集計
        records = (
            Record.objects
            .filter(user=user)
            .annotate(month=TruncMonth('date'))
            .values('month', 'item_type')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )

        # 月ごとのデータを収入/支出で分けて集計
        data = defaultdict(lambda: {'income': 0, 'expense': 0})
        for record in records:
            month = record['month'].strftime('%Y-%m')
            data[month][record['item_type']] = record['total']

        # Chart.js 用のデータ
        context['labels'] = list(data.keys())
        context['income_data'] = [data[m]['income'] for m in data]
        context['expense_data'] = [data[m]['expense'] for m in data]

        return context
    
class ChartDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'ledger/chart_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        view_type = self.request.GET.get('view', 'all')
        today = now().date()

        if view_type == 'monthly':
            start_date = today.replace(day=1)
            end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
            label = today.strftime('%Y年%m月')
        elif view_type == 'daily':
            start_date = end_date = today
            label = today.strftime('%Y年%m月%d日')
        else:
            start_date = None
            end_date = None
            label = '最新50件'

        # データ取得
        if start_date and end_date:
            records = Record.objects.filter(user=user, date__range=(start_date, end_date)).order_by('-date')
        else:
            # スライス前のデータ（集計用）
            records_all = Record.objects.filter(user=user).order_by('-date')
            records = records_all[:50]

        # 集計用：スライス前の records_all または records を使う
        if start_date and end_date:
            records_for_aggregate = records
        else:
            records_for_aggregate = records_all

        income_total = records_for_aggregate.filter(item_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        expense_total = records_for_aggregate.filter(item_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

        context['label'] = label
        context['income_total'] = income_total
        context['expense_total'] = expense_total

        return context
    
class TutorialView(TemplateView):
    template_name = "ledger/tutorial.html"