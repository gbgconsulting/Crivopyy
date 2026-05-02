from django.views.generic import ListView, CreateView, TemplateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone 
from datetime import timedelta 
from django.db.models.functions import TruncDay 
from django.http import JsonResponse


from .models import Job
from .forms import JobForm
from documents.models import Document


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'hub/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Available jobs for the dropdown
        context['available_jobs'] = Job.objects.filter(user=user, status=Job.ACTIVE)

        # General KPIs (Always general as requested)
        context['active_jobs_count'] = Job.objects.filter(user=user, status=Job.ACTIVE).count()
        context['total_documents_count'] = Document.objects.filter(job__user=user).count()
        context['pending_documents_count'] = Document.objects.filter(job__user=user, status='pending').count()
        context['approved_documents_count'] = Document.objects.filter(job__user=user, status='approved').count()

        # Last 6 candidates
        context['recent_documents'] = (
            Document.objects
            .filter(job__user=user)
            .select_related('job')
            .order_by('-created_at')[:6]
        )

        # 1. Pipeline Data (Initial Load - All)
        pipeline_stats = (
            Document.objects.filter(job__user=user)
            .values('status')
            .annotate(total=Count('id'))
        )
        
        status_map = {
            'pending': 'Pendentes', 
            'reviewing': 'Em Análise', 
            'approved': 'Aprovados', 
            'rejected': 'Reprovados'
        }
        
        context['pipeline_labels'] = [status_map.get(s['status'], s['status']) for s in pipeline_stats]
        context['pipeline_values'] = [s['total'] for s in pipeline_stats]

        # 2. Evolution Data (Always General)
        today = timezone.now().replace(hour=23, minute=59, second=59)
        seven_days_ago = (today - timedelta(days=6)).replace(hour=0, minute=0, second=0)
        
        evolution_stats = (
            Document.objects.filter(job__user=user, created_at__gte=seven_days_ago)
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        context['evolution_labels'] = [s['day'].strftime('%d/%m') for s in evolution_stats]
        context['evolution_values'] = [s['count'] for s in evolution_stats]

        return context


class PipelineDataView(LoginRequiredMixin, View):
    '''
    API endpoint to return filtered pipeline data for Chart.js.
    '''
    def get(self, request):
        user = request.user
        job_id = request.GET.get('job')
        
        query = Document.objects.filter(job__user=user)
        if job_id and job_id != 'all':
            query = query.filter(job_id=job_id)
            
        stats = query.values('status').annotate(total=Count('id'))
        
        status_map = {
            'pending': 'Pendentes', 
            'reviewing': 'Em Análise', 
            'approved': 'Aprovados', 
            'rejected': 'Reprovados'
        }
        
        data = {
            'labels': [status_map.get(s['status'], s['status']) for s in stats],
            'values': [s['total'] for s in stats]
        }
        return JsonResponse(data)


class JobListView(LoginRequiredMixin, ListView):
    model = Job
    template_name = 'hub/job_list.html'
    context_object_name = 'jobs'

    def get_queryset(self):
        return Job.objects.filter(user=self.request.user).annotate(
            total_candidates=Count('documents'),
            approved_candidates=Count('documents', filter=Q(documents__status='approved')),
            pending_candidates=Count('documents', filter=Q(documents__status='pending')),
            reviewing_candidates=Count('documents', filter=Q(documents__status='reviewing')),
        )


class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'hub/job_form.html'
    success_url = reverse_lazy('hub:job-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Vaga criada com sucesso!')
        return super().form_valid(form)


class JobUpdateView(LoginRequiredMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'hub/job_form.html'
    success_url = reverse_lazy('hub:job-list')

    def get_queryset(self):
        return Job.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Vaga atualizada com sucesso!')
        return super().form_valid(form)


class JobArchiveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, user=request.user)
        job.status = Job.ARCHIVED
        job.save()
        messages.success(request, f'A vaga "{job.title}" foi arquivada.')
        return redirect('hub:job-list')