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

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'ledger/home.html'

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
    
class RecordConnectionView(LoginRequiredMixin, TemplateView):
    template_name = 'ledger/record_connection.html'
    
class RecordCreateView(LoginRequiredMixin, CreateView):
    model = Record
    fields = ['title', 'amount', 'item_type', 'receipt_image']
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

        # Record モデルに保存
        Record.objects.create(
            user=self.request.user,
            title=f"{template.name} * {quantity}",
            amount=template.price * quantity,
            item_type=template.item_type,
        )

        return super().form_valid(form)
    
class RecordListView(LoginRequiredMixin, ListView):
    model = Record
    template_name = 'ledger/record_list.html'
    context_object_name = 'records'

    def get_queryset(self):
        return Record.objects.filter(user=self.request.user).order_by('-date')
    
class RecordUpdateView(LoginRequiredMixin, UpdateView):
    model = Record
    fields = ['title', 'amount', 'item_type', 'receipt_image']
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