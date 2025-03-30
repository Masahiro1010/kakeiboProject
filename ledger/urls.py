from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('template/connection/', views.TemplateItemConnectionView.as_view(), name='templateitem_connection'),
    path('template/create/', views.TemplateItemCreateView.as_view(), name='templateitem_create'),
    path('record/connection/', views.RecordConnectionView.as_view(), name='record_connection'),
    path('record/create/', views.RecordCreateView.as_view(), name='record_create'),
    path('record/from-template/', views.TemplateToRecordView.as_view(), name='record_from_template'),
    path('record/list/', views.RecordListView.as_view(), name='record_list'),
    path('record/<int:pk>/edit/', views.RecordUpdateView.as_view(), name='record_edit'),
    path('record/<int:pk>/delete/', views.RecordDeleteView.as_view(), name='record_delete'),
    path('record/summary/', views.MonthlySummaryView.as_view(), name='monthly_summary'),
    path('chart/', views.ChartView.as_view(), name='chart'),
]

