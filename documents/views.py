from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib import messages
from hub.models import Job
from .models import Document
from .forms import DocumentUploadForm, DocumentStatusForm
from django.views import View
from django.shortcuts import redirect
from .forms import CandidateApplyForm
from django.views.generic import FormView, DetailView



class DocumentListView(LoginRequiredMixin, ListView):
    '''
    Task 4.4.1: List documents for a specific job, ensuring ownership.
    '''
    model = Document
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'

    def get_queryset(self):
        # Securely fetch the job or 404 if it doesn't belong to the user
        self.job = get_object_or_404(
            Job, 
            pk=self.kwargs['job_pk'], 
            user=self.request.user
        )
        return Document.objects.filter(job=self.job)

    def get_context_data(self, **kwargs):
        # Task 4.4.2: Inject job object into context for the template header
        context = super().get_context_data(**kwargs)
        context['job'] = self.job
        return context

class DocumentUploadView(LoginRequiredMixin, CreateView):
    '''
    Task 4.4.3: Handle PDF resume uploads for a specific job.
    '''
    model = Document
    form_class = DocumentUploadForm
    template_name = 'documents/document_upload.html'

    def dispatch(self, request, *args, **kwargs):
        # Task 4.4.5: Pre-validation of job ownership before processing the request
        self.job = get_object_or_404(
            Job, 
            pk=self.kwargs['job_pk'], 
            user=self.request.user
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = self.job  # Isso envia a vaga para o template
        return context

    def form_valid(self, form):
        form.instance.job = self.job
        messages.success(self.request, 'O currículo foi enviado e está pronto para análise.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('document-list', kwargs={'job_pk': self.job.pk})



    def form_valid(self, form):
        # Task 4.4.4: Link the document to the job identified in the URL
        form.instance.job = self.job
        messages.success(self.request, 'O currículo foi enviado e está pronto para análise.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('document-list', kwargs={'job_pk': self.job.pk})

class DocumentStatusUpdateView(LoginRequiredMixin, View):
    '''
    Atualiza o status de triagem de um documento via POST e redireciona
    de volta para a lista de documentos da vaga.
    '''

    def post(self, request, pk):
        document = get_object_or_404(
            Document,
            pk=pk,
            job__user=request.user,
        )
        new_status = request.POST.get('status', '')
        valid_statuses = ['pending', 'reviewing', 'approved', 'rejected']

        if new_status in valid_statuses:
            document.status = new_status
            document.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Status atualizado com sucesso.')
        else:
            messages.error(request, 'Status inválido.')

        return redirect('document-list', job_pk=document.job.pk)
    

class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    '''
    Task 4.4.8: Remove a candidate document.
    '''
    model = Document
    template_name = 'documents/document_confirm_delete.html'

    def get_queryset(self):
        # Task 4.4.9: Security check to prevent deleting documents from other users
        return Document.objects.filter(job__user=self.request.user)

    def get_success_url(self):
        job_pk = self.object.job.pk
        messages.success(self.request, 'Registro do candidato removido do sistema.')
        return reverse('document-list', kwargs={'job_pk': job_pk})
    
class PublicApplyView(FormView):
    template_name = 'documents/public_apply.html'
    form_class = CandidateApplyForm

    def dispatch(self, request, *args, **kwargs):
        # Busca a vaga pelo token público. Se não existir, dá 404.
        self.job = get_object_or_404(Job, public_token=self.kwargs['token'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = self.job # Passa os dados da vaga para o candidato ler
        return context

    def form_valid(self, form):
        # Vincula o currículo à vaga encontrada pelo token
        form.instance.job = self.job
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        # Redireciona para uma página de sucesso simples
        return reverse('apply-success', kwargs={'token': self.job.public_token})

class PublicSuccessView(DetailView):
    model = Job
    template_name = 'documents/public_success.html'
    slug_field = 'public_token'
    slug_url_kwarg = 'token'
    context_object_name = 'job'